from django.contrib import admin
from .data_models import EquipmentData

@admin.register(EquipmentData)
class EquipmentDataAdmin(admin.ModelAdmin):
    """设备数据后台管理"""
    list_display = ['equipment', 'data_type', 'value', 'unit', 'record_date', 'note']
    list_filter = ['data_type', 'equipment']
    search_fields = ['equipment__name', 'note']
    date_hierarchy = 'record_date'