from django.contrib import admin
from .models import ChatbotSettings, LocalFAQ, ConversationLog

@admin.register(ChatbotSettings)
class ChatbotSettingsAdmin(admin.ModelAdmin):
    list_display = ("__str__", "is_enabled", "max_messages_per_session")
    fieldsets = (
        ("General Status", {"fields": ("is_enabled", "max_messages_per_session")}),
        ("AI Text Prompts", {"fields": ("welcome_message", "ai_personality")}),
    )

    def has_add_permission(self, request):
        # Prevent adding more settings since it is a singleton
        return not ChatbotSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(LocalFAQ)
class LocalFAQAdmin(admin.ModelAdmin):
    list_display = ("question", "is_active")
    list_filter = ("is_active",)
    search_fields = ("question", "answer")

@admin.register(ConversationLog)
class ConversationLogAdmin(admin.ModelAdmin):
    list_display = ("__str__", "session_id", "created_at")
    list_filter = ("created_at",)
    search_fields = ("session_id", "message", "reply", "user__username")
    readonly_fields = ("session_id", "user", "message", "reply", "created_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        # Admin can delete logs if needed
        return True
