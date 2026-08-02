from django.contrib import admin
from .models import EmailGroup

@admin.register(EmailGroup)
class EmailGroupAdmin(admin.ModelAdmin):
    """EmailGroup 管理界面"""
    list_display = ('name', 'description', 'created_by', 'created_at')
    list_filter = ('created_by', 'created_at')
    search_fields = ('name', 'emails')
    ordering = ('-created_at',)