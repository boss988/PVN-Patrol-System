from django.db import models

# 这个 App 暂时不需要额外模型
# 因为 UserProfile 已经定义在 core/models.py 中
# 这里保持最小化，方便以后扩展

class Meta:
    verbose_name = "用户管理"
    verbose_name_plural = "用户管理"