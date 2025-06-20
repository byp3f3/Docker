from rest_framework import permissions
from rest_framework.permissions import IsAdminUser, IsAuthenticated


class AdminPostPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        # Разрешаем GET, HEAD, OPTIONS всем
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Для POST, PUT, PATCH, DELETE проверяем, что пользователь - администратор
        return request.user and request.user.is_staff


class AdminOnlyPermission(permissions.BasePermission):
    
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class ReadOnlyOrAdminPermission(permissions.BasePermission):
    
    def has_permission(self, request, view):
        # Разрешаем чтение аутентифицированным пользователям
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Разрешаем запись только администраторам
        return request.user and request.user.is_staff


class CartPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Пользователь может управлять только своей корзиной
        if hasattr(obj, 'customer'):
            return obj.customer.user == request.user
        elif hasattr(obj, 'cart'):
            return obj.cart.customer.user == request.user
        return False
