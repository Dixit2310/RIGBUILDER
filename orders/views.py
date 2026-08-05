from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db import transaction

from products.models import Product, Country, Currency
from accounts.models import Address
from builder.models import PCBuild
from .models import Cart, CartItem, Wishlist, Order, OrderItem, Coupon, Payment, Invoice, Notification, Inventory, StockHistory
from .utils import generate_invoice_pdf

def get_or_create_cart(request):
    """Retrieves or initializes the cart for a user (or session-based guest)"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return cart
    else:
        # Session-based cart for guest users
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
        return cart

def cart_view(request):
    cart = get_or_create_cart(request)
    
    # Selected Country details for currency conversion
    selected_country_id = request.session.get('country_id')
    country = Country.objects.filter(id=selected_country_id).first()
    if not country:
        country = Country.objects.first()

    # Calculate pricing totals
    subtotal_usd = sum(item.get_subtotal_usd() for item in cart.items.all())
    
    # Coupon discount calculation
    coupon_id = request.session.get('applied_coupon_id')
    discount_usd = 0.00
    applied_coupon = None
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            if coupon.is_valid():
                applied_coupon = coupon
                if coupon.discount_type == Coupon.DiscountType.PERCENTAGE:
                    discount_usd = float(subtotal_usd) * (float(coupon.value) / 100)
                else:
                    discount_usd = float(coupon.value)
            else:
                del request.session['applied_coupon_id']
        except Coupon.DoesNotExist:
            del request.session['applied_coupon_id']

    subtotal_after_discount = max(0.00, float(subtotal_usd) - discount_usd)
    
    # Resolve active currency
    selected_currency_id = request.session.get('currency_id')
    selected_currency = None
    if selected_currency_id:
        selected_currency = Currency.objects.filter(id=selected_currency_id).first()

    if selected_currency:
        rate = selected_currency.exchange_rate_to_usd
        symbol = selected_currency.symbol
    elif country:
        rate = country.currency.exchange_rate_to_usd
        symbol = country.currency.symbol
    else:
        rate = 1.0
        symbol = "$"
    
    tax_rate = country.default_tax_rate if country else 18.0
    tax_usd = subtotal_after_discount * (float(tax_rate) / 100)
    
    shipping_usd = float(country.default_shipping_charge) if country and subtotal_usd > 0 else 0.00
    grand_total_usd = subtotal_after_discount + tax_usd + shipping_usd

    # Local Currency Conversions
    context = {
        'cart': cart,
        'coupon': applied_coupon,
        'country': country,
        'symbol': symbol,
        'subtotal': round(float(subtotal_usd) * float(rate), 2),
        'discount': round(float(discount_usd) * float(rate), 2),
        'tax': round(float(tax_usd) * float(rate), 2),
        'shipping': round(float(shipping_usd) * float(rate), 2),
        'grand_total': round(float(grand_total_usd) * float(rate), 2),
    }
    return render(request, 'orders/cart.html', context)

def cart_add_view(request, product_id):
    cart = get_or_create_cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    
    # Check inventory
    inventory = Inventory.objects.filter(product=product).first()
    available = inventory.available_stock if inventory else product.stock
    
    if available < quantity:
        msg = f"Cannot add quantity. Only {available} units available in stock."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('accept') == 'application/json':
            return JsonResponse({'status': 'error', 'message': msg})
        messages.error(request, msg)
        return redirect(request.META.get('HTTP_REFERER', 'catalog'))

    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += quantity
    else:
        item.quantity = quantity
    item.save()
    
    msg = f"Added {product.name} to your cart."
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('accept') == 'application/json':
        return JsonResponse({'status': 'success', 'message': msg})
        
    messages.success(request, msg)
    return redirect('cart')

def cart_add_build_view(request, build_id):
    cart = get_or_create_cart(request)
    build = get_object_or_404(PCBuild, id=build_id)
    
    item, created = CartItem.objects.get_or_create(cart=cart, pc_build=build)
    if not created:
        item.quantity += 1
    item.save()
    
    msg = f"Added configuration '{build.name}' to your cart."
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('accept') == 'application/json':
        return JsonResponse({'status': 'success', 'message': msg})
        
    messages.success(request, msg)
    return redirect('cart')

def cart_remove_view(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    name = item.product.name if item.product else item.pc_build.name
    item.delete()
    messages.success(request, f"Removed {name} from your cart.")
    return redirect('cart')

def cart_update_quantity_view(request, item_id, action):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    
    if action == 'increase':
        # Check stock limits
        if item.product:
            inventory = Inventory.objects.filter(product=item.product).first()
            available = inventory.available_stock if inventory else item.product.stock
            if item.quantity >= available:
                messages.error(request, "Out of stock / Maximum inventory reached.")
                return redirect('cart')
        item.quantity += 1
        item.save()
    elif action == 'decrease':
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()
            
    return redirect('cart')

def apply_coupon_view(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code', '').strip()
        coupon = Coupon.objects.filter(code__iexact=code, is_active=True).first()
        
        if coupon and coupon.is_valid():
            request.session['applied_coupon_id'] = coupon.id
            messages.success(request, f"Coupon '{coupon.code}' applied successfully!")
        else:
            messages.error(request, "Invalid, expired, or deactivated coupon code.")
            
    return redirect('cart')

@login_required
def checkout_view(request):
    cart = get_or_create_cart(request)
    if not cart.items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('cart')
        
    addresses = request.user.addresses.all()
    if not addresses.exists():
        messages.warning(request, "Please configure at least one billing/shipping address first.")
        return redirect('address_add')
        
    # Totals calculation
    selected_country_id = request.session.get('country_id')
    country = Country.objects.filter(id=selected_country_id).first() or Country.objects.first()
    
    subtotal_usd = sum(item.get_subtotal_usd() for item in cart.items.all())
    
    coupon_id = request.session.get('applied_coupon_id')
    discount_usd = 0.00
    applied_coupon = None
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            if coupon.is_valid():
                applied_coupon = coupon
                if coupon.discount_type == Coupon.DiscountType.PERCENTAGE:
                    discount_usd = float(subtotal_usd) * (float(coupon.value) / 100)
                else:
                    discount_usd = float(coupon.value)
        except Coupon.DoesNotExist:
            pass
            
    subtotal_after_discount = max(0.00, float(subtotal_usd) - discount_usd)
    tax_rate = country.default_tax_rate
    tax_usd = subtotal_after_discount * (float(tax_rate) / 100)
    shipping_usd = float(country.default_shipping_charge)
    grand_total_usd = subtotal_after_discount + tax_usd + shipping_usd
    # Resolve active currency
    selected_currency_id = request.session.get('currency_id')
    selected_currency = None
    if selected_currency_id:
        selected_currency = Currency.objects.filter(id=selected_currency_id).first()

    if selected_currency:
        rate = selected_currency.exchange_rate_to_usd
        symbol = selected_currency.symbol
    elif country:
        rate = country.currency.exchange_rate_to_usd
        symbol = country.currency.symbol
    else:
        rate = 1.0
        symbol = "$"

    context = {
        'cart': cart,
        'addresses': addresses,
        'coupon': applied_coupon,
        'country': country,
        'symbol': symbol,
        'subtotal': round(float(subtotal_usd) * float(rate), 2),
        'discount': round(float(discount_usd) * float(rate), 2),
        'tax': round(float(tax_usd) * float(rate), 2),
        'shipping': round(float(shipping_usd) * float(rate), 2),
        'grand_total': round(float(grand_total_usd) * float(rate), 2),
    }
    return render(request, 'orders/checkout.html', context)

@login_required
def place_order_view(request):
    if request.method != 'POST':
        return redirect('checkout')
        
    cart = get_or_create_cart(request)
    if not cart.items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('cart')

    shipping_address_id = request.POST.get('shipping_address')
    billing_address_id = request.POST.get('billing_address')
    payment_method = request.POST.get('payment_method', 'COD')

    if not shipping_address_id or not billing_address_id:
        messages.error(request, "Please select both billing and shipping addresses.")
        return redirect('checkout')

    shipping_addr = get_object_or_404(Address, id=shipping_address_id, user=request.user)
    billing_addr = get_object_or_404(Address, id=billing_address_id, user=request.user)

    # Localized Calculations
    selected_country_id = request.session.get('country_id')
    country = Country.objects.filter(id=selected_country_id).first() or Country.objects.first()
    
    subtotal_usd = sum(item.get_subtotal_usd() for item in cart.items.all())
    
    coupon_id = request.session.get('applied_coupon_id')
    discount_usd = 0.00
    applied_coupon = None
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            if coupon.is_valid():
                applied_coupon = coupon
                if coupon.discount_type == Coupon.DiscountType.PERCENTAGE:
                    discount_usd = float(subtotal_usd) * (float(coupon.value) / 100)
                else:
                    discount_usd = float(coupon.value)
                coupon.used_count += 1
                coupon.save()
        except Coupon.DoesNotExist:
            pass

    subtotal_after_discount = max(0.00, float(subtotal_usd) - discount_usd)
    tax_usd = subtotal_after_discount * (float(country.default_tax_rate) / 100)
    shipping_usd = float(country.default_shipping_charge)
    grand_total_usd = subtotal_after_discount + tax_usd + shipping_usd

    # Create Order object inside transaction
    with transaction.atomic():
        order = Order.objects.create(
            user=request.user,
            email=request.user.email or "customer@example.com",
            phone_number=shipping_addr.phone_number or request.user.phone_number or "9999999999",
            country=country,
            shipping_address=f"{shipping_addr.full_name}\n{shipping_addr.street_address}, {shipping_addr.city}, {shipping_addr.state} - {shipping_addr.postal_code}\nPhone: {shipping_addr.phone_number}",
            billing_address=f"{billing_addr.full_name}\n{billing_addr.street_address}, {billing_addr.city}, {billing_addr.state} - {billing_addr.postal_code}\nPhone: {billing_addr.phone_number}",
            subtotal_usd=subtotal_usd,
            discount_usd=discount_usd,
            tax_usd=tax_usd,
            shipping_usd=shipping_usd,
            grand_total_usd=grand_total_usd,
            coupon=applied_coupon,
            status=Order.OrderStatus.CONFIRMED if payment_method == 'COD' else Order.OrderStatus.PENDING
        )

        # Move cart items to order items and update inventory
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                pc_build=item.pc_build,
                quantity=item.quantity,
                price_usd=item.product.final_price_usd if item.product else item.pc_build.calculate_total_price_usd()
            )
            
            # Decrease product stock and record history
            if item.product:
                product = item.product
                product.stock = max(0, product.stock - item.quantity)
                product.save()
                
                # Update inventory details
                inventory = Inventory.objects.filter(product=product).first()
                if inventory:
                    inventory.total_stock = product.stock
                    inventory.save()
                
                StockHistory.objects.create(
                    product=product,
                    change_amount=-item.quantity,
                    notes=f"Sold in order {order.order_number}"
                )
            elif item.pc_build:
                # Deduct stock for all components of the build
                build = item.pc_build
                parts = [
                    build.cpu, build.motherboard, build.ram, build.gpu, build.ssd, build.hdd,
                    build.nvme, build.psu, build.cabinet, build.cpu_cooler, build.case_fans
                ]
                for part in parts:
                    if part:
                        part.stock = max(0, part.stock - item.quantity)
                        part.save()
                        inventory = Inventory.objects.filter(product=part).first()
                        if inventory:
                            inventory.total_stock = part.stock
                            inventory.save()
                        StockHistory.objects.create(
                            product=part,
                            change_amount=-item.quantity,
                            notes=f"Sold as part of build '{build.name}' in order {order.order_number}"
                        )

        # Clear cart and coupon session
        cart.items.all().delete()
        if 'applied_coupon_id' in request.session:
            del request.session['applied_coupon_id']

    # Simulate payment gateways and route accordingly
    if payment_method == 'COD':
        # Create Payment
        Payment.objects.create(
            order=order,
            payment_method=Payment.payment_method.COD,
            status=Payment.PaymentStatus.COMPLETED,
            amount_paid=order.grand_total_local,
            currency_code=country.currency.code
        )
        Invoice.objects.create(order=order)
        Notification.objects.create(
            user=request.user,
            title="Order Placed Successfully",
            message=f"Thank you for placing order {order.order_number}. We are preparing your shipment!",
            notification_type=Notification.NotificationType.ORDER
        )
        messages.success(request, f"Order {order.order_number} placed successfully using Cash on Delivery!")
        return redirect('order_tracking', order_number=order.order_number)
    else:
        # Simulate redirection to payment success page for other online methods
        # This allows 100% local testing of Stripe/PayPal flow
        return redirect('simulate_payment', order_number=order.order_number, method=payment_method)

def simulate_payment_view(request, order_number, method):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'orders/payment_gateway.html', {
        'order': order,
        'method': method
    })

def payment_success_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    method = request.GET.get('method', 'STRIPE')
    
    # Finalize payment state
    with transaction.atomic():
        order.status = Order.OrderStatus.CONFIRMED
        order.save()
        
        Payment.objects.create(
            order=order,
            payment_method=method,
            transaction_id=f"TXN-{timezone.now().strftime('%Y%H%M%S')}",
            status=Payment.PaymentStatus.COMPLETED,
            amount_paid=order.grand_total_local,
            currency_code=order.country.currency.code
        )
        
        Invoice.objects.create(order=order)
        
        Notification.objects.create(
            user=request.user,
            title="Online Payment Complete",
            message=f"Payment for order {order.order_number} was successfully processed via {method}.",
            notification_type=Notification.NotificationType.ORDER
        )
        
    messages.success(request, f"Online payment processed successfully via {method}! Order confirmed.")
    return redirect('order_tracking', order_number=order.order_number)

def order_tracking_view(request, order_number):
    if request.user.is_staff or request.user.is_superuser or getattr(request.user, 'role', '') == 'ADMIN':
        order = get_object_or_404(Order, order_number=order_number)
    else:
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    # Progress bars details
    status_steps = [
        ('PENDING', 'Pending', 10),
        ('CONFIRMED', 'Confirmed', 25),
        ('PACKED', 'Packed', 45),
        ('READY', 'Ready', 60),
        ('SHIPPED', 'Shipped', 75),
        ('OUT_FOR_DELIVERY', 'Out For Delivery', 90),
        ('DELIVERED', 'Delivered', 100),
    ]
    
    current_progress = 10
    step_index = 0
    for idx, (code, label, pct) in enumerate(status_steps):
        if order.status == code:
            current_progress = pct
            step_index = idx
            break
            
    # timeline logs
    timeline = []
    for idx, (code, label, pct) in enumerate(status_steps):
        is_completed = idx <= step_index
        timeline.append({
            'label': label,
            'completed': is_completed,
            'date': order.updated_at if is_completed and order.status == code else None
        })

    return render(request, 'orders/tracking.html', {
        'order': order,
        'timeline': timeline,
        'progress': current_progress,
        'delivery_date': order.created_at + timezone.timedelta(days=5)
    })

@login_required
def order_history_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/history.html', {'orders': orders})

@login_required
def reorder_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    cart = get_or_create_cart(request)
    
    for item in order.items.all():
        if item.product:
            CartItem.objects.create(cart=cart, product=item.product, quantity=item.quantity)
        elif item.pc_build:
            CartItem.objects.create(cart=cart, pc_build=item.pc_build, quantity=item.quantity)
            
    messages.success(request, "Items from order copied back to your cart.")
    return redirect('cart')

def invoice_download_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    
    # Secure access: check user ownership
    if request.user.is_authenticated and order.user != request.user and not request.user.is_staff:
        return HttpResponse("Unauthorized", status=403)
        
    pdf_bytes = generate_invoice_pdf(order)
    
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="invoice_{order.order_number}.pdf"'
    return response

@login_required
def cancel_order_view(request, order_number):
    from .models import Order, Payment, Inventory, Notification
    
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    if not order.is_cancellable:
        messages.error(request, "This order cannot be cancelled as it has already shipped or completed.")
        return redirect('order_history')
        
    restocking_fee = 0
    refund_percentage = 100
    
    if order.restocking_fee_applies:
        restocking_fee = 15
        refund_percentage = 85
        
    order.status = Order.OrderStatus.CANCELLED
    order.save()
    
    # Refund logic (simulate payment refund status update)
    if hasattr(order, 'payment') and order.payment:
        payment = order.payment
        payment.status = Payment.PaymentStatus.REFUNDED
        payment.save()
        
    # Restore inventory stock if cancelled
    for item in order.items.all():
        if item.product:
            inventory = Inventory.objects.filter(product=item.product).first()
            if inventory:
                inventory.total_stock += item.quantity
                inventory.save()
                
    # Create notification for user
    Notification.objects.create(
        user=request.user,
        title=f"Order Cancelled: {order.order_number}",
        message=(
            f"Your order {order.order_number} has been successfully cancelled. "
            f"A refund of {refund_percentage}% has been processed back to your payment method "
            f"(Restocking Fee: {restocking_fee}%)."
        ),
        notification_type=Notification.NotificationType.ORDER
    )
    
    if restocking_fee > 0:
        messages.warning(
            request, 
            f"Order {order.order_number} cancelled. A 15% restocking fee was applied. "
            f"An 85% refund of local currency has been initiated."
        )
    else:
        messages.success(
            request, 
            f"Order {order.order_number} cancelled successfully. "
            f"A full refund has been initiated."
        )
        
    return redirect('order_history')


@login_required
def wishlist_view(request):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    products = wishlist.products.select_related('brand', 'category').all()
    pc_builds = wishlist.pc_builds.all()
    
    # Resolve active currency for price display
    selected_currency_id = request.session.get('currency_id')
    selected_country_id = request.session.get('country_id')
    
    currency = None
    if selected_currency_id:
        try:
            currency = Currency.objects.get(id=selected_currency_id)
        except Currency.DoesNotExist:
            pass
            
    country = None
    if selected_country_id:
        try:
            country = Country.objects.get(id=selected_country_id)
        except Country.DoesNotExist:
            pass
            
    if not currency:
        if country:
            currency = country.currency
        else:
            currency = Currency.objects.filter(code='INR').first() or Currency.objects.first()
            
    # Annotate/format pricing details for each product
    wishlist_items = []
    for product in products:
        price_details = product.get_price_for_currency_and_country(currency, country)
        wishlist_items.append({
            'product': product,
            'price_details': price_details
        })
        
    context = {
        'wishlist_items': wishlist_items,
        'pc_builds': pc_builds,
        'selected_currency': currency,
        'selected_country': country,
    }
    return render(request, 'orders/wishlist.html', context)


@login_required
def wishlist_toggle_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    if wishlist.products.filter(id=product.id).exists():
        wishlist.products.remove(product)
        added = False
        msg = f"Removed {product.name} from your wishlist."
    else:
        wishlist.products.add(product)
        added = True
        msg = f"Added {product.name} to your wishlist."
        
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('accept') == 'application/json':
        return JsonResponse({
            'status': 'success',
            'added': added,
            'message': msg,
            'wishlist_count': wishlist.products.count() + wishlist.pc_builds.count()
        })
        
    messages.success(request, msg)
    return redirect(request.META.get('HTTP_REFERER', 'wishlist'))


@login_required
def wishlist_toggle_build_view(request, build_id):
    build = get_object_or_404(PCBuild, id=build_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    if wishlist.pc_builds.filter(id=build.id).exists():
        wishlist.pc_builds.remove(build)
        added = False
        msg = f"Removed configuration '{build.name}' from your wishlist."
    else:
        wishlist.pc_builds.add(build)
        added = True
        msg = f"Added configuration '{build.name}' to your wishlist."
        
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('accept') == 'application/json':
        return JsonResponse({
            'status': 'success',
            'added': added,
            'message': msg,
            'wishlist_count': wishlist.products.count() + wishlist.pc_builds.count()
        })
        
    messages.success(request, msg)
    return redirect(request.META.get('HTTP_REFERER', 'wishlist'))

