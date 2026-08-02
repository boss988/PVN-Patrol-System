from django.urls import path
from .search_views import global_search

app_name = 'search'

urlpatterns = [
    path('search/', global_search, name='global_search'),
]