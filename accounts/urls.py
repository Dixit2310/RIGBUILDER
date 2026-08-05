from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/remove-picture/', views.remove_profile_picture_view, name='remove_profile_picture'),
    path('address/add/', views.address_create_view, name='address_add'),
    path('address/edit/<int:pk>/', views.address_edit_view, name='address_edit'),
    path('address/delete/<int:pk>/', views.address_delete_view, name='address_delete'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
]
