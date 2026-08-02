from django.db import models
from core.core_models import Equipment
from django.utils import timezone

class EquipmentData(models.Model):
    """
    设备数据模型（振动/CT/传感器）
    输入：Excel导入
    输出：趋势图 + 健康度扣分
    """
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='data_records')
    data_type = models.CharField(max_length=20, choices=[
        ('vibration', '振动值'),
        ('ct', 'CT值'),
        ('temperature', '温度'),
        ('pressure', '压力'),
    ], verbose_name="数据类型")
    value = models.FloatField(verbose_name="测量值")
    unit = models.CharField(max_length=20, default="mm/s", verbose_name="单位")
    record_date = models.DateTimeField(default=timezone.now, verbose_name="记录时间")
    note = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.equipment.name} - {self.data_type} ({self.value})"