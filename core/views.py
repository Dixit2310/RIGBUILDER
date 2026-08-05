from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count, F, Q
from django.contrib.auth.decorators import user_passes_test

from products.models import Product, Category, Brand, Country, Currency
from builder.models import PCBuild
from orders.models import Order, Payment, Inventory
from accounts.models import User
from .models import BlogPost, FAQ, ContactRequest, NewsletterSubscriber, SupportTicket

def home_view(request):
    """Core landing page representing premium NZXT/Origin PC aesthetics"""
    featured_products = Product.objects.filter(is_featured=True)[:8]
    if not featured_products.exists():
        featured_products = Product.objects.all().order_by('-rating')[:8]
    categories = Category.objects.all()[:6]
    presets = PCBuild.objects.filter(is_preset=True)[:3]
    blogs = BlogPost.objects.order_by('-created_at')[:3]
    faqs = FAQ.objects.filter(is_active=True)[:4]

    return render(request, 'core/home.html', {
        'featured_products': featured_products,
        'categories': categories,
        'presets': presets,
        'blogs': blogs,
        'faqs': faqs
    })

def blog_list_view(request):
    blogs = BlogPost.objects.all().order_by('-created_at')
    return render(request, 'core/blog_list.html', {'blogs': blogs})

def blog_detail_view(request, slug):
    blog = get_object_or_404(BlogPost, slug=slug)
    recent_blogs = BlogPost.objects.exclude(id=blog.id).order_by('-created_at')[:3]
    return render(request, 'core/blog_detail.html', {'blog': blog, 'recent_blogs': recent_blogs})

def faq_view(request):
    faqs = FAQ.objects.filter(is_active=True)
    return render(request, 'core/faq.html', {'faqs': faqs})

def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        if name and email and message:
            ContactRequest.objects.create(
                name=name, email=email, subject=subject, message=message
            )
            messages.success(request, "Your contact message was delivered successfully. Our staff will contact you shortly!")
            return redirect('contact')
        else:
            messages.error(request, "Please fill in all required fields.")
            
    return render(request, 'core/contact.html')

def newsletter_subscribe_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if email:
            sub, created = NewsletterSubscriber.objects.get_or_create(email=email)
            if created:
                return JsonResponse({'status': 'success', 'message': 'Subscribed successfully to our newsletter!'})
            else:
                return JsonResponse({'status': 'info', 'message': 'You are already a subscriber!'})
        return JsonResponse({'status': 'error', 'message': 'Please provide a valid email.'})
    return redirect('home')

def is_admin(user):
    return user.is_authenticated and (user.role == 'ADMIN' or user.is_staff or user.is_superuser)

@user_passes_test(is_admin)
def admin_dashboard_view(request):
    """Custom Administrative Analytics Control Panel"""
    # Fetch active currency exchange rate
    selected_currency_id = request.session.get('currency_id')
    rate = 1.0
    if selected_currency_id:
        try:
            currency = Currency.objects.get(id=selected_currency_id)
            rate = float(currency.exchange_rate_to_usd)
        except (Currency.DoesNotExist, ValueError):
            pass
    else:
        # Fallback to active country
        selected_country_id = request.session.get('country_id')
        if selected_country_id:
            try:
                country = Country.objects.get(id=selected_country_id)
                rate = float(country.currency.exchange_rate_to_usd)
            except (Country.DoesNotExist, ValueError):
                pass

    # KPI Calculations
    total_sales_base = Order.objects.filter(status='DELIVERED').aggregate(Sum('grand_total_usd'))['grand_total_usd__sum'] or 0.00
    total_sales = float(total_sales_base) * rate
    orders_count = Order.objects.count()
    users_count = User.objects.filter(role='CUSTOMER').count()
    
    # Query low stock products based on Inventory table, fallback to product.stock if no inventory record
    low_stock_products = Product.objects.filter(
        Q(inventory__total_stock__lt=5) |
        Q(inventory__isnull=True, stock__lt=5)
    ).select_related('brand', 'inventory').distinct()
    low_stock_alerts = low_stock_products.count()
    
    # Revenue trend data (All orders for dynamic selector)
    import json
    recent_orders_all = Order.objects.order_by('-created_at')
    revenue_chart_data_all = [
        {
            'date': o.created_at.strftime('%b %d'),
            'amount': float(o.grand_total_usd) * rate
        }
        for o in reversed(recent_orders_all)
    ]
    revenue_chart_data_json = json.dumps(revenue_chart_data_all)

    # Top selling categories
    top_categories = Category.objects.annotate(num_products=Count('products')).order_by('-num_products')[:5]
    category_chart_data = {
        'labels': [c.name for c in top_categories],
        'data': [c.num_products for c in top_categories]
    }

    # Low stock items list (already queried above)
    recent_payments = Payment.objects.select_related('order').all().order_by('-created_at')[:5]

    return render(request, 'core/admin_dashboard.html', {
        'total_sales': total_sales,
        'orders_count': orders_count,
        'users_count': users_count,
        'low_stock_alerts': low_stock_alerts,
        'revenue_chart_data_all': revenue_chart_data_json,
        'category_chart_data': category_chart_data,
        'low_stock_products': low_stock_products,
        'recent_payments': recent_payments
    })

@user_passes_test(is_admin)
def generate_revenue_pdf_view(request):
    """Generates a premium structured and designable PDF report of system revenue"""
    from django.utils import timezone
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from django.http import FileResponse
    import io

    # Parse limit parameter
    limit = request.GET.get('limit', '6')
    if limit == 'all':
        recent_orders = Order.objects.all().order_by('-created_at')
        section_title = "Transactions Log (All Orders)"
    else:
        try:
            limit_val = int(limit)
            recent_orders = Order.objects.all().order_by('-created_at')[:limit_val]
            section_title = f"Recent Transactions Log (Last {limit_val} Orders)"
        except ValueError:
            recent_orders = Order.objects.all().order_by('-created_at')[:6]
            section_title = "Recent Transactions Log (Last 6 Orders)"

    # Fetch active currency/exchange rate
    selected_currency_id = request.session.get('currency_id')
    rate = 1.0
    currency_code = 'INR'
    currency_symbol = '₹'
    if selected_currency_id:
        try:
            currency = Currency.objects.get(id=selected_currency_id)
            rate = float(currency.exchange_rate_to_usd)
            currency_code = currency.code
            currency_symbol = currency.symbol
        except (Currency.DoesNotExist, ValueError):
            pass
    else:
        selected_country_id = request.session.get('country_id')
        if selected_country_id:
            try:
                country = Country.objects.get(id=selected_country_id)
                rate = float(country.currency.exchange_rate_to_usd)
                currency_code = country.currency.code
                currency_symbol = country.currency.symbol
            except (Country.DoesNotExist, ValueError):
                pass

    # Fetch data
    total_sales_base = Order.objects.filter(status='DELIVERED').aggregate(Sum('grand_total_usd'))['grand_total_usd__sum'] or 0.00
    total_sales = float(total_sales_base) * rate
    orders_count = Order.objects.count()
    users_count = User.objects.filter(role='CUSTOMER').count()
    
    # Calculate Average Order Value
    avg_order_value_base = float(total_sales_base) / orders_count if orders_count > 0 else 0.00
    avg_order_value = avg_order_value_base * rate
    
    # Create buffer
    buffer = io.BytesIO()
    
    # Setup document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Define custom styling palette matching our theme
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#06b6d4'),
        spaceAfter=8
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=25
    )
    
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=17,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=15,
        spaceAfter=12
    )

    label_style = ParagraphStyle(
        'LabelStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        textColor=colors.HexColor('#1e293b')
    )

    value_style = ParagraphStyle(
        'ValueStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=12,
        textColor=colors.HexColor('#0f172a')
    )

    header_cell_style = ParagraphStyle(
        'HeaderCell',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white
    )

    body_cell_style = ParagraphStyle(
        'BodyCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#334155')
    )
    
    # Header Section
    story.append(Paragraph("Custom PC Builder - Revenue & Sales Report", title_style))
    gen_time = timezone.now().strftime('%B %d, %Y - %H:%M')
    story.append(Paragraph(f"Generated by: {request.user.username} | Management Portal | Date: {gen_time}", subtitle_style))
    
    # KPI Grid Table
    kpi_data = [
        [
            Paragraph(f"Total Revenue ({currency_code}):", label_style),
            Paragraph(f"{currency_symbol} {total_sales:,.2f}", value_style),
            Paragraph("Total Orders Placed:", label_style),
            Paragraph(str(orders_count), value_style)
        ],
        [
            Paragraph(f"Average Order Value ({currency_code}):", label_style),
            Paragraph(f"{currency_symbol} {avg_order_value:,.2f}", value_style),
            Paragraph("Total Customers:", label_style),
            Paragraph(str(users_count), value_style)
        ]
    ]
    
    kpi_table = Table(kpi_data, colWidths=[140, 130, 140, 130])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BORDER', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('PADDING', (0,0), (-1,-1), 10),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    story.append(kpi_table)
    story.append(Spacer(1, 20))
    
    # Recent Transactions Section
    story.append(Paragraph(section_title, section_heading))
    
    # Order log table headers
    table_data = [[
        Paragraph("Order #", header_cell_style),
        Paragraph("User Email", header_cell_style),
        Paragraph("Payment Method", header_cell_style),
        Paragraph("Status", header_cell_style),
        Paragraph("Total Amount", header_cell_style)
    ]]
    
    # Calculate sum of listed orders
    total_listed_amount = sum(float(o.grand_total_usd) * rate for o in recent_orders)

    # Populate order log rows
    for o in recent_orders:
        payment_method = o.payment.payment_method if hasattr(o, 'payment') else 'N/A'
        table_data.append([
            Paragraph(o.order_number, body_cell_style),
            Paragraph(o.email, body_cell_style),
            Paragraph(payment_method, body_cell_style),
            Paragraph(o.status.upper(), body_cell_style),
            Paragraph(f"{currency_symbol} {float(o.grand_total_usd) * rate:,.2f}", body_cell_style)
        ])

    # Append total row
    total_row_style = ParagraphStyle(
        'TotalRowCell',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#0f172a')
    )
    table_data.append([
        Paragraph("<b>TOTAL (Listed Orders)</b>", total_row_style),
        Paragraph("", body_cell_style),
        Paragraph("", body_cell_style),
        Paragraph("", body_cell_style),
        Paragraph(f"<b>{currency_symbol} {total_listed_amount:,.2f}</b>", total_row_style)
    ])
        
    order_table = Table(table_data, colWidths=[100, 160, 100, 80, 100])
    order_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('TOPPADDING', (0,0), (-1,0), 10),
        ('GRID', (0,0), (-1,-2), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.HexColor('#f8fafc')]),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#e2e8f0')),
        ('LINEABOVE', (0,-1), (-1,-1), 1.5, colors.HexColor('#0f172a')),
        ('PADDING', (0,-1), (-1,-1), 10),
    ]))
    
    story.append(order_table)
    
    # Build Document
    doc.build(story)
    
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename="Revenue_Sales_Report.pdf")

# Custom Admin Dashboard Subpages Views (opening in same tab inside the custom theme)

@user_passes_test(is_admin)
def admin_products_view(request):
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')
    
    products = Product.objects.select_related('brand', 'category').all().order_by('-created_at')
    if query:
        products = products.filter(Q(name__icontains=query) | Q(brand__name__icontains=query) | Q(tags__icontains=query))
    if category_id:
        products = products.filter(category_id=category_id)
        
    categories = Category.objects.all()
    return render(request, 'core/admin_products.html', {
        'products': products,
        'categories': categories,
        'selected_category': category_id,
        'query': query
    })

@user_passes_test(is_admin)
def admin_product_create_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        brand_id = request.POST.get('brand')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        image = request.POST.get('image')
        original_price = request.POST.get('original_price_usd')
        discount = request.POST.get('discount_percentage', '0')
        stock = request.POST.get('stock', '10')
        power = request.POST.get('power_consumption_watts', '0')
        rgb = request.POST.get('rgb_support') == 'on'
        featured = request.POST.get('is_featured') == 'on'
        socket = request.POST.get('socket', '')
        ram_type = request.POST.get('ram_type', '')
        form_factor = request.POST.get('form_factor', '')
        
        try:
            brand = Brand.objects.get(id=brand_id)
            category = Category.objects.get(id=category_id)
            product = Product.objects.create(
                name=name,
                brand=brand,
                category=category,
                description=description,
                image=image,
                original_price_usd=original_price,
                discount_percentage=discount,
                stock=stock,
                power_consumption_watts=power,
                rgb_support=rgb,
                is_featured=featured,
                socket=socket,
                ram_type=ram_type,
                form_factor=form_factor
            )
            # Create a corresponding inventory record too
            from django.apps import apps
            Inventory = apps.get_model('orders', 'Inventory')
            Inventory.objects.create(product=product, total_stock=stock, low_stock_threshold=5)
            
            messages.success(request, f"Product '{name}' created successfully!")
            return redirect('admin_products')
        except Exception as e:
            messages.error(request, f"Error creating product: {e}")
            
    brands = Brand.objects.all()
    categories = Category.objects.all()
    return render(request, 'core/admin_product_form.html', {
        'brands': brands,
        'categories': categories,
        'action': 'Create'
    })

@user_passes_test(is_admin)
def admin_product_edit_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.name = request.POST.get('name')
        brand_id = request.POST.get('brand')
        category_id = request.POST.get('category')
        product.description = request.POST.get('description')
        product.image = request.POST.get('image')
        product.original_price_usd = request.POST.get('original_price_usd')
        product.discount_percentage = request.POST.get('discount_percentage', '0')
        product.stock = request.POST.get('stock', '10')
        product.power_consumption_watts = request.POST.get('power_consumption_watts', '0')
        product.rgb_support = request.POST.get('rgb_support') == 'on'
        product.is_featured = request.POST.get('is_featured') == 'on'
        product.socket = request.POST.get('socket', '')
        product.ram_type = request.POST.get('ram_type', '')
        product.form_factor = request.POST.get('form_factor', '')
        
        try:
            product.brand = Brand.objects.get(id=brand_id)
            product.category = Category.objects.get(id=category_id)
            product.save()
            
            # Sync corresponding inventory record
            from django.apps import apps
            Inventory = apps.get_model('orders', 'Inventory')
            inv, _ = Inventory.objects.get_or_create(product=product)
            inv.total_stock = product.stock
            inv.save()
            
            messages.success(request, f"Product '{product.name}' updated successfully!")
            return redirect('admin_products')
        except Exception as e:
            messages.error(request, f"Error updating product: {e}")
            
    brands = Brand.objects.all()
    categories = Category.objects.all()
    
    # Resolve correct image input box value (stripping MEDIA_URL prefix if relative path)
    image_val = str(product.image)
    from django.conf import settings
    if image_val.startswith(settings.MEDIA_URL):
        image_val = image_val[len(settings.MEDIA_URL):]
        
    return render(request, 'core/admin_product_form.html', {
        'product': product,
        'image_val': image_val,
        'brands': brands,
        'categories': categories,
        'action': 'Edit'
    })

@user_passes_test(is_admin)
def admin_product_delete_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    name = product.name
    try:
        product.delete()
        messages.success(request, f"Product '{name}' deleted successfully!")
    except Exception as e:
        messages.error(request, f"Error deleting product: {e}")
    return redirect('admin_products')

@user_passes_test(is_admin)
def admin_orders_view(request):
    status_filter = request.GET.get('status', '')
    query = request.GET.get('q', '').strip()
    
    orders = Order.objects.select_related('user').all().order_by('-created_at')
    if status_filter:
        orders = orders.filter(status=status_filter)
    if query:
        orders = orders.filter(Q(order_number__icontains=query) | Q(user__username__icontains=query) | Q(user__email__icontains=query))
        
    return render(request, 'core/admin_orders.html', {
        'orders': orders,
        'status_filter': status_filter,
        'query': query,
        'status_choices': Order.OrderStatus.choices,
    })

@user_passes_test(is_admin)
def admin_order_update_status_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.OrderStatus.choices):
            order.status = new_status
            order.save()
            messages.success(request, f"Order #{order.order_number} status updated to {order.get_status_display()}!")
        else:
            messages.error(request, "Invalid status selected.")
    return redirect('admin_orders')

@user_passes_test(is_admin)
def admin_users_view(request):
    query = request.GET.get('q', '').strip()
    users = User.objects.all().order_by('-date_joined')
    if query:
        users = users.filter(Q(username__icontains=query) | Q(email__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query))
        
    return render(request, 'core/admin_users.html', {
        'users': users,
        'query': query
    })

