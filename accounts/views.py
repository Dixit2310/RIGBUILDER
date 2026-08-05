from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import random

from .models import User, Address
from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm, AddressForm
from products.models import Country
from orders.models import Wishlist, Cart

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Create user
            user = form.save(commit=False)
            password = form.cleaned_data.get('password')
            ref_code_used = form.cleaned_data.get('referral_code_used')
            
            # Handle referral code
            if ref_code_used:
                try:
                    referrer = User.objects.get(referral_code=ref_code_used.upper())
                    user.referred_by = referrer
                    messages.success(request, f"Referral code from {referrer.username} applied successfully!")
                except User.DoesNotExist:
                    messages.warning(request, "Invalid referral code. Registration will proceed anyway.")
            
            user.set_password(password)
            user.save()
            
            user.is_email_verified = True
            user.save()
            
            # Initialize Wishlist & Cart
            Wishlist.objects.create(user=user)
            Cart.objects.get_or_create(user=user)
            
            # Log the user in immediately
            login(request, user)
            
            messages.success(request, "Registration successful! Welcome to Custom PC Builder.")
            return redirect('home')
    else:
        form = UserRegistrationForm()
        
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        if request.user.role == 'ADMIN' or request.user.is_staff or request.user.is_superuser:
            return redirect('admin_dashboard')
        return redirect('home')
        
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me')
            
            # Allow login via username or email
            user = None
            if '@' in username:
                user_obj = User.objects.filter(email=username).first()
                if user_obj:
                    user = authenticate(username=user_obj.username, password=password)
            else:
                user = authenticate(username=username, password=password)
                
            if user is not None:
                login(request, user)
                
                # Remember me logic
                if remember_me:
                    request.session.set_expiry(1209600) # 2 weeks in seconds
                else:
                    request.session.set_expiry(0) # expires when browser closes
                    
                messages.success(request, f"Welcome back, {user.username}!")
                if user.role == 'ADMIN' or user.is_staff or user.is_superuser:
                    return redirect('admin_dashboard')
                return redirect('home')
            else:
                messages.error(request, "Invalid username/email or password.")
    else:
        form = UserLoginForm()
        
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, "You have logged out successfully.")
    return redirect('home')

def verify_otp_view(request):
    user_id = request.session.get('verify_user_id')
    if not user_id:
        return redirect('login')
        
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        if user.otp_code == entered_otp and user.otp_expiry > timezone.now():
            user.is_email_verified = True
            user.otp_code = None
            user.otp_expiry = None
            user.save()
            
            # Automatically log in the user
            login(request, user)
            del request.session['verify_user_id']
            
            messages.success(request, "Email verified successfully! Welcome to Custom PC Builder.")
            return redirect('home')
        else:
            messages.error(request, "Invalid or expired OTP. Please try again.")
            
    return render(request, 'accounts/verify_otp.html', {'user': user})

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
        
    addresses = request.user.addresses.all()
    orders = request.user.orders.all().order_by('-created_at')
    referrals = request.user.referrals.all().order_by('-date_joined')
    
    referred_users_count = referrals.count()
    successful_referrals_count = referrals.filter(orders__status='DELIVERED').distinct().count()
    estimated_earnings = successful_referrals_count * 50.00
    
    return render(request, 'accounts/profile.html', {
        'form': form,
        'addresses': addresses,
        'orders': orders,
        'referrals': referrals,
        'referred_users_count': referred_users_count,
        'successful_referrals_count': successful_referrals_count,
        'estimated_earnings': estimated_earnings
    })

@login_required
def address_create_view(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Address added successfully!")
            return redirect('profile')
    else:
        form = AddressForm()
        
    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Add New Address'})

@login_required
def address_edit_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, "Address updated successfully!")
            return redirect('profile')
    else:
        form = AddressForm(instance=address)
        
    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Edit Address'})

@login_required
def address_delete_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.delete()
    messages.success(request, "Address deleted successfully.")
    return redirect('profile')

# Simple Mock Forgot Password Views for Full Completion
def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        if user:
            # Generate OTP for reset password
            user.otp_code = str(random.randint(100000, 999999))
            user.otp_expiry = timezone.now() + timedelta(minutes=10)
            user.save()
            
            # Print to console log
            print(f"\n--- PASSWORD RESET OTP FOR {user.username} ({user.email}): {user.otp_code} ---\n")
            
            # Send actual email
            from django.core.mail import send_mail
            subject = "Password Reset OTP - RIGBUILDER"
            message = (
                f"Hello {user.username},\n\n"
                f"You requested to reset your password. Your OTP code is:\n\n"
                f"   {user.otp_code}\n\n"
                f"This OTP is valid for 10 minutes.\n\n"
                f"If you did not request this, please ignore this email.\n\n"
                f"Best regards,\n"
                f"The RIGBUILDER Team"
            )
            from_email = "noreply@rigbuilder.com"
            recipient_list = [user.email]
            
            try:
                send_mail(subject, message, from_email, recipient_list, fail_silently=False)
                messages.success(request, f"A password reset OTP has been sent to {user.email}.")
            except Exception as e:
                print(f"Error sending password reset email: {e}")
                messages.warning(request, f"Could not send email directly: {e}. However, your OTP is simulated in the console: {user.otp_code}")
                
            request.session['reset_user_id'] = user.id
            return redirect('reset_password')
        else:
            messages.error(request, "No user found with that email address.")
    return render(request, 'accounts/forgot_password.html')

def reset_password_view(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        return redirect('login')
        
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if user.otp_code == entered_otp and user.otp_expiry > timezone.now():
            if new_password == confirm_password:
                user.set_password(new_password)
                user.otp_code = None
                user.otp_expiry = None
                user.save()
                del request.session['reset_user_id']
                messages.success(request, "Password reset successfully! Please login with your new password.")
                return redirect('login')
            else:
                messages.error(request, "Passwords do not match.")
        else:
            messages.error(request, "Invalid or expired OTP.")
            
    return render(request, 'accounts/reset_password.html')


@login_required
def remove_profile_picture_view(request):
    user = request.user
    if user.profile_picture:
        user.profile_picture.delete(save=True)
        messages.success(request, "Profile picture removed successfully.")
    else:
        messages.info(request, "You do not have a profile picture to remove.")
    return redirect('profile')

