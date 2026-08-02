from django.shortcuts import render, redirect   # ← 必须加上 redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db import models
import json

from core.core_models import Equipment
from .models import Line, LineEquipment
from search.search_forms import GlobalSearchForm



@login_required
def production_line(request):
    """产线看板主页面（带页面搜索）"""
    line_name = request.GET.get('line', 'F44F')
    lines = Line.objects.all().order_by('name')

    if not lines.exists():
        Line.objects.create(name='F44F')
        lines = Line.objects.all()

    current_line = lines.filter(name=line_name).first() or lines.first()

    # ====================== 搜索逻辑 ======================
    form = GlobalSearchForm(request.GET)
    results = Equipment.objects.all()

    if form.is_valid():
        id_search = form.cleaned_data['id_search'].strip()
        name = form.cleaned_data['name'].strip()
        area = form.cleaned_data['area'].strip()
        line_filter = form.cleaned_data['line'].strip()
        model_type = form.cleaned_data['model_type'].strip()
        station = form.cleaned_data['station'].strip()

        if id_search:
            results = results.filter(models.Q(code__icontains=id_search) | models.Q(rfid_card__icontains=id_search))
        if name:
            results = results.filter(name__icontains=name)
        if area:
            results = results.filter(area__icontains=area)
        if line_filter:
            results = results.filter(line__icontains=line_filter)
        if model_type:
            results = results.filter(model_type__icontains=model_type)
        if station:
            results = results.filter(station__icontains=station)

    # 当前产线已添加的设备
    line_equipments = LineEquipment.objects.filter(line=current_line).order_by('position')
    equipments = [le.equipment for le in line_equipments]

    return render(request, 'production/production_line.html', {
        'lines': lines,
        'current_line': current_line,
        'equipments': equipments,
        'form': form,
        'results': results,
    })


@csrf_exempt
@require_POST
@login_required
def update_order(request):
    """拖拽保存顺序"""
    data = json.loads(request.body)
    line_name = data.get('line')
    new_order = data.get('order', [])

    line = Line.objects.get(name=line_name)
    for index, eq_id in enumerate(new_order):
        LineEquipment.objects.filter(line=line, equipment_id=eq_id).update(position=index)

    return JsonResponse({'status': 'success'})

@login_required
def add_to_line(request):
    """AJAX 插入设备（最终稳定版）"""
    line_name = request.GET.get('line')
    equipment_id = request.GET.get('equipment_id')

    if not line_name or not equipment_id:
        return JsonResponse({'status': 'error', 'msg': '参数错误'}, status=400)

    line = Line.objects.get(name=line_name)
    equipment = Equipment.objects.get(id=equipment_id)

    # 使用 get_or_create 防止重复
    obj, created = LineEquipment.objects.get_or_create(
        line=line,
        equipment=equipment,
        defaults={'position': LineEquipment.objects.filter(line=line).count()}
    )

    if created:
        return JsonResponse({'status': 'success', 'msg': f'✅ {equipment.name} 已成功插入！'})
    else:
        return JsonResponse({'status': 'exists', 'msg': f'⚠️ {equipment.name} 已经在产线上！'})

@login_required
def remove_from_line(request):
    """从产线删除设备（点小X）"""
    line_name = request.GET.get('line')
    equipment_id = request.GET.get('equipment_id')

    if line_name and equipment_id:
        LineEquipment.objects.filter(
            line__name=line_name,
            equipment_id=equipment_id
        ).delete()

    return redirect('production:production_line')

@login_required
def add_equipment_page(request):
    """小窗口搜索页面 - 完全对齐保养模块搜索逻辑"""
    line_name = request.GET.get('line', 'F44F')

    # 自动创建产线（防止 DoesNotExist）
    line, _ = Line.objects.get_or_create(name=line_name)

    form = GlobalSearchForm(request.GET)
    results = Equipment.objects.all()

    if form.is_valid():
        id_search = form.cleaned_data['id_search'].strip()
        name = form.cleaned_data['name'].strip()
        area = form.cleaned_data['area'].strip()
        line_filter = form.cleaned_data['line'].strip()   # ← 现在用保养一样的字段
        model_type = form.cleaned_data['model_type'].strip()
        station = form.cleaned_data['station'].strip()

        # 完全复制保养模块的过滤逻辑（关键！）
        if id_search:
            results = results.filter(
                models.Q(code__icontains=id_search) | models.Q(rfid_card__icontains=id_search)
            )
        if name:
            results = results.filter(name__icontains=name)
        if area:
            results = results.filter(area__icontains=area)
        if line_filter:
            results = results.filter(line__icontains=line_filter)  # ← 改成 equipment__line
        if model_type:
            results = results.filter(model_type__icontains=model_type)
        if station:
            results = results.filter(station__icontains=station)

    return render(request, 'production/add_equipment.html', {
        'form': form,
        'results': results,
        'line_name': line_name,
    })