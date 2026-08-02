from django.db import models
from django.utils import timezone

class Alert(models.Model):
    equipment = models.ForeignKey('core.Equipment', on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=50, choices=[
        ('red_light', '红灯报警'),
        ('error_code', '错误代码'),
        ('sensor', '传感器异常'),
        ('other', '其他'),
    ], verbose_name="报警类型")
    desc = models.TextField(verbose_name="报警描述")
    occur_time = models.DateTimeField(default=timezone.now, verbose_name="发生时间")
    handled = models.BooleanField(default=False, verbose_name="是否处理")
    handler = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.SET_NULL, verbose_name="处理人")

    def __str__(self):
        return f"{self.equipment.name} - {self.alert_type}"

    @property
    def is_unhandled(self):
        return not self.handled