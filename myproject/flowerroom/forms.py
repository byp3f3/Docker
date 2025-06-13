from django import forms
from .models import *

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role']

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['user', 'first_name', 'last_name', 'phone']

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'name', 'description', 'price', 'stock_quantity', 'suppliers', 'image']

class PlantForm(forms.ModelForm):
    class Meta:
        model = Plant
        fields = ['plant_type', 'product', 'scientific_name', 'attributes']

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer', 'status', 'total_amount', 'certificate']

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['order', 'product', 'quantity', 'unit_price']

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['product', 'customer', 'rating', 'comment']

class CertificateForm(forms.ModelForm):
    class Meta:
        model = Certificate
        fields = ['code', 'amount', 'expiry_date', 'is_used', 'used_by']

class DeliveryAddressForm(forms.ModelForm):
    class Meta:
        model = DeliveryAddress
        fields = ['city', 'street', 'building', 'apartment', 'postal_code']

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'phone', 'email', 'address']

