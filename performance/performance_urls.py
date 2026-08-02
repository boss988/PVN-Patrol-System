from django.urls import path
from .performance_views import global_performance_list, performance_create

app_name = 'performance'
urlpatterns = [
    path('performance/', global_performance_list, name='global_performance_list'),
    path('performance/create/', performance_create, name='performance_create'),
]