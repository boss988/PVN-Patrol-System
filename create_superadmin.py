# create_superadmin.py
# 一键创建或升级为超级管理员（可重复运行）

import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'equipment_health.settings')
django.setup()

from django.contrib.auth.models import User, Group
from django.apps import apps

UserProfile = apps.get_model('core', 'UserProfile')

def create_or_upgrade_superadmin():
    print("=== 创建或升级超级管理员账号 ===\n")

    username = input("请输入工号: ").strip()
    password = input("请输入密码 (如果用户已存在，可直接回车不修改): ").strip()
    name = input("请输入姓名 (可直接回车): ").strip()

    if not username:
        print("❌ 工号不能为空！")
        return

    # 检查用户是否存在
    user_exists = User.objects.filter(username=username).exists()

    if user_exists:
        user = User.objects.get(username=username)
        print(f"✅ 用户 {username} 已存在，正在升级为管理员...")
    else:
        if not password:
            print("❌ 新用户必须输入密码！")
            return
        user = User.objects.create_superuser(username=username, password=password, email='')
        print(f"✅ 新用户 {username} 创建成功，正在设置为管理员...")

    # 更新或创建 UserProfile
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.work_number = username
    if name:
        profile.name = name
    profile.role = 'admin'
    profile.save()

    # 加入管理员组
    admin_group = Group.objects.get(name='管理员')
    user.groups.add(admin_group)

    print("\n🎉 操作成功！")
    print(f"   工号: {username}")
    print(f"   姓名: {profile.name}")
    print(f"   角色: 管理员（已保护，不可删除）")
    if password:
        print(f"   密码: {password}")
    print("\n现在可以用这个账号登录系统了！")

if __name__ == "__main__":
    create_or_upgrade_superadmin()