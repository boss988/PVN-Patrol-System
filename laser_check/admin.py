from django.contrib import admin
from .models import LaserCheckConfig

@admin.register(LaserCheckConfig)
class LaserCheckConfigAdmin(admin.ModelAdmin):
    list_display = ['product_folder', 'laser_folder', 'mapping_excel', 'updated_at']
    fieldsets = (
        ('路径设置', {
            'fields': ('product_folder', 'laser_folder', 'mapping_excel')
        }),
    )