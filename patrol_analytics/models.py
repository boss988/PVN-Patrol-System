from django.db import models


class PatrolSummaryRecord(models.Model):
    """点检汇总看板手动输入的数据（数据库存储版）"""

    save_date = models.DateTimeField(auto_now_add=True, verbose_name="保存时间")
    start_date = models.DateField(verbose_name="数据开始日期")
    end_date = models.DateField(verbose_name="数据结束日期")

    # 把整个表格数据保存成 JSON（结构和原来完全一样）
    data = models.JSONField(verbose_name="汇总数据")

    class Meta:
        verbose_name = "点检汇总记录"
        verbose_name_plural = "点检汇总记录"
        ordering = ['-save_date']

    def __str__(self):
        return f"汇总数据 {self.start_date} ~ {self.end_date} ({self.save_date.strftime('%Y-%m-%d %H:%M')})"