from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from .models import Product, Category, Brand, ProductReview, Country, Currency

def product_list_view(request):
    """View to list products with advanced sidebar filters, searching, and sorting"""
    # Fetch filter options
    categories = Category.objects.all()
    brands = Brand.objects.all()
    
    # Query parameters
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '')
    brand_slug = request.GET.get('brand', '')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    socket = request.GET.get('socket', '')
    form_factor = request.GET.get('form_factor', '')
    ram_type = request.GET.get('ram_type', '')
    rgb = request.GET.get('rgb', '')
    availability = request.GET.get('availability', '')
    sort_by = request.GET.get('sort_by', 'popular')
    
    # Base Query
    products = Product.objects.select_related('brand', 'category').all()
    
    # Text Search (Instant & Voice search target)
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(brand__name__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__icontains=query)
        )
        
    # Categories & Brands
    if category_slug:
        products = products.filter(category__slug=category_slug)
    if brand_slug:
        products = products.filter(brand__slug=brand_slug)
        
    # Compatibility attributes
    if socket:
        products = products.filter(socket__iexact=socket)
    if form_factor:
        products = products.filter(form_factor__iexact=form_factor)
    if ram_type:
        products = products.filter(ram_type__iexact=ram_type)
    if rgb:
        products = products.filter(rgb_support=(rgb == 'true'))
        
    # Availability
    if availability == 'in_stock':
        products = products.filter(stock__gt=0)
    elif availability == 'out_of_stock':
        products = products.filter(stock=0)
        
    # Convert user inputs from selected currency back to base currency before querying
    selected_currency_id = request.session.get('currency_id')
    rate = 1.0
    if selected_currency_id:
        try:
            currency = Currency.objects.get(id=selected_currency_id)
            rate = float(currency.exchange_rate_to_usd)
        except (Currency.DoesNotExist, ValueError):
            pass
    else:
        selected_country_id = request.session.get('country_id')
        if selected_country_id:
            try:
                country = Country.objects.get(id=selected_country_id)
                rate = float(country.currency.exchange_rate_to_usd)
            except (Country.DoesNotExist, ValueError):
                pass

    if price_min:
        try:
            price_min_base = float(price_min) / rate
            products = products.filter(original_price_usd__gte=price_min_base)
        except ValueError:
            pass
    if price_max:
        try:
            price_max_base = float(price_max) / rate
            products = products.filter(original_price_usd__lte=price_max_base)
        except ValueError:
            pass

    # Sorting
    if sort_by == 'latest':
        products = products.order_by('-created_at')
    elif sort_by == 'price_low':
        # Sort on base USD final price
        products = products.order_by('original_price_usd')
    elif sort_by == 'price_high':
        products = products.order_by('-original_price_usd')
    elif sort_by == 'rating':
        products = products.order_by('-rating')
    else: # popular / default
        products = products.order_by('-is_featured', '-rating')

    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Dynamic sockets, form factors, RAM types for filters
    sockets = Product.objects.exclude(socket__isnull=True).exclude(socket='').values_list('socket', flat=True).distinct()
    form_factors = Product.objects.exclude(form_factor__isnull=True).exclude(form_factor='').values_list('form_factor', flat=True).distinct()
    ram_types = Product.objects.exclude(ram_type__isnull=True).exclude(ram_type='').values_list('ram_type', flat=True).distinct()

    # Get wishlist product ids
    wishlist_product_ids = []
    if request.user.is_authenticated:
        from orders.models import Wishlist
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        wishlist_product_ids = list(wishlist.products.values_list('id', flat=True))

    return render(request, 'products/catalog.html', {
        'page_obj': page_obj,
        'wishlist_product_ids': wishlist_product_ids,
        'categories': categories,
        'brands': brands,
        'sockets': sockets,
        'form_factors': form_factors,
        'ram_types': ram_types,
        'selected_category': category_slug,
        'selected_brand': brand_slug,
        'query': query,
        'price_min': price_min,
        'price_max': price_max,
        'selected_socket': socket,
        'selected_form_factor': form_factor,
        'selected_ram_type': ram_type,
        'selected_rgb': rgb,
        'selected_availability': availability,
        'selected_sort': sort_by,
    })

def product_detail_view(request, slug):
    """View showing detailed product details, specs list, and reviews"""
    product = get_object_or_404(Product.objects.select_related('brand', 'category'), slug=slug)
    
    # Fetch verified user purchase status for review form
    is_verified = False
    if request.user.is_authenticated:
        from orders.models import OrderItem
        is_verified = OrderItem.objects.filter(
            order__user=request.user, 
            order__status='DELIVERED', 
            product=product
        ).exists()
        
    # Handle Review Post
    if request.method == 'POST' and request.user.is_authenticated:
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        image = request.FILES.get('image')
        
        if rating:
            review, created = ProductReview.objects.update_or_create(
                product=product,
                user=request.user,
                defaults={
                    'rating': int(rating),
                    'comment': comment,
                    'image': image,
                    'is_verified_purchase': is_verified
                }
            )
            messages.success(request, "Review submitted successfully!")
            return redirect('product_detail', slug=slug)
        else:
            messages.error(request, "Please provide a star rating.")

    reviews = product.reviews.select_related('user').all()
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    
    # Calculate price based on selected country/currency session
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
            
    price_details = product.get_price_for_currency_and_country(currency, country)

    is_in_wishlist = False
    if request.user.is_authenticated:
        from orders.models import Wishlist
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        is_in_wishlist = wishlist.products.filter(id=product.id).exists()

    return render(request, 'products/detail.html', {
        'product': product,
        'reviews': reviews,
        'related_products': related_products,
        'is_verified': is_verified,
        'price_details': price_details,
        'is_in_wishlist': is_in_wishlist,
    })

def product_compare_view(request):
    """View to compare up to 4 products side by side"""
    product_ids_str = request.GET.get('ids', '')
    product_ids = [int(x) for x in product_ids_str.split(',') if x.isdigit()]
    
    products = Product.objects.filter(id__in=product_ids).select_related('category', 'brand')
    
    if not products.exists():
        messages.error(request, "Select products to compare.")
        return redirect('catalog')
        
    # Get common category to confirm we are comparing matching product types
    category = products.first().category
    
    # Resolve active currency for price row
    selected_currency_id = request.session.get('currency_id')
    rate = 1.0
    symbol = '₹'
    code = 'INR'
    if selected_currency_id:
        try:
            currency = Currency.objects.get(id=selected_currency_id)
            rate = float(currency.exchange_rate_to_usd)
            symbol = currency.symbol
            code = currency.code
        except (Currency.DoesNotExist, ValueError):
            pass
    else:
        selected_country_id = request.session.get('country_id')
        if selected_country_id:
            try:
                country = Country.objects.get(id=selected_country_id)
                rate = float(country.currency.exchange_rate_to_usd)
                symbol = country.currency.symbol
                code = country.currency.code
            except (Country.DoesNotExist, ValueError):
                pass

    # List of specification headers to check
    spec_headers = [
        ('Component Name', lambda p: f"{p.brand.name} {p.name}"),
        (f'Price ({code})', lambda p: f"{symbol} {float(p.final_price_usd) * rate:,.2f}"),
        ('Brand', lambda p: p.brand.name),
        ('Power (TDP)', lambda p: f"{p.power_consumption_watts} W" if p.power_consumption_watts else "N/A"),
        ('RGB Support', lambda p: "Yes" if p.rgb_support else "No"),
        ('Warranty', lambda p: f"{p.warranty_years} Years"),
        ('Socket', lambda p: p.socket or "N/A"),
        ('RAM Type', lambda p: p.ram_type or "N/A"),
        ('RAM Speed', lambda p: f"{p.ram_speed} MHz" if p.ram_speed else "N/A"),
        ('Form Factor', lambda p: p.form_factor or "N/A"),
        ('PCIe Version', lambda p: p.pcie_version or "N/A"),
        ('Cooler Height Limit', lambda p: f"{p.max_cooler_height} mm" if p.max_cooler_height else "N/A"),
        ('GPU Length Limit', lambda p: f"{p.gpu_length_limit} mm" if p.gpu_length_limit else "N/A"),
    ]
    
    comparison_table = []
    for header, extractor in spec_headers:
        row = {'header': header, 'values': []}
        # Check if at least one product has a value for this spec header
        has_any_data = False
        for p in products:
            val = extractor(p)
            row['values'].append(val)
            if val != "N/A" and val != "":
                has_any_data = True
        if has_any_data:
            comparison_table.append(row)
            
    return render(request, 'products/compare.html', {
        'products': products,
        'comparison_table': comparison_table,
        'category': category
    })

def search_autocomplete_view(request):
    """AJAX endpoint for instant search dropdown suggestions"""
    term = request.GET.get('term', '').strip()
    if len(term) < 2:
        return JsonResponse([], safe=False)
        
    products = Product.objects.filter(
        Q(name__icontains=term) | Q(brand__name__icontains=term)
    ).select_related('brand')[:8]
    
    selected_currency_id = request.session.get('currency_id')
    rate = 1.0
    symbol = '₹'
    if selected_currency_id:
        try:
            currency = Currency.objects.get(id=selected_currency_id)
            rate = float(currency.exchange_rate_to_usd)
            symbol = currency.symbol
        except (Currency.DoesNotExist, ValueError):
            pass
    else:
        selected_country_id = request.session.get('country_id')
        if selected_country_id:
            try:
                country = Country.objects.get(id=selected_country_id)
                rate = float(country.currency.exchange_rate_to_usd)
                symbol = country.currency.symbol
            except (Country.DoesNotExist, ValueError):
                pass
                
    results = []
    for p in products:
        local_price = float(p.final_price_usd) * rate
        results.append({
            'label': f"{p.brand.name} {p.name}",
            'value': f"{p.brand.name} {p.name}",
            'url': f"/products/detail/{p.slug}/",
            'price': f"{symbol} {local_price:,.2f}",
            'image': p.image.url if p.image else ''
        })
        
    return JsonResponse(results, safe=False)

def select_country_view(request, country_id):
    """View to change the global selected country/currency session variable"""
    country = get_object_or_404(Country, id=country_id)
    request.session['country_id'] = country.id
    if hasattr(country, 'currency') and country.currency:
        request.session['currency_id'] = country.currency.id
    messages.success(request, f"Country switched to {country.name} ({country.currency.symbol})")
    return redirect(request.META.get('HTTP_REFERER', '/'))

def select_currency_view(request, currency_id):
    """View to change the global selected currency session variable"""
    currency = get_object_or_404(Currency, id=currency_id)
    request.session['currency_id'] = currency.id
    
    # Also find a matching country to update country_id for shipping/tax
    matching_country = Country.objects.filter(currency=currency).first()
    if matching_country:
        request.session['country_id'] = matching_country.id
        
    messages.success(request, f"Currency switched to {currency.name} ({currency.symbol} {currency.code})")
    return redirect(request.META.get('HTTP_REFERER', '/'))
