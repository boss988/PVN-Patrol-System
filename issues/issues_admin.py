from django.contrib import admin
from .issues_models import EquipmentIssue, PatrolIssue   # 两个模型都注册

@admin.register(EquipmentIssue)
class EquipmentIssueAdmin(admin.ModelAdmin):
    """
    EquipmentIssue 的 admin 配置（已开启删除功能）
    """
    list_display = ('issue_code', 'equipment', 'desc', 'occur_date', 'severity', 'reoccur_status')
    list_filter = ('severity', 'reoccur_status', 'occur_date')
    search_fields = ('issue_code', 'desc', 'equipment__code', 'root_cause')
    date_hierarchy = 'occur_date'
    ordering = ('-occur_date',)

    # 开启批量删除功能
    actions = ['delete_selected']

    def delete_selected(self, request, queryset):
        queryset.delete()
        self.message_user(request, "✅ 选中的问题点已删除！")
    delete_selected.short_description = "🗑 删除选中的问题点"


@admin.register(PatrolIssue)
class PatrolIssueAdmin(admin.ModelAdmin):
    """
    PatrolIssue 的 admin 配置（点检记录也支持删除）
    """
    list_display = ('date', 'line', 'station', 'problem_desc', 'op_responsible', 'status')
    list_filter = ('status', 'date')
    search_fields = ('problem_desc', 'line', 'station')
    date_hierarchy = 'date'
    ordering = ('-date',)

    actions = ['delete_selected']

    def delete_selected(self, request, queryset):
        queryset.delete()
        self.message_user(request, "✅ 选中的点检记录已删除！")
    delete_selected.short_description = "🗑 删除选中的点检记录"