from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import *

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['user', 'first_name', 'last_name', 'phone']
    search_fields = ['first_name', 'last_name', 'user__username', 'user__email']

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    pass

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    pass

@admin.register(PlantType)
class PlantTypeAdmin(admin.ModelAdmin):
    pass

@admin.register(PlantAttribute)
class PlantAttributeAdmin(admin.ModelAdmin):
    pass

@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    pass

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    pass

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    pass

@admin.register(DeliveryAddress)
class DeliveryAddressAdmin(admin.ModelAdmin):
    pass

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    pass

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    pass

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    pass

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    pass

