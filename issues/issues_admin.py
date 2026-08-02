from django.contrib import admin
from .issues_models import EquipmentIssue, PatrolIssue, PatrolCategory


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