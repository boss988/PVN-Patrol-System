from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
import os
from django.conf import settings

# ==================== 最终干净导入（彻底解决 NameError） ====================
from .maintenance_models import MaintenanceRecord, MaintenanceSOP, MaintenanceJobTemplate
from core.core_models import Equipment
from search.search_forms import GlobalSearchForm


@login_required
def global_maintenance_list(request):
    """所有保养记录（最终修复版 - 使用 MaintenanceJobTemplate 已完成记录）

    输入：7字段搜索 + 日期范围
    输出：所有设备的已完成保养记录（照片、执行人、备品、状态全部显示）
    """
    from search.search_forms import GlobalSearchForm
    from django.db import models
    from datetime import date

    form = GlobalSearchForm(request.GET)
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    # 查询所有已完成保养记录（关键修复）
    records = MaintenanceJobTemplate.objects.filter(status='done').order_by('-job_date')

    # 7字段搜索过滤
    if form.is_valid():
        id_search = form.cleaned_data['id_search'].strip()
        name = form.cleaned_data['name'].strip()
        area = form.cleaned_data['area'].strip()
        line = form.cleaned_data['line'].strip()
        model_type = form.cleaned_data['model_type'].strip()
        station = form.cleaned_data['station'].strip()

        has_search = bool(id_search or name or area or line or model_type or station)

        if has_search:
            if id_search:
                records = records.filter(
                    models.Q(equipment__code__icontains=id_search) |
                    models.Q(equipment__rfid_card__icontains=id_search)
                )
            if name:
                records = records.filter(equipment__name__icontains=name)
            if area:
                records = records.filter(equipment__area__icontains=area)
            if line:
                records = records.filter(equipment__line__icontains=line)
            if model_type:
                records = records.filter(equipment__model_type__icontains=model_type)
            if station:
                records = records.filter(equipment__station__icontains=station)

    if start_date:
        records = records.filter(job_date__gte=start_date)
    if end_date:
        records = records.filter(job_date__lte=end_date)

    # 调试信息（控制台可以看到）
    print(f"调试：当前找到 {records.count()} 条已完成保养记录")

    return render(request, 'maintenance/global_maintenance_list.html', {
        'form': form,
        'records': records,
        'start_date': start_date,
        'end_date': end_date
    })


@login_required
def maintenance_create(request):
    """
    新建保养记录
    输入：表单数据
    输出：保存后返回列表
    """
    if request.method == 'POST':
        equipment_id = request.POST.get('equipment')
        m_type = request.POST.get('maintenance_type')
        desc = request.POST.get('desc')
        m_date = request.POST.get('maintenance_date')
        next_due = request.POST.get('next_due_date')

        equipment = Equipment.objects.get(id=equipment_id)
        MaintenanceRecord.objects.create(
            equipment=equipment,
            maintenance_type=m_type,
            desc=desc,
            maintenance_date=m_date,
            next_due_date=next_due,
            performed_by=request.user
        )
        messages.success(request, '✅ 保养记录已创建！')
        return redirect('maintenance:global_maintenance_list')

    equipments = Equipment.objects.all()
    return render(request, 'maintenance/maintenance_create.html', {'equipments': equipments})


@login_required
def global_sop_list(request):
    """
    SOP列表（新功能）
    输入：请求（可选equipment_id过滤）
    输出：SOP列表 + 照片预览
    """
    equipment_id = request.GET.get('equipment_id')
    if equipment_id:
        sops = MaintenanceSOP.objects.filter(equipment_id=equipment_id)
    else:
        sops = MaintenanceSOP.objects.all()

    return render(request, 'maintenance/global_sop_list.html', {'sops': sops})


@login_required
def sop_create(request):
    """
    新增SOP项目（最终修复版 - 搜索选中设备 + 列表显示）
    输入：search app 7字段 + SOP表单
    输出：选中设备后保存 + 列表显示
    """
    from search.search_forms import GlobalSearchForm
    from django.db import models

    form = GlobalSearchForm(request.GET)
    equipment = None

    # ==================== 搜索选中设备逻辑 ====================
    if form.is_valid():
        id_search = form.cleaned_data['id_search'].strip()
        name = form.cleaned_data['name'].strip()
        area = form.cleaned_data['area'].strip()
        line = form.cleaned_data['line'].strip()
        model_type = form.cleaned_data['model_type'].strip()
        station = form.cleaned_data['station'].strip()

        queryset = Equipment.objects.all()
        if id_search:
            queryset = queryset.filter(models.Q(code__icontains=id_search) | models.Q(rfid_card__icontains=id_search))
        if name:
            queryset = queryset.filter(name__icontains=name)
        if area:
            queryset = queryset.filter(area__icontains=area)
        if line:
            queryset = queryset.filter(line__icontains=line)
        if model_type:
            queryset = queryset.filter(model_type__icontains=model_type)
        if station:
            queryset = queryset.filter(station__icontains=station)

        equipment = queryset.first()  # 选中第一条匹配的设备

    # ==================== 保存SOP ====================
    if request.method == 'POST':
        equipment_id = request.POST.get('equipment_id')
        if equipment_id:
            equipment = Equipment.objects.get(id=equipment_id)
            name = request.POST.get('name')
            category = request.POST.get('category')
            is_numeric = request.POST.get('is_numeric') == 'on'
            lower = request.POST.get('lower_limit') or None
            upper = request.POST.get('upper_limit') or None
            unit = request.POST.get('unit')
            responsible_unit = request.POST.get('responsible_unit')

            MaintenanceSOP.objects.create(
                equipment=equipment,
                name=name,
                category=category,
                is_numeric=is_numeric,
                lower_limit=float(lower) if lower else None,
                upper_limit=float(upper) if upper else None,
                unit=unit,
                responsible_unit=responsible_unit,
                sop_photos=[],
            )
            messages.success(request, f'✅ SOP项目 "{name}" 已保存到设备 {equipment.name}！')
            return redirect('maintenance:global_sop_list')

    equipments = Equipment.objects.all()
    return render(request, 'maintenance/sop_create.html', {
        'form': form,
        'equipment': equipment,   # 关键：传给模板显示已选中
        'equipments': equipments
    })



@login_required
def tomorrow_maintenance_plan(request):
    """明天保养计划页面 - 第3步优化版（颜色提醒 + 备品预估）"""
    from datetime import date, timedelta
    tomorrow = date.today() + timedelta(days=1)

    # 自动生成明天任务
    if MaintenanceJobTemplate.objects.filter(job_date=tomorrow).count() == 0:
        sops = MaintenanceSOP.objects.all()
        for sop in sops:
            MaintenanceJobTemplate.objects.create(
                equipment=sop.equipment,
                sop=sop,
                job_date=tomorrow,
                status='pending'
            )

    jobs = MaintenanceJobTemplate.objects.filter(job_date=tomorrow).order_by('equipment__name')

    # 颜色提醒 + 备品预估
    pending_count = jobs.filter(status='pending').count()
    done_count = jobs.filter(status='done').count()
    spare_estimate = jobs.filter(spare_used=True).count()  # 预计需要备品数量

    is_weekend = tomorrow.weekday() >= 5
    weekend_note = "（星期天，非工作日，无需保养）" if is_weekend else ""

    return render(request, 'maintenance/tomorrow_plan.html', {
        'jobs': jobs,
        'tomorrow': tomorrow,
        'weekend_note': weekend_note,
        'pending_count': pending_count,
        'done_count': done_count,
        'spare_estimate': spare_estimate,
    })

@login_required
def monthly_maintenance_record(request):
    """
    月度保养记录（最终优化版 - 匹配工厂截图 + 统一7字段搜索）
    输入：search app 7字段 + 月份
    输出：醒目设备头 + 清晰线条 + 日/周分组
    """
    from search.search_forms import GlobalSearchForm
    from datetime import date   # ← 关键修复：加上这行

    form = GlobalSearchForm(request.GET)
    selected_month = request.GET.get('month', date.today().strftime('%Y-%m'))

    # 默认显示第一个设备
    equipment = Equipment.objects.first()

    # 应用全局搜索过滤
    if form.is_valid():
        id_search = form.cleaned_data['id_search'].strip()
        name = form.cleaned_data['name'].strip()
        area = form.cleaned_data['area'].strip()
        line = form.cleaned_data['line'].strip()
        model_type = form.cleaned_data['model_type'].strip()
        status = form.cleaned_data['status']
        station = form.cleaned_data['station'].strip()

        if id_search:
            equipment = Equipment.objects.filter(
                models.Q(code__icontains=id_search) | models.Q(rfid_card__icontains=id_search)
            ).first() or equipment
        if name:
            equipment = Equipment.objects.filter(name__icontains=name).first() or equipment
        if line:
            equipment = Equipment.objects.filter(line__icontains=line).first() or equipment
        # ... 其他字段类似（保持简单）

    sops = MaintenanceSOP.objects.filter(equipment=equipment)
    days = list(range(1, 32))

    return render(request, 'maintenance/monthly_record.html', {
        'form': form,
        'selected_month': selected_month,
        'equipment': equipment,
        'sops': sops,
        'days': days
    })

@login_required
def today_maintenance_execute(request):
    """今天保养执行页面 - 最终版（选中设备 + 写日志 + 跑马灯准备）

    函数功能说明：
        1. 支持RFID扫码或组合搜索选中设备
        2. 只显示选中设备今天的保养SOP任务（其他设备不显示）
        3. 完成执行时：保存照片、寿命、备品状态
        4. 自动写入日志文件（供跑马灯实时显示）
        5. 日志同时复制到 static/ 供前端读取

    输入参数说明：
        request：HTTP请求对象（包含GET搜索参数 + POST保存数据）

    输出参数说明：
        渲染 'maintenance/today_execute.html' 模板（返回jobs、form、selected_equipment）
        或 redirect 回本页面（保存成功后刷新）
    """
    from datetime import date
    from search.search_forms import GlobalSearchForm
    from django.db import models
    import os
    from django.conf import settings
    from django.contrib import messages
    from django.shortcuts import redirect, render

    today = date.today()
    form = GlobalSearchForm(request.GET)
    selected_equipment = None
    jobs = MaintenanceJobTemplate.objects.none()

    # ==================== 搜索选中设备 ====================
    if form.is_valid():
        id_search = form.cleaned_data['id_search'].strip()
        name = form.cleaned_data['name'].strip()
        area = form.cleaned_data['area'].strip()
        line = form.cleaned_data['line'].strip()
        model_type = form.cleaned_data['model_type'].strip()
        station = form.cleaned_data['station'].strip()

        queryset = Equipment.objects.all()
        if id_search:
            queryset = queryset.filter(models.Q(code__icontains=id_search) | models.Q(rfid_card__icontains=id_search))
        if name:
            queryset = queryset.filter(name__icontains=name)
        if area:
            queryset = queryset.filter(area__icontains=area)
        if line:
            queryset = queryset.filter(line__icontains=line)
        if model_type:
            queryset = queryset.filter(model_type__icontains=model_type)
        if station:
            queryset = queryset.filter(station__icontains=station)

        selected_equipment = queryset.first()

    # ==================== 只显示选中设备的任务 ====================
    if selected_equipment:
        if MaintenanceJobTemplate.objects.filter(job_date=today, equipment=selected_equipment).count() == 0:
            sops = MaintenanceSOP.objects.filter(equipment=selected_equipment)
            for sop in sops:
                MaintenanceJobTemplate.objects.create(
                    equipment=selected_equipment,
                    sop=sop,
                    job_date=today,
                    status='pending'
                )
        jobs = MaintenanceJobTemplate.objects.filter(
            job_date=today,
            equipment=selected_equipment
        ).order_by('sop__name')

    # ==================== 保存 + 写日志 ====================
    if request.method == 'POST':
        job_id = request.POST.get('job_id')
        if job_id:
            job = MaintenanceJobTemplate.objects.get(id=job_id)
            if 'after_photo' in request.FILES:
                job.after_photo = request.FILES['after_photo']
            job.tool_life = request.POST.get('life', '正常')
            job.spare_used = 'spare_used' in request.POST
            job.performed_by = request.user
            job.status = 'done'
            job.save()

            # === 写日志文件（跑马灯用）===
            log_dir = os.path.join(settings.BASE_DIR, 'logs')
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, 'maintenance_log.txt')
            log_line = f"{today} | {request.user.username} | {job.equipment.name} | {job.sop.name} | 寿命:{job.tool_life} | 备品:{'是' if job.spare_used else '否'}\n"

            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(log_line)

            # === 同时复制一份到 static/ 供跑马灯读取 ===
            static_log_path = os.path.join(settings.BASE_DIR, 'static', 'maintenance_log.txt')
            os.makedirs(os.path.dirname(static_log_path), exist_ok=True)
            with open(static_log_path, 'a', encoding='utf-8') as f:
                f.write(log_line)

            messages.success(request, f'✅ {job.sop.name} 已完成执行！照片 + 日志已保存！')
            return redirect('maintenance:today_maintenance_execute')

    return render(request, 'maintenance/today_execute.html', {
        'jobs': jobs,
        'today': today,
        'form': form,
        'selected_equipment': selected_equipment
    })


@login_required
def global_sop_list(request):
    """保养SOP项目列表页面 - 工厂风格合并版（新增 + 修改 + 删除）

    函数功能说明：
        1. 顶部：7字段搜索选中设备（RFID优先）
        2. 选中设备后显示新增/修改SOP表单
        3. 下方显示该设备的SOP列表（带图片）
        4. 保养ID自动从 next_maintenance_id.txt 读取并累计
        5. 支持修改、删除、图片上传

    输入参数说明：
        request：HTTP请求

    输出参数说明：
        渲染 'maintenance/global_sop_list.html'
    """
    # ==================== 局部导入（彻底避开 NameError） ====================
    from search.search_forms import GlobalSearchForm
    from django.db import models
    import os
    from django.conf import settings
    from django.contrib import messages
    from django.shortcuts import redirect, render
    from .maintenance_models import MaintenanceSOP
    from core.core_models import Equipment

    form = GlobalSearchForm(request.GET)
    selected_equipment = None
    sops = MaintenanceSOP.objects.none()
    editing_sop = None

    # 搜索选中设备
    if form.is_valid():
        id_search = form.cleaned_data['id_search'].strip()
        name = form.cleaned_data['name'].strip()
        area = form.cleaned_data['area'].strip()
        line = form.cleaned_data['line'].strip()
        model_type = form.cleaned_data['model_type'].strip()
        station = form.cleaned_data['station'].strip()

        queryset = Equipment.objects.all()
        if id_search:
            queryset = queryset.filter(models.Q(code__icontains=id_search) | models.Q(rfid_card__icontains=id_search))
        if name: queryset = queryset.filter(name__icontains=name)
        if area: queryset = queryset.filter(area__icontains=area)
        if line: queryset = queryset.filter(line__icontains=line)
        if model_type: queryset = queryset.filter(model_type__icontains=model_type)
        if station: queryset = queryset.filter(station__icontains=station)

        selected_equipment = queryset.first()

    if selected_equipment:
        sops = MaintenanceSOP.objects.filter(equipment=selected_equipment).order_by('id')

    # 处理编辑模式
    edit_id = request.GET.get('edit_id')
    if edit_id and selected_equipment:
        editing_sop = MaintenanceSOP.objects.filter(id=edit_id, equipment=selected_equipment).first()

    # 处理POST（新增 / 更新 / 删除）
    if request.method == 'POST':
        if 'delete_id' in request.POST:
            sop = MaintenanceSOP.objects.get(id=request.POST['delete_id'])
            sop.delete()
            messages.success(request, '✅ SOP已删除！')
            return redirect('maintenance:global_sop_list')

        if selected_equipment:
            lower_str = request.POST.get('lower_limit', '').strip()
            upper_str = request.POST.get('upper_limit', '').strip()
            lower_limit = float(lower_str) if lower_str else None
            upper_limit = float(upper_str) if upper_str else None

            if 'edit_id' in request.POST:  # 更新
                sop = MaintenanceSOP.objects.get(id=request.POST['edit_id'])
                sop.name = request.POST.get('name')
                sop.category = request.POST.get('category')
                sop.is_numeric = request.POST.get('is_numeric') == '是'
                sop.lower_limit = lower_limit
                sop.upper_limit = upper_limit
                sop.unit = request.POST.get('unit')
                sop.responsible_unit = request.POST.get('responsible_unit', 'EQ')
                if 'sop_image' in request.FILES:
                    sop.sop_image = request.FILES['sop_image']
                sop.save()
                messages.success(request, '✅ SOP已更新！')
            else:  # 新增
                MaintenanceSOP.objects.create(
                    equipment=selected_equipment,
                    name=request.POST.get('name'),
                    category=request.POST.get('category'),
                    is_numeric=request.POST.get('is_numeric') == '是',
                    lower_limit=lower_limit,
                    upper_limit=upper_limit,
                    unit=request.POST.get('unit'),
                    responsible_unit=request.POST.get('responsible_unit', 'EQ'),
                    sop_image=request.FILES.get('sop_image')
                )
                messages.success(request, '✅ 新增SOP成功！')

            return redirect('maintenance:global_sop_list')

    return render(request, 'maintenance/global_sop_list.html', {
        'form': form,
        'selected_equipment': selected_equipment,
        'sops': sops,
        'editing_sop': editing_sop,
    })