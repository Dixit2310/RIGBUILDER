from django.urls import path
from . import views

urlpatterns = [
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.cart_add_view, name='cart_add'),
    path('cart/add-build/<int:build_id>/', views.cart_add_build_view, name='cart_add_build'),
    path('cart/remove/<int:item_id>/', views.cart_remove_view, name='cart_remove'),
    path('cart/update/<int:item_id>/<str:action>/', views.cart_update_quantity_view, name='cart_update_quantity'),
    path('coupon/apply/', views.apply_coupon_view, name='apply_coupon'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('place-order/', views.place_order_view, name='place_order'),
    path('payment/simulate/<str:order_number>/<str:method>/', views.simulate_payment_view, name='simulate_payment'),
    path('payment/success/<str:order_number>/', views.payment_success_view, name='payment_success'),
    path('tracking/<str:order_number>/', views.order_tracking_view, name='order_tracking'),
    path('history/', views.order_history_view, name='order_history'),
    path('reorder/<int:order_id>/', views.reorder_view, name='reorder'),
    path('invoice/download/<str:order_number>/', views.invoice_download_view, name='invoice_download'),
    path('cancel/<str:order_number>/', views.cancel_order_view, name='cancel_order'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.wishlist_toggle_view, name='wishlist_toggle'),
    path('wishlist/toggle-build/<int:build_id>/', views.wishlist_toggle_build_view, name='wishlist_toggle_build'),
]
