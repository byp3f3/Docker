from django.urls import path, include
from .views import *

urlpatterns = [
    path('', info_view, name='info'),
    path('info', info_view, name='info'),
    
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user_detail'),
    path('users/create/', UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/update/', UserUpdateView.as_view(), name='user_update'),
    path('users/<int:pk>/delete/', UserDeleteView.as_view(), name='user_delete'),
    
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('products/create/', ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/update/', ProductUpdateView.as_view(), name='product_update'),
    path('products/<int:pk>/delete/', ProductDeleteView.as_view(), name='product_delete'),
    
    path('plants/', PlantListView.as_view(), name='plant_list'),
    path('plants/<int:pk>/', PlantDetailView.as_view(), name='plant_detail'),
    path('plants/create/', PlantCreateView.as_view(), name='plant_create'),
    path('plants/<int:pk>/update/', PlantUpdateView.as_view(), name='plant_update'),
    path('plants/<int:pk>/delete/', PlantDeleteView.as_view(), name='plant_delete'),
    
    path('orders/', OrderListView.as_view(), name='order_list'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    path('orders/create/', OrderCreateView.as_view(), name='order_create'),
    path('orders/<int:pk>/update/', OrderUpdateView.as_view(), name='order_update'),
    path('orders/<int:pk>/delete/', OrderDeleteView.as_view(), name='order_delete'),
    
    path('customers/', CustomerListView.as_view(), name='customer_list'),
    path('customers/<int:pk>/', CustomerDetailView.as_view(), name='customer_detail'),
    path('customers/create/', CustomerCreateView.as_view(), name='customer_create'),
    path('customers/<int:pk>/update/', CustomerUpdateView.as_view(), name='customer_update'),
    path('customers/<int:pk>/delete/', CustomerDeleteView.as_view(), name='customer_delete'),
    
    path('reviews/', ReviewListView.as_view(), name='review_list'),
    path('reviews/<int:pk>/', ReviewDetailView.as_view(), name='review_detail'),
    path('reviews/create/', ReviewCreateView.as_view(), name='review_create'),
    path('reviews/<int:pk>/update/', ReviewUpdateView.as_view(), name='review_update'),
    path('reviews/<int:pk>/delete/', ReviewDeleteView.as_view(), name='review_delete'),
    
    path('certificates/', CertificateListView.as_view(), name='certificate_list'),
    path('certificates/<int:pk>/', CertificateDetailView.as_view(), name='certificate_detail'),
    path('certificates/create/', CertificateCreateView.as_view(), name='certificate_create'),
    path('certificates/<int:pk>/update/', CertificateUpdateView.as_view(), name='certificate_update'),
    path('certificates/<int:pk>/delete/', CertificateDeleteView.as_view(), name='certificate_delete'),

]