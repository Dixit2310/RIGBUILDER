from django.db import models
from django.conf import settings
from products.models import Product, Country
from builder.models import PCBuild
from django.utils.crypto import get_random_string

class Coupon(models.Model):
    class DiscountType(models.TextChoices):
        PERCENTAGE = 'PERCENTAGE', 'Percentage'
        FIXED = 'FIXED', 'Fixed Amount (USD)'
        
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DiscountType.choices, default=DiscountType.PERCENTAGE)
    value = models.DecimalField(max_digits=10, decimal_places=2) # e.g. 10.00 for 10% or $10
    expiry_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)

    def is_valid(self):
        from django.utils import timezone
        return self.is_active and self.expiry_date > timezone.now() and (self.max_uses is None or self.used_count < self.max_uses)

    def __str__(self):
        return f"{self.code} ({self.value} {self.discount_type})"

class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='cart')
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart {self.id} (User: {self.user.username if self.user else 'Guest'})"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    pc_build = models.ForeignKey(PCBuild, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    def get_subtotal_usd(self):
        if self.pc_build:
            return self.pc_build.calculate_total_price_usd() * self.quantity
        elif self.product:
            return self.product.final_price_usd * self.quantity
        return 0

    def __str__(self):
        item_name = self.product.name if self.product else (self.pc_build.name if self.pc_build else "Unknown Item")
        return f"{self.quantity} x {item_name}"

class Wishlist(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
    products = models.ManyToManyField(Product, blank=True, related_name='wishlisted_by')
    pc_builds = models.ManyToManyField(PCBuild, blank=True, related_name='wishlisted_by')

    def __str__(self):
        return f"Wishlist of {self.user.username}"

class Order(models.Model):
    class OrderStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        PACKED = 'PACKED', 'Packed'
        READY = 'READY', 'Ready for Shipping'
        SHIPPED = 'SHIPPED', 'Shipped'
        OUT_FOR_DELIVERY = 'OUT_FOR_DELIVERY', 'Out For Delivery'
        DELIVERED = 'DELIVERED', 'Delivered'
        CANCELLED = 'CANCELLED', 'Cancelled'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    order_number = models.CharField(max_length=50, unique=True)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    
    # localized price calculations stored at time of order
    country = models.ForeignKey(Country, on_delete=models.PROTECT)
    shipping_address = models.TextField()
    billing_address = models.TextField()
    
    # Financial details in USD (Base)
    subtotal_usd = models.DecimalField(max_digits=12, decimal_places=2)
    discount_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_usd = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_usd = models.DecimalField(max_digits=12, decimal_places=2)
    grand_total_usd = models.DecimalField(max_digits=12, decimal_places=2)
    
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=30, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = 'ORD-' + get_random_string(12).upper()
        super().save(*args, **kwargs)

    @property
    def grand_total_local(self):
        rate = self.country.currency.exchange_rate_to_usd
        return round(self.grand_total_usd * rate, 2)

    @property
    def is_custom_assembly(self):
        """Returns True if any item in the order is a custom PC configuration build"""
        return self.items.filter(pc_build__isnull=False).exists()

    @property
    def is_cancellable(self):
        """
        Component orders can be cancelled before shipping.
        Custom assembly orders can be cancelled before shipping, but conditions apply.
        Cannot cancel if shipped, out for delivery, or delivered, or already cancelled.
        """
        if self.status in [self.OrderStatus.SHIPPED, self.OrderStatus.OUT_FOR_DELIVERY, self.OrderStatus.DELIVERED, self.OrderStatus.CANCELLED]:
            return False
        return True

    @property
    def restocking_fee_applies(self):
        """
        Returns True if a 15% restocking fee applies to cancellation.
        Applies to custom assembly orders if:
        - 24 hours have passed since order placement, OR
        - status is PACKED or READY for shipping.
        """
        if not self.is_custom_assembly:
            return False
            
        from django.utils import timezone
        hours_since_placement = (timezone.now() - self.created_at).total_seconds() / 3600.0
        
        if hours_since_placement > 24.0 or self.status in [self.OrderStatus.PACKED, self.OrderStatus.READY]:
            return True
            
        return False

    def __str__(self):
        return f"{self.order_number} ({self.status})"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    pc_build = models.ForeignKey(PCBuild, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price_usd = models.DecimalField(max_digits=12, decimal_places=2) # Snapshotted price at order

    @property
    def price_local(self):
        rate = self.order.country.currency.exchange_rate_to_usd
        return round(self.price_usd * rate, 2)

    def __str__(self):
        name = self.product.name if self.product else (self.pc_build.name if self.pc_build else "Item")
        return f"{self.quantity} x {name} for Order {self.order.order_number}"

class Payment(models.Model):
    class PaymentMethod(models.TextChoices):
        RAZORPAY = 'RAZORPAY', 'Razorpay'
        STRIPE = 'STRIPE', 'Stripe'
        PAYPAL = 'PAYPAL', 'PayPal'
        COD = 'COD', 'Cash On Delivery'

    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2) # Local currency
    currency_code = models.CharField(max_length=10) # Local currency code e.g. INR, USD
    payment_data = models.TextField(blank=True, null=True) # Full payload JSON in text format
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.id} for Order {self.order.order_number} ({self.status})"

class Invoice(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=50, unique=True)
    pdf_file = models.FileField(upload_to='invoices/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = 'INV-' + get_random_string(10).upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.invoice_number

class Notification(models.Model):
    class NotificationType(models.TextChoices):
        ORDER = 'ORDER', 'Order Notification'
        SHIPPING = 'SHIPPING', 'Shipping Alert'
        ACCOUNT = 'ACCOUNT', 'Account/Security'
        PROMOTION = 'PROMOTION', 'Offers and Promos'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=150)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices, default=NotificationType.ORDER)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} for {self.user.username}"

class Inventory(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='inventory')
    total_stock = models.PositiveIntegerField(default=10)
    reserved_stock = models.PositiveIntegerField(default=0) # Stock in active unpaid carts or pending orders
    low_stock_threshold = models.PositiveIntegerField(default=3)
    last_restocked = models.DateTimeField(auto_now=True)

    @property
    def available_stock(self):
        return max(0, self.total_stock - self.reserved_stock)

    def __str__(self):
        return f"Inventory for {self.product.name} (Stock: {self.total_stock})"

class StockHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_history')
    change_amount = models.IntegerField() # Positive for restocking, negative for sales
    notes = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Stock Histories"

    def __str__(self):
        return f"Stock Change: {self.product.name} ({self.change_amount:+d}) at {self.created_at}"
