# fix_groups.py
# 一键修复 Group 和超级用户权限

import os
import django
from django.core.exceptions import ObjectDoesNotExist

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'equipment_health.settings')
django.setup()

from django.contrib.auth.models import User, Group
from core.models import UserProfile

print("开始修复管理员组和权限...")

# 1. 创建必要的组
admin_group, created = Group.objects.get_or_create(name='管理员')
if created:
    print("✅ 已创建 '管理员' 组")
else:
    print("✅ '管理员' 组已存在")

user_group, created = Group.objects.get_or_create(name='用户')
if created:
    print("✅ 已创建 '用户' 组")
else:
    print("✅ '用户' 组已存在")

# 2. 修复你的超级用户（perry_chen）
try:
    user = User.objects.get(username='perry_chen')   # ← 如果你的用户名不是 perry_chen，请改成你自己的
    user.is_superuser = True
    user.is_staff = True
    user.save()
    print(f"✅ 用户 {user.username} 已设置为超级用户")

    # 创建或更新 UserProfile
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'work_number': user.username,
            'name': '超级管理员',
            'role': 'admin'
        }
    )
    if not created:
        profile.role = 'admin'
        profile.save()
    print("✅ UserProfile 已修复为管理员")

    # 加入管理员组
    user.groups.add(admin_group)
    print("✅ 已加入 '管理员' 组")

    print("\n🎉 修复完成！现在可以正常新建管理员账号了")

except User.DoesNotExist:
    print("❌ 未找到用户 'perry_chen'，请确认用户名是否正确")
except Exception as e:
    print(f"❌ 发生错误: {e}")