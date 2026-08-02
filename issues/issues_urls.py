from django.urls import path
from .issues_views import (
    issues_list,
    issue_create,
    import_issues,
    global_issues_list,
    patrol_list,
    patrol_create,
    patrol_edit,
    patrol_import,
    patrol_export,
    patrol_delete,
    patrol_update_problem  # ← 新增的函数
)

app_name = 'issues'

urlpatterns = [
    # 特定设备的问题点列表
    path('issues/<int:equipment_pk>/', issues_list, name='issues_list'),

    # 新增问题点
    path('issues/<int:equipment_pk>/create/', issue_create, name='issue_create'),

    # Excel 导入（特定设备）
    path('issues/<int:equipment_pk>/import/', import_issues, name='import_issues'),

    # 全局问题点列表
    path('issues/', global_issues_list, name='global_issues_list'),

    # 全局导入（不带 equipment_pk）
    path('issues/import/', import_issues, name='import_issues_global'),

    # ==================== 点检问题点记录 ====================
    path('patrol/', patrol_list, name='patrol_list'),
    path('patrol/create/', patrol_create, name='patrol_create'),
    path('patrol/<int:pk>/edit/', patrol_edit, name='patrol_edit'),
    path('patrol/import/', patrol_import, name='patrol_import'),
    path('patrol/export/', patrol_export, name='patrol_export'),
    path('patrol/<int:pk>/delete/', patrol_delete, name='patrol_delete'),

    # 新增：双击编辑“问题要改善”字段
    path('patrol/update-problem/<int:pk>/', patrol_update_problem, name='patrol_update_problem'),
]