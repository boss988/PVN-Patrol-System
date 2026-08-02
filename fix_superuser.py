# python fix_superuser.py
# 一键修复超级用户权限（使用 django.setup() 正确加载环境）

import os
import django
from django.core.exceptions import ObjectDoesNotExist

# ==================== 关键：正确加载 Django 项目环境 ====================
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'equipment_health.settings')
django.setup()

# 现在再导入模型
from django.contrib.auth.models import User, Group
from django.apps import apps

UserProfile = apps.get_model('core', 'UserProfile')   # 使用 get_model 避免 import 失败

def fix_superuser(username):
    try:
        user = User.objects.get(username=username)
        print(f"✅ 找到用户: {username}")

        # 设置超级用户权限
        user.is_superuser = True
        user.is_staff = True
        user.save()

        # 创建或更新 UserProfile
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'work_number': username,
                'name': '超级管理员',
                'role': 'admin'
            }
        )

        if created:
            print("✅ 已创建 UserProfile")
        else:
            profile.role = 'admin'
            profile.save()
            print("✅ 已更新 UserProfile 为管理员")

        # 加入管理员组
        admin_group = Group.objects.get(name='管理员')
        user.groups.add(admin_group)
        print("✅ 已加入 '管理员' 组")

        print(f"\n🎉 用户 {username} 已成功修复为超级管理员权限！")
        print("现在可以重新登录后台了")

    except User.DoesNotExist:
        print(f"❌ 用户 {username} 不存在！请检查用户名是否正确")
    except ObjectDoesNotExist:
        print("❌ 未找到 '管理员' 组，请确认组已存在")

if __name__ == "__main__":
    username = input("请输入你要修复的超级用户名: ").strip()
    if username:
        fix_superuser(username)
    else:
        print("用户名不能为空")

