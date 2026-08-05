from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Currency, Country, Brand, Category, Product, ProductReview

class PriceRangeFilter(admin.SimpleListFilter):
    title = _('price range')
    parameter_name = 'price_range'

    def lookups(self, request, model_admin):
        return (
            ('under_50', _('Under $50')),
            ('50_to_100', _('$50 to $100')),
            ('100_to_250', _('$100 to $250')),
            ('250_to_500', _('$250 to $500')),
            ('500_to_1000', _('$500 to $1000')),
            ('over_1000', _('Over $1000')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'under_50':
            return queryset.filter(original_price_usd__lt=50)
        if self.value() == '50_to_100':
            return queryset.filter(original_price_usd__gte=50, original_price_usd__lt=100)
        if self.value() == '100_to_250':
            return queryset.filter(original_price_usd__gte=100, original_price_usd__lt=250)
        if self.value() == '250_to_500':
            return queryset.filter(original_price_usd__gte=250, original_price_usd__lt=500)
        if self.value() == '500_to_1000':
            return queryset.filter(original_price_usd__gte=500, original_price_usd__lt=1000)
        if self.value() == 'over_1000':
            return queryset.filter(original_price_usd__gte=1000)

class StockStatusFilter(admin.SimpleListFilter):
    title = _('stock status')
    parameter_name = 'stock_status'

    def lookups(self, request, model_admin):
        return (
            ('out_of_stock', _('Out of Stock (0)')),
            ('low_stock', _('Low Stock (< 5)')),
            ('in_stock', _('In Stock (5+)')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'out_of_stock':
            return queryset.filter(stock=0)
        if self.value() == 'low_stock':
            return queryset.filter(stock__gt=0, stock__lt=5)
        if self.value() == 'in_stock':
            return queryset.filter(stock__gte=5)
        return queryset

class ProductAdmin(admin.ModelAdmin):
    list_display = ('brand', 'name', 'category', 'original_price_usd', 'discount_percentage', 'stock_status', 'rating')
    list_filter = ('category', 'brand', PriceRangeFilter, StockStatusFilter, 'socket', 'ram_type', 'form_factor')
    search_fields = ('name', 'brand__name', 'category__name', 'tags')
    prepopulated_fields = {'slug': ('name',)}

    def stock_status(self, obj):
        if obj.stock == 0:
            return format_html('<span style="color: #ef4444; font-weight: bold; background-color: #fee2e2; padding: 4px 8px; border-radius: 4px; border: 1px solid #fecaca; font-size: 0.75rem; text-transform: uppercase;">Out of Stock</span>')
        elif obj.stock < 5:
            return format_html('<span style="color: #d97706; font-weight: bold; background-color: #fef3c7; padding: 4px 8px; border-radius: 4px; border: 1px solid #fde68a; font-size: 0.75rem; text-transform: uppercase;">Low Stock ({})</span>', obj.stock)
        return format_html('<span style="color: #10b981; font-weight: bold; background-color: #d1fae5; padding: 4px 8px; border-radius: 4px; border: 1px solid #a7f3d0; font-size: 0.75rem; text-transform: uppercase;">In Stock ({})</span>', obj.stock)

    stock_status.short_description = 'Stock Status'
    stock_status.admin_order_field = 'stock'

class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'currency', 'default_tax_rate', 'default_shipping_charge')
    list_filter = ('currency',)

admin.site.register(Currency)
admin.site.register(Country, CountryAdmin)
admin.site.register(Brand)
admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductReview)

# Customizing Django Admin Site branding
admin.site.site_header = "Custom PC Builder Administration Console"
admin.site.site_title = "PC Builder Admin Portal"
admin.site.index_title = "Welcome to the Custom PC Builder Database Manager"
