from django.urls import path
from . import views

urlpatterns = [
    path('', views.builder_view, name='builder'),
    path('add/<int:product_id>/', views.add_to_build_view, name='add_to_build'),
    path('remove/<str:slot_name>/', views.remove_from_build_view, name='remove_from_build'),
    path('clear/', views.clear_build_view, name='clear_build'),
    path('save/', views.save_build_view, name='save_build'),
    path('update-target/', views.update_target_system_view, name='update_target_system'),
    path('presets/', views.presets_list_view, name='presets_list'),
    path('presets/load/<int:preset_id>/', views.load_preset_view, name='load_preset'),
    path('ai-recommend/', views.ai_recommendation_view, name='ai_recommend'),
]
