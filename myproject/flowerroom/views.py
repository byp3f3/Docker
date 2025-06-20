from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.models import User
from .models import *
from .forms import *
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
from django.conf import settings

def info_view(request):
    context = {}
    if request.user.is_authenticated:
        try:
            context['customer'] = Customer.objects.get(user=request.user)
        except Customer.DoesNotExist:
            context['customer'] = None
    api_url = request.build_absolute_uri('/api/products/')
    params = {'page': 1, 'page_size': 3, 'ordering': 'name'}
    try:
        api_response = requests.get(api_url, params=params)
        if api_response.status_code == 200:
            main_products = api_response.json().get('results', [])
            for product in main_products:
                product['image_url'] = product.get('image')
            context['main_products'] = main_products
        else:
            context['main_products'] = []
    except Exception:
        context['main_products'] = []
    return render(request, 'info.html', context)


class UserListView(UserPassesTestMixin, ListView):
    template_name = 'user/user_list.html'
    context_object_name = 'users'

    def get_queryset(self):
        api_url = self.request.build_absolute_uri('/api/users/')
        response = requests.get(api_url, cookies=self.request.COOKIES)
        if response.status_code == 200:
            return response.json().get('results', [])
        return []

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')

class UserDetailView(UserPassesTestMixin, DetailView):
    template_name = 'user/user_detail.html'
    context_object_name = 'user'

    def get_object(self):
        user_id = self.kwargs['pk']
        api_url = self.request.build_absolute_uri(f'/api/users/{user_id}/')
        response = requests.get(api_url, cookies=self.request.COOKIES)
        if response.status_code == 200:
            return response.json()
        return None

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')

@user_passes_test(lambda u: u.is_superuser)
def user_create_view(request):
    form = UserForm()
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            api_url = request.build_absolute_uri('/api/users/')
            data = form.cleaned_data
            response = requests.post(api_url, json=data, cookies=request.COOKIES)
            if response.status_code == 201:
                messages.success(request, 'Пользователь успешно создан.')
                return redirect('user_list')
            else:
                messages.error(request, f"Ошибка API: {response.json()}")
    return render(request, 'user/user_form.html', {'form': form})

@user_passes_test(lambda u: u.is_superuser)
def user_update_view(request, pk):
    api_url = request.build_absolute_uri(f'/api/users/{pk}/')
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            response = requests.put(api_url, json=data, cookies=request.COOKIES)
            if response.status_code == 200:
                messages.success(request, 'Пользователь успешно обновлен.')
                return redirect('user_list')
            else:
                messages.error(request, f"Ошибка API: {response.json()}")
    else:
        response = requests.get(api_url, cookies=request.COOKIES)
        if response.status_code == 200:
            form = UserForm(initial=response.json())
        else:
            messages.error(request, 'Не удалось загрузить данные пользователя.')
            return redirect('user_list')
    return render(request, 'user/user_form.html', {'form': form})

@user_passes_test(lambda u: u.is_superuser)
def user_delete_view(request, pk):
    api_url = request.build_absolute_uri(f'/api/users/{pk}/')
    if request.method == 'POST':
        response = requests.delete(api_url, cookies=request.COOKIES)
        if response.status_code == 204:
            messages.success(request, 'Пользователь успешно удален.')
            return redirect('user_list')
        else:
            messages.error(request, 'Ошибка при удалении пользователя.')
            return redirect('user_list')
    
    response = requests.get(api_url, cookies=request.COOKIES)
    if response.status_code == 200:
        user = response.json()
        return render(request, 'user/user_delete.html', {'user': user})
    else:
        messages.error(request, 'Пользователь не найден.')
        return redirect('user_list')

class CustomerListView(UserPassesTestMixin, ListView):
    template_name = 'customer/customer_list.html'
    context_object_name = 'customers'

    def get_queryset(self):
        api_url = self.request.build_absolute_uri('/api/customers/')
        response = requests.get(api_url, cookies=self.request.COOKIES)
        if response.status_code == 200:
            return response.json().get('results', [])
        return []

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')

class CustomerDetailView(UserPassesTestMixin, DetailView):
    template_name = 'customer/customer_detail.html'
    context_object_name = 'customer'

    def get_object(self):
        customer_id = self.kwargs['pk']
        api_url = self.request.build_absolute_uri(f'/api/customers/{customer_id}/')
        response = requests.get(api_url, cookies=self.request.COOKIES)
        if response.status_code == 200:
            return response.json()
        return None

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')

@user_passes_test(lambda u: u.is_superuser)
def customer_create_view(request):
    form = CustomerForm()
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            api_url = request.build_absolute_uri('/api/customers/')
            data = form.cleaned_data
            response = requests.post(api_url, json=data, cookies=request.COOKIES)
            if response.status_code == 201:
                messages.success(request, 'Покупатель успешно создан.')
                return redirect('customer_list')
            else:
                messages.error(request, f"Ошибка API: {response.json()}")
    return render(request, 'customer/customer_form.html', {'form': form})

@user_passes_test(lambda u: u.is_superuser)
def customer_update_view(request, pk):
    api_url = request.build_absolute_uri(f'/api/customers/{pk}/')
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            response = requests.put(api_url, json=data, cookies=request.COOKIES)
            if response.status_code == 200:
                messages.success(request, 'Покупатель успешно обновлен.')
                return redirect('customer_list')
            else:
                messages.error(request, f"Ошибка API: {response.json()}")
    else:
        response = requests.get(api_url, cookies=request.COOKIES)
        if response.status_code == 200:
            form = CustomerForm(initial=response.json())
        else:
            messages.error(request, 'Не удалось загрузить данные покупателя.')
            return redirect('customer_list')
    return render(request, 'customer/customer_form.html', {'form': form})

@user_passes_test(lambda u: u.is_superuser)
def customer_delete_view(request, pk):
    api_url = request.build_absolute_uri(f'/api/customers/{pk}/')
    if request.method == 'POST':
        response = requests.delete(api_url, cookies=request.COOKIES)
        if response.status_code == 204:
            messages.success(request, 'Покупатель успешно удален.')
            return redirect('customer_list')
        else:
            messages.error(request, 'Ошибка при удалении покупателя.')
            return redirect('customer_list')

    response = requests.get(api_url, cookies=request.COOKIES)
    if response.status_code == 200:
        customer = response.json()
        return render(request, 'customer/customer_delete.html', {'customer': customer})
    else:
        messages.error(request, 'Покупатель не найден.')
        return redirect('customer_list')

class ProductListView(UserPassesTestMixin, ListView):
    template_name = 'product/product_list.html'
    context_object_name = 'products'

    def get_queryset(self):
        api_url = self.request.build_absolute_uri('/api/products/')
        response = requests.get(api_url, cookies=self.request.COOKIES)
        if response.status_code == 200:
            return response.json().get('results', [])
        return []

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')

class ProductDetailView(UserPassesTestMixin, DetailView):
    template_name = 'product/product_detail.html'
    context_object_name = 'product'

    def get_object(self):
        product_id = self.kwargs['pk']
        api_url = self.request.build_absolute_uri(f'/api/products/{product_id}/')
        response = requests.get(api_url, cookies=self.request.COOKIES)
        if response.status_code == 200:
            return response.json()
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # The API response is the object
        product = context['object']
        if product:
             # Manually add related data if needed by the template
            context['product'] = product
            # Example for related reviews if API provides them
            # reviews_url = self.request.build_absolute_uri(f'/api/reviews/?product={product["id"]}')
            # reviews_response = requests.get(reviews_url, cookies=self.request.COOKIES)
            # if reviews_response.status_code == 200:
            #     context['reviews'] = reviews_response.json().get('results', [])
        return context

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')

@user_passes_test(lambda u: u.is_superuser)
def product_create_view(request):
    if request.method == 'POST':
        # Manually construct data from request.POST
        data = {
            'name': request.POST.get('name'),
            'description': request.POST.get('description'),
            'price': request.POST.get('price'),
            'category': request.POST.get('category'),
            'stock_quantity': request.POST.get('stock_quantity'),
            # Add other fields as necessary
        }
        api_url = request.build_absolute_uri('/api/products/')
        # Use files=request.FILES if you handle image uploads
        response = requests.post(api_url, data=data, files=request.FILES, cookies=request.COOKIES)
        if response.status_code == 201:
            messages.success(request, 'Товар успешно создан.')
            return redirect('product_list')
        else:
            messages.error(request, f"Ошибка API: {response.text}")
            # Re-render form with posted data and error
            form = ProductForm(request.POST)
            return render(request, 'product/product_form.html', {'form': form})

    form = ProductForm()
    return render(request, 'product/product_form.html', {'form': form})

@user_passes_test(lambda u: u.is_superuser)
def product_update_view(request, pk):
    api_url = request.build_absolute_uri(f'/api/products/{pk}/')
    if request.method == 'POST':
        data = {
            'name': request.POST.get('name'),
            'description': request.POST.get('description'),
            'price': request.POST.get('price'),
            'category': request.POST.get('category'),
            'stock_quantity': request.POST.get('stock_quantity'),
        }
        response = requests.put(api_url, data=data, files=request.FILES, cookies=request.COOKIES)
        if response.status_code == 200:
            messages.success(request, 'Товар успешно обновлен.')
            return redirect('product_list')
        else:
            messages.error(request, f"Ошибка API: {response.text}")
            # Re-render form with posted data and error
            form = ProductForm(request.POST, instance=lambda: None) # Dummy instance
            return render(request, 'product/product_form.html', {'form': form})

    response = requests.get(api_url, cookies=request.COOKIES)
    if response.status_code == 200:
        product_data = response.json()
        form = ProductForm(initial=product_data)
        return render(request, 'product/product_form.html', {'form': form, 'product': product_data})
    else:
        messages.error(request, 'Не удалось загрузить данные товара.')
        return redirect('product_list')

@user_passes_test(lambda u: u.is_superuser)
def product_delete_view(request, pk):
    api_url = request.build_absolute_uri(f'/api/products/{pk}/')
    if request.method == 'POST':
        response = requests.delete(api_url, cookies=request.COOKIES)
        if response.status_code == 204:
            messages.success(request, 'Товар успешно удален.')
            return redirect('product_list')
        else:
            messages.error(request, f"Ошибка при удалении товара: {response.text}")
            return redirect('product_list')
    
    response = requests.get(api_url, cookies=request.COOKIES)
    if response.status_code == 200:
        product = response.json()
        return render(request, 'product/product_delete.html', {'product': product})
    else:
        messages.error(request, 'Товар не найден.')
        return redirect('product_list')

class PlantListView(UserPassesTestMixin, ListView):
    template_name = 'plant/plant_list.html'
    context_object_name = 'plants'

    def get_queryset(self):
        api_url = self.request.build_absolute_uri('/api/plants/')
        response = requests.get(api_url, cookies=self.request.COOKIES)
        if response.status_code == 200:
            return response.json().get('results', [])
        return []

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')

class PlantDetailView(UserPassesTestMixin, DetailView):
    template_name = 'plant/plant_detail.html'
    context_object_name = 'plant'

    def get_object(self):
        plant_id = self.kwargs['pk']
        api_url = self.request.build_absolute_uri(f'/api/plants/{plant_id}/')
        response = requests.get(api_url, cookies=self.request.COOKIES)
        if response.status_code == 200:
            return response.json()
        return None

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')
    
@user_passes_test(lambda u: u.is_superuser)
def plant_create_view(request):
    if request.method == 'POST':
        data = {
            'product': request.POST.get('product'),
            'plant_type': request.POST.get('plant_type'),
            'scientific_name': request.POST.get('scientific_name'),
            'attributes': request.POST.getlist('attributes'),
        }
        api_url = request.build_absolute_uri('/api/plants/')
        response = requests.post(api_url, json=data, cookies=request.COOKIES)
        if response.status_code == 201:
            messages.success(request, 'Растение успешно создано.')
            return redirect('plant_list')
        else:
            messages.error(request, f"Ошибка API: {response.json()}")
            form = PlantForm(request.POST)
            return render(request, 'plant/plant_form.html', {'form': form})
            
    form = PlantForm()
    return render(request, 'plant/plant_form.html', {'form': form})

@user_passes_test(lambda u: u.is_superuser)
def plant_update_view(request, pk):
    api_url = request.build_absolute_uri(f'/api/plants/{pk}/')
    if request.method == 'POST':
        data = {
            'product': request.POST.get('product'),
            'plant_type': request.POST.get('plant_type'),
            'scientific_name': request.POST.get('scientific_name'),
            'attributes': request.POST.getlist('attributes'),
        }
        response = requests.put(api_url, json=data, cookies=request.COOKIES)
        if response.status_code == 200:
            messages.success(request, 'Растение успешно обновлено.')
            return redirect('plant_list')
        else:
            messages.error(request, f"Ошибка API: {response.json()}")
            form = PlantForm(request.POST)
            return render(request, 'plant/plant_form.html', {'form': form})

    response = requests.get(api_url, cookies=request.COOKIES)
    if response.status_code == 200:
        plant_data = response.json()
        form = PlantForm(initial=plant_data)
        # For ManyToMany fields, you might need to extract IDs
        if 'attributes' in plant_data and isinstance(plant_data['attributes'], list):
            plant_data['attributes'] = [attr['id'] for attr in plant_data['attributes']]
        form = PlantForm(initial=plant_data)
        return render(request, 'plant/plant_form.html', {'form': form, 'plant': plant_data})
    else:
        messages.error(request, 'Не удалось загрузить данные растения.')
        return redirect('plant_list')

@user_passes_test(lambda u: u.is_superuser)
def plant_delete_view(request, pk):
    api_url = request.build_absolute_uri(f'/api/plants/{pk}/')
    if request.method == 'POST':
        response = requests.delete(api_url, cookies=request.COOKIES)
        if response.status_code == 204:
            messages.success(request, 'Растение успешно удалено.')
            return redirect('plant_list')
        else:
            messages.error(request, 'Ошибка при удалении растения.')
            return redirect('plant_list')

    response = requests.get(api_url, cookies=request.COOKIES)
    if response.status_code == 200:
        plant = response.json()
        return render(request, 'plant/plant_delete.html', {'plant': plant})
    else:
        messages.error(request, 'Растение не найдено.')
        return redirect('plant_list')

class CertificateListView(UserPassesTestMixin, ListView):
    template_name = 'certificate/certificate_list.html'
    context_object_name = 'certificates'

    def get_queryset(self):
        api_url = self.request.build_absolute_uri('/api/certificates/')
        response = requests.get(api_url, cookies=self.request.COOKIES)
        if response.status_code == 200:
            return response.json().get('results', [])
        return []

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')

class CertificateDetailView(UserPassesTestMixin, DetailView):
    template_name = 'certificate/certificate_detail.html'
    context_object_name = 'certificate'

    def get_object(self):
        certificate_id = self.kwargs['pk']
        api_url = self.request.build_absolute_uri(f'/api/certificates/{certificate_id}/')
        response = requests.get(api_url, cookies=self.request.COOKIES)
        if response.status_code == 200:
            return response.json()
        return None

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')
    
@user_passes_test(lambda u: u.is_superuser)
def certificate_create_view(request):
    if request.method == 'POST':
        # Create a mutable copy of request.POST
        post_data = request.POST.copy()
        # Handle checkbox value
        post_data['is_active'] = request.POST.get('is_active') == 'on'
        form = CertificateForm(post_data)
        if form.is_valid():
            api_url = request.build_absolute_uri('/api/certificates/')
            data = form.cleaned_data
            response = requests.post(api_url, json=data, cookies=request.COOKIES)
            if response.status_code == 201:
                messages.success(request, 'Сертификат успешно создан.')
                return redirect('certificate_list')
            else:
                messages.error(request, f"Ошибка API: {response.json()}")
    else:
        form = CertificateForm()
    return render(request, 'certificate/certificate_form.html', {'form': form})

@user_passes_test(lambda u: u.is_superuser)
def certificate_update_view(request, pk):
    api_url = request.build_absolute_uri(f'/api/certificates/{pk}/')
    if request.method == 'POST':
        post_data = request.POST.copy()
        post_data['is_active'] = request.POST.get('is_active') == 'on'
        form = CertificateForm(post_data)
        if form.is_valid():
            data = form.cleaned_data
            response = requests.put(api_url, json=data, cookies=request.COOKIES)
            if response.status_code == 200:
                messages.success(request, 'Сертификат успешно обновлен.')
                return redirect('certificate_list')
            else:
                messages.error(request, f"Ошибка API: {response.json()}")
    else:
        response = requests.get(api_url, cookies=request.COOKIES)
        if response.status_code == 200:
            form = CertificateForm(initial=response.json())
        else:
            messages.error(request, 'Не удалось загрузить данные сертификата.')
            return redirect('certificate_list')
    return render(request, 'certificate/certificate_form.html', {'form': form})

@user_passes_test(lambda u: u.is_superuser)
def certificate_delete_view(request, pk):
    api_url = request.build_absolute_uri(f'/api/certificates/{pk}/')
    if request.method == 'POST':
        response = requests.delete(api_url, cookies=request.COOKIES)
        if response.status_code == 204:
            messages.success(request, 'Сертификат успешно удален.')
            return redirect('certificate_list')
        else:
            messages.error(request, 'Ошибка при удалении сертификата.')
            return redirect('certificate_list')

    response = requests.get(api_url, cookies=request.COOKIES)
    if response.status_code == 200:
        certificate = response.json()
        return render(request, 'certificate/certificate_delete.html', {'certificate': certificate})
    else:
        messages.error(request, 'Сертификат не найден.')
        return redirect('certificate_list')

class OrderListView(UserPassesTestMixin, ListView):
    template_name = 'order/order_list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        api_url = self.request.build_absolute_uri('/api/orders/')
        response = requests.get(api_url, cookies=self.request.COOKIES)
        if response.status_code == 200:
            orders = response.json().get('results', [])
            # Manually add status display for each order
            for order in orders:
                order['get_status_display'] = self.get_status_display(order.get('status'))
            return orders
        return []

    def get_status_display(self, status_code):
        # This should match the choices in your Order model on the API side
        statuses = {'new': 'Новый', 'processing': 'В обработке', 'shipped': 'Отправлен', 'delivered': 'Доставлен', 'cancelled': 'Отменен'}
        return statuses.get(status_code, 'Неизвестный статус')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')

class OrderDetailView(UserPassesTestMixin, DetailView):
    template_name = 'order/order_detail.html'
    context_object_name = 'order'

    def get_object(self):
        order_id = self.kwargs['pk']
        api_url = self.request.build_absolute_uri(f'/api/orders/{order_id}/')
        response = requests.get(api_url, cookies=self.request.COOKIES)
        if response.status_code == 200:
            order = response.json()
            order['get_status_display'] = self.get_status_display(order.get('status'))
            # Fetch order items if they are not nested
            items_url = self.request.build_absolute_uri(f'/api/orders/{order_id}/items/')
            items_response = requests.get(items_url, cookies=self.request.COOKIES)
            if items_response.status_code == 200:
                order['orderitem_set'] = items_response.json()
            else:
                 order['orderitem_set'] = []
            return order
        return None

    def get_status_display(self, status_code):
        statuses = {'new': 'Новый', 'processing': 'В обработке', 'shipped': 'Отправлен', 'delivered': 'Доставлен', 'cancelled': 'Отменен'}
        return statuses.get(status_code, 'Неизвестный статус')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')

@user_passes_test(lambda u: u.is_superuser)
def order_create_view(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            api_url = request.build_absolute_uri('/api/orders/')
            data = form.cleaned_data
            response = requests.post(api_url, json=data, cookies=request.COOKIES)
            if response.status_code == 201:
                messages.success(request, 'Заказ успешно создан.')
                return redirect('order_list')
            else:
                messages.error(request, f"Ошибка API: {response.json()}")
    else:
        form = OrderForm()
    return render(request, 'order/order_form.html', {'form': form})

@user_passes_test(lambda u: u.is_superuser)
def order_update_view(request, pk):
    api_url = request.build_absolute_uri(f'/api/orders/{pk}/')
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            # Only send fields that can be updated
            update_data = {'status': data.get('status'), 'address': data.get('address')}
            response = requests.patch(api_url, json=update_data, cookies=request.COOKIES)
            if response.status_code == 200:
                messages.success(request, 'Заказ успешно обновлен.')
                return redirect('order_list')
            else:
                messages.error(request, f"Ошибка API: {response.json()}")
    else:
        response = requests.get(api_url, cookies=request.COOKIES)
        if response.status_code == 200:
            form = OrderForm(initial=response.json())
        else:
            messages.error(request, 'Не удалось загрузить данные заказа.')
            return redirect('order_list')
    return render(request, 'order/order_form.html', {'form': form})

@user_passes_test(lambda u: u.is_superuser)
def order_delete_view(request, pk):
    api_url = request.build_absolute_uri(f'/api/orders/{pk}/')
    if request.method == 'POST':
        response = requests.delete(api_url, cookies=request.COOKIES)
        if response.status_code == 204:
            messages.success(request, 'Заказ успешно удален.')
            return redirect('order_list')
        else:
            messages.error(request, 'Ошибка при удалении заказа.')
            return redirect('order_list')

    response = requests.get(api_url, cookies=request.COOKIES)
    if response.status_code == 200:
        order = response.json()
        return render(request, 'order/order_delete.html', {'order': order})
    else:
        messages.error(request, 'Заказ не найден.')
        return redirect('order_list')

def register_view(request):
    if request.method == 'POST':
        data = {
            'username': request.POST.get('username'),
            'password': request.POST.get('password1'),
            'first_name': request.POST.get('first_name'),
            'last_name': request.POST.get('last_name'),
            'email': request.POST.get('email'),
            'phone': request.POST.get('phone'),
        }
        api_url = request.build_absolute_uri('/api/auth/register/')
        api_response = requests.post(api_url, data=data)
        try:
            api_json = api_response.json()
        except Exception:
            messages.error(request, 'Ошибка регистрации (ответ API не JSON)')
            form = UserRegistrationForm()
            return render(request, 'auth/register.html', {'form': form})
        if api_response.status_code == 200 and api_json.get('success'):
            # После успешной регистрации сразу логиним через API
            login_url = request.build_absolute_uri('/api/auth/login/')
            login_response = requests.post(login_url, data={'username': data['username'], 'password': data['password']}, cookies=api_response.cookies)
            if login_response.status_code == 200 and login_response.json().get('success'):
                # Django login для сессии
                user = authenticate(username=data['username'], password=data['password'])
                if user:
                    login(request, user)
                    messages.success(request, 'Регистрация прошла успешно!')
                    return redirect('profile')
        messages.error(request, api_json.get('error', 'Ошибка регистрации'))
        form = UserRegistrationForm()
    return render(request, 'auth/register.html', {'form': form})

def login_view(request):
    form = UserLoginForm()
    if request.method == 'POST':
        data = {
            'username': request.POST.get('username'),
            'password': request.POST.get('password'),
        }
        api_url = request.build_absolute_uri('/api/auth/login/')
        api_response = requests.post(api_url, data=data)
        if api_response.status_code == 200 and api_response.json().get('success'):
            user = authenticate(username=data['username'], password=data['password'])
            if user:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {data["username"]}!')
                return redirect('profile')
        messages.error(request, api_response.json().get('error', 'Ошибка входа'))
        form = UserLoginForm()
    return render(request, 'auth/login.html', {'form': form})

@login_required
def logout_view(request):
    api_url = request.build_absolute_uri('/api/auth/logout/')
    requests.post(api_url, cookies=request.COOKIES)
    logout(request)
    messages.info(request, 'Вы вышли из системы.')
    return redirect('info')

@login_required
def profile_view(request):
    api_url = request.build_absolute_uri('/api/auth/profile/')
    api_response = requests.get(api_url, cookies=request.COOKIES)
    if api_response.status_code == 200:
        data = api_response.json()
        customer = data.get('customer') or {}
        api_user = data.get('user') or {}
        is_admin = request.user.is_superuser
        return render(request, 'auth/profile.html', {'customer': customer, 'api_user': api_user, 'is_admin': is_admin})
    messages.error(request, 'Ошибка загрузки профиля')
    return redirect('info')

@login_required
def profile_edit_view(request):
    api_url = request.build_absolute_uri('/api/auth/profile/')
    if request.method == 'POST':
        data = {
            'first_name': request.POST.get('first_name'),
            'last_name': request.POST.get('last_name'),
            'email': request.POST.get('email'),
            'phone': request.POST.get('phone'),
        }
        api_response = requests.put(api_url, data=data, cookies=request.COOKIES)
        if api_response.status_code == 200:
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('profile')
        messages.error(request, 'Ошибка обновления профиля')
    # GET — получить текущие данные
    api_response = requests.get(api_url, cookies=request.COOKIES)
    if api_response.status_code == 200:
        data = api_response.json()
        customer = data.get('customer') or {}
        api_user = data.get('user') or {}
        initial_data = {
            'first_name': api_user.get('first_name', ''),
            'last_name': api_user.get('last_name', ''),
            'email': api_user.get('email', ''),
            'phone': customer.get('phone', ''),
        }
        form = ProfileEditForm(initial=initial_data)
        return render(request, 'auth/profile_edit.html', {'form': form, 'customer': customer, 'api_user': api_user})
    messages.error(request, 'Ошибка загрузки профиля')
    return redirect('profile')

@user_passes_test(lambda u: u.is_superuser, login_url='/')
def admin_panel_view(request):
    context = {}
    profile_api_url = request.build_absolute_uri('/api/auth/profile/')
    profile_response = requests.get(profile_api_url, cookies=request.COOKIES)
    if profile_response.status_code == 200:
        context['customer'] = profile_response.json().get('customer')

    # Fetching statistics from different API endpoints
    try:
        users_api_url = request.build_absolute_uri('/api/users/')
        products_api_url = request.build_absolute_uri('/api/products/')
        orders_api_url = request.build_absolute_uri('/api/orders/')
        customers_api_url = request.build_absolute_uri('/api/customers/')
        
        context['total_users'] = requests.get(users_api_url, cookies=request.COOKIES).json().get('count', 0)
        context['total_products'] = requests.get(products_api_url, cookies=request.COOKIES).json().get('count', 0)
        context['total_orders'] = requests.get(orders_api_url, cookies=request.COOKIES).json().get('count', 0)
        context['total_customers'] = requests.get(customers_api_url, cookies=request.COOKIES).json().get('count', 0)
    except Exception as e:
        messages.error(request, f'Ошибка при загрузке статистики: {e}')

    return render(request, 'auth/admin_panel.html', context)

def catalog_view(request):
    # Получаем параметры поиска, фильтрации и сортировки
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    sort_by = request.GET.get('sort', 'name')
    page = request.GET.get('page', '1')
    page_size = request.GET.get('page_size', '20')

    # Формируем параметры для API
    params = {'page': page, 'page_size': page_size}
    if search_query:
        params['search'] = search_query
    if category_id:
        params['category'] = category_id
    # Сортировка
    if sort_by == 'price_low':
        params['ordering'] = 'price'
    elif sort_by == 'price_high':
        params['ordering'] = '-price'
    else:
        params['ordering'] = 'name'

    # Получаем товары через API
    api_url = request.build_absolute_uri('/api/products/')
    try:
        api_response = requests.get(api_url, params=params)
        if api_response.status_code == 200:
            products = api_response.json().get('results', [])
            for product in products:
                product['image_url'] = product.get('image')
        else:
            products = []
    except Exception:
        products = []

    # Получаем категории через API
    cat_url = request.build_absolute_uri('/api/categories/')
    try:
        cat_response = requests.get(cat_url)
        if cat_response.status_code == 200:
            categories = cat_response.json()
        else:
            categories = []
    except Exception:
        categories = []
    
    context = {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
        'sort_by': sort_by,
    }
    return render(request, 'catalog/catalog.html', context)

def product_detail_view(request, product_id):
    # Получаем товар через API
    api_url = request.build_absolute_uri(f'/api/products/{product_id}/')
    api_response = requests.get(api_url, cookies=request.COOKIES)
    if api_response.status_code != 200:
        messages.error(request, 'Товар не найден.')
        return redirect('catalog')
    product = api_response.json()
    product['image_url'] = product.get('image')
    # Получаем растение через API (если есть)
    plant = None
    plant_url = request.build_absolute_uri(f'/api/plants/?product={product_id}')
    plant_response = requests.get(plant_url, cookies=request.COOKIES)
    if plant_response.status_code == 200 and plant_response.json().get('results'):
        plant = plant_response.json()['results'][0]
    # Получаем отзывы через API
    reviews_url = request.build_absolute_uri(f'/api/reviews/?product={product_id}&ordering=-review_date&page_size=5')
    reviews_response = requests.get(reviews_url, cookies=request.COOKIES)
    reviews = reviews_response.json().get('results', []) if reviews_response.status_code == 200 else []
    # Получаем похожие товары через API
    similar_url = request.build_absolute_uri(f'/api/products/?category={product["category"]["id"]}&exclude={product_id}&page_size=4')
    similar_response = requests.get(similar_url, cookies=request.COOKIES)
    similar_products = [p for p in similar_response.json().get('results', []) if p['id'] != product_id][:4] if similar_response.status_code == 200 else []
    for p in similar_products:
        p['image_url'] = p.get('image')
    context = {
        'product': product,
        'plant': plant,
        'reviews': reviews,
        'similar_products': similar_products,
    }
    return render(request, 'catalog/product_detail.html', context)

@login_required
def add_to_cart_view(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        api_url = request.build_absolute_uri('/api/cart/')
        api_response = requests.post(api_url, data={'product_id': product_id, 'quantity': quantity}, cookies=request.COOKIES)
        if api_response.status_code == 200:
            return JsonResponse({'success': True, 'message': 'Товар добавлен в корзину.'})
        else:
            msg = api_response.json().get('message', 'Ошибка добавления в корзину')
            return JsonResponse({'success': False, 'message': msg})
    return JsonResponse({'success': False, 'message': 'Неверный метод'})

@login_required
def cart_view(request):
    api_url = request.build_absolute_uri('/api/cart/')
    api_response = requests.get(api_url, cookies=request.COOKIES)
    items = []
    total_sum = 0
    if api_response.status_code == 200:
        cart = api_response.json()
        for item in cart.get('items', []):
            product = item['product']
            item['product']['image_url'] = product.get('image')
            item['sum'] = float(product['price']) * int(item['quantity'])
            total_sum += item['sum']
            items.append(item)
    return render(request, 'cart/cart.html', {'items': items, 'total_sum': total_sum})

@require_POST
@csrf_exempt
def update_cart_item_quantity(request):
    item_id = request.POST.get('item_id')
    quantity = request.POST.get('quantity')
    try:
        item = CartItem.objects.get(id=item_id)
        quantity = int(quantity)
        if quantity > 0:
            item.quantity = quantity
            item.save()
            total_sum = sum(i.product.price * i.quantity for i in item.cart.items.select_related('product'))
            item_sum = item.product.price * item.quantity
            return JsonResponse({'success': True, 'item_sum': f'{item_sum:.2f}', 'total_sum': f'{total_sum:.2f}'})
        else:
            item.delete()
            total_sum = sum(i.product.price * i.quantity for i in item.cart.items.select_related('product'))
            return JsonResponse({'success': True, 'item_deleted': True, 'total_sum': f'{total_sum:.2f}'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

class ReviewListView(UserPassesTestMixin, ListView):
    template_name = 'review/review_list.html'
    context_object_name = 'reviews'

    def get_queryset(self):
        api_url = self.request.build_absolute_uri('/api/reviews/')
        response = requests.get(api_url, cookies=self.request.COOKIES)
        if response.status_code == 200:
            reviews = response.json().get('results', [])
            for review in reviews:
                review['get_status_display'] = self.get_status_display(review.get('status'))
            return reviews
        return []

    def get_status_display(self, status_code):
        statuses = {'pending': 'На рассмотрении', 'approved': 'Одобрен', 'rejected': 'Отклонен'}
        return statuses.get(status_code, 'Неизвестный статус')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')

class ReviewDetailView(UserPassesTestMixin, DetailView):
    template_name = 'review/review_detail.html'
    context_object_name = 'review'

    def get_object(self):
        review_id = self.kwargs['pk']
        api_url = self.request.build_absolute_uri(f'/api/reviews/{review_id}/')
        response = requests.get(api_url, cookies=self.request.COOKIES)
        if response.status_code == 200:
            review = response.json()
            review['get_status_display'] = self.get_status_display(review.get('status'))
            return review
        return None

    def get_status_display(self, status_code):
        statuses = {'pending': 'На рассмотрении', 'approved': 'Одобрен', 'rejected': 'Отклонен'}
        return statuses.get(status_code, 'Неизвестный статус')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')

@user_passes_test(lambda u: u.is_superuser)
def review_create_view(request):
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            api_url = request.build_absolute_uri('/api/reviews/')
            data = form.cleaned_data
            response = requests.post(api_url, json=data, cookies=request.COOKIES)
            if response.status_code == 201:
                messages.success(request, 'Отзыв успешно создан.')
                return redirect('review_list')
            else:
                messages.error(request, f"Ошибка API: {response.json()}")
    else:
        form = ReviewForm()
    return render(request, 'review/review_form.html', {'form': form})

@user_passes_test(lambda u: u.is_superuser)
def review_update_view(request, pk):
    api_url = request.build_absolute_uri(f'/api/reviews/{pk}/')
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            response = requests.patch(api_url, json=data, cookies=request.COOKIES)
            if response.status_code == 200:
                messages.success(request, 'Отзыв успешно обновлен.')
                return redirect('review_list')
            else:
                messages.error(request, f"Ошибка API: {response.json()}")
    else:
        response = requests.get(api_url, cookies=request.COOKIES)
        if response.status_code == 200:
            form = ReviewForm(initial=response.json())
        else:
            messages.error(request, 'Не удалось загрузить данные отзыва.')
            return redirect('review_list')
    return render(request, 'review/review_form.html', {'form': form})

@user_passes_test(lambda u: u.is_superuser)
def review_delete_view(request, pk):
    api_url = request.build_absolute_uri(f'/api/reviews/{pk}/')
    if request.method == 'POST':
        response = requests.delete(api_url, cookies=request.COOKIES)
        if response.status_code == 204:
            messages.success(request, 'Отзыв успешно удален.')
            return redirect('review_list')
        else:
            messages.error(request, 'Ошибка при удалении отзыва.')
            return redirect('review_list')

    response = requests.get(api_url, cookies=request.COOKIES)
    if response.status_code == 200:
        review = response.json()
        return render(request, 'review/review_delete.html', {'review': review})
    else:
        messages.error(request, 'Отзыв не найден.')
        return redirect('review_list')

