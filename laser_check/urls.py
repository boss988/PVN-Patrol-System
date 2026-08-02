from django.urls import path
from . import views

app_name = 'laser_check'

urlpatterns = [
    path('', views.search_page, name='search_page'),
    path('check/<str:part_number>/', views.check_detail, name='check_detail'),
    path('settings/', views.settings_page, name='settings_page'),

    # 新增：AI 检测页面
    path('ai-check/<str:part_number>/', views.ai_check, name='ai_check'),

    # 文件服务
    path('serve/pdf/<path:filename>', views.serve_pdf, name='serve_pdf'),
    path('serve/ezd-svg/<path:filename>', views.serve_ezd_svg, name='serve_ezd_svg'),
    path('serve/<str:file_type>/<path:filename>', views.serve_file, name='serve_file'),
    path('ai-history/<str:part_number>/', views.ai_history, name='ai_history'),
]

