from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from products.models import Product, Brand, Category, Country, Currency
from orders.models import Order, Payment, Inventory

User = get_user_model()

class AdminDashboardTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create currency and country
        self.usd = Currency.objects.create(code="USD", name="US Dollar", symbol="$", exchange_rate_to_usd=1.0000)
        self.country = Country.objects.create(name="United States", code="US", currency=self.usd, default_tax_rate=10, default_shipping_charge=25)

        # Create admin and customer users
        self.admin_user = User.objects.create_superuser(username='adminuser', password='password123', email='admin@test.com')
        self.customer = User.objects.create_user(username='customeruser', password='password123', email='customer@test.com')
        
        # Create brand & category
        self.brand = Brand.objects.create(name='Intel')
        self.category = Category.objects.create(name='CPU', is_pc_component=True)
        
        # Create low stock product
        self.product = Product.objects.create(
            name='Core i9-14900K',
            brand=self.brand,
            category=self.category,
            description='Intel processor',
            original_price_usd=500.00,
            stock=2
        )
        
        # Create Inventory for low stock product
        self.inventory = Inventory.objects.create(
            product=self.product,
            total_stock=2,
            reserved_stock=0,
            low_stock_threshold=3
        )
        
        # Create order & payment
        self.order = Order.objects.create(
            user=self.customer,
            email="customer@test.com",
            phone_number="1234567890",
            country=self.country,
            shipping_address="123 Street",
            billing_address="123 Street",
            subtotal_usd=500.00,
            tax_usd=50.00,
            shipping_usd=25.00,
            grand_total_usd=575.00,
            status=Order.OrderStatus.DELIVERED
        )
        
        self.payment = Payment.objects.create(
            order=self.order,
            payment_method=Payment.PaymentMethod.STRIPE,
            transaction_id='ch_123',
            status=Payment.PaymentStatus.COMPLETED,
            amount_paid=575.00,
            currency_code='USD'
        )

    def test_admin_dashboard_anonymous_redirect(self):
        """Anonymous users should be redirected to login"""
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_admin_dashboard_customer_denied(self):
        """Customer role should be redirected/denied"""
        self.client.login(username='customeruser', password='password123')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_admin_dashboard_access_allowed(self):
        """Admin user should access dashboard successfully"""
        self.client.login(username='adminuser', password='password123')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/admin_dashboard.html')
        
        # Verify context data
        self.assertEqual(response.context['low_stock_alerts'], 1)
        self.assertIn(self.product, response.context['low_stock_products'])
        self.assertIn(self.payment, response.context['recent_payments'])
