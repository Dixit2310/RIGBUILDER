from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from products.models import Product, Brand, Category
from builder.models import PCBuild
from orders.models import Wishlist

User = get_user_model()

class WishlistTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        
        # Create dependencies for Product
        self.brand = Brand.objects.create(name='TestBrand')
        self.category = Category.objects.create(name='TestCategory', is_pc_component=True)
        
        # Create test Product
        self.product = Product.objects.create(
            name='Test Product',
            brand=self.brand,
            category=self.category,
            description='Test description',
            original_price_usd=100.00,
            stock=5
        )
        
        # Create test PCBuild
        self.build = PCBuild.objects.create(
            user=self.user,
            name='Ultimate Gaming Rig',
            build_type='gaming'
        )
        
        # Create user wishlist (accounts app views do it on registration, let's do it manually)
        self.wishlist = Wishlist.objects.create(user=self.user)

    def test_wishlist_view_anonymous_redirect(self):
        """Anonymous users should be redirected to login"""
        response = self.client.get(reverse('wishlist'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_wishlist_view_authenticated(self):
        """Authenticated users can see their wishlist page"""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('wishlist'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'orders/wishlist.html')

    def test_wishlist_toggle_product_add(self):
        """Adding a product to wishlist via toggle"""
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('wishlist_toggle', args=[self.product.id]))
        
        # Check redirect
        self.assertEqual(response.status_code, 302)
        
        # Verify in DB
        self.assertTrue(self.wishlist.products.filter(id=self.product.id).exists())

    def test_wishlist_toggle_product_remove(self):
        """Removing a product from wishlist via toggle if it exists"""
        self.wishlist.products.add(self.product)
        self.client.login(username='testuser', password='password123')
        
        response = self.client.post(reverse('wishlist_toggle', args=[self.product.id]))
        self.assertEqual(response.status_code, 302)
        
        # Verify removed in DB
        self.assertFalse(self.wishlist.products.filter(id=self.product.id).exists())

    def test_wishlist_toggle_product_ajax(self):
        """AJAX request should return JSON response"""
        self.client.login(username='testuser', password='password123')
        response = self.client.post(
            reverse('wishlist_toggle', args=[self.product.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertTrue(data['added'])
        self.assertEqual(data['wishlist_count'], 1)

    def test_wishlist_toggle_build_add(self):
        """Adding a PC build to wishlist via toggle"""
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('wishlist_toggle_build', args=[self.build.id]))
        self.assertEqual(response.status_code, 302)
        
        # Verify in DB
        self.assertTrue(self.wishlist.pc_builds.filter(id=self.build.id).exists())
