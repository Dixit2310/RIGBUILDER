from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.crypto import get_random_string
import uuid

class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = 'CUSTOMER', 'Customer'
        ADMIN = 'ADMIN', 'Admin'
    
    role = models.CharField(
        max_length=15, 
        choices=Role.choices, 
        default=Role.CUSTOMER
    )
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    
    # OTP verification details
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_expiry = models.DateTimeField(blank=True, null=True)
    
    # Profile information
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    
    # Referral system
    referral_code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    referred_by = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='referrals'
    )
    
    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = get_random_string(8).upper()
        if self.is_superuser:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.username} ({self.role})"

class Address(models.Model):
    class AddressType(models.TextChoices):
        BILLING = 'BILLING', 'Billing Address'
        SHIPPING = 'SHIPPING', 'Shipping Address'
        
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=10, choices=AddressType.choices, default=AddressType.SHIPPING)
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.ForeignKey('products.Country', on_delete=models.CASCADE, related_name='addresses')
    is_default = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = "Addresses"
        
    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user, address_type=self.address_type).update(is_default=False)
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.full_name} - {self.street_address}, {self.city} ({self.address_type})"
