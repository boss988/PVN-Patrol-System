from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.models import Group   # ← 新增这一行

class Equipment(models.Model):
    """ 设备总表模型：主档案，所有模块关联中心。 """
    code = models.CharField(max_length=50, unique=True, verbose_name="设备编号")
    name = models.CharField(max_length=100, verbose_name="设备名称")
    model = models.CharField(max_length=100, verbose_name="型号")
    location = models.CharField(max_length=200, verbose_name="位置")
    install_date = models.DateField(verbose_name="安装日期")
    status = models.CharField(max_length=20, choices=[('active', '活跃'), ('inactive', '停用'), ('maintenance', '保养中')], default='active', verbose_name="状态")
    responsible = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="负责人")

    # ===== 新增字段（全部可空，不影响现有任何数据）=====
    rfid_card = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name="RFID卡号")
    station = models.CharField(max_length=50, null=True, blank=True, verbose_name="站别")
    line = models.CharField(max_length=50, null=True, blank=True, verbose_name="线别")
    model_type = models.CharField(max_length=100, null=True, blank=True, verbose_name="机种")
    area = models.CharField(max_length=100, null=True, blank=True, verbose_name="区域")
    category = models.CharField(max_length=50, null=True, blank=True, verbose_name="类别")
    eq_type = models.CharField(max_length=50, null=True, blank=True, verbose_name="设备类型")
    position = models.IntegerField(default=0, verbose_name="产线位置排序")
    photo = models.ImageField(upload_to='equipment_photos/', null=True, blank=True, verbose_name="设备照片")

    # ==================== 龙虾AI预测结果 ====================
    ai_score = models.FloatField(default=0, verbose_name="龙虾AI健康度")
    ai_fault_prob = models.FloatField(default=0, verbose_name="下周故障概率(%)")
    ai_remaining_life = models.IntegerField(default=0, verbose_name="剩余寿命(天)")
    ai_suggestion = models.TextField(blank=True, verbose_name="龙虾AI建议")
    ai_last_predict = models.DateTimeField(null=True, blank=True, verbose_name="最后预测时间")
    ai_top_risks = models.JSONField(default=list, blank=True, verbose_name="主要风险模块")

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def health_score(self):
        """健康度总分（0-100）——超级防御版"""
        base = 100
        try:
            if hasattr(self, 'design_info') and self.design_info:
                base -= getattr(self.design_info, 'design_risk_score', 0)

            issues_count = self.issues.count() if hasattr(self, 'issues') else 0
            base -= min(issues_count * 5, 30)

            alerts_count = 0
            try:
                alerts_count = self.alarms.filter(status='未处理').count()
            except:
                pass
            base -= min(alerts_count * 10, 30)

            spares_count = 0
            try:
                spares_count = self.spares.filter(stock_qty__lt=models.F('min_stock')).count()
            except:
                pass
            base -= min(spares_count * 15, 30)

            maintenance_count = 0
            try:
                maintenance_count = self.maintenance_records.filter(is_overdue=True).count()
            except:
                pass
            base -= min(maintenance_count * 10, 20)

        except Exception:
            pass

        return max(0, base)


class AlarmRecord(models.Model):
    """报警记录"""
    equipment = models.ForeignKey('Equipment', on_delete=models.CASCADE, related_name='alarms')
    alarm_type = models.CharField(max_length=50, choices=[
        ('red_light', '红灯报警'),
        ('sensor', '传感器异常'),
        ('other', '其他')
    ], verbose_name="报警类型")
    level = models.IntegerField(default=1, verbose_name="严重等级")
    occur_time = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, default='未处理', choices=[('未处理', '未处理'), ('已处理', '已处理')])
    desc = models.TextField(blank=True, verbose_name="描述")
    handler = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.equipment.name} - {self.alarm_type}"


# ==================== 新增：用户权限扩展模型 ====================
class UserProfile(models.Model):
    """用户扩展信息（工号、角色、权限领域等）"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # 工号（作为登录账号）
    work_number = models.CharField(max_length=50, unique=True, verbose_name="工号")

    # 基本信息
    name = models.CharField(max_length=100, blank=True, verbose_name="姓名")
    department = models.CharField(max_length=100, blank=True, verbose_name="部门/职能")
    line = models.CharField(max_length=100, blank=True, verbose_name="负责线体")

    # 权限角色
    ROLE_CHOICES = [
        ('admin', '管理员'),
        ('user', '普通用户'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user', verbose_name="用户角色")

    # 其他参考字段
    permission_area = models.CharField(max_length=100, blank=True, verbose_name="权限领域")

    def __str__(self):
        return f"{self.work_number} - {self.name} ({self.get_role_display()})"

    class Meta:
        verbose_name = "用户扩展信息"
        verbose_name_plural = "用户扩展信息"


# ==================== 信号：新建用户时自动创建 UserProfile ====================
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """每当新建一个 User 时，自动创建对应的 UserProfile"""
    if created:
        UserProfile.objects.create(
            user=instance,
            work_number=instance.username,   # 默认把登录账号当作工号
            name=instance.username,
            role='user'                      # 默认是普通用户
        )
        # 默认加入“用户”组
        user_group = Group.objects.get(name='用户')
        instance.groups.add(user_group)
        print(f"✅ 已为用户 {instance.username} 自动创建 UserProfile 并加入用户组")