from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from core.core_views import ai_assistant_parse   # ← 新增这一行
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [

    # 根路径自动跳设备总表（最重要！）
    path('', RedirectView.as_view(url='/equipments/')),
    # ==================== 多语言切换路由（必须加） ====================
    path('i18n/', include('django.conf.urls.i18n')),     # ← 关键！语言切换

    path('admin/', admin.site.urls),
    # path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/login/', csrf_exempt(auth_views.LoginView.as_view(template_name='registration/login.html')), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

    # ==================== 核心修复（只改这一行） ====================
    path('equipments/', include('core.core_urls')),   # ←←← 使用明确前缀
    path('', include('design.design_urls')),
    path('', include('issues.issues_urls')),
    path('', include('spares.spares_urls')),
    path('', include('alerts.alerts_urls')),
    path('', include('maintenance.maintenance_urls')),
    path('data/', include('data.data_urls')),
    path('personnel/', include('personnel.personnel_urls')),
    path('performance/', include('performance.performance_urls')),
    path('search/', include('search.search_urls')),
    path('production/', include('production.urls')),
    path('notification/', include('notification.urls')),
    path('users/', include('users.urls')),  # ← 新增这一行
    # 龙虾AI独立助手页面
    path('ai-assistant/', ai_assistant_parse, name='ai_assistant_parse'), # 注意这行
    # ==================== 新增：镭雕图检查工具（独立功能） ====================
    path('laser-check/', include('laser_check.urls')),
    path('patrol-analytics/', include('patrol_analytics.urls')),
]

# ==================== 照片访问配置（第1步必须） ====================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)