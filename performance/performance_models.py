from django.db import models
from core.core_models import Equipment
from django.utils import timezone

class PerformanceKPI(models.Model):
    """
    设备性能KPI模型
    输入：定时计算（基于问题/报警/数据）
    输出：MTBF/MTTR/OEE + 健康度扣分
    """
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='performance_kpis')
    calc_date = models.DateField(default=timezone.now, verbose_name="计算日期")
    mtbf = models.FloatField(default=0, verbose_name="MTBF(小时)")
    mttr = models.FloatField(default=0, verbose_name="MTTR(小时)")
    oee = models.FloatField(default=0, verbose_name="OEE(%)")

    def __str__(self):
        return f"{self.equipment.name} - {self.calc_date}"

    @property
    def kpi_score(self):
        """KPI综合评分（用于健康度）"""
        return (self.mtbf / 100) * 40 + (100 - self.mttr * 10) * 30 + self.oee * 30