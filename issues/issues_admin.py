from django.contrib import admin
from .issues_models import EquipmentIssue, PatrolIssue, PatrolCategory
from .issues_models import EquipmentIssue, PatrolIssue, EquipmentIssueCategory,ProductionLineConfig


@admin.register(PatrolCategory)
class PatrolCategoryAdmin(admin.ModelAdmin):
    """
    点检类别管理（可在后台随时增删改）
    """
    list_display = ('order', 'name', 'is_active', 'created_at')
    list_display_links = ('name',)  # ← 新增这一行（关键！）
    list_editable = ('order', 'is_active')          # 可直接在列表页改排序和启用状态
    search_fields = ('name',)
    ordering = ('order',)


@admin.register(PatrolIssue)
class PatrolIssueAdmin(admin.ModelAdmin):
    """
    PatrolIssue 的 admin 配置（点检记录也支持删除）
    """
    list_display = ('date', 'line', 'station', 'category', 'problem_desc', 'op_responsible', 'supervisor', 'status')
    list_filter = ('status', 'date', 'category')    # 增加按类别筛选
    search_fields = ('problem_desc', 'line', 'station', 'supervisor')
    date_hierarchy = 'date'
    ordering = ('-date',)
    raw_id_fields = ('category',)                   # 类别多的时候更好用

    actions = ['delete_selected']

    def delete_selected(self, request, queryset):
        queryset.delete()
        self.message_user(request, "选中的点检记录已删除！")
    delete_selected.short_description = "删除选中的点检记录"

@admin.register(EquipmentIssueCategory)
class EquipmentIssueCategoryAdmin(admin.ModelAdmin):
    """设备异常问题类别后台管理"""
    list_display = ('order', 'name', 'is_active', 'created_at')
    list_display_links = ('name',)          # 避免 list_editable 报错
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('order', 'id')

@admin.register(ProductionLineConfig)
class ProductionLineConfigAdmin(admin.ModelAdmin):
    list_display = ('order', 'model_type', 'category', 'line', 'supervisor', 'is_active')
    list_display_links = ('line',)
    list_editable = ('order', 'is_active')
    list_filter = ('model_type', 'category', 'is_active')
    search_fields = ('model_type', 'category', 'line', 'supervisor')
    ordering = ('order', 'model_type', 'category', 'line')