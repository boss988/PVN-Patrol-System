from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.apps import apps

UserProfile = apps.get_model('core', 'UserProfile')


@login_required
def user_list(request):
    try:
        if request.user.profile.role != 'admin':
            messages.error(request, '❌ 普通用户无权访问用户管理页面')
            return redirect('core:equipment_list')
    except:
        messages.error(request, '❌ 权限验证失败')
        return redirect('core:equipment_list')

    users = User.objects.all().order_by('username')
    return render(request, 'users/user_list.html', {'users': users})


@login_required
def user_create(request):
    """新建用户 - 最终稳定版（彻底解决 UNIQUE 错误）"""
    UserProfile = apps.get_model('core', 'UserProfile')
    try:
        if request.user.profile.role != 'admin':
            messages.error(request, '❌ 普通用户无权创建新用户')
            return redirect('core:equipment_list')
    except:
        messages.error(request, '❌ 权限验证失败')
        return redirect('core:equipment_list')

    if request.method == 'POST':
        username = request.POST.get('username').strip()
        password = request.POST.get('password')
        name = request.POST.get('name', '').strip()
        department = request.POST.get('department', '')
        permission_area = request.POST.get('permission_area', '')
        role = request.POST.get('role', 'user')

        if not username or not password:
            messages.error(request, '❌ 工号和密码不能为空')
            return redirect('users:user_create')

        if User.objects.filter(username=username).exists():
            messages.error(request, '❌ 该工号已存在！')
            return redirect('users:user_create')

        # 创建 User
        user = User.objects.create_user(username=username, password=password)

        # 关键修复：使用 get_or_create 防止重复
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'work_number': username,
                'name': name or username,
                'department': department,
                'permission_area': permission_area,
                'role': role
            }
        )

        # 强制更新角色（确保管理员能正确保存）
        profile.role = role
        profile.name = name or username
        profile.department = department
        profile.permission_area = permission_area
        profile.save()

        # 加入权限组
        group_name = '管理员' if role == 'admin' else '用户'
        group = Group.objects.get(name=group_name)
        user.groups.add(group)

        messages.success(request, f'✅ 用户 {username} 创建成功！角色：{profile.get_role_display()}')
        return redirect('users:user_list')

    return render(request, 'users/user_create.html')


@login_required
def user_edit(request, pk):
    """编辑用户 - 增加超级管理员保护"""
    try:
        if request.user.profile.role != 'admin':
            messages.error(request, '❌ 普通用户无权编辑')
            return redirect('users:user_list')
    except:
        messages.error(request, '❌ 权限验证失败')
        return redirect('users:user_list')

    user = get_object_or_404(User, pk=pk)
    profile = UserProfile.objects.get(user=user)

    # ==================== 超级管理员保护 ====================
    protected_accounts = ['s20038978', 'superadmin', 'admin001', 'perry_chen']

    if user.username in protected_accounts:
        if request.user.username not in protected_accounts:
            messages.error(request, '❌ 该账号是系统超级管理员，其他管理员无权修改其权限！')
            return redirect('users:user_list')

    # 最后一名管理员保护（防止系统完全没有管理员）
    if profile.role == 'admin':
        admin_count = UserProfile.objects.filter(role='admin').count()
        if admin_count == 1 and request.user != user:
            messages.error(request, '❌ 系统必须至少保留一位管理员，不能修改最后一位管理员的角色！')
            return redirect('users:user_list')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        department = request.POST.get('department', '')
        permission_area = request.POST.get('permission_area', '')
        role = request.POST.get('role', 'user')

        profile.name = name or user.username
        profile.department = department
        profile.permission_area = permission_area
        profile.role = role
        profile.save()

        # 更新用户组
        user.groups.clear()
        group_name = '管理员' if role == 'admin' else '用户'
        group = Group.objects.get(name=group_name)
        user.groups.add(group)

        messages.success(request, f'✅ 用户 {user.username} 编辑成功！')
        return redirect('users:user_list')

    return render(request, 'users/user_edit.html', {'user': user, 'profile': profile})

@login_required
def user_delete(request, pk):
    """删除用户 - 加强超级管理员保护"""
    try:
        if request.user.profile.role != 'admin':
            messages.error(request, '❌ 普通用户无权删除用户')
            return redirect('users:user_list')
    except:
        messages.error(request, '❌ 权限验证失败')
        return redirect('users:user_list')

    user = get_object_or_404(User, pk=pk)

    # ==================== 超级管理员保护（最严格） ====================
    protected_accounts = ['s20038978', 'superadmin', 'perry_chen']

    if user.username in protected_accounts:
        messages.error(request, f'❌ 该账号是系统超级管理员，不可被任何人删除！')
        return redirect('users:user_list')

    # 最后一名管理员保护
    if UserProfile.objects.get(user=user).role == 'admin':
        admin_count = UserProfile.objects.filter(role='admin').count()
        if admin_count == 1:
            messages.error(request, '❌ 系统必须至少保留一位管理员，不能删除最后一位管理员！')
            return redirect('users:user_list')

    # 执行删除
    username = user.username
    user.delete()
    messages.success(request, f'✅ 用户 {username} 已成功删除！')
    return redirect('users:user_list')