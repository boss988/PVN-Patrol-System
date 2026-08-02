from django.db import models
from django.contrib.auth.models import User  # 使用 Django 默认用户模型


class LaserCheckConfig(models.Model):
    """镭雕图检查工具的全局路径配置"""
    product_folder = models.CharField(max_length=500, verbose_name="产品图文件夹路径")
    laser_folder = models.CharField(max_length=500, verbose_name="镭雕图文件夹路径")
    mapping_excel = models.CharField(max_length=500, verbose_name="料号映射Excel路径", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "镭雕图检查配置"
        verbose_name_plural = "镭雕图检查配置"

    def __str__(self):
        return f"配置 (ID: {self.id})"


# ==================== 新增 AI 检测记录模型 ====================
class AIComparison(models.Model):
    """AI 检测记录（产品图 vs 镭雕图）"""
    part_number = models.CharField(max_length=50, verbose_name="料号", db_index=True)

    product_image = models.ImageField(
        upload_to='ai_compare/product/%Y/%m/%d/',
        verbose_name="产品图截图",
        blank=True,
        null=True
    )

    laser_image = models.ImageField(
        upload_to='ai_compare/laser/%Y/%m/%d/',
        verbose_name="镭雕图截图",
        blank=True,
        null=True
    )

    result_text = models.TextField(verbose_name="AI检测结果")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="检测时间")
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="检测人员"
    )

    class Meta:
        verbose_name = "AI检测记录"
        verbose_name_plural = "AI检测记录"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.part_number} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"