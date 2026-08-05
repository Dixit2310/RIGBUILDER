from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Address

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'phone_number', 'is_email_verified', 'is_staff')
    list_filter = ('role', 'is_email_verified', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Attributes', {'fields': ('role', 'phone_number', 'is_phone_verified', 'is_email_verified', 'profile_picture', 'bio', 'referral_code', 'referred_by')}),
    )

class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'address_type', 'full_name', 'city', 'state', 'country', 'is_default')
    list_filter = ('address_type', 'country', 'is_default')
    search_fields = ('user__username', 'full_name', 'street_address')

admin.site.register(User, CustomUserAdmin)
admin.site.register(Address, AddressAdmin)
