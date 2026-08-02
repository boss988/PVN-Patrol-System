# create_groups.py
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'equipment_health.settings')
django.setup()

from django.contrib.auth.models import Group

Group.objects.get_or_create(name='管理员')
Group.objects.get_or_create(name='用户')

print("✅ 已成功创建 '管理员' 和 '用户' 组")
print("现在可以关闭这个窗口了")
