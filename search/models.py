from django.db import models

class SearchLog(models.Model):
    """搜索日志（可选，后期可做搜索热度统计）"""
    keyword = models.CharField(max_length=200, verbose_name="搜索关键词")
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.keyword} ({self.created_at})"