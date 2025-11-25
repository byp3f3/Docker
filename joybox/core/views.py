from rest_framework import generics, filters, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import authenticate
from django.db import models
from django.shortcuts import render, redirect
from .models import Product, Category, Brand, Review, Wishlist, ParentChild, User, Order
from .serializers import (
    ProductListSerializer, 
    ProductDetailSerializer,
    CategorySerializer,
    BrandSerializer,
    ReviewSerializer,
    UserSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
    LoginSerializer,
    WishlistSerializer,
    OrderSerializer
)
from .filters import ProductFilter
from django.shortcuts import render
from django.db.models import Count, Avg

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class BrandListView(generics.ListAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer

class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['productName', 'productDescription']
    ordering_fields = ['price', 'productName', 'createdAt']
    ordering = ['productName']

class PopularProductsListView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    
    def get_queryset(self):
        # Get products with at least one review, ordered by average rating and review count
        return Product.objects.filter(
            review__isnull=False
        ).annotate(
            avg_rating=Avg('review__rating'),
            review_count=Count('review')
        ).order_by('-avg_rating', '-review_count')[:12]

class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer

class ProductReviewsListView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    
    def get_queryset(self):
        product_id = self.kwargs['product_id']
        return Review.objects.filter(productId=product_id).select_related('userId')

class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]  # Explicitly allow any user to register
    
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(ObtainAuthToken):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]  # Explicitly allow any user to login
    
    def post(self, request, *args, **kwargs):
        try:
            serializer = self.serializer_class(data=request.data,
                                               context={'request': request})
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            })
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def dispatch(self, request, *args, **kwargs):
        # Ensure we always return JSON, even for errors
        try:
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            return Response({'detail': str(e)}, status=400)

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]  # Keep this as IsAuthenticated
    
    def get_object(self):
        return self.request.user

def info_view(request):
    # Check if user is admin or manager and redirect to admin panel
    if request.user.is_authenticated:
        if hasattr(request.user, 'roleId') and request.user.roleId.roleName in ['Администратор', 'Менеджер']:
            return redirect('/admin-panel/')
    return render(request, 'info.html')

def catalog_page(request):
    # Check if user is admin or manager and redirect to admin panel
    if request.user.is_authenticated:
        if hasattr(request.user, 'roleId') and request.user.roleId.roleName in ['Администратор', 'Менеджер']:
            return redirect('/admin-panel/')
    return render(request, 'catalog.html')

def product_detail_page(request, pk):
    # Check if user is admin or manager and redirect to admin panel
    if request.user.is_authenticated:
        if hasattr(request.user, 'roleId') and request.user.roleId.roleName in ['Администратор', 'Менеджер']:
            return redirect('/admin-panel/')
    return render(request, 'product_detail.html', {'product_id': pk})

def profile_page(request):
    # Admin and manager users can access their profile
    # Other users are redirected to admin panel if they try to access other pages
    return render(request, 'profile.html')

def admin_panel_page(request):
    # Render the admin panel page regardless of authentication status
    # Authentication will be handled by the frontend JavaScript
    return render(request, 'admin_panel.html')

def login_page(request):
    return render(request, 'login.html')

def register_page(request):
    return render(request, 'register.html')

class WishlistListView(generics.ListAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # If user is a parent (Покупатель), include wishlist items for their children
        if user.roleId.roleName == 'Покупатель':
            # Get children of this parent
            children = User.objects.filter(parentchild__userId=user)
            # Include wishlist items for the parent and their children
            return Wishlist.objects.filter(
                models.Q(userId=user) | models.Q(userId__in=children)
            ).select_related('userId', 'productId')
        else:
            # For other users, only show their own wishlist
            return Wishlist.objects.filter(userId=user).select_related('userId', 'productId')

class AdminPanelView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user
        # Check if user is admin or manager
        if user.roleId.roleName in ['Администратор', 'Менеджер']:
            # Return admin panel data
            return Response({
                'message': 'Welcome to admin panel',
                'role': user.roleId.roleName
            })
        else:
            # Redirect to regular site
            return Response({
                'message': 'Access denied. Redirecting to main site.',
                'redirect': '/'
            }, status=403)

class AdminDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user
        # Check if user is admin or manager
        if user.roleId.roleName in ['Администратор', 'Менеджер']:
            # Get statistics
            total_products = Product.objects.count()
            total_users = User.objects.count()
            total_orders = Order.objects.count()
            # Calculate total revenue (simplified)
            total_revenue = sum(order.total for order in Order.objects.all())
            
            return Response({
                'total_products': total_products,
                'total_users': total_users,
                'total_orders': total_orders,
                'total_revenue': float(total_revenue)
            })
        else:
            return Response({'error': 'Access denied'}, status=403)

class AdminProductsView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # Check if user is admin or manager
        if user.roleId.roleName in ['Администратор', 'Менеджер']:
            return Product.objects.all().select_related('categoryId', 'brandId')
        else:
            return Product.objects.none()

class AdminUsersView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # Check if user is admin or manager
        if user.roleId.roleName in ['Администратор', 'Менеджер']:
            return User.objects.all().select_related('roleId')
        else:
            return User.objects.none()

class AdminOrdersView(generics.ListAPIView):
    serializer_class = OrderSerializer  # We'll need to create this serializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # Check if user is admin or manager
        if user.roleId.roleName in ['Администратор', 'Менеджер']:
            return Order.objects.all().select_related('userId', 'orderStatusId')
        else:
            return Order.objects.none()
