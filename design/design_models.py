from django.db import models
from core.core_models import Equipment  # 交互接口：外键关联总表

class DesignInfo(models.Model):
    """
    设备设计信息模型（已按你的6大优化点升级）。
    输入：通过表单或上传创建。
    输出：设计风险数据，供健康计算用。
    功能：存储设计细节，计算风险评分。
    交互：OneToOne到Equipment（每设备一个设计）。
    """
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='design_info')

    # ===== 硬件/软件配置（扣分项）=====
    has_computer = models.BooleanField(default=False, verbose_name="工业电脑")
    has_robot_arm = models.BooleanField(default=False, verbose_name="机械手")
    has_screw_feeder = models.BooleanField(default=False, verbose_name="螺丝供料器")
    has_scanner = models.BooleanField(default=False, verbose_name="扫描仪")
    has_printer = models.BooleanField(default=False, verbose_name="打印机")
    vision_type = models.CharField(max_length=20, choices=[('AI', 'AI视觉'), ('normal', '普通视觉'), ('none', '无')], default='none', verbose_name="视觉类型")
    plc_model = models.CharField(max_length=100, blank=True, verbose_name="PLC型号")

    # ===== 文件上传 =====
    dvp_file = models.FileField(upload_to='design/dvp/', blank=True, verbose_name="DVP文件")
    pmp_file = models.FileField(upload_to='design/pmp/', blank=True, verbose_name="PMP文件")
    image = models.ImageField(upload_to='designs/', null=True, blank=True, verbose_name="设备照片")

    # 原有字段保留
    risk_points_text = models.TextField(verbose_name="风险点描述", blank=True)
    vulnerable_parts_list = models.TextField(verbose_name="易损部件列表", blank=True)
    software_risks = models.TextField(verbose_name="软件风险", blank=True)
    has附属 = models.BooleanField(default=False, verbose_name="有附属")
    has_scan = models.BooleanField(default=False, verbose_name="有扫码")
    multi_model = models.BooleanField(default=False, verbose_name="多机种")
    perf_req = models.CharField(max_length=200, verbose_name="性能要求", blank=True)
    novel_design = models.BooleanField(default=False, verbose_name="新特异设计")

    def __str__(self):
        return f"设计 - {self.equipment.code}"

    @property
    def design_risk_score(self):
        """
        设计风险扣分（自动计算，供健康度使用）。
        输入：模型字段。
        输出：扣分值（越高越危险）。
        """
        score = 0
        if self.has_computer: score += 6
        if self.has_robot_arm: score += 8
        if self.has_screw_feeder: score += 4
        if self.has_scanner: score += 4
        if self.has_printer: score += 4
        if self.vision_type == 'normal': score += 10
        if self.multi_model or self.novel_design: score += 20
        return min(100, score)


# ==================== 新增：文件临时共享模型 ====================
class SharedFile(models.Model):
    """文件临时共享中心使用的文件记录"""

    # 上传人（自动记录当前登录用户）
    uploader = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name="上传人")

    # 文件本身
    file = models.FileField(upload_to='shared_files/', verbose_name="文件")

    # 其他信息
    file_name = models.CharField(max_length=255, verbose_name="文件名")
    file_size = models.BigIntegerField(verbose_name="文件大小（字节）")
    upload_time = models.DateTimeField(auto_now_add=True, verbose_name="上传时间")

    class Meta:
        verbose_name = "共享文件"
        verbose_name_plural = "共享文件"
        ordering = ['-upload_time']  # 按上传时间倒序显示

    def __str__(self):
        return f"{self.file_name} ({self.uploader.username})"