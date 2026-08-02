from django.urls import path
from . import views

app_name = 'patrol_analytics'

urlpatterns = [
    path('dashboard/', views.patrol_analytics_dashboard, name='dashboard'),
    path('save-summary/', views.save_summary, name='save_summary'),   # ← 新增这一行
]