from django.urls import path
from .maintenance_views import global_maintenance_list, maintenance_create, global_sop_list, sop_create, today_maintenance_execute, tomorrow_maintenance_plan, monthly_maintenance_record

app_name = 'maintenance'
urlpatterns = [
    path('maintenance/', global_maintenance_list, name='global_maintenance_list'),
    path('maintenance/create/', maintenance_create, name='maintenance_create'),

    # 新增SOP路径
    path('sops/', global_sop_list, name='global_sop_list'),
    path('sops/create/', sop_create, name='sop_create'),
    path('today-execute/', today_maintenance_execute, name='today_maintenance_execute'),
    path('tomorrow-plan/', tomorrow_maintenance_plan, name='tomorrow_maintenance_plan'),
    path('monthly-record/', monthly_maintenance_record, name='monthly_maintenance_record'),
]