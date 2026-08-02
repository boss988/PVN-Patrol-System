from django.urls import path
from .data_views import global_data_list, import_data

app_name = 'data'
urlpatterns = [
    path('data/', global_data_list, name='global_data_list'),
    path('data/import/', import_data, name='import_data'),
]