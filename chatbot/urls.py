from django.urls import path
from . import views

urlpatterns = [
    path('api/chat/', views.chatbot_api_view, name='chatbot_api'),
]
