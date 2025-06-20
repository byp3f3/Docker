from rest_framework import serializers
from flowerroom.models import Customer, ProductCategory, Supplier, Product, PlantType, PlantAttribute, Plant, Certificate, City, DeliveryAddress, Order, OrderItem, Review, CartItem, Cart
from django.contrib.auth.models import User
from django.conf import settings

class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']
    def get_role(self, obj):
        if obj.is_superuser:
            return 'Администратор'
        return 'Пользователь'

class CustomerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Customer
        fields = ['id', 'user', 'first_name', 'last_name', 'phone']

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'description']

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'contact_person', 'phone', 'email', 'address']

class ProductSerializer(serializers.ModelSerializer):
    category = ProductCategorySerializer(read_only=True)
    suppliers = SupplierSerializer(many=True, read_only=True)
    image = serializers.SerializerMethodField()
    class Meta:
        model = Product
        fields = ['id', 'category', 'name', 'description', 'price', 'stock_quantity', 'suppliers', 'image']
    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            url = obj.image.url
            if request is not None:
                return request.build_absolute_uri(url)
            # Абсолютный URL если request нет
            return settings.SITE_URL.rstrip('/') + url
        return None

class PlantTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlantType
        fields = ['id', 'name', 'description']

class PlantAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlantAttribute
        fields = ['id', 'name', 'description']

class PlantSerializer(serializers.ModelSerializer):
    plant_type = PlantTypeSerializer(read_only=True)
    product = ProductSerializer(read_only=True)
    attributes = PlantAttributeSerializer(many=True, read_only=True)
    class Meta:
        model = Plant
        fields = ['id', 'plant_type', 'product', 'scientific_name', 'attributes']

class CertificateSerializer(serializers.ModelSerializer):
    used_by = CustomerSerializer(read_only=True)
    created_at = serializers.DateTimeField(format='%d.%m.%Y %H:%M', read_only=True)
    expiry_date = serializers.DateField(format='%d.%m.%Y', read_only=True)
    used_date = serializers.DateTimeField(format='%d.%m.%Y %H:%M', read_only=True)
    class Meta:
        model = Certificate
        fields = ['id', 'code', 'amount', 'created_at', 'expiry_date', 'is_used', 'used_by', 'used_date']

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['id', 'name']

class DeliveryAddressSerializer(serializers.ModelSerializer):
    city = CitySerializer(read_only=True)
    class Meta:
        model = DeliveryAddress
        fields = ['id', 'city', 'street', 'building', 'apartment', 'postal_code']

class OrderSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    address = DeliveryAddressSerializer(read_only=True)
    certificate = CertificateSerializer(read_only=True)
    order_date = serializers.DateTimeField(format='%d.%m.%Y %H:%M', read_only=True)
    class Meta:
        model = Order
        fields = ['id', 'customer', 'address', 'order_date', 'status', 'total_amount', 'certificate', 'discount_amount']

class OrderItemSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    product = ProductSerializer(read_only=True)
    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'product', 'quantity', 'unit_price']

class ReviewSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    customer = CustomerSerializer(read_only=True)
    review_date = serializers.DateTimeField(format='%d.%m.%Y %H:%M', read_only=True)
    class Meta:
        model = Review
        fields = ['id', 'product', 'customer', 'rating', 'comment', 'review_date']

class CartItemProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'image']
    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            url = obj.image.url
            if request is not None:
                return request.build_absolute_uri(url)
            from django.conf import settings
            return settings.SITE_URL.rstrip('/') + url
        return None

class CartItemSerializer(serializers.ModelSerializer):
    product = CartItemProductSerializer(read_only=True)
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    class Meta:
        model = Cart
        fields = ['id', 'items']
