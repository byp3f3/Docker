from .models import Customer

def customer_processor(request):
    context = {}
    if request.user.is_authenticated:
        try:
            context['customer'] = Customer.objects.get(user=request.user)
        except Customer.DoesNotExist:
            context['customer'] = None
        context['is_admin'] = request.user.is_superuser
    else:
        context['customer'] = None
        context['is_admin'] = False
    return context 