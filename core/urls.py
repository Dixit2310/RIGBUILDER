from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('blogs/', views.blog_list_view, name='blog_list'),
    path('blogs/<slug:slug>/', views.blog_detail_view, name='blog_detail'),
    path('faq/', views.faq_view, name='faq'),
    path('contact/', views.contact_view, name='contact'),
    path('newsletter/subscribe/', views.newsletter_subscribe_view, name='newsletter_subscribe'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-dashboard/revenue-pdf/', views.generate_revenue_pdf_view, name='generate_revenue_pdf'),
    path('admin-dashboard/products/', views.admin_products_view, name='admin_products'),
    path('admin-dashboard/products/create/', views.admin_product_create_view, name='admin_product_create'),
    path('admin-dashboard/products/edit/<int:product_id>/', views.admin_product_edit_view, name='admin_product_edit'),
    path('admin-dashboard/products/delete/<int:product_id>/', views.admin_product_delete_view, name='admin_product_delete'),
    path('admin-dashboard/orders/', views.admin_orders_view, name='admin_orders'),
    path('admin-dashboard/orders/update-status/<int:order_id>/', views.admin_order_update_status_view, name='admin_order_update_status'),
    path('admin-dashboard/users/', views.admin_users_view, name='admin_users'),
]
