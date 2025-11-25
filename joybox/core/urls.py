from django.urls import path, include
from . import views  # Добавьте этот импорт

urlpatterns = [
    path('', views.info_view, name='info_view'),
    path('catalog/', views.catalog_page, name='catalog'),
    path('product/<int:pk>/', views.product_detail_page, name='product_detail_page'),
    path('login/', views.login_page, name='login_page'),
    path('register/', views.register_page, name='register_page'),
    path('profile/', views.profile_page, name='profile_page'),
    path('admin-panel/', views.admin_panel_page, name='admin_panel_page'),
    
    path('api/catalog/categories/', views.CategoryListView.as_view(), name='categories'),
    path('api/catalog/brands/', views.BrandListView.as_view(), name='brands'),
    path('api/catalog/products/', views.ProductListView.as_view(), name='products'),
    path('api/catalog/products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('api/catalog/popular-products/', views.PopularProductsListView.as_view(), name='popular-products'),
    path('api/catalog/products/<int:product_id>/reviews/', views.ProductReviewsListView.as_view(), name='product-reviews'),
    
    path('api/auth/register/', views.UserRegistrationView.as_view(), name='user-register'),
    path('api/auth/login/', views.LoginView.as_view(), name='user-login'),
    path('api/auth/profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('api/auth/wishlist/', views.WishlistListView.as_view(), name='user-wishlist'),
    path('api/admin/panel/', views.AdminPanelView.as_view(), name='admin-panel'),
    path('api/admin/dashboard/', views.AdminDashboardView.as_view(), name='admin-dashboard'),
    path('api/admin/products/', views.AdminProductsView.as_view(), name='admin-products'),
    path('api/admin/users/', views.AdminUsersView.as_view(), name='admin-users'),
    path('api/admin/orders/', views.AdminOrdersView.as_view(), name='admin-orders'),
]