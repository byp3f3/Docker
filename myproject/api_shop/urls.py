from django.urls import path, include
from rest_framework import routers

from .views import (
    CustomerViewSet,
    ProductCategoryViewSet,
    SupplierViewSet,
    ProductViewSet,
    PlantTypeViewSet,
    PlantAttributeViewSet,
    PlantViewSet,
    CertificateViewSet,
    CityViewSet,
    DeliveryAddressViewSet,
    OrderViewSet,
    OrderItemViewSet,
    ReviewViewSet,
    RegisterAPIView,
    LoginAPIView,
    LogoutAPIView,
    ProfileAPIView,
    CartAPIView,
    CartItemAPIView,
    UserViewSet,
)

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'categories', ProductCategoryViewSet, basename='category')
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'plant-types', PlantTypeViewSet, basename='planttype')
router.register(r'plant-attributes', PlantAttributeViewSet, basename='plantattribute')
router.register(r'plants', PlantViewSet, basename='plant')
router.register(r'certificates', CertificateViewSet, basename='certificate')
router.register(r'cities', CityViewSet, basename='city')
router.register(r'addresses', DeliveryAddressViewSet, basename='address')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'order-items', OrderItemViewSet, basename='orderitem')
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', RegisterAPIView.as_view(), name='api_register'),
    path('auth/login/', LoginAPIView.as_view(), name='api_login'),
    path('auth/logout/', LogoutAPIView.as_view(), name='api_logout'),
    path('auth/profile/', ProfileAPIView.as_view(), name='api_profile'),
    path('cart/', CartAPIView.as_view(), name='api_cart'),
    path('cart/item/<int:item_id>/', CartItemAPIView.as_view(), name='api_cart_item'),
]
