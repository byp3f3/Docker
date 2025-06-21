import logging
from .serializers import *
from rest_framework import viewsets
from flowerroom.models import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from .permissions import AdminPostPermission, AdminOnlyPermission, ReadOnlyOrAdminPermission, CartPermission
from django.utils import timezone

logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [AdminPostPermission]

class ProductCategoryViewSet(viewsets.ModelViewSet):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    permission_classes = [AdminPostPermission]

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [AdminPostPermission]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [AdminPostPermission]

class PlantTypeViewSet(viewsets.ModelViewSet):
    queryset = PlantType.objects.all()
    serializer_class = PlantTypeSerializer
    permission_classes = [AdminPostPermission]

class PlantAttributeViewSet(viewsets.ModelViewSet):
    queryset = PlantAttribute.objects.all()
    serializer_class = PlantAttributeSerializer
    permission_classes = [AdminPostPermission]

class PlantViewSet(viewsets.ModelViewSet):
    queryset = Plant.objects.all()
    serializer_class = PlantSerializer
    permission_classes = [AdminPostPermission]

class CertificateViewSet(viewsets.ModelViewSet):
    queryset = Certificate.objects.all()
    serializer_class = CertificateSerializer
    permission_classes = [AdminPostPermission]

class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [permissions.AllowAny]

class DeliveryAddressViewSet(viewsets.ModelViewSet):
    queryset = DeliveryAddress.objects.all()
    serializer_class = DeliveryAddressSerializer
    permission_classes = [ReadOnlyOrAdminPermission]

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [ReadOnlyOrAdminPermission]

class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [ReadOnlyOrAdminPermission]

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [ReadOnlyOrAdminPermission]

class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        data = request.data
        required_fields = ['username', 'password', 'first_name', 'last_name', 'email']
        for field in required_fields:
            if not data.get(field):
                return Response({'error': f'Поле {field} обязательно'}, status=400)
        if User.objects.filter(username=data.get('username')).exists():
            return Response({'error': 'Пользователь с таким именем уже существует.'}, status=400)
        user = User.objects.create_user(
            username=data.get('username'),
            password=data.get('password'),
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            email=data.get('email', '')
        )
        Customer.objects.create(
            user=user,
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            phone=data.get('phone', '')
        )
        return Response({'success': True, 'user': UserSerializer(user).data})

class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return Response({'success': True, 'user': UserSerializer(user).data})
        return Response({'success': False, 'error': 'Неверные данные для входа.'}, status=400)

class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        logout(request)
        return Response({'success': True})

class ProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        customer = Customer.objects.get(user=request.user)
        return Response({
            'user': UserSerializer(request.user).data,
            'customer': CustomerSerializer(customer).data,
            'is_authenticated': request.user.is_authenticated,
            'username': request.user.username
        })
    def put(self, request):
        customer = Customer.objects.get(user=request.user)
        user = request.user
        user.first_name = request.data.get('first_name', user.first_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.email = request.data.get('email', user.email)
        user.save()
        customer.first_name = request.data.get('first_name', customer.first_name)
        customer.last_name = request.data.get('last_name', customer.last_name)
        customer.phone = request.data.get('phone', customer.phone)
        customer.save()
        return Response({'user': UserSerializer(user).data, 'customer': CustomerSerializer(customer).data, 'is_authenticated': True, 'username': user.username})

class CartAPIView(APIView):
    permission_classes = [CartPermission]
    def get(self, request):
        logger.info(f"Cart GET request from user: {request.user}")
        customer = request.user.customer
        cart, _ = Cart.objects.get_or_create(customer=customer)
        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data)
    def post(self, request):
        logger.info(f"Cart POST request from user: {request.user}, data: {request.data}")
        customer = request.user.customer
        cart, _ = Cart.objects.get_or_create(customer=customer)
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        product = Product.objects.filter(id=product_id).first()
        if not product or product.stock_quantity < 1:
            return Response({'success': False, 'message': 'Товар не найден или нет в наличии.'}, status=400)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()
        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data)

class CartItemAPIView(APIView):
    permission_classes = [CartPermission]
    def patch(self, request, item_id):
        customer = request.user.customer
        cart = Cart.objects.filter(customer=customer).first()
        item = CartItem.objects.filter(id=item_id, cart=cart).first()
        if not item:
            return Response({'success': False, 'message': 'Позиция не найдена.'}, status=404)
        quantity = int(request.data.get('quantity', 1))
        if quantity > 0:
            item.quantity = quantity
            item.save()
            serializer = CartItemSerializer(item, context={'request': request})
            return Response(serializer.data)
        else:
            item.delete()
            return Response({'success': True, 'item_deleted': True})
    def delete(self, request, item_id):
        customer = request.user.customer
        cart = Cart.objects.filter(customer=customer).first()
        item = CartItem.objects.filter(id=item_id, cart=cart).first()
        if not item:
            return Response({'success': False, 'message': 'Позиция не найдена.'}, status=404)
        item.delete()
        return Response({'success': True, 'item_deleted': True})

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

class CheckoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        customer = request.user.customer
        cart = Cart.objects.filter(customer=customer).first()
        if not cart or not cart.items.exists():
            return Response({'success': False, 'message': 'Корзина пуста'}, status=400)

        address_data = request.data.get('address', {})
        certificate_code = request.data.get('certificate_code', '').strip()

        # Создание адреса
        address = DeliveryAddress.objects.create(
            city_id=address_data.get('city'),
            street=address_data.get('street'),
            building=address_data.get('building'),
            apartment=address_data.get('apartment', ''),
            postal_code=address_data.get('postal_code', '')
        )

        total_amount = sum(item.product.price * item.quantity for item in cart.items.all())
        discount_amount = 0
        certificate = None

        # Проверка сертификата
        if certificate_code:
            try:
                # Сначала проверяем, существует ли сертификат с таким кодом
                certificate = Certificate.objects.get(code=certificate_code)
                
                # Проверяем, не использован ли уже сертификат
                if certificate.is_used:
                    return Response({
                        'success': False, 
                        'message': 'Сертификат уже был использован',
                        'error_type': 'certificate_used'
                    }, status=400)
                
                # Проверяем срок действия сертификата
                if certificate.expiry_date and certificate.expiry_date < timezone.now().date():
                    return Response({
                        'success': False, 
                        'message': 'Сертификат просрочен',
                        'error_type': 'certificate_expired'
                    }, status=400)
                
                # Если все проверки пройдены, применяем сертификат
                discount_amount = min(certificate.amount, total_amount)
                certificate.is_used = True
                certificate.used_by = customer
                certificate.used_date = timezone.now()
                certificate.save()
                
            except Certificate.DoesNotExist:
                return Response({
                    'success': False, 
                    'message': 'Сертификат с таким кодом не найден',
                    'error_type': 'certificate_not_found'
                }, status=400)

        # Создание заказа
        order = Order.objects.create(
            customer=customer,
            address=address,
            status='Pending',
            total_amount=total_amount - discount_amount,
            certificate=certificate,
            discount_amount=discount_amount
        )

        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                unit_price=item.product.price
            )
            item.product.stock_quantity -= item.quantity
            item.product.save()

        cart.items.all().delete()

        return Response({'success': True, 'order_id': order.id, 'total_amount': float(order.total_amount), 'discount_amount': float(discount_amount)})

