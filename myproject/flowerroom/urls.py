from django.urls import path, include
from .views import *

urlpatterns = [
    path('', info_view, name='info'),
    path('info', info_view, name='info'),
    
    # Аутентификация
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', profile_edit_view, name='profile_edit'),
    path('admin-panel/', admin_panel_view, name='admin_panel'),
    
    # Каталог для покупателей
    path('catalog/', catalog_view, name='catalog'),
    path('product/product_details/<int:product_id>/', product_detail_view, name='product_details'),
    
    
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user_detail'),
    path('users/create/', user_create_view, name='user_create'),
    path('users/<int:pk>/update/', user_update_view, name='user_update'),
    path('users/<int:pk>/delete/', user_delete_view, name='user_delete'),
    
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('products/create/', product_create_view, name='product_create'),
    path('products/<int:pk>/update/', product_update_view, name='product_update'),
    path('products/<int:pk>/delete/', product_delete_view, name='product_delete'),
    
    path('plants/', PlantListView.as_view(), name='plant_list'),
    path('plants/<int:pk>/', PlantDetailView.as_view(), name='plant_detail'),
    path('plants/create/', plant_create_view, name='plant_create'),
    path('plants/<int:pk>/update/', plant_update_view, name='plant_update'),
    path('plants/<int:pk>/delete/', plant_delete_view, name='plant_delete'),
    
    # path('orders/', OrderListView.as_view(), name='order_list'),
    # path('orders/<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    # path('orders/create/', OrderCreateView.as_view(), name='order_create'),
    # path('orders/<int:pk>/update/', OrderUpdateView.as_view(), name='order_update'),
    # path('orders/<int:pk>/delete/', OrderDeleteView.as_view(), name='order_delete'),
    
    path('customers/', CustomerListView.as_view(), name='customer_list'),
    path('customers/<int:pk>/', CustomerDetailView.as_view(), name='customer_detail'),
    path('customers/create/', customer_create_view, name='customer_create'),
    path('customers/<int:pk>/update/', customer_update_view, name='customer_update'),
    path('customers/<int:pk>/delete/', customer_delete_view, name='customer_delete'),
    
    # path('reviews/', ReviewListView.as_view(), name='review_list'),
    # path('reviews/<int:pk>/', ReviewDetailView.as_view(), name='review_detail'),
    # path('reviews/create/', ReviewCreateView.as_view(), name='review_create'),
    # path('reviews/<int:pk>/update/', ReviewUpdateView.as_view(), name='review_update'),
    # path('reviews/<int:pk>/delete/', ReviewDeleteView.as_view(), name='review_delete'),
    
    path('certificates/', CertificateListView.as_view(), name='certificate_list'),
    path('certificates/<int:pk>/', CertificateDetailView.as_view(), name='certificate_detail'),
    path('certificates/create/', certificate_create_view, name='certificate_create'),
    path('certificates/<int:pk>/update/', certificate_update_view, name='certificate_update'),
    path('certificates/<int:pk>/delete/', certificate_delete_view, name='certificate_delete'),

    path('cart/add/', add_to_cart_view, name='add_to_cart'),
    path('cart/', cart_view, name='cart'),
    path('cart/update-quantity/', update_cart_item_quantity, name='update_cart_item_quantity'),
    path('my-orders/', my_orders_view, name='my_orders'),
    path('my-orders/<int:order_id>/cancel/', cancel_order_view, name='cancel_order'),

    path('admin/order-status/', order_status_admin_view, name='order_status_admin'),
]