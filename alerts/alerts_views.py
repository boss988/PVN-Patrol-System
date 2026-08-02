from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .alerts_models import Alert
from core.core_models import Equipment

@login_required
def global_alerts_list(request):
    """
    全局报警列表
    输入：请求
    输出：所有未处理报警
    """
    alerts = Alert.objects.all().order_by('-occur_time')
    return render(request, 'alerts/global_alerts_list.html', {'alerts': alerts})

@login_required
def alert_mark_handled(request, pk):
    """
    标记报警已处理
    输入：报警ID
    输出：返回列表页
    """
    alert = get_object_or_404(Alert, pk=pk)
    alert.handled = True
    alert.handler = request.user
    alert.save()
    messages.success(request, f'✅ 已标记处理：{alert.desc}')
    return redirect('alerts:global_alerts_list')


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .alerts_models import Alert
from core.core_models import Equipment


@login_required
def alert_create(request):
    """
    手动新建报警
    输入：表单
    输出：保存后返回列表
    """
    if request.method == 'POST':
        equipment_id = request.POST.get('equipment')
        alert_type = request.POST.get('alert_type')
        desc = request.POST.get('desc')

        equipment = Equipment.objects.get(id=equipment_id)
        Alert.objects.create(
            equipment=equipment,
            alert_type=alert_type,
            desc=desc
        )
        messages.success(request, '✅ 报警记录已创建！')
        return redirect('alerts:global_alerts_list')

    equipments = Equipment.objects.all()
    return render(request, 'alerts/alert_create.html', {'equipments': equipments})