from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .spares_models import SparePart
from core.core_models import Equipment
from datetime import datetime
import pandas as pd
from django.shortcuts import render
from core.core_models import Equipment
from .spares_models import SparePart


@login_required
def spares_list(request, equipment_pk):
    """单台设备的备品列表 - 最终稳定版"""
    equipment = get_object_or_404(Equipment, pk=equipment_pk)
    print(f"=== spares_list 被调用 === 设备ID: {equipment_pk} ({equipment.name})")

    spares = SparePart.objects.filter(equipment=equipment).order_by('-id')

    print(f"找到备品数量: {spares.count()} 条")

    return render(request, 'spares/spares_list.html', {
        'equipment': equipment,
        'spares': spares,
        'title': f'{equipment.name} - 备品清单'
    })

@login_required
def import_spares(request):
    """
    备品Excel导入函数（已完整支持你清单所有列）
    """
    if request.method == 'POST' and 'excel_file' in request.FILES:
        excel_file = request.FILES['excel_file']
        try:
            df = pd.read_excel(excel_file, sheet_name=2)  # 锁定备品Sheet
            print("=== 开始导入备品调试 ===")
            print(f"总行数: {len(df)}")
            print(f"实际列名: {list(df.columns)}")
            count = 0

            for idx, row in df.iterrows():
                if idx < 1: continue  # 跳过标题

                equip_name = str(row.get('站别（設備名稱）', '')).strip()
                name = str(row.get('品名', '')).strip()
                if not name or not equip_name: continue

                equipment = Equipment.objects.filter(name__icontains=equip_name).first()
                if not equipment: continue

                SparePart.objects.create(
                    equipment=equipment,
                    name=name,
                    spec=str(row.get('規格型號', '')),
                    supplier=str(row.get('品牌', '')),
                    stock_qty=int(row.get('庫存數量', 0)) if str(row.get('庫存數量', '')).replace('.', '', 1).isdigit() else 0,
                    min_stock=int(row.get('安全庫存', 5)) if str(row.get('安全庫存', '')).replace('.', '', 1).isdigit() else 5,
                    usage_qty=int(row.get('當站使用數量', 0)) if str(row.get('當站使用數量', '')).replace('.', '',
                                                                                              1).isdigit() else 0,
                    life_months=int(row.get('使用壽命', 30)) if str(row.get('使用壽命', '')).replace('.', '',
                                                                                             1).isdigit() else 30,
                    difference=int(row.get('差異', 0)) if str(row.get('差異', '')).replace('.', '', 1).isdigit() else 0
                )
                count += 1

            return render(request, 'spares/import_form.html', {
                'success': f'✅ 成功导入 {count} 条完整备品记录！（所有列已显示）'
            })
        except Exception as e:
            return render(request, 'spares/import_form.html', {'error': f'导入失败：{str(e)}'})
    return render(request, 'spares/import_form.html', {})


from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages

@login_required
def spare_delete(request, pk):
    """
    删除单条备品
    输入：备品ID
    输出：删除后返回列表页
    """
    spare = get_object_or_404(SparePart, pk=pk)
    spare.delete()
    messages.success(request, f'✅ 已删除备品：{spare.name}')
    return redirect('spares:global_spares_list')


@login_required
def global_spares_list(request):
    """
    全局备品列表 - 已改成和设计/问题点模块完全一致的风格
    支持搜索 + 绿条 + 从设备详情页自动选中当前设备
    """
    from search.search_forms import GlobalSearchForm
    from django.db import models

    print("=== global_spares_list 被调用 ===")
    print("完整请求URL:", request.get_full_path())

    form = GlobalSearchForm(request.GET)
    spares = SparePart.objects.all().order_by('equipment__code')
    selected_equipment = None

    # ==================== 自动选中设备（从雷达图跳转时带参数） ====================
    equipment_pk = request.GET.get('equipment_pk') or request.GET.get('equipment_id')
    print(f"收到参数 equipment_pk/equipment_id: {equipment_pk}")

    if equipment_pk:
        selected_equipment = Equipment.objects.filter(pk=equipment_pk).first()
        print(f"✅ 成功选中设备: {selected_equipment}")

    # ==================== 手动搜索逻辑 ====================
    if form.is_valid() and not selected_equipment:
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
        print(f"手动搜索选中设备: {selected_equipment}")

    # 如果选中了设备，只显示该设备的备品
    if selected_equipment:
        spares = spares.filter(equipment=selected_equipment)
        print(f"过滤后 spares 数量: {spares.count()} 条")

    return render(request, 'spares/global_spares_list.html', {
        'spares': spares,
        'form': form,
        'selected_equipment': selected_equipment,
    })

@login_required
def spare_create(request, equipment_pk):
    """新增备品 - 支持照片上传 + 真正保存"""
    equipment = get_object_or_404(Equipment, pk=equipment_pk)

    if request.method == 'POST':
        photos = request.FILES.getlist('photos')
        photo_urls = []

        try:
            spare = SparePart.objects.create(
                equipment=equipment,
                name=request.POST.get('name'),
                spec=request.POST.get('spec', ''),
                supplier=request.POST.get('supplier', ''),
                stock_qty=int(request.POST.get('stock_qty', 0) or 0),
                min_stock=int(request.POST.get('min_stock', 5) or 5),
                usage_qty=int(request.POST.get('usage_qty', 0) or 0),
                life_months=int(request.POST.get('life_months', 30) or 30),
                difference=int(request.POST.get('difference', 0) or 0),
            )

            # 保存照片（支持多张）
            for photo in photos:
                if photo:
                    spare.photo = photo
                    spare.save()          # 必须先save才能获得url
                    photo_urls.append(spare.photo.url)

            spare.photos = photo_urls
            spare.save()

            print(f"✅ 备品保存成功！照片数量: {len(photo_urls)}")
            messages.success(request, f'✅ 备品【{spare.name}】保存成功！')
            return redirect('spares:spares_list', equipment_pk=equipment_pk)

        except Exception as e:
            print("❌ 保存失败:", str(e))
            messages.error(request, f'保存失败：{str(e)}')

    return render(request, 'spares/spare_form.html', {
        'equipment': equipment,
    })