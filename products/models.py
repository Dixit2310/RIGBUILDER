from django.db import models
from django.utils.text import slugify
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class ImageString(str):
    @property
    def url(self):
        return self

class OnlineImageField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 500)
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection):
        if not value:
            return ImageString("")
        if value.startswith('http://') or value.startswith('https://') or value.startswith('/'):
            return ImageString(value)
        return ImageString(f"{settings.MEDIA_URL}{value}")

    def to_python(self, value):
        if value is None:
            return value
        if isinstance(value, ImageString):
            return value
        if not value:
            return ImageString("")
        if value.startswith('http://') or value.startswith('https://') or value.startswith('/'):
            return ImageString(value)
        return ImageString(f"{settings.MEDIA_URL}{value}")

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value:
            media_url = settings.MEDIA_URL
            if value.startswith(media_url) and not value.startswith('http://') and not value.startswith('https://'):
                return value[len(media_url):]
        return value

class Currency(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10, unique=True) # e.g. USD, INR, EUR, GBP
    symbol = models.CharField(max_length=10) # e.g. $, ₹, €, £
    exchange_rate_to_usd = models.DecimalField(max_digits=12, decimal_places=4, default=1.0) # Multiply USD price by this
    
    class Meta:
        verbose_name_plural = "Currencies"

    def __str__(self):
        return f"{self.name} ({self.code})"

class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=5, unique=True) # e.g. IN, US, GB, CA, AU, AE, DE, FR, JP, SG
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name='countries')
    flag_emoji = models.CharField(max_length=10, blank=True, null=True) # e.g. 🇮🇳, 🇺🇸
    default_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18.0) # GST percentage
    default_shipping_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.0) # base shipping in USD
    
    class Meta:
        verbose_name_plural = "Countries"
        
    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    logo = OnlineImageField(blank=True, null=True)
    website_url = models.URLField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    image = OnlineImageField(blank=True, null=True)
    
    # Is this an essential PC build component or an accessory?
    is_pc_component = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    description = models.TextField()
    image = OnlineImageField()
    original_price_usd = models.DecimalField(max_digits=10, decimal_places=2) # base price in USD
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0) # discount
    stock = models.PositiveIntegerField(default=10)
    warranty_years = models.DecimalField(max_digits=3, decimal_places=1, default=1.0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.0)
    power_consumption_watts = models.PositiveIntegerField(default=0) # TDP
    rgb_support = models.BooleanField(default=False)
    tags = models.CharField(max_length=255, blank=True, null=True) # comma separated tags like: gaming, budget, premium
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- COMPATIBILITY FIELDS ---
    # CPU & Motherboard socket (e.g., LGA1700, AM5, AM4)
    socket = models.CharField(max_length=50, blank=True, null=True)
    
    # RAM Type (e.g. DDR4, DDR5) for RAM, Motherboard, and CPUs
    ram_type = models.CharField(max_length=20, blank=True, null=True)
    ram_speed = models.PositiveIntegerField(blank=True, null=True) # e.g. 3200, 5200, 6000 MHz
    
    # Form Factor (e.g. ATX, Micro-ATX, Mini-ITX) for Motherboard, Cabinet, PSU
    form_factor = models.CharField(max_length=50, blank=True, null=True)
    
    # GPU constraints
    gpu_length_limit = models.PositiveIntegerField(blank=True, null=True) # for Cabinet, in mm
    gpu_length = models.PositiveIntegerField(blank=True, null=True) # for GPU, in mm
    
    # PSU Wattage (output wattage for PSU)
    psu_wattage_rating = models.PositiveIntegerField(blank=True, null=True)
    
    # Motherboard details
    nvme_slots_count = models.PositiveIntegerField(blank=True, null=True)
    pcie_version = models.CharField(max_length=20, blank=True, null=True) # e.g., Gen3, Gen4, Gen5
    
    # Storage details
    is_nvme = models.BooleanField(default=False) # for SSDs
    
    # Cooler specifications
    cooler_socket_support = models.CharField(max_length=255, blank=True, null=True) # Comma-separated sockets
    cooler_height = models.PositiveIntegerField(blank=True, null=True) # in mm
    max_cooler_height = models.PositiveIntegerField(blank=True, null=True) # for Cabinet, in mm

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.brand.name} {self.name}")
        super().save(*args, **kwargs)

    @property
    def final_price_usd(self):
        return self.original_price_usd * (1 - (self.discount_percentage / 100))

    def get_price_for_currency_and_country(self, currency, country=None):
        """Returns (original_price, final_price, tax, shipping, total) in local currency/country settings"""
        rate = currency.exchange_rate_to_usd
        
        orig_local = self.original_price_usd * rate
        final_local = self.final_price_usd * rate
        
        if country:
            tax = final_local * (country.default_tax_rate / 100)
            shipping = country.default_shipping_charge * rate
        else:
            from decimal import Decimal
            tax = Decimal('0.00')
            shipping = Decimal('0.00')
            
        total = final_local + tax + shipping
        
        return {
            'currency_code': currency.code,
            'currency_symbol': currency.symbol,
            'original_price': round(orig_local, 2),
            'final_price': round(final_local, 2),
            'tax': round(tax, 2),
            'shipping': round(shipping, 2),
            'total': round(total, 2),
            'discount_amount': round(orig_local - final_local, 2)
        }

    def get_price_for_country(self, country):
        """Returns (original_price, final_price, tax, shipping, total) in local currency"""
        return self.get_price_for_currency_and_country(country.currency, country)

    def __str__(self):
        return f"{self.brand.name} {self.name} ({self.category.name})"

class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    image = models.ImageField(upload_to='reviews/', blank=True, null=True)
    is_verified_purchase = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update product average rating
        reviews = self.product.reviews.all()
        if reviews.exists():
            avg_rating = sum(r.rating for r in reviews) / len(reviews)
            self.product.rating = round(avg_rating, 2)
            self.product.save(update_fields=['rating'])

    def __str__(self):
        return f"Review for {self.product.name} by {self.user.username} ({self.rating} stars)"
