from django.db import models
from core.core_models import Equipment
from datetime import datetime


# ==================== 设备异常问题类别（独立管理，可后台增减） ====================
class EquipmentIssueCategory(models.Model):
    """
    设备异常问题类别
    用途：录入生产异常时选择（硬件问题 / 软件问题 / 其它...）
    后台可随时新增、修改、停用
    """
    name = models.CharField(max_length=50, unique=True, verbose_name="类别名称")
    order = models.PositiveIntegerField(default=0, verbose_name="排序（数字越小越靠前）")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "设备异常问题类别"
        verbose_name_plural = "设备异常问题类别"
        ordering = ['order', 'id']

    def __str__(self):
        return self.name

# ==================== 产线层级配置（仅设备异常用，与点检无关） ====================
class ProductionLineConfig(models.Model):
    """
    机种 → 类别 → 线体 固定关系
    站别仍从设备总表按线体带出，不写在本表
    """
    model_type = models.CharField(max_length=50, verbose_name="机种")
    category = models.CharField(max_length=50, verbose_name="类别")
    line = models.CharField(max_length=50, verbose_name="线体")
    supervisor = models.CharField(max_length=100, blank=True, default='', verbose_name="默认主管")
    order = models.PositiveIntegerField(default=0, verbose_name="排序")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    remark = models.CharField(max_length=200, blank=True, default='', verbose_name="备注")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "产线层级配置"
        verbose_name_plural = "产线层级配置"
        ordering = ['order', 'model_type', 'category', 'line']
        unique_together = [('model_type', 'category', 'line')]

    def __str__(self):
        return f"{self.model_type} / {self.category} / {self.line}"

class EquipmentIssue(models.Model):
    """
    升级版问题记录模型（适配新Excel格式）
    输入：你的新Excel
    输出：完整根因 + 可导入保养/设计/维修项目 + 自动生成ID
    """
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='issues')
    issue_code = models.CharField(max_length=50, verbose_name="问题码")
    desc = models.TextField(verbose_name="异常现象及原因")
    occur_date = models.DateField(verbose_name="发生日期")
    severity = models.IntegerField(choices=[(1,'低'),(2,'中'),(3,'高')], default=2)
    # ==================== 问题类别（外键，新建时建议必选，历史数据允许空） ====================
    category = models.ForeignKey(
        EquipmentIssueCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="问题类别",
        related_name="equipment_issues"
    )
    # ==================== 责任主管 + 备用字段 ====================
    supervisor = models.CharField(
        max_length=100, blank=True, default='',
        verbose_name="责任主管"
    )
    # 三个备用字段，减少以后改库
    spare_field_1 = models.CharField(max_length=200, blank=True, default='', verbose_name="备用字段1")
    spare_field_2 = models.CharField(max_length=200, blank=True, default='', verbose_name="备用字段2")
    spare_field_3 = models.CharField(max_length=200, blank=True, default='', verbose_name="备用字段3")
    root_cause = models.TextField(blank=True, verbose_name="处理方法")
    reoccur_status = models.BooleanField(default=False, verbose_name="再次发生")
    source_excel = models.CharField(max_length=200, blank=True)

    # === 新增字段（完全匹配你附件）===
    abnormal_work_time = models.IntegerField(default=0, verbose_name="异常工时(min)")
    work_time_type = models.CharField(max_length=20, blank=True, verbose_name="异常工时甄别(硬件/软件/其它)")
    can_import_maintenance = models.BooleanField(default=False, verbose_name="可否导入保养")
    maintenance_id = models.CharField(max_length=50, blank=True, verbose_name="保养ID")
    maintenance_content = models.TextField(blank=True, verbose_name="保养内容")
    can_import_design = models.BooleanField(default=False, verbose_name="可否导入设计改善")
    design_id = models.CharField(max_length=50, blank=True, verbose_name="设计ID")
    design_content = models.TextField(blank=True, verbose_name="设计内容")
    can_import_training = models.BooleanField(default=False, verbose_name="可否导入人员培训")
    training_id = models.CharField(max_length=50, blank=True, verbose_name="培训ID")
    training_content = models.TextField(blank=True, verbose_name="培训内容")
    can_import_repair = models.BooleanField(default=False, verbose_name="可否导入现场维修改善")
    repair_id = models.CharField(max_length=50, blank=True, verbose_name="维修ID")
    repair_content = models.TextField(blank=True, verbose_name="维修内容")
    risk_id = models.CharField(max_length=50, blank=True, verbose_name="RISK ID")  # 自动生成
    # ==================== 新增照片支持（和 PatrolIssue 保持一致） ====================
    photos = models.JSONField(default=list, blank=True, verbose_name="照片列表（多张）")
    photo = models.ImageField(upload_to='issues_photos/', null=True, blank=True, verbose_name="照片/视频（单张兼容）")

    def __str__(self):
        return f"{self.issue_code} - {self.equipment.name}"


class PatrolIssue(models.Model):
    """
    点检问题点记录（独立于设备总表，每天小点检专用）
    输入：人工输入或Excel导入
    输出：列表 + 多张照片 + 状态
    """
    sequence = models.IntegerField(verbose_name="顺序", null=True, blank=True)
    date = models.DateField(verbose_name="日期")
    line = models.CharField(max_length=50, verbose_name="线别")
    station = models.CharField(max_length=50, verbose_name="站别")
    problem_desc = models.TextField(verbose_name="问题要改善")

    # === 修改为支持多张照片 ===
    photos = models.JSONField(default=list, blank=True, verbose_name="照片列表（多张）")
    # 保留原来的单文件字段（兼容旧数据）
    photo = models.FileField(upload_to='patrol_photos/', null=True, blank=True, verbose_name="照片/视频（单张兼容）")

    op_responsible = models.CharField(max_length=100, verbose_name="越南负责人（OP）")
    supervisor = models.CharField(max_length=100, verbose_name="责任单位主管")
    status = models.CharField(
        max_length=10,
        choices=[('Open', 'Open'), ('Closed', 'Closed')],
        default='Open',
        verbose_name="情况"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.date} - {self.line} - {self.station}"

    class Meta:
        ordering = ['-date']
        verbose_name = "点检问题点记录"
        verbose_name_plural = "点检问题点记录"


class PatrolCategory(models.Model):
    """
    点检问题类别（独立管理表）
    可以在后台随时增加、修改、停用
    """
    name = models.CharField(max_length=50, unique=True, verbose_name="类别名称")
    order = models.PositiveIntegerField(default=0, verbose_name="排序（数字越小越靠前）")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "点检类别"
        verbose_name_plural = "点检类别"

    def __str__(self):
        return self.name


class PatrolIssue(models.Model):
    """
    点检问题点记录（独立于设备总表，每天小点检专用）
    输入：人工输入或Excel导入
    输出：列表 + 多张照片 + 状态
    """
    sequence = models.IntegerField(verbose_name="顺序", null=True, blank=True)
    date = models.DateField(verbose_name="日期")
    line = models.CharField(max_length=50, verbose_name="线别")
    station = models.CharField(max_length=50, verbose_name="站别")
    problem_desc = models.TextField(verbose_name="问题要改善")

    # === 修改为支持多张照片 ===
    photos = models.JSONField(default=list, blank=True, verbose_name="照片列表（多张）")
    # 保留原来的单文件字段（兼容旧数据）
    photo = models.FileField(upload_to='patrol_photos/', null=True, blank=True, verbose_name="照片/视频（单张兼容）")

    op_responsible = models.CharField(max_length=100, verbose_name="越南负责人（OP）")
    supervisor = models.CharField(max_length=100, verbose_name="责任单位主管")
    status = models.CharField(
        max_length=10,
        choices=[('Open', 'Open'), ('Closed', 'Closed')],
        default='Open',
        verbose_name="情况"
    )

    # ==================== 新增字段（2026-08） ====================
    # 点检类别（外键，新建时必填，历史数据允许为空）
    category = models.ForeignKey(
        PatrolCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,          # 数据库允许空（兼容旧数据）
        verbose_name="点检类别",
        related_name="issues"
    )

    # 两个备用字段（防止以后频繁改数据库）
    spare_field_1 = models.CharField(max_length=200, blank=True, null=True, verbose_name="备用字段1")
    spare_field_2 = models.CharField(max_length=200, blank=True, null=True, verbose_name="备用字段2")
    # ===========================================================

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.date} - {self.line} - {self.station}"

    class Meta:
        ordering = ['-date']
        verbose_name = "点检问题点记录"
        verbose_name_plural = "点检问题点记录"

class MarqueeNotice(models.Model):
    """
    公屏通知（跑马灯优先显示）
    整个系统只使用最新的一条启用中的通知
    """
    content = models.CharField(max_length=200, verbose_name="通知内容")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_by = models.CharField(max_length=50, blank=True, verbose_name="发布人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="发布时间")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "公屏通知"
        verbose_name_plural = "公屏通知"
        ordering = ['-created_at']

    def __str__(self):
        status = "启用" if self.is_active else "已关闭"
        return f"[{status}] {self.content[:30]}"

