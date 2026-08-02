from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User  # ← 关键：加上这行！

from .personnel_models import PersonnelInfo
from core.core_models import Equipment


@login_required
def global_personnel_list(request):
    """
    全局看护人员列表
    输入：请求
    输出：所有人员分配记录
    """
    personnel = PersonnelInfo.objects.all()
    return render(request, 'personnel/global_personnel_list.html', {'personnel': personnel})


@login_required
def personnel_assign(request):
    """
    分配/编辑看护人员
    输入：表单
    输出：保存后返回列表
    """
    if request.method == 'POST':
        equipment_id = request.POST.get('equipment')
        user_id = request.POST.get('user')
        start_date = request.POST.get('start_date')
        duration = int(request.POST.get('equip_duration', 0))
        skills = request.POST.get('skills_list', '')
        training = request.POST.get('training_history', '')

        equipment = Equipment.objects.get(id=equipment_id)
        user = User.objects.get(id=user_id)

        PersonnelInfo.objects.create(
            equipment=equipment,
            user=user,
            start_date=start_date,
            equip_duration=duration,
            skills_list=skills,
            training_history=training
        )
        messages.success(request, '✅ 看护人员分配成功！')
        return redirect('personnel:global_personnel_list')

    equipments = Equipment.objects.all()
    users = User.objects.all()
    return render(request, 'personnel/personnel_assign.html', {
        'equipments': equipments,
        'users': users
    })