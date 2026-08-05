from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from orders.models import Order
from products.models import Country, Currency

User = get_user_model()

class ProfileViewTestCase(TestCase):
    def setUp(self):
        # Create currency and country
        self.usd = Currency.objects.create(code="USD", name="US Dollar", symbol="$", exchange_rate_to_usd=1.0000)
        self.country = Country.objects.create(name="United States", code="US", currency=self.usd, default_tax_rate=10, default_shipping_charge=25)

        # Create main user
        self.user = User.objects.create_user(
            username="main_user",
            email="main@test.com",
            password="testpassword123",
            first_name="John",
            last_name="Doe"
        )
        # Create referred user
        self.referred = User.objects.create_user(
            username="ref_user",
            email="ref@test.com",
            password="testpassword123",
            referred_by=self.user
        )
        
        # Create an order for the referred user
        self.order = Order.objects.create(
            user=self.referred,
            email="ref@test.com",
            phone_number="1234567890",
            country=self.country,
            shipping_address="123 Main St",
            billing_address="123 Main St",
            subtotal_usd=1000.00,
            tax_usd=100.00,
            shipping_usd=25.00,
            grand_total_usd=1125.00,
            status=Order.OrderStatus.DELIVERED
        )
        
        # Login client
        self.client = Client()
        self.client.login(username="main_user", password="testpassword123")

    def test_profile_view_context(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        
        # Check context variables
        self.assertEqual(response.context['referred_users_count'], 1)
        self.assertEqual(response.context['successful_referrals_count'], 1)
        self.assertEqual(response.context['estimated_earnings'], 50.00)
        self.assertEqual(list(response.context['referrals']), [self.referred])

    def test_remove_profile_picture_anonymous(self):
        self.client.logout()
        response = self.client.get(reverse('remove_profile_picture'))
        self.assertEqual(response.status_code, 302)

    def test_remove_profile_picture_authenticated(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x05\x04\x04'
            b'\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44'
            b'\x01\x00\x3b'
        )
        avatar = SimpleUploadedFile("avatar.gif", small_gif, content_type="image/gif")
        self.user.profile_picture = avatar
        self.user.save()
        
        self.assertTrue(self.user.profile_picture)
        
        response = self.client.get(reverse('remove_profile_picture'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('profile'))
        
        self.user.refresh_from_db()
        self.assertFalse(self.user.profile_picture)
