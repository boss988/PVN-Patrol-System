from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .performance_models import PerformanceKPI
from core.core_models import Equipment


@login_required
def global_performance_list(request):
    """
    全局性能KPI列表
    输入：请求
    输出：所有设备KPI
    """
    kpis = PerformanceKPI.objects.all().order_by('-calc_date')
    return render(request, 'performance/global_performance_list.html', {'kpis': kpis})


@login_required
def performance_create(request):
    """
    手动新建KPI数据
    输入：表单
    输出：保存后返回列表
    """
    if request.method == 'POST':
        equipment_id = request.POST.get('equipment')
        mtbf = float(request.POST.get('mtbf', 0))
        mttr = float(request.POST.get('mttr', 0))
        oee = float(request.POST.get('oee', 0))

        equipment = Equipment.objects.get(id=equipment_id)
        PerformanceKPI.objects.create(
            equipment=equipment,
            mtbf=mtbf,
            mttr=mttr,
            oee=oee
        )
        messages.success(request, '✅ KPI数据已手动添加！')
        return redirect('performance:global_performance_list')

    equipments = Equipment.objects.all()
    return render(request, 'performance/performance_create.html', {'equipments': equipments})