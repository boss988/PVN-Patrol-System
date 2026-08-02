from django.urls import path
from .views import production_line, update_order, add_to_line, remove_from_line, add_equipment_page   # ← 加这个

app_name = 'production'

urlpatterns = [
    path('', production_line, name='production_line'),
    path('update-order/', update_order, name='update_order'),
    path('add-to-line/', add_to_line, name='add_to_line'),
    path('remove-from-line/', remove_from_line, name='remove_from_line'),
    path('add/', add_equipment_page, name='add_equipment_page'),   # ← 新增这一行
]