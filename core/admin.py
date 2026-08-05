from django.contrib import admin
from .models import BlogPost, FAQ, ContactRequest, SupportTicket, NewsletterSubscriber

class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    prepopulated_fields = {'slug': ('title',)}

class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'user', 'subject', 'status', 'priority', 'created_at')
    list_filter = ('status', 'priority')

admin.site.register(BlogPost, BlogPostAdmin)
admin.site.register(FAQ)
admin.site.register(ContactRequest)
admin.site.register(SupportTicket, SupportTicketAdmin)
admin.site.register(NewsletterSubscriber)
