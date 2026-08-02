from django.db import models
from django.contrib.auth.models import User

class EmailGroup(models.Model):
    """邮件群组（普通用户也能创建）"""
    name = models.CharField(max_length=100, verbose_name="群组名称")
    description = models.CharField(max_length=200, blank=True, verbose_name="描述")
    emails = models.TextField(verbose_name="邮箱列表（一行一个或逗号分隔）")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="创建人")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "邮件群组"
        verbose_name_plural = "邮件群组"