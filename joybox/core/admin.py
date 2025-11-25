from django.contrib import admin
from .models import (
    Role, User, Category, Brand, Product, ProductImage, ProductAttribute,
    Address, OrderStatus, Order, OrderItem, Review, Wishlist, Cart,
    ParentChild, AuditLog
)

# Register your models here.
admin.site.register(Role)
admin.site.register(User)
admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(ProductAttribute)
admin.site.register(Address)
admin.site.register(OrderStatus)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Review)
admin.site.register(Wishlist)
admin.site.register(Cart)
admin.site.register(ParentChild)
admin.site.register(AuditLog)