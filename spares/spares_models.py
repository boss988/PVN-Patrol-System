from django.db import models
from core.core_models import Equipment


class SparePart(models.Model):
    """
    备品模型（已扩展你清单所有字段）
    输入：Excel导入
    输出：库存 + 使用寿命 + 差異
    """
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='spares')
    name = models.CharField(max_length=100, verbose_name="备品名称")
    spec = models.CharField(max_length=100, verbose_name="规格")
    supplier = models.CharField(max_length=100, blank=True, verbose_name="品牌")
    stock_qty = models.IntegerField(default=0, verbose_name="庫存數量")
    min_stock = models.IntegerField(default=5, verbose_name="安全庫存")

    # 新增你要求的字段
    usage_qty = models.IntegerField(default=0, verbose_name="當站使用數量")
    life_months = models.IntegerField(default=30, verbose_name="使用壽命(月)")
    difference = models.IntegerField(default=0, verbose_name="差異")
    # ==================== 照片字段（支持多张） ====================
    photo = models.ImageField(upload_to='spares_photos/', null=True, blank=True, verbose_name="照片")
    photos = models.JSONField(default=list, blank=True, verbose_name="照片列表（多张）")


    def __str__(self):
        return f"{self.name} ({self.equipment.name})"

    @property
    def is_low_stock(self):
        """低库存判断"""
        return self.stock_qty < self.min_stock