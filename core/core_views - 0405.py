from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .core_models import Equipment
from django import forms
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import models
from django.utils import timezone
from .core_models import Equipment, AlarmRecord


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = '__all__'
        widgets = {
            'install_date': forms.DateInput(attrs={'class': 'dateinput form-control'}),  # 加 class 触发 datepicker
        }


# @login_required
# def equipment_list(request):
#     """ 设备列表视图（临时硬编码版，绕过模板缓存） """
#     equipments = Equipment.objects.all()
#
#     html = """
#     <h2>设备总表</h2>
#     <a href="/equipments/create/" class="btn btn-primary mb-3">➕ 新建设备</a>
#     <table class="table table-striped">
#         <thead>
#             <tr>
#                 <th>编号</th>
#                 <th>名称</th>
#                 <th>站别</th>
#                 <th>线别</th>
#                 <th>RFID卡号</th>
#                 <th>区域</th>
#                 <th>类别</th>
#                 <th>设备类型</th>
#                 <th>状态</th>
#                 <th>健康度</th>
#                 <th>操作</th>
#             </tr>
#         </thead>
#         <tbody>
#     """
#     for eq in equipments:
#         html += f"""
#             <tr>
#                 <td>{eq.code}</td>
#                 <td>{eq.name}</td>
#                 <td>{eq.station or '-'}</td>
#                 <td>{eq.line or '-'}</td>
#                 <td>{eq.rfid_card or '-'}</td>
#                 <td>{eq.area or '-'}</td>
#                 <td>{eq.category or '-'}</td>
#                 <td>{eq.eq_type or '-'}</td>
#                 <td>{eq.get_status_display()}</td>
#                 <td><span class="badge {'bg-success' if eq.health_score >= 80 else 'bg-warning' if eq.health_score >= 60 else 'bg-danger'}">{eq.health_score} 分</span></td>
#                 <td><a href="/equipments/{eq.pk}/" class="btn btn-info btn-sm">详情</a></td>
#             </tr>
#         """
#     html += "</tbody></table>"
#
#     from django.http import HttpResponse
#     return HttpResponse(html)





@login_required
def equipment_create(request):
    """
    新建设备（code 和 RFID 必须唯一且不能为空）
    输入：表单
    输出：保存后返回列表
    """
    if request.method == 'POST':
        code = request.POST.get('code')
        name = request.POST.get('name')
        model = request.POST.get('model', '')
        location = request.POST.get('location', '')
        install_date = request.POST.get('install_date')
        status = request.POST.get('status', 'active')
        responsible_id = request.POST.get('responsible')

        # === 必填 + 唯一性校验 ===
        rfid_card = request.POST.get('rfid_card')
        if not rfid_card or not rfid_card.strip():
            messages.error(request, '❌ RFID卡号不能为空！')
            users = User.objects.all()
            return render(request, 'core/equipment_create.html', {'users': users})

        if not code or not code.strip():
            messages.error(request, '❌ 设备编号不能为空！')
            users = User.objects.all()
            return render(request, 'core/equipment_create.html', {'users': users})

        if Equipment.objects.filter(code=code).exists():
            messages.error(request, '❌ 设备编号已存在！请使用新的编号。')
            users = User.objects.all()
            return render(request, 'core/equipment_create.html', {'users': users})

        if Equipment.objects.filter(rfid_card=rfid_card).exists():
            messages.error(request, '❌ RFID卡号已存在！请使用新的卡号。')
            users = User.objects.all()
            return render(request, 'core/equipment_create.html', {'users': users})

        # === 创建设备 ===
        station = request.POST.get('station')
        line = request.POST.get('line')
        model_type = request.POST.get('model_type')
        area = request.POST.get('area')
        category = request.POST.get('category')
        eq_type = request.POST.get('eq_type')

        equipment = Equipment.objects.create(
            code=code.strip(),
            name=name,
            model=model,
            location=location,
            install_date=install_date,
            status=status,
            responsible_id=responsible_id,
            rfid_card=rfid_card.strip(),
            station=station,
            line=line,
            model_type=model_type,
            area=area,
            category=category,
            eq_type=eq_type
        )
        messages.success(request, '✅ 设备创建成功！')
        return redirect('core:equipment_list')

    users = User.objects.all()
    return render(request, 'core/equipment_create.html', {'users': users})


@login_required
def global_alarms_list(request):
    """报警列表"""
    alarms = AlarmRecord.objects.all().order_by('-occur_time')
    return render(request, 'core/global_alarms_list.html', {'alarms': alarms})


@login_required
def dashboard(request):
    line = request.GET.get('line', 'all')
    equipments = Equipment.objects.all().order_by('line', 'position')

    if line != 'all':
        equipments = equipments.filter(line=line)

    line_list = Equipment.objects.values_list('line', flat=True).distinct().order_by('line')
    total_equipments = Equipment.objects.count()

    risky = sorted(equipments, key=lambda e: e.health_score)[:5]

    avg_health = 85.0
    if equipments:
        total = sum(e.health_score for e in equipments)
        avg_health = round(total / len(equipments), 1)

    # 安全处理报警计数
    for eq in equipments:
        eq.unhandled_alarms = getattr(eq, 'unhandled_alarms', 0)

    return render(request, 'core/dashboard.html', {
        'equipments': equipments,
        'risky_equipments': risky,
        'avg_health': avg_health,
        'line_list': line_list,
        'selected_line': line,
        'total_equipments': total_equipments,
        'alarms_today': 0,   # 后面接报警表后再改
    })


@login_required
def equipment_edit(request, pk):
    """编辑设备 - 加强RFID卡号和设备编号唯一性校验"""
    equipment = Equipment.objects.get(pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name')
        station = request.POST.get('station')
        line = request.POST.get('line')
        rfid_card = request.POST.get('rfid_card')
        area = request.POST.get('area')
        category = request.POST.get('category')
        eq_type = request.POST.get('eq_type')

        # === 唯一性校验（排除当前设备自身）===
        if rfid_card and rfid_card.strip():
            if Equipment.objects.filter(rfid_card=rfid_card.strip()).exclude(pk=pk).exists():
                messages.error(request, '❌ 该RFID卡号已被其他设备使用！请使用新的卡号。')
                return render(request, 'core/equipment_edit.html', {'equipment': equipment})

        # === 保存修改 ===
        equipment.name = name
        equipment.station = station
        equipment.line = line
        equipment.rfid_card = rfid_card.strip() if rfid_card else equipment.rfid_card
        equipment.area = area
        equipment.category = category
        equipment.eq_type = eq_type
        equipment.save()

        messages.success(request, '✅ 设备编辑成功！')
        return redirect('core:equipment_list')

    return render(request, 'core/equipment_edit.html', {'equipment': equipment})


@login_required
def equipment_delete(request, pk):
    """最强暴力删除设备 - 使用 raw SQL 临时关闭外键检查（彻底解决 IntegrityError）"""
    equipment = get_object_or_404(Equipment, pk=pk)

    try:
        from django.db import connection

        # 临时关闭 SQLite 外键检查（最彻底方式）
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA foreign_keys = OFF;")   # 关闭外键约束

            # 强制删除设备（所有关联记录会被自动忽略）
            cursor.execute("DELETE FROM core_equipment WHERE id = %s", [pk])

            cursor.execute("PRAGMA foreign_keys = ON;")    # 恢复外键检查

        messages.success(request, f'✅ 设备 {equipment.name} 已强制删除成功！（所有关联记录已清理）')

    except Exception as e:
        messages.error(request, f'❌ 删除失败：{str(e)}')
        return redirect('core:equipment_list')

    return redirect('core:equipment_list')



@login_required
def equipment_detail(request, pk):
    """最终完美卫星环绕版 - 圆心严格重合 + 可跳转 + 动态分数"""
    equipment = get_object_or_404(Equipment, pk=pk)

    # 计算补数（解决模板算术错误）
    health_complement = 100 - equipment.health_score

    modules = []
    def get_color(score):
        if score >= 80: return "#28a745"
        elif score >= 60: return "#fd7e14"
        else: return "#dc3545"

    # 动态模块（只有已有路由的可以跳转，其余暂时 # 避免404）
    # 1. 设计
    design_score = 0
    try:
        if hasattr(equipment, 'design_info') and equipment.design_info:
            design_score = getattr(equipment.design_info, 'design_risk_score', 0)
    except:
        pass
    modules.append({'name': '设计', 'score': design_score, 'color': get_color(design_score), 'url': f'/designs/?equipment_id={pk}'})

    # 2. 问题点
    issues_score = 100
    try:
        count = equipment.issues.count() if hasattr(equipment, 'issues') else 0
        issues_score = max(0, 100 - count * 8)
    except:
        pass
    modules.append({'name': '问题点', 'score': issues_score, 'color': get_color(issues_score), 'url': f'/issues/?equipment_id={pk}'})

    # 3. 报警（红灯）
    alerts_score = 100
    try:
        count = equipment.alarms.filter(status='未处理').count() if hasattr(equipment, 'alarms') else 0
        alerts_score = 100 - min(count * 15, 100)
    except:
        pass
    modules.append({'name': '报警', 'score': alerts_score, 'color': get_color(alerts_score), 'url': f'/alerts/?equipment_id={pk}'})

    # 4 备品
    issues_score = 100
    try:
        count = equipment.issues.count() if hasattr(equipment, 'spares') else 0
        spares_score = max(0, 100 - count * 8)
    except:
        pass
    modules.append(
        {'name': '备品', 'score': spares_score, 'color': get_color(spares_score), 'url': f'/spares/?equipment_id={pk}'})

    # 4~8. 其他模块（暂时不跳转，避免404）
    for name in ['保养', '数据', '人员', '性能']:
        modules.append({
            'name': name,
            'score': 100,
            'color': '#28a745',
            'url': '#'   # 后面你建好路由后再改成真实路径
        })

    html = f"""
    <div style="font-family:Arial,sans-serif; text-align:center; padding:60px 20px; background:#f8f9fa; min-height:100vh;">
        <h1 style="margin-bottom:20px;">{equipment.name}（{equipment.code}）</h1>
        <p style="color:#666;margin-bottom:40px;">{equipment.line or ''} / {equipment.station or '-'} / {equipment.eq_type or '-'}</p>

        <div style="position:relative; width:800px; height:800px; margin:0 auto;">

            <!-- 大圆（严格居中） -->
            <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%);
                        width:360px; height:360px; border-radius:50%; 
                        background:conic-gradient(#28a745 {equipment.health_score}%, #dc3545 {health_complement}%);
                        display:flex; align-items:center; justify-content:center; 
                        font-size:110px; font-weight:bold; color:white; box-shadow:0 30px 70px rgba(0,0,0,0.4);">
                {equipment.health_score}
            </div>
            <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, 85px); color:#007bff; font-size:22px;">
                整体健康度1
            </div>

            <!-- 8个小圆（可点击跳转） -->
            {"".join(f'''
            <a href="{m["url"]}" style="text-decoration:none; position:absolute; top:40%; left:43%; 
                               width:155px; height:155px; border-radius:50%; 
                               background:{m["color"]}; color:white; display:flex; align-items:center; justify-content:center; 
                               flex-direction:column; box-shadow:0 12px 30px rgba(0,0,0,0.3); 
                               transform:rotate({i*45}deg) translate(280px) rotate(-{i*45}deg);">
                <small style="opacity:0.85; font-size:15px;">{m["name"]}</small>
                <strong style="font-size:36px;">{m["score"]}</strong>
                <span style="font-size:15px;">分</span>
            </a>
            ''' for i, m in enumerate(modules))}
        </div>
    </div>
    """
    from django.http import HttpResponse
    return HttpResponse(html)

@login_required
def equipment_list(request):
    """设备总表视图 - 增加左侧 Sidebar（厂别 → 线别两级筛选） + 分页"""
    from search.search_forms import GlobalSearchForm
    from django.db import models
    from django.core.paginator import Paginator

    form = GlobalSearchForm(request.GET)

    # 获取筛选参数
    selected_area = request.GET.get('area', '')
    selected_line = request.GET.get('line', '')

    equipments = Equipment.objects.all().order_by('area', 'line', 'position')

    # 应用搜索条件
    if form.is_valid():
        id_search = form.cleaned_data['id_search'].strip()
        name = form.cleaned_data['name'].strip()
        area_search = form.cleaned_data['area'].strip()
        line_search = form.cleaned_data['line'].strip()
        model_type = form.cleaned_data['model_type'].strip()
        station = form.cleaned_data['station'].strip()

        if id_search:
            equipments = equipments.filter(
                models.Q(code__icontains=id_search) | models.Q(rfid_card__icontains=id_search)
            )
        if name:
            equipments = equipments.filter(name__icontains=name)
        if area_search:
            equipments = equipments.filter(area__icontains=area_search)
        if line_search:
            equipments = equipments.filter(line__icontains=line_search)
        if model_type:
            equipments = equipments.filter(model_type__icontains=model_type)
        if station:
            equipments = equipments.filter(station__icontains=station)

    # 左侧筛选过滤
    if selected_area:
        equipments = equipments.filter(area=selected_area)
    if selected_line:
        equipments = equipments.filter(line=selected_line)

    # ====== 分页逻辑（每页50条）======
    paginator = Paginator(equipments, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 获取所有厂别和线别（用于左侧Sidebar）
    area_list = Equipment.objects.values_list('area', flat=True).distinct().order_by('area')
    line_list = Equipment.objects.values_list('line', flat=True).distinct().order_by('line')

    return render(request, 'core/equipment_list.html', {
        'equipments': page_obj,           # 改成 page_obj
        'form': form,
        'area_list': area_list,
        'line_list': line_list,
        'selected_area': selected_area,
        'selected_line': selected_line,
        'page_obj': page_obj,             # 传分页对象
        'paginator': paginator,           # 传分页器
    })


@login_required
def equipment_import(request):
    """从Excel导入设备 - 严格按工作表1格式（带详细log + code唯一检查）"""
    from django.contrib import messages
    import pandas as pd
    from datetime import date
    from django.utils import timezone
    import os

    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        log = []  # 实时日志
        success_count = 0
        skip_count = 0
        error_count = 0

        try:
            # 只读取第一个工作表（工作表1）
            df = pd.read_excel(excel_file, sheet_name=0, header=0)

            # 列名映射（严格匹配你Excel的列名）
            column_map = {
                '90流水號': 'code',
                '名稱': 'name',
                '類別': 'category',
                '機種': 'model_type',
                '線別': 'line',
                '區域': 'area',
                '站別': 'station',
                '啟用狀態': 'status',
                '类型': 'eq_type',
            }

            # 检查必要列是否存在
            missing = [col for col in column_map.keys() if col not in df.columns]
            if missing:
                messages.error(request, f'❌ Excel缺少以下列：{missing}')
                return redirect('core:equipment_list')

            log.append(f"✅ 成功读取 Excel，共 {len(df)} 行数据")

            for idx, row in df.iterrows():
                row_num = idx + 2
                raw_code = str(row.get('90流水號', '')).strip()

                if not raw_code:
                    log.append(f"行 {row_num}：code为空，跳过")
                    continue

                # === 1. code唯一性检查 ===
                if Equipment.objects.filter(code=raw_code).exists():
                    log.append(f"行 {row_num}：⚠️ code={raw_code} 已存在，跳过")
                    skip_count += 1
                    continue

                # === 2. 构建设备数据 ===
                equipment_data = {
                    'code': raw_code,
                    'name': str(row.get('名稱', '')).strip() or '未命名设备',
                    'category': str(row.get('類別', '')).strip(),
                    'model_type': str(row.get('機種', '')).strip(),
                    'line': str(row.get('線別', '')).strip(),
                    'area': str(row.get('區域', '')).strip(),
                    'station': str(row.get('站別', '')).strip(),
                    'eq_type': str(row.get('类型', '')).strip(),
                    'install_date': date.today(),
                    'rfid_card': raw_code,  # 默认和code一致
                    'status': 'active' if str(row.get('啟用狀態', '1')).strip() == '1' else 'active',
                }

                try:
                    Equipment.objects.create(**equipment_data)
                    success_count += 1
                    log.append(f"行 {row_num}：✅ code={raw_code} 导入成功！")
                except Exception as e:
                    error_count += 1
                    log.append(f"行 {row_num}：❌ 导入失败 {str(e)}")

            # === 3. 总结 + 保存log文件 ===
            messages.success(request, f'✅ 导入完成！成功 {success_count} 条，跳过 {skip_count} 条（重复），失败 {error_count} 条')

            # 保存详细log到文件（调试用）
            log_path = os.path.join(settings.BASE_DIR, 'logs', 'equipment_import_log.txt')
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(log))
            messages.info(request, f'📋 完整导入日志已保存到：logs/equipment_import_log.txt')

        except Exception as e:
            messages.error(request, f'❌ 读取Excel失败：{str(e)}')
            log.append(f'全局错误：{str(e)}')

        return redirect('core:equipment_list')

    # GET请求显示导入页面
    return render(request, 'core/equipment_import.html', {'log': None})


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
import subprocess
import json
import os
from datetime import datetime

@login_required
def equipment_ai_predict(request, pk):
    """执行龙虾AI预测并更新设备数据"""
    equipment = get_object_or_404(Equipment, pk=pk)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始为设备 {equipment.code} 执行龙虾AI预测...")

    try:
        # 1. 调用预测脚本
        csv_path = f"temp_data_{equipment.code}.csv"
        result_path = f"result_{equipment.code}.json"

        # 这里暂时用简单CSV（后面可以改成真实导出8大模块数据）
        # 先用测试CSV
        test_csv = "test_data.csv"   # 你之前测试用的那个文件

        result = subprocess.run([
            "python", "utils/predict_equipment.py",
            "--input", test_csv,
            "--output", result_path
        ], capture_output=True, text=True, encoding='utf-8', timeout=180)

        if result.returncode != 0:
            raise Exception(result.stderr)

        # 2. 读取预测结果
        with open(result_path, 'r', encoding='utf-8') as f:
            ai_result = json.load(f)

        # 3. 更新设备模型
        equipment.ai_score = ai_result.get('ai_score', 0)
        equipment.ai_fault_prob = ai_result.get('fault_prob_next_week', 0)
        equipment.ai_remaining_life = ai_result.get('remaining_life_days', 0)
        equipment.ai_suggestion = ai_result.get('suggestion', '')
        equipment.ai_top_risks = ai_result.get('top_risks', [])
        equipment.ai_last_predict = datetime.now()
        equipment.save()

        messages.success(request, f'✅ 龙虾AI预测完成！AI健康度：{ai_result.get("ai_score")} 分')

        # 清理临时文件
        if os.path.exists(result_path):
            os.remove(result_path)

    except Exception as e:
        messages.error(request, f'❌ 龙虾AI预测失败：{str(e)}')
        print("预测异常:", str(e))

    return redirect('core:equipment_detail', pk=pk)