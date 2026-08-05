from django.contrib import admin
from .models import Coupon, Cart, CartItem, Wishlist, Order, OrderItem, Payment, Invoice, Notification, Inventory, StockHistory

class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'email', 'status', 'grand_total_usd', 'created_at')
    list_editable = ('status',)
    list_filter = ('status', 'country')
    search_fields = ('order_number', 'email', 'phone_number')

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'payment_method', 'transaction_id', 'status', 'amount_paid', 'currency_code')
    list_filter = ('payment_method', 'status')

admin.site.register(Coupon)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Wishlist)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Invoice)
admin.site.register(Notification)
admin.site.register(Inventory)
admin.site.register(StockHistory)
