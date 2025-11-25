# from prometheus_client.core import GaugeMetricFamily

# class UserByRoleNameCollector:
#     def collect(self):
#         from django.db.models import Count
#         from .models import User, Role

#         metric = GaugeMetricFamily(
#             'shop_users_by_roles_name',
#             'Число пользователей по ролям',
#             labels=['roleName']
#         )

#         for row in (User.objects
#                    .select_related('roleId')  
#                    .values('roleId__roleName')  
#                    .annotate(count_user=Count('userId'))):
#             role_name = row['roleId__roleName']
#             metric.add_metric([role_name], float(row['count_user']))

        
#         existing_role_names = {row['roleId__roleName'] 
#                               for row in User.objects
#                               .select_related('roleId')
#                               .values('roleId__roleName')}

        
#         all_roles = Role.objects.all()
#         for role in all_roles:
#             if role.roleName not in existing_role_names:
#                 metric.add_metric([role.roleName], 0.0)

#         yield metric

# class OrdersByPaymentType:
#     def collect(self):
#         from django.db.models import Count
#         from .models import Order

#         metric = GaugeMetricFamily(
#             'shop_orders_by_payment_type',
#             'Число заказов по видам оплаты',
#             labels=['paymentType']
#         )

#         for row in Order.objects.values('paymentType').annotate(count_order=Count('orderId')):
#             metric.add_metric([row['paymentType']], float(row['count_order']))
        
#         existing = {row['paymentType']for row in Order.objects.values('paymentType')}

#         for code, _ in Order.PAYMENT_TYPE_CHOICES:
#             if code not in existing:
#                 metric.add_metric([code], 0.0)     
                    
#         yield metric

# class OrdersDetailedCollector:
#     def collect(self):
#         from django.db.models.functions import ExtractYear, ExtractMonth, ExtractDay
#         from .models import Order
#         from django.db.models import Count

#         metric = GaugeMetricFamily(
#             'shop_orders_detailed',
#             'Детальная информация о заказах',
#             labels=['year', 'month', 'day', 'date']
#         )

#         orders_with_dates = (Order.objects
#                             .annotate(
#                                 year=ExtractYear('createdAt'),
#                                 month=ExtractMonth('createdAt'),
#                                 day=ExtractDay('createdAt')
#                             )
#                             .values('year', 'month', 'day')
#                             .annotate(count=Count('orderId')))

#         for row in orders_with_dates:
#             year = str(row['year'])
#             month = str(row['month']).zfill(2)
#             day = str(row['day']).zfill(2)
#             date_str = f"{year}-{month}-{day}"
            
#             metric.add_metric([year, month, day, date_str], float(row['count']))

#         yield metric

import os
from django.conf import settings
from django.db.models import Count
from django.db.models.functions import ExtractYear, ExtractMonth, ExtractDay
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

class InfluxDBMetrics:
    def __init__(self):
        self.token = getattr(settings, 'INFLUXDB_TOKEN', os.environ.get("INFLUXDB_TOKEN"))
        self.org = "MPT"
        self.url = "http://localhost:8086"
        self.bucket ="metrics"
        
        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
    
    def write_user_metrics_by_role(self):
        from core.models import User, Role
        
        try:
            for row in (User.objects
                       .select_related('roleId')  
                       .values('roleId__roleName')  
                       .annotate(count_user=Count('userId'))):
                role_name = row['roleId__roleName']
                count = float(row['count_user'])
                
                point = (
                    Point("user_metrics")
                    .tag("metric_type", "users_by_role")
                    .tag("role_name", role_name)
                    .field("user_count", count)
                )
                self.write_api.write(bucket=self.bucket, record=point)

            existing_role_names = {row['roleId__roleName'] 
                                  for row in User.objects
                                  .select_related('roleId')
                                  .values('roleId__roleName')}
            
            all_roles = Role.objects.all()
            for role in all_roles:
                if role.roleName not in existing_role_names:
                    point = (
                        Point("user_metrics")
                        .tag("metric_type", "users_by_role")
                        .tag("role_name", role.roleName)
                        .field("user_count", 0.0)
                    )
                    self.write_api.write(bucket=self.bucket, record=point)
                    
            return True
            
        except:
            return False

    def write_orders_by_payment_type(self):
        from core.models import Order
        
        try:
            for row in Order.objects.values('paymentType').annotate(count_order=Count('orderId')):
                payment_type = row['paymentType']
                count = float(row['count_order'])
                
                point = (
                    Point("order_metrics")
                    .tag("metric_type", "orders_by_payment_type")
                    .tag("payment_type", payment_type)
                    .field("order_count", count)
                )
                self.write_api.write(bucket=self.bucket, record=point)

            existing_payment_types = {row['paymentType'] for row in Order.objects.values('paymentType')}
            
            for code, _ in Order.PAYMENT_TYPE_CHOICES:
                if code not in existing_payment_types:
                    point = (
                        Point("order_metrics")
                        .tag("metric_type", "orders_by_payment_type")
                        .tag("payment_type", code)
                        .field("order_count", 0.0)
                    )
                    self.write_api.write(bucket=self.bucket, record=point)
                    
            return True
            
        except:
            return False

    def write_orders_detailed(self):
        from core.models import Order
        
        try:
            orders_with_dates = (Order.objects
                                .annotate(
                                    year=ExtractYear('createdAt'),
                                    month=ExtractMonth('createdAt'),
                                    day=ExtractDay('createdAt')
                                )
                                .values('year', 'month', 'day')
                                .annotate(count=Count('orderId')))

            for row in orders_with_dates:
                year = str(row['year'])
                month = str(row['month']).zfill(2)
                day = str(row['day']).zfill(2)
                date_str = f"{year}-{month}-{day}"
                count = float(row['count'])
                
                point = (
                    Point("order_metrics")
                    .tag("metric_type", "orders_detailed")
                    .tag("year", year)
                    .tag("month", month)
                    .tag("day", day)
                    .tag("date", date_str)
                    .field("order_count", count)
                )
                self.write_api.write(bucket=self.bucket, record=point)
                    
            return True
            
        except:
            return False

    def write_all_metrics(self):
        results = []
        
        results.append(self.write_user_metrics_by_role())
        results.append(self.write_orders_by_payment_type())
        results.append(self.write_orders_detailed())
        
        return all(results)
    
    def close(self):
        self.client.close()