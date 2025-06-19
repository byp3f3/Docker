from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import *

class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label='Имя', 
                                widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=True, label='Фамилия',
                               widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=11, required=False, label='Телефон',
                           widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, label='Email',
                            widget=forms.EmailInput(attrs={'class': 'form-control'}))
    username = forms.CharField(label='Имя пользователя',
                              widget=forms.TextInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(label='Пароль',
                               widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='Подтверждение пароля',
                               widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2']

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Имя пользователя',
                              widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label='Пароль')

class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

class UserForm(forms.ModelForm):
    ROLE_CHOICES = [
        (False, 'Пользователь'),
        (True, 'Администратор'),
    ]
    
    is_superuser = forms.ChoiceField(
        choices=ROLE_CHOICES,
        label='Роль',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text='Оставьте пустым, чтобы не изменять пароль'
    )
    
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_superuser']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Для существующего пользователя устанавливаем текущее значение
            self.fields['is_superuser'].initial = self.instance.is_superuser
            self.fields['password1'].help_text = 'Оставьте пустым, чтобы не изменять пароль'
        else:
            # Для нового пользователя пароль обязателен
            self.fields['password1'].required = True
            self.fields['password2'].required = True
            self.fields['password1'].help_text = 'Введите пароль для нового пользователя'
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if not self.instance.pk:  # Новый пользователь
            if password1 and password2:
                if password1 != password2:
                    raise forms.ValidationError("Пароли не совпадают")
            else:
                raise forms.ValidationError("Пароль обязателен для нового пользователя")
        else:  # Существующий пользователь
            if password1 or password2:
                if password1 != password2:
                    raise forms.ValidationError("Пароли не совпадают")
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Преобразуем строковое значение обратно в boolean
        user.is_superuser = self.cleaned_data['is_superuser'] == 'True'
        
        # Устанавливаем пароль, если он указан
        password1 = self.cleaned_data.get('password1')
        if password1:
            user.set_password(password1)
        
        if commit:
            user.save()
        return user

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

class ProfileEditForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите имя'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите фамилию'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите email'
        })
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите номер телефона'
        })
    )

    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'phone']

