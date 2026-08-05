from products.models import Country, Currency, Category
from orders.models import Cart, Wishlist, Notification
from django.db import connection

def global_settings(request):
    # Safe check: if tables don't exist yet, return empty dict to prevent migrations from crashing
    db_tables = connection.introspection.table_names()
    if 'products_country' not in db_tables or 'orders_cart' not in db_tables:
        return {}

    # Get all countries and currencies for country selector
    countries = Country.objects.select_related('currency').all()
    currencies = Currency.objects.all()
    
    # Get or set selected country in session
    selected_country_id = request.session.get('country_id')
    selected_country = None
    
    if selected_country_id:
        try:
            selected_country = Country.objects.select_related('currency').get(id=selected_country_id)
        except Country.DoesNotExist:
            pass
            
    if not selected_country:
        # Fallback: Get India, USA, or first available country
        selected_country = Country.objects.filter(code='IN').first() or Country.objects.filter(code='US').first() or Country.objects.first()
        if selected_country:
            request.session['country_id'] = selected_country.id

    # Get or set selected currency in session
    selected_currency_id = request.session.get('currency_id')
    selected_currency = None
    
    if selected_currency_id:
        try:
            selected_currency = Currency.objects.get(id=selected_currency_id)
        except Currency.DoesNotExist:
            pass
            
    if not selected_currency:
        if selected_country:
            selected_currency = selected_country.currency
        else:
            selected_currency = Currency.objects.filter(code='INR').first() or Currency.objects.filter(code='USD').first() or Currency.objects.first()
        if selected_currency:
            request.session['currency_id'] = selected_currency.id

    # Cart item count calculation
    cart_count = 0
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart_count = sum(item.quantity for item in cart.items.all())
    else:
        # Check session cart for guests
        session_key = request.session.session_key
        if session_key:
            cart = Cart.objects.filter(session_key=session_key).first()
            if cart:
                cart_count = sum(item.quantity for item in cart.items.all())

    # Wishlist count calculation
    wishlist_count = 0
    if request.user.is_authenticated:
        wishlist = Wishlist.objects.filter(user=request.user).first()
        if wishlist:
            wishlist_count = wishlist.products.count() + wishlist.pc_builds.count()

    # Unread notifications
    unread_notifications_count = 0
    if request.user.is_authenticated:
        unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()

    # Fetch categories for navigation dropdown
    categories_list = Category.objects.all().order_by('name')

    return {
        'countries': countries,
        'selected_country': selected_country,
        'currencies': currencies,
        'selected_currency': selected_currency,
        'cart_count': cart_count,
        'wishlist_count': wishlist_count,
        'unread_notifications_count': unread_notifications_count,
        'nav_categories': categories_list,
    }
