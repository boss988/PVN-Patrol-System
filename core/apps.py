from django.apps import AppConfig

class CoreConfig(AppConfig):
    """
    Core App的配置类。
    输入：无（Django自动调用）。
    输出：无（配置App行为）。
    功能：定义App配置，并在ready()中安全导入模型，避免早加载错误。
    """
    default_auto_field = 'django.db.models.BigAutoField'  # 默认主键类型
    name = 'core'  # App名称

    def ready(self):
        """
        ready方法：在App注册表准备好后调用。
        输入：无。
        输出：无。
        功能：延迟导入模型文件，确保时机正确。
        """
        import core.core_models  # 导入整个模块（或 from core.core_models import * 如果需要暴露特定模型）