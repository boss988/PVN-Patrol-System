from django.db import models
from django.utils import timezone
from core.core_models import Equipment

class MaintenanceRecord(models.Model):
    """
    保养记录模型
    输入：手动新建 + 定时提醒
    输出：保养历史 + 影响健康度（逾期扣分）
    """
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='maintenance_records')
    maintenance_type = models.CharField(max_length=50, choices=[
        ('daily', '日常保养'),
        ('weekly', '周保养'),
        ('monthly', '月保养'),
        ('quarterly', '季度保养'),
        ('yearly', '年度保养'),
    ], verbose_name="保养类型")
    desc = models.TextField(verbose_name="保养内容/描述")
    maintenance_date = models.DateField(default=timezone.now, verbose_name="保养日期")
    next_due_date = models.DateField(verbose_name="下次到期日期")
    performed_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, verbose_name="执行人")

    def __str__(self):
        return f"{self.equipment.name} - {self.maintenance_type} ({self.maintenance_date})"

    @property
    def is_overdue(self):
        """是否逾期"""
        return self.next_due_date < timezone.now().date()




class MaintenanceSOP(models.Model):
    """
    保养SOP标准模型（超越现有SOP截图）
    输入：后台添加SOP项目
    输出：用于自动生成计划 + 执行模板
    """
    equipment = models.ForeignKey('core.Equipment', on_delete=models.CASCADE, related_name='sops', verbose_name="所属设备")

    name = models.CharField(max_length=200, verbose_name="保养项目名称")
    category = models.CharField(max_length=20, choices=[
        ('daily', '日常保养'),
        ('weekly', '周保养'),
        ('monthly', '月保养'),
        ('quarterly', '季度保养'),
        ('half_year', '半年保养'),
    ], verbose_name="保养类别")

    is_numeric = models.BooleanField(default=False, verbose_name="是否需要数值")
    lower_limit = models.FloatField(null=True, blank=True, verbose_name="下限")
    upper_limit = models.FloatField(null=True, blank=True, verbose_name="上限")
    unit = models.CharField(max_length=20, blank=True, verbose_name="单位")

    responsible_unit = models.CharField(max_length=50, blank=True, verbose_name="保养负责人单位")

    # ==================== 新增：SOP图片（工厂截图需要的字段） ====================
    sop_image = models.ImageField(
        upload_to='sop_images/',
        blank=True,
        null=True,
        verbose_name="SOP图片"
    )

    # 照片与文档（多张照片用JSONField简单存储）
    sop_photos = models.JSONField(default=list, blank=True, verbose_name="SOP照片URL列表")
    sop_document = models.FileField(upload_to='sops/docs/', blank=True, null=True, verbose_name="SOP文档")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.equipment.name} - {self.name} ({self.get_category_display()})"


class MaintenanceJobTemplate(models.Model):
    """
    每日保养作业模板（OP打卡核心模型）
    输入：凌晨自动从SOP生成
    输出：今天保养执行页面 + 照片 + 寿命 + 备品
    """
    equipment = models.ForeignKey('core.Equipment', on_delete=models.CASCADE, related_name='job_templates')
    sop = models.ForeignKey(MaintenanceSOP, on_delete=models.CASCADE, related_name='jobs')

    job_date = models.DateField(verbose_name="执行日期")
    status = models.CharField(max_length=20, choices=[('pending', '待执行'), ('done', '已完成')], default='pending')

    # 执行数据
    before_photo = models.ImageField(upload_to='jobs/before/', blank=True, null=True, verbose_name="执行前照片")
    after_photo = models.ImageField(upload_to='jobs/after/', blank=True, null=True, verbose_name="执行后照片")

    tool_life = models.CharField(max_length=50, blank=True, verbose_name="起子头/吸盘寿命")
    spare_used = models.BooleanField(default=False, verbose_name="是否使用备品")

    performed_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, verbose_name="执行人")
    audited_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='+', verbose_name="稽核人")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.equipment.name} - {self.sop.name} ({self.job_date})"