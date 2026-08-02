from django.urls import path
from .alerts_views import global_alerts_list, alert_mark_handled, alert_create

app_name = 'alerts'
urlpatterns = [
    path('alerts/', global_alerts_list, name='global_alerts_list'),
    path('alerts/mark_handled/<int:pk>/', alert_mark_handled, name='alert_mark_handled'),
    path('alerts/create/', alert_create, name='alert_create'),
]