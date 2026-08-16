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
    patrol_update_problem,  # ← 新增的函数
    marquee_notice_manage,
    marquee_content_api,
    issue_detail, # ← 新增3个设备问题点函数
    issue_edit,
    issue_delete,
    equipment_issue_export,
    # equipment_analytics_dashboard,# ← 问题点分析
    equipment_analytics_home,
    equipment_analytics_trend,
    equipment_analytics_lines,
    equipment_analytics_stations,
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
  # 新增公屏路由
    path('patrol/marquee-notice/', marquee_notice_manage, name='marquee_notice_manage'),
    path('patrol/marquee-content/', marquee_content_api, name='marquee_content_api'),
   # 新增设备异常（不依赖某个设备 pk，表单里自己选机种/线/站）
    path('issues/create/', issue_create, name='issue_create_global'),
    path('issues/<int:pk>/detail/', issue_detail, name='issue_detail'),
    path('issues/<int:pk>/edit/', issue_edit, name='issue_edit'),
    path('issues/<int:pk>/delete/', issue_delete, name='issue_delete'),
    path('issues/export/', equipment_issue_export, name='equipment_issue_export'),
    # ---------- 设备异常分析看板（拆分页面） ----------
    path('issues/analytics/', equipment_analytics_home, name='equipment_analytics'),
    path('issues/analytics/<str:model>/', equipment_analytics_trend, name='equipment_analytics_trend'),
    path('issues/analytics/<str:model>/<str:mode>/<str:point>/', equipment_analytics_lines, name='equipment_analytics_lines'),
    path(
    'issues/analytics/<str:model>/<str:mode>/<str:point>/line/<path:line>/',
    equipment_analytics_stations,
    name='equipment_analytics_stations',
),
]