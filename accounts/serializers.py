from rest_framework import serializers
from .models import User, Address

class AddressSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source='country.name', read_only=True)
    country_code = serializers.CharField(source='country.code', read_only=True)
    
    class Meta:
        model = Address
        fields = [
            'id', 'address_type', 'full_name', 'phone_number', 
            'street_address', 'city', 'state', 'postal_code', 
            'country', 'country_name', 'country_code', 'is_default'
        ]

class UserSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'role', 'phone_number', 'is_phone_verified', 'is_email_verified',
            'profile_picture', 'bio', 'referral_code', 'addresses'
        ]
        read_only_fields = ['role', 'is_phone_verified', 'is_email_verified', 'referral_code']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    referral_code_used = serializers.CharField(required=False, write_only=True, allow_blank=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'phone_number', 'referral_code_used']
        
    def create(self, validated_data):
        ref_code = validated_data.pop('referral_code_used', None)
        password = validated_data.pop('password')
        
        referred_by_user = None
        if ref_code:
            try:
                referred_by_user = User.objects.get(referral_code=ref_code.upper())
            except User.DoesNotExist:
                pass
                
        user = User.objects.create_user(
            referred_by=referred_by_user,
            **validated_data
        )
        user.set_password(password)
        user.save()
        return user
