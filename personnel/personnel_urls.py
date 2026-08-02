from django.urls import path
from .personnel_views import global_personnel_list, personnel_assign

app_name = 'personnel'
urlpatterns = [
    path('personnel/', global_personnel_list, name='global_personnel_list'),
    path('personnel/assign/', personnel_assign, name='personnel_assign'),
]