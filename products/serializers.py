from rest_framework import serializers
from .models import Brand, Category, Product, ProductReview
from accounts.serializers import UserSerializer

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'logo', 'website_url']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image', 'is_pc_component']

class ProductReviewSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = ProductReview
        fields = ['id', 'product', 'user', 'user_details', 'rating', 'comment', 'image', 'is_verified_purchase', 'created_at']
        read_only_fields = ['user', 'is_verified_purchase']

class ProductListSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    final_price = serializers.DecimalField(source='final_price_usd', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'brand', 'brand_name', 'category', 'category_name', 
            'image', 'original_price_usd', 'discount_percentage', 'final_price',
            'stock', 'rating', 'power_consumption_watts', 'rgb_support', 'is_featured'
        ]

class ProductDetailSerializer(serializers.ModelSerializer):
    brand_details = BrandSerializer(source='brand', read_only=True)
    category_details = CategorySerializer(source='category', read_only=True)
    final_price = serializers.DecimalField(source='final_price_usd', max_digits=10, decimal_places=2, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'brand', 'brand_details', 'category', 'category_details', 
            'description', 'image', 'original_price_usd', 'discount_percentage', 'final_price',
            'stock', 'warranty_years', 'rating', 'power_consumption_watts', 'rgb_support', 
            'tags', 'is_featured', 'created_at', 'updated_at', 'reviews',
            
            # Compatibility Details
            'socket', 'ram_type', 'ram_speed', 'form_factor', 'gpu_length_limit', 
            'gpu_length', 'psu_wattage_rating', 'nvme_slots_count', 'pcie_version', 
            'is_nvme', 'cooler_socket_support', 'cooler_height', 'max_cooler_height'
        ]
