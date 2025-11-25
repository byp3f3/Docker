# from django.http import HttpResponse

# def prometheus_metrics_view(_request):
#     from os import getenv
#     from prometheus_client import multiprocess
#     from prometheus_client import CollectorRegistry, CONTENT_TYPE_LATEST, generate_latest, REGISTRY

#     if getenv('PROMETHEUS_MULTIPROC_DIR'):
#         registry = CollectorRegistry()
#         multiprocess.MultiProcessCollector(registry)
#     else:
#         registry = REGISTRY

#     from .metrics import UserByRoleNameCollector, OrdersByPaymentType, OrdersDetailedCollector

#     try:
#         registry.register(UserByRoleNameCollector())
#         registry.register(OrdersByPaymentType())
#         registry.register(OrdersDetailedCollector())
#     except ValueError as e:
#         if 'Duplicated timeseries' not in str(e):
#             raise

#     output = generate_latest(registry)
#     return HttpResponse(output, content_type=CONTENT_TYPE_LATEST)
    
from django.http import JsonResponse
from .metrics import InfluxDBMetrics


def influxdb_metrics_view(_request):
    try:
        metrics_writer = InfluxDBMetrics()
        success = metrics_writer.write_all_metrics()
        metrics_writer.close()
        
        if success:
            return JsonResponse({
                "status": "success",
                "message": "All metrics successfully written",
                "metrics_written": [
                    "users_by_role",
                    "orders_by_payment_type", 
                    "orders_detailed"
                ]
            })
        else:
            return JsonResponse({
                "status": "error",
                "message": "Error"
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Error: {str(e)}"
        }, status=500)