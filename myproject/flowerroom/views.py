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

def info_view(request):
    context = {}
    if request.user.is_authenticated:
        try:
            context['customer'] = Customer.objects.get(user=request.user)
        except Customer.DoesNotExist:
            context['customer'] = None
    context['main_products'] = Product.objects.order_by('?')[:3]
    return render(request, 'info.html', context)


class UserListView(UserPassesTestMixin, ListView):
    model = User
    template_name = 'user/user_list.html'
    context_object_name = 'users'

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')

class UserDetailView(UserPassesTestMixin, DetailView):
    model = User
    template_name = 'user/user_detail.html'
    context_object_name = 'user'

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')

class UserCreateView(UserPassesTestMixin, CreateView):
    model = User
    form_class = UserForm
    template_name = 'user/user_form.html'
    success_url = reverse_lazy('user_list')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')

class UserUpdateView(UserPassesTestMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'user/user_form.html'
    success_url = reverse_lazy('user_list')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')

class UserDeleteView(UserPassesTestMixin, DeleteView):
    model = User
    template_name = 'user/user_delete.html'
    success_url = reverse_lazy('user_list')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')

class CustomerListView(UserPassesTestMixin, ListView):
    model = Customer
    template_name = 'customer/customer_list.html'
    context_object_name = 'customers'

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')

class CustomerDetailView(UserPassesTestMixin, DetailView):
    model = Customer
    template_name = 'customer/customer_detail.html'
    context_object_name = 'customer'

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')

class CustomerCreateView(UserPassesTestMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customer/customer_form.html'
    success_url = reverse_lazy('customer_list')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')

class CustomerUpdateView(UserPassesTestMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customer/customer_form.html'
    success_url = reverse_lazy('customer_list')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')

class CustomerDeleteView(UserPassesTestMixin, DeleteView):
    model = Customer
    template_name = 'customer/customer_delete.html'
    success_url = reverse_lazy('customer_list')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')

class ProductListView(UserPassesTestMixin, ListView):
    model = Product
    template_name = 'product/product_list.html'
    context_object_name = 'products'

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')
    
class ProductDetailView(UserPassesTestMixin, DetailView):
    model = Product
    template_name = 'product/product_detail.html'
    context_object_name = 'product'

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')
    
class ProductCreateView(UserPassesTestMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'product/product_form.html'
    success_url = reverse_lazy('product_list')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')
    
class ProductUpdateView(UserPassesTestMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'product/product_form.html'
    success_url = reverse_lazy('product_list')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')
    
class ProductDeleteView(UserPassesTestMixin, DeleteView):
    model = Product
    template_name = 'product/product_delete.html'
    success_url = reverse_lazy('product_list')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')

class PlantListView(UserPassesTestMixin, ListView):
    model = Plant
    template_name = 'plant/plant_list.html'
    context_object_name = 'plants'

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')
    
class PlantDetailView(UserPassesTestMixin, DetailView):
    model = Plant
    template_name = 'plant/plant_detail.html'
    context_object_name = 'plant'

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')
    
class PlantCreateView(UserPassesTestMixin, CreateView):
    model = Plant
    form_class = PlantForm
    template_name = 'plant/plant_form.html'
    success_url = reverse_lazy('plant_list')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')
    
class PlantUpdateView(UserPassesTestMixin, UpdateView):
    model = Plant
    form_class = PlantForm
    template_name = 'plant/plant_form.html'
    success_url = reverse_lazy('plant_list')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')
    
class PlantDeleteView(UserPassesTestMixin, DeleteView):
    model = Plant
    template_name = 'plant/plant_delete.html'
    success_url = reverse_lazy('plant_list')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')

class OrderListView(UserPassesTestMixin, ListView):
    model = Order
    template_name = 'order/order_list.html'
    context_object_name = 'orders'

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')
    
class OrderDetailView(UserPassesTestMixin, DetailView):
    model = Order
    template_name = 'order/order_detail.html'
    context_object_name = 'order'

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')
    
class OrderCreateView(UserPassesTestMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'order/order_form.html'
    success_url = reverse_lazy('order_list')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')
    
class OrderUpdateView(UserPassesTestMixin, UpdateView):
    model = Order
    form_class = OrderForm
    template_name = 'order/order_form.html'
    success_url = reverse_lazy('order_list')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')
    
class OrderDeleteView(UserPassesTestMixin, DeleteView):
    model = Order
    template_name = 'order/order_delete.html'
    success_url = reverse_lazy('order_list')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')

class ReviewListView(UserPassesTestMixin, ListView):
    model = Review
    template_name = 'review/review_list.html'
    context_object_name = 'reviews'

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')
    
class ReviewDetailView(UserPassesTestMixin, DetailView):
    model = Review
    template_name = 'review/review_detail.html'
    context_object_name = 'review'

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')
    
class ReviewCreateView(UserPassesTestMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'review/review_form.html'
    success_url = reverse_lazy('review_list')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')
    
class ReviewUpdateView(UserPassesTestMixin, UpdateView):
    model = Review
    form_class = ReviewForm
    template_name = 'review/review_form.html'
    success_url = reverse_lazy('review_list')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')
    
class ReviewDeleteView(UserPassesTestMixin, DeleteView):
    model = Review
    template_name = 'review/review_delete.html'
    success_url = reverse_lazy('review_list')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')

class CertificateListView(UserPassesTestMixin, ListView):
    model = Certificate
    template_name = 'certificate/certificate_list.html'
    context_object_name = 'certificates'

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')
    
class CertificateDetailView(UserPassesTestMixin, DetailView):
    model = Certificate
    template_name = 'certificate/certificate_detail.html'
    context_object_name = 'certificate'

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')
    
class CertificateCreateView(UserPassesTestMixin, CreateView):
    model = Certificate
    form_class = CertificateForm
    template_name = 'certificate/certificate_form.html'
    success_url = reverse_lazy('certificate_list')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')
    
class CertificateUpdateView(UserPassesTestMixin, UpdateView):
    model = Certificate
    form_class = CertificateForm
    template_name = 'certificate/certificate_form.html'
    success_url = reverse_lazy('certificate_list')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')
    
class CertificateDeleteView(UserPassesTestMixin, DeleteView):
    model = Certificate
    template_name = 'certificate/certificate_delete.html'
    success_url = reverse_lazy('certificate_list')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('/')
    
def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Создаем профиль покупателя
            Customer.objects.create(
                user=user,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                phone=form.cleaned_data.get('phone', '')
            )
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('profile')
    else:
        form = UserRegistrationForm()
    return render(request, 'auth/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {user.username}!')
                return redirect('profile')
    else:
        form = UserLoginForm()
    return render(request, 'auth/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли из системы.')
    return redirect('info')

@login_required
def profile_view(request):
    customer = Customer.objects.get(user=request.user)
    return render(request, 'auth/profile.html', {'customer': customer})

@login_required
def profile_edit_view(request):
    try:
        customer = Customer.objects.get(user=request.user)
    except Customer.DoesNotExist:
        messages.error(request, 'Профиль не найден.')
        return redirect('profile')
    
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=customer)
        if form.is_valid():
            # Обновляем данные пользователя
            user = request.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            
            # Обновляем данные покупателя
            customer = form.save(commit=False)
            customer.user = user
            customer.save()
            
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('profile')
    else:
        # Инициализируем форму текущими данными
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'phone': customer.phone,
        }
        form = ProfileEditForm(instance=customer, initial=initial_data)
    
    context = {
        'form': form,
        'customer': customer
    }
    return render(request, 'auth/profile_edit.html', context)

@user_passes_test(lambda u: u.is_superuser, login_url='/')
def admin_panel_view(request):
    try:
        customer = Customer.objects.get(user=request.user)
    except Customer.DoesNotExist:
        messages.error(request, 'Профиль не найден.')
        return redirect('profile')
    
    # Статистика для админ-панели
    total_users = User.objects.count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_customers = Customer.objects.count()
    
    context = {
        'customer': customer,
        'total_users': total_users,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_customers': total_customers,
    }
    return render(request, 'auth/admin_panel.html', context)

def catalog_view(request):
    products = Product.objects.all()
    categories = ProductCategory.objects.all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(name__icontains=search_query)
    
    category_id = request.GET.get('category', '')
    if category_id:
        products = products.filter(category_id=category_id)
    
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    else:
        products = products.order_by('name')
    
    context = {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
        'sort_by': sort_by,
    }
    return render(request, 'catalog/catalog.html', context)

def product_detail_view(request, product_id):
    """Детальная страница товара для покупателей"""
    try:
        product = Product.objects.get(id=product_id)
        # Получаем связанное растение, если есть
        try:
            plant = Plant.objects.get(product=product)
        except Plant.DoesNotExist:
            plant = None
        
        # Получаем отзывы для этого товара
        reviews = Review.objects.filter(product=product).order_by('-review_date')[:5]
        
        # Получаем похожие товары из той же категории
        similar_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
        
    except Product.DoesNotExist:
        messages.error(request, 'Товар не найден.')
        return redirect('catalog')
    
    context = {
        'product': product,
        'plant': plant,
        'reviews': reviews,
        'similar_products': similar_products,
    }
    return render(request, 'catalog/product_detail.html', context)

@login_required
@require_POST
def add_to_cart_view(request):
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))
    product = Product.objects.filter(id=product_id).first()
    if not product or product.stock_quantity < 1:
        return JsonResponse({'success': False, 'message': 'Товар не найден или нет в наличии.'})
    customer = Customer.objects.get(user=request.user)
    cart, _ = Cart.objects.get_or_create(customer=customer)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    cart_item.save()
    return JsonResponse({'success': True, 'message': 'Товар добавлен в корзину.'})

@login_required
def cart_view(request):
    customer = Customer.objects.get(user=request.user)
    cart = Cart.objects.filter(customer=customer).first()
    items = cart.items.select_related('product') if cart else []
    for item in items:
        item.sum = item.product.price * item.quantity
    # Обработка изменения количества и удаления
    if request.method == 'POST' and cart:
        if 'remove' in request.POST:
            item_id = request.POST.get('remove')
            CartItem.objects.filter(id=item_id, cart=cart).delete()
            return redirect('cart')
        elif 'update' in request.POST:
            for item in items:
                qty = request.POST.get(f'quantity_{item.id}')
                if qty:
                    try:
                        qty = int(qty)
                        if qty > 0:
                            item.quantity = qty
                            item.save()
                    except ValueError:
                        pass
            return redirect('cart')
    total_sum = sum(item.product.price * item.quantity for item in items)
    return render(request, 'cart/cart.html', {'cart': cart, 'items': items, 'total_sum': total_sum})

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

