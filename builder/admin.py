from django.contrib import admin
from .models import PCBuild, CompatibilityRule

class PCBuildAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'build_type', 'is_preset', 'is_favorite', 'created_at')
    list_filter = ('build_type', 'is_preset', 'is_favorite')
    search_fields = ('name', 'user__username')

admin.site.register(PCBuild, PCBuildAdmin)
admin.site.register(CompatibilityRule)
