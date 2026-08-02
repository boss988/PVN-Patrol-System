from django.db import models
from core.core_models import Equipment
from django.contrib.auth.models import User

class PersonnelInfo(models.Model):
    """
    设备看护人员信息模型
    输入：手动分配
    输出：经验评估 + 健康度加分
    """
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='personnel')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="看护人员")
    start_date = models.DateField(verbose_name="开始看护日期")
    equip_duration = models.IntegerField(default=0, verbose_name="设备看护时长(月)")
    skills_list = models.TextField(blank=True, verbose_name="可处理异常技能")
    training_history = models.TextField(blank=True, verbose_name="培训记录")

    def __str__(self):
        return f"{self.user.username} - {self.equipment.name}"

    @property
    def experience_score(self):
        """经验评分（用于健康度加分）"""
        return min(100, self.equip_duration * 5 + 20)  # 每月加5分