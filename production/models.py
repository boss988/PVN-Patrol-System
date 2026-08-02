from django.db import models
from core.core_models import Equipment

class Line(models.Model):
    """产线模型（F44F、F44G 等）"""
    name = models.CharField(max_length=50, unique=True, verbose_name="产线名称")
    description = models.CharField(max_length=200, blank=True, verbose_name="描述")

    def __str__(self):
        return self.name

class LineEquipment(models.Model):
    """产线设备关联（多对多 + 位置排序）"""
    line = models.ForeignKey(Line, on_delete=models.CASCADE, related_name='line_equipments')
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='line_positions')
    position = models.IntegerField(default=0, verbose_name="排序位置")

    class Meta:
        unique_together = ('line', 'equipment')  # 防止重复关联
        ordering = ['position']

    def __str__(self):
        return f"{self.line.name} - {self.equipment.name} (位置 {self.position})"