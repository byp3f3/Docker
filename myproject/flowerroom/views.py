from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import *
from .forms import *

def info_view(request):
    return render(request, 'info.html')

class UserListView(ListView):
    model = User
    template_name = 'user/user_list.html'
    context_object_name = 'users'

class UserDetailView(DetailView):
    model = User
    template_name = 'user/user_detail.html'
    context_object_name = 'user'

class UserCreateView(CreateView):
    model = User
    form_class = UserForm
    template_name = 'user/user_form.html'
    success_url = reverse_lazy('user_list')

class UserUpdateView(UpdateView):
    model = User
    form_class = UserForm
    template_name = 'user/user_form.html'
    success_url = reverse_lazy('user_list')

class UserDeleteView(DeleteView):
    model = User
    template_name = 'user/user_delete.html'
    success_url = reverse_lazy('user_list')

class CustomerListView(ListView):
    model = Customer
    template_name = 'customer/customer_list.html'
    context_object_name = 'customers'

class CustomerDetailView(DetailView):
    model = Customer
    template_name = 'customer/customer_detail.html'
    context_object_name = 'customer'

class CustomerCreateView(CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customer/customer_form.html'
    success_url = reverse_lazy('customer_list')

class CustomerUpdateView(UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customer/customer_form.html'
    success_url = reverse_lazy('customer_list')

class CustomerDeleteView(DeleteView):
    model = Customer
    template_name = 'customer/customer_delete.html'
    success_url = reverse_lazy('customer_list')


class ProductListView(ListView):
    model = Product
    template_name = 'product/product_list.html'
    context_object_name = 'products'

class ProductDetailView(DetailView):
    model = Product
    template_name = 'product/product_detail.html'
    context_object_name = 'product'

class ProductCreateView(CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'product/product_form.html'
    success_url = reverse_lazy('product_list')

class ProductUpdateView(UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'product/product_form.html'
    success_url = reverse_lazy('product_list')

class ProductDeleteView(DeleteView):
    model = Product
    template_name = 'product/product_delete.html'
    success_url = reverse_lazy('product_list')


class PlantListView(ListView):
    model = Plant
    template_name = 'plant/plant_list.html'
    context_object_name = 'plants'

class PlantDetailView(DetailView):
    model = Plant
    template_name = 'plant/plant_detail.html'
    context_object_name = 'plant'

class PlantCreateView(CreateView):
    model = Plant
    form_class = PlantForm
    template_name = 'plant/plant_form.html'
    success_url = reverse_lazy('plant_list')

class PlantUpdateView(UpdateView):
    model = Plant
    form_class = PlantForm
    template_name = 'plant/plant_form.html'
    success_url = reverse_lazy('plant_list')

class PlantDeleteView(DeleteView):
    model = Plant
    template_name = 'plant/plant_delete.html'
    success_url = reverse_lazy('plant_list')


class OrderListView(ListView):
    model = Order
    template_name = 'order/order_list.html'
    context_object_name = 'orders'

class OrderDetailView(DetailView):
    model = Order
    template_name = 'order/order_detail.html'
    context_object_name = 'order'

class OrderCreateView(CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'order/order_form.html'
    success_url = reverse_lazy('order_list')

class OrderUpdateView(UpdateView):
    model = Order
    form_class = OrderForm
    template_name = 'order/order_form.html'
    success_url = reverse_lazy('order_list')

class OrderDeleteView(DeleteView):
    model = Order
    template_name = 'order/order_delete.html'
    success_url = reverse_lazy('order_list')


class ReviewListView(ListView):
    model = Review
    template_name = 'review/review_list.html'
    context_object_name = 'reviews'

class ReviewDetailView(DetailView):
    model = Review
    template_name = 'review/review_detail.html'
    context_object_name = 'review'

class ReviewCreateView(CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'review/review_form.html'
    success_url = reverse_lazy('review_list')

class ReviewUpdateView(UpdateView):
    model = Review
    form_class = ReviewForm
    template_name = 'review/review_form.html'
    success_url = reverse_lazy('review_list')

class ReviewDeleteView(DeleteView):
    model = Review
    template_name = 'review/review_delete.html'
    success_url = reverse_lazy('review_list')


class CertificateListView(ListView):
    model = Certificate
    template_name = 'certificate/certificate_list.html'
    context_object_name = 'certificates'

class CertificateDetailView(DetailView):
    model = Certificate
    template_name = 'certificate/certificate_detail.html'
    context_object_name = 'certificate'

class CertificateCreateView(CreateView):
    model = Certificate
    form_class = CertificateForm
    template_name = 'certificate/certificate_form.html'
    success_url = reverse_lazy('certificate_list')

class CertificateUpdateView(UpdateView):
    model = Certificate
    form_class = CertificateForm
    template_name = 'certificate/certificate_form.html'
    success_url = reverse_lazy('certificate_list')

class CertificateDeleteView(DeleteView):
    model = Certificate
    template_name = 'certificate/certificate_delete.html'
    success_url = reverse_lazy('certificate_list')

