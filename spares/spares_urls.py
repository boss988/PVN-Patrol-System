from django.urls import path
from .spares_views import global_spares_list, spares_list, import_spares, spare_delete, spare_create

app_name = 'spares'
urlpatterns = [
    path('spares/', global_spares_list, name='global_spares_list'),
    path('spares/<int:equipment_pk>/', spares_list, name='spares_list'),
    path('spares/<int:equipment_pk>/create/', spare_create, name='spare_create'),   # ← 新增这一行
    path('spares/import/', import_spares, name='import_spares'),
    path('spares/delete/<int:pk>/', spare_delete, name='spare_delete'),

]