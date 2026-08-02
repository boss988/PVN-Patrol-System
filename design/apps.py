from django.apps import AppConfig

class DesignConfig(AppConfig):
    """
    Design App的配置类。
    输入：无。
    输出：无。
    功能：定义App配置，并在ready()中导入模型。
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'design'

    def ready(self):
        import design.design_models