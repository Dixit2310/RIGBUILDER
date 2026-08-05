from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    RegisterAPIView, UserProfileAPIView, AddressViewSet,
    ProductViewSet, CategoryViewSet, BrandViewSet, ProductReviewViewSet,
    CartViewSet, PCBuildViewSet, OrderViewSet, WishlistViewSet
)

router = DefaultRouter()
router.register(r'addresses', AddressViewSet, basename='api-address')
router.register(r'products', ProductViewSet, basename='api-product')
router.register(r'categories', CategoryViewSet, basename='api-category')
router.register(r'brands', BrandViewSet, basename='api-brand')
router.register(r'reviews', ProductReviewViewSet, basename='api-review')
router.register(r'cart', CartViewSet, basename='api-cart')
router.register(r'builds', PCBuildViewSet, basename='api-build')
router.register(r'orders', OrderViewSet, basename='api-order')
router.register(r'wishlist', WishlistViewSet, basename='api-wishlist')

urlpatterns = [
    path('auth/register/', RegisterAPIView.as_view(), name='api-register'),
    path('auth/profile/', UserProfileAPIView.as_view(), name='api-profile'),
    path('', include(router.urls)),
]
