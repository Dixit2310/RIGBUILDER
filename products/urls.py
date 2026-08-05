from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list_view, name='catalog'),
    path('detail/<slug:slug>/', views.product_detail_view, name='product_detail'),
    path('compare/', views.product_compare_view, name='product_compare'),
    path('search-autocomplete/', views.search_autocomplete_view, name='search_autocomplete'),
    path('select-country/<int:country_id>/', views.select_country_view, name='select_country'),
    path('select-currency/<int:currency_id>/', views.select_currency_view, name='select_currency'),
]
