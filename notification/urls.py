from django.urls import path
from .views import patrol_send_email, create_email_group

app_name = 'notification'

urlpatterns = [
    path('patrol/send/', patrol_send_email, name='patrol_send_email'),
    path('create-group/', create_email_group, name='create_email_group'),
]