from django.apps import AppConfig

class SparesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'spares'
    # ready() 已删除（这是导致WinError 123的根源）