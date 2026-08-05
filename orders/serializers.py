from rest_framework import serializers
from .models import Coupon, Cart, CartItem, Wishlist, Order, OrderItem, Payment, Invoice, Notification
from products.serializers import ProductListSerializer
from builder.serializers import PCBuildSerializer

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ['id', 'code', 'discount_type', 'value', 'expiry_date', 'is_active']

class CartItemSerializer(serializers.ModelSerializer):
    product_details = ProductListSerializer(source='product', read_only=True)
    pc_build_details = PCBuildSerializer(source='pc_build', read_only=True)
    subtotal = serializers.DecimalField(source='get_subtotal_usd', max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'pc_build', 'quantity', 'product_details', 'pc_build_details', 'subtotal']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'session_key', 'items', 'total_price', 'created_at', 'updated_at']

    def get_total_price(self, obj):
        return sum(item.get_subtotal_usd() for item in obj.items.all())

class OrderItemSerializer(serializers.ModelSerializer):
    product_details = ProductListSerializer(source='product', read_only=True)
    pc_build_details = PCBuildSerializer(source='pc_build', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'pc_build', 'quantity', 'price_usd', 'product_details', 'pc_build_details']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'payment_method', 'transaction_id', 'status', 'amount_paid', 'currency_code', 'created_at']

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ['id', 'invoice_number', 'pdf_file', 'created_at']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payment = PaymentSerializer(read_only=True)
    invoice = InvoiceSerializer(read_only=True)
    country_name = serializers.CharField(source='country.name', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'email', 'phone_number', 'country', 'country_name',
            'shipping_address', 'billing_address', 'subtotal_usd', 'discount_usd', 
            'tax_usd', 'shipping_usd', 'grand_total_usd', 'coupon', 'status', 
            'items', 'payment', 'invoice', 'created_at', 'updated_at'
        ]
        read_only_fields = ['order_number', 'status', 'created_at', 'updated_at']

class WishlistSerializer(serializers.ModelSerializer):
    products = ProductListSerializer(many=True, read_only=True)
    pc_builds = PCBuildSerializer(many=True, read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'products', 'pc_builds']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'notification_type', 'is_read', 'created_at']
