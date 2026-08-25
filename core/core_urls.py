from django.urls import path
from .core_views import (
    equipment_list,
    equipment_detail,
    equipment_create,
    global_alarms_list,
    dashboard,
    equipment_edit,
    equipment_delete,
    equipment_import,
    equipment_ai_predict,
    ai_assistant_parse,#测试AI用
    equipment_update_position,#设备position
)

app_name = 'core'

urlpatterns = [
    path('', equipment_list, name='equipment_list'),
    path('<int:pk>/', equipment_detail, name='equipment_detail'),
    path('create/', equipment_create, name='equipment_create'),
    path('alarms/', global_alarms_list, name='global_alarms_list'),
    path('dashboard/', dashboard, name='dashboard'),

    # 下面这两行是修改和删除的正确路径（只保留一次）
    path('edit/<int:pk>/', equipment_edit, name='equipment_edit'),
    path('edit/<int:pk>/position/', equipment_update_position, name='equipment_update_position'),
    path('delete/<int:pk>/', equipment_delete, name='equipment_delete'),
    path('equipments/import/', equipment_import, name='equipment_import'),
    # 新增：龙虾AI预测
    path('<int:pk>/ai-predict/', equipment_ai_predict, name='equipment_ai_predict'),
    # 新增：龙虾AI助手页面
    path('ai-assistant/', ai_assistant_parse, name='ai_assistant_parse'),

]