from rest_framework import serializers
from rest_framework.authtoken.models import Token
from .models import Product, Category, Brand, ProductImage, ProductAttribute, Review, User, Role, Wishlist, Order

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['categoryId', 'categoryName', 'categoryDescription']

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['brandId', 'brandName', 'brandDescription', 'brandCountry']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['productImageId', 'url', 'altText', 'isMain']

class ProductAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttribute
        fields = ['productAttributeId', 'productAttributeName', 'productAttributeValue', 'productAttributeUnit']

class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(source='categoryId', read_only=True)
    brand = BrandSerializer(source='brandId', read_only=True)
    main_image = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'productId', 'productName', 'productDescription', 
            'category', 'brand', 'price', 'ageRating', 
            'quantity', 'weightKg', 'dimensions', 'main_image',
            'average_rating', 'review_count'
        ]
    
    def get_main_image(self, obj):
        main_image = obj.productimage_set.filter(isMain=True).first()
        if main_image:
            return ProductImageSerializer(main_image).data
        return None
    
    def get_average_rating(self, obj):
        return obj.get_average_rating()
    
    def get_review_count(self, obj):
        return obj.get_review_count()

class ProductDetailSerializer(ProductListSerializer):
    images = ProductImageSerializer(many=True, read_only=True, source='productimage_set')
    attributes = ProductAttributeSerializer(many=True, read_only=True, source='productattribute_set')
    
    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + ['images', 'attributes']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['userId', 'firstName', 'lastName', 'email', 'phone', 'birthDate']

class UserProfileSerializer(serializers.ModelSerializer):
    roleName = serializers.CharField(source='roleId.roleName', read_only=True)
    
    class Meta:
        model = User
        fields = ['userId', 'firstName', 'lastName', 'middleName', 'email', 'phone', 'birthDate', 'roleName']
        read_only_fields = ['userId', 'email']

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirmPassword = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['firstName', 'lastName', 'middleName', 'email', 'password', 'confirmPassword', 'phone', 'birthDate']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirmPassword']:
            raise serializers.ValidationError("Пароли не совпадают")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirmPassword')
        # Get or create the default role
        try:
            role, created = Role.objects.get_or_create(roleName='Покупатель')
            validated_data['roleId'] = role
        except Exception as e:
            raise serializers.ValidationError(f"Ошибка при создании роли: {str(e)}")
        
        # Set username to email if not provided
        if 'username' not in validated_data:
            validated_data['username'] = validated_data['email']
            
        # Set createdAt to current time
        from django.utils import timezone
        validated_data['createdAt'] = timezone.now()
        
        # Create user with proper password handling
        user = User(
            firstName=validated_data['firstName'],
            lastName=validated_data['lastName'],
            middleName=validated_data.get('middleName'),
            email=validated_data['email'],
            username=validated_data['username'],
            phone=validated_data['phone'],
            birthDate=validated_data['birthDate'],
            roleId=validated_data['roleId'],
            createdAt=validated_data['createdAt']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        from django.contrib.auth import authenticate
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'),
                                email=email, password=password)
            if not user:
                raise serializers.ValidationError('Неверный email или пароль')
        else:
            raise serializers.ValidationError('Необходимо указать email и пароль')

        attrs['user'] = user
        return attrs

class TokenSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Token
        fields = ['key', 'user']

class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(source='userId', read_only=True)
    
    class Meta:
        model = Review
        fields = ['reviewId', 'productId', 'user', 'rating', 'reviewText', 'createdAt', 'updatedAt']

class WishlistSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(source='productId', read_only=True)
    user = UserSerializer(source='userId', read_only=True)
    
    class Meta:
        model = Wishlist
        fields = ['wishlistId', 'product', 'user']

class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(source='userId', read_only=True)
    status = serializers.CharField(source='orderStatusId.orderStatusName', read_only=True)
    
    class Meta:
        model = Order
        fields = ['orderId', 'user', 'total', 'status', 'createdAt']
