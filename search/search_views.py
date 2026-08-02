from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import models
from core.core_models import Equipment
from .search_forms import GlobalSearchForm
from .models import SearchLog

@login_required
def global_search(request):
    """
    全局搜索视图（7字段组合版 - 严格按Equipment模型字段）
    输入：ID + 设备名称 + 厂别 + 线别 + 机种名称 + 设备状态 + 站别
    输出：精准匹配设备列表
    """
    form = GlobalSearchForm(request.GET)
    results = Equipment.objects.all()

    if form.is_valid():
        id_search = form.cleaned_data['id_search'].strip()
        name = form.cleaned_data['name'].strip()
        area = form.cleaned_data['area'].strip()
        line = form.cleaned_data['line'].strip()
        model_type = form.cleaned_data['model_type'].strip()
        status = form.cleaned_data['status']
        station = form.cleaned_data['station'].strip()

        if id_search:
            results = results.filter(
                models.Q(code__icontains=id_search) | models.Q(rfid_card__icontains=id_search)
            )
        if name:
            results = results.filter(name__icontains=name)
        if area:
            results = results.filter(area__icontains=area)
        if line:
            results = results.filter(line__icontains=line)
        if model_type:
            results = results.filter(model_type__icontains=model_type)   # ← 修正为 model_type
        if status != 'all':
            results = results.filter(status=status)
        if station:
            results = results.filter(station__icontains=station)

    return render(request, 'search/global_search.html', {
        'form': form,
        'results': results
    })