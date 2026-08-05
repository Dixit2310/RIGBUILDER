from rest_framework import viewsets, permissions, status, views
from rest_framework.response import Response
from rest_framework.decorators import action

from accounts.models import User, Address
from accounts.serializers import UserSerializer, RegisterSerializer, AddressSerializer

from products.models import Brand, Category, Product, ProductReview
from products.serializers import BrandSerializer, CategorySerializer, ProductListSerializer, ProductDetailSerializer, ProductReviewSerializer

from builder.models import PCBuild, CompatibilityRule
from builder.serializers import PCBuildSerializer
from builder.compatibility import CompatibilityChecker
from builder.utils import calculate_performance_scores, estimate_fps, calculate_bottleneck, estimate_temperatures, estimate_build_time

from orders.models import Cart, CartItem, Wishlist, Order, OrderItem, Coupon, Payment, Notification
from orders.serializers import CartSerializer, CartItemSerializer, WishlistSerializer, OrderSerializer, CouponSerializer, NotificationSerializer

# --- AUTHENTICATION ENDPOINTS ---
class RegisterAPIView(views.APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
        
    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AddressViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AddressSerializer
    
    def get_queryset(self):
        return Address.objects.filter(user=self.user)
        
    @property
    def user(self):
        return self.request.user

    def perform_create(self, serializer):
        serializer.save(user=self.user)

# --- PRODUCT ENDPOINTS ---
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer

    def get_queryset(self):
        queryset = Product.objects.all()
        category = self.request.query_params.get('category')
        brand = self.request.query_params.get('brand')
        socket = self.request.query_params.get('socket')
        form_factor = self.request.query_params.get('form_factor')
        ram_type = self.request.query_params.get('ram_type')
        search = self.request.query_params.get('search')
        
        if category:
            queryset = queryset.filter(category__slug=category)
        if brand:
            queryset = queryset.filter(brand__slug=brand)
        if socket:
            queryset = queryset.filter(socket__iexact=socket)
        if form_factor:
            queryset = queryset.filter(form_factor__iexact=form_factor)
        if ram_type:
            queryset = queryset.filter(ram_type__iexact=ram_type)
        if search:
            queryset = queryset.filter(name__icontains=search) | queryset.filter(brand__name__icontains=search)
            
        return queryset

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer

class IsOwnerOrAdminOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user or request.user.is_staff or request.user.role == 'ADMIN' or request.user.is_superuser

class ProductReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrAdminOrReadOnly]
    
    def get_queryset(self):
        return ProductReview.objects.filter(product_id=self.request.query_params.get('product'))

    def perform_create(self, serializer):
        # Mark as verified purchase if user actually bought the item
        user = self.request.user
        product_id = self.request.data.get('product')
        is_verified = OrderItem.objects.filter(order__user=user, order__status='DELIVERED', product_id=product_id).exists()
        serializer.save(user=user, is_verified_purchase=is_verified)

# --- CART ENDPOINTS ---
class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Cart.objects.filter(user=self.request.user)
        session_key = self.request.session.session_key
        if not session_key:
            self.request.session.create()
            session_key = self.request.session.session_key
        return Cart.objects.filter(session_key=session_key)

    def get_object(self):
        queryset = self.get_queryset()
        obj = queryset.first()
        if not obj:
            if self.request.user.is_authenticated:
                obj = Cart.objects.create(user=self.request.user)
            else:
                session_key = self.request.session.session_key
                obj = Cart.objects.create(session_key=session_key)
        return obj

    @action(detail=False, methods=['post'])
    def add_item(self, request):
        cart = self.get_object()
        product_id = request.data.get('product')
        build_id = request.data.get('pc_build')
        quantity = int(request.data.get('quantity', 1))

        if product_id:
            item, created = CartItem.objects.get_or_create(cart=cart, product_id=product_id)
            if not created:
                item.quantity += quantity
            else:
                item.quantity = quantity
            item.save()
            return Response(CartItemSerializer(item).data)
            
        elif build_id:
            item, created = CartItem.objects.get_or_create(cart=cart, pc_build_id=build_id)
            if not created:
                item.quantity += quantity
            else:
                item.quantity = quantity
            item.save()
            return Response(CartItemSerializer(item).data)

        return Response({"error": "Provide product_id or pc_build_id"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        cart = self.get_object()
        item_id = request.data.get('item_id')
        try:
            item = CartItem.objects.get(cart=cart, id=item_id)
            item.delete()
            return Response({"success": "Item removed from cart"})
        except CartItem.DoesNotExist:
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)

# --- BUILDER ENDPOINTS ---
class PCBuildViewSet(viewsets.ModelViewSet):
    serializer_class = PCBuildSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return PCBuild.objects.filter(user=self.request.user)
        return PCBuild.objects.none()

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()

    @action(detail=True, methods=['get'])
    def check_compatibility(self, request, pk=None):
        build = self.get_object()
        checker = CompatibilityChecker(build)
        result = checker.check()
        return Response(result)

    @action(detail=True, methods=['get'])
    def get_estimates(self, request, pk=None):
        build = self.get_object()
        scores = calculate_performance_scores(build)
        fps = estimate_fps(build)
        bottleneck = calculate_bottleneck(build)
        temps = estimate_temperatures(build)
        build_time = estimate_build_time(build)

        return Response({
            'scores': scores,
            'fps': fps,
            'bottleneck': bottleneck,
            'temperatures': temps,
            'build_time': build_time
        })

# --- ORDER ENDPOINTS ---
class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# --- WISHLIST ENDPOINTS ---
class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

    def get_object(self):
        wishlist, created = Wishlist.objects.get_or_create(user=self.request.user)
        return wishlist

    @action(detail=False, methods=['post'])
    def toggle_product(self, request):
        wishlist = self.get_object()
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({"error": "Provide product_id"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        if wishlist.products.filter(id=product.id).exists():
            wishlist.products.remove(product)
            return Response({"success": f"Removed {product.name} from wishlist", "added": False})
        else:
            wishlist.products.add(product)
            return Response({"success": f"Added {product.name} to wishlist", "added": True})

