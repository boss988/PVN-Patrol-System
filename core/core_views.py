from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .core_models import Equipment
from django import forms
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import models
from django.utils import timezone
from .core_models import Equipment, AlarmRecord


def normalize_area(area):
    """
    厂别自动纠正：去掉空格，英文字母改大写
    例：F4 4f / F4 4F / f44f → F44F
    """
    raw = (area or '').strip()
    if not raw or raw.lower() == 'nan':
        return ''
    return ''.join(ch for ch in raw.upper() if ch.isalnum())


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = '__all__'
        widgets = {
            'install_date': forms.DateInput(attrs={'class': 'dateinput form-control'}),  # 加 class 触发 datepicker
        }


@login_required
def equipment_create(request):
    """
    新建设备
    机种/类别/线别：来自产线层级配置表（下拉）
    站别：手填
    """
    from issues.issues_models import ProductionLineConfig
    import json

    configs = list(
        ProductionLineConfig.objects.filter(is_active=True)
        .order_by('order', 'model_type', 'category', 'line')
        .values('model_type', 'category', 'line')
    )
    model_types = []
    for c in configs:
        if c['model_type'] not in model_types:
            model_types.append(c['model_type'])

    def _form_context(extra=None):
        ctx = {
            'users': User.objects.all(),
            'model_types': model_types,
            'configs_json': json.dumps(configs, ensure_ascii=False),
        }
        if extra:
            ctx.update(extra)
        return ctx

    if request.method == 'POST':
        code = request.POST.get('code')
        name = request.POST.get('name')
        model = request.POST.get('model', '')
        location = request.POST.get('location', '')
        install_date = request.POST.get('install_date')
        status = request.POST.get('status', 'active')
        responsible_id = request.POST.get('responsible')
        rfid_card = request.POST.get('rfid_card')
        station = request.POST.get('station', '').strip()
        line = request.POST.get('line', '').strip()
        model_type = request.POST.get('model_type', '').strip()
        area = normalize_area(request.POST.get('area', ''))
        category = request.POST.get('category', '').strip()  # 设备/治具类别
        eq_type = request.POST.get('eq_type', '')

        if not rfid_card or not rfid_card.strip():
            messages.error(request, '❌ RFID卡号不能为空！')
            return render(request, 'core/equipment_create.html', _form_context())

        if not code or not code.strip():
            messages.error(request, '❌ 设备编号不能为空！')
            return render(request, 'core/equipment_create.html', _form_context())

        if Equipment.objects.filter(code=code).exists():
            messages.error(request, '❌ 设备编号已存在！请使用新的编号。')
            return render(request, 'core/equipment_create.html', _form_context())

        if Equipment.objects.filter(rfid_card=rfid_card).exists():
            messages.error(request, '❌ RFID卡号已存在！请使用新的卡号。')
            return render(request, 'core/equipment_create.html', _form_context())

        # 机种/线别建议在配置表中（不强制拦截，避免紧急建档失败；你要强制可打开下面注释）
        # if model_type and not ProductionLineConfig.objects.filter(is_active=True, model_type=model_type).exists():
        #     messages.error(request, '机种不在产线配置表中，请先在后台添加！')
        #     return render(request, 'core/equipment_create.html', _form_context())

        equipment = Equipment.objects.create(
            code=code.strip(),
            name=name,
            model=model,
            location=location,
            install_date=install_date,
            status=status,
            responsible_id=responsible_id or None,
            rfid_card=rfid_card.strip(),
            station=station,
            line=line,
            model_type=model_type,
            area=area,
            category=category,
            eq_type=eq_type,
        )
        messages.success(request, f'✅ 设备 {equipment.code} 已创建')
        return redirect('core:equipment_list')

    return render(request, 'core/equipment_create.html', _form_context())


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
def equipment_update_position(request, pk):
    """
    总表双击修改产线排序（只改 position，按机种+线体各自编号）
    """
    from django.http import JsonResponse

    if request.method != 'POST':
        return JsonResponse({'ok': False, 'msg': '只接受POST'}, status=405)

    equipment = get_object_or_404(Equipment, pk=pk)
    raw = request.POST.get('position', '').strip()
    try:
        pos = int(raw)
    except Exception:
        return JsonResponse({'ok': False, 'msg': '请输入整数'})

    equipment.position = pos
    equipment.save(update_fields=['position'])
    return JsonResponse({'ok': True, 'position': pos})


@login_required
def equipment_edit(request, pk):
    """编辑设备（机种/类别/线别读配置表）"""
    from issues.issues_models import ProductionLineConfig
    import json

    equipment = get_object_or_404(Equipment, pk=pk)

    configs = list(
        ProductionLineConfig.objects.filter(is_active=True)
        .order_by('order', 'model_type', 'category', 'line')
        .values('model_type', 'category', 'line')
    )
    model_types = []
    for c in configs:
        if c['model_type'] not in model_types:
            model_types.append(c['model_type'])

    # 若当前机种不在配置表，也放进下拉，避免显示空白
    if equipment.model_type and equipment.model_type not in model_types:
        model_types.insert(0, equipment.model_type)

    context = {
        'equipment': equipment,
        'model_types': model_types,
        'configs_json': json.dumps(configs, ensure_ascii=False),
    }

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        station = request.POST.get('station', '').strip()
        line = request.POST.get('line', '').strip()
        rfid_card = request.POST.get('rfid_card', '').strip()
        area = normalize_area(request.POST.get('area', ''))
        category = request.POST.get('category', '').strip()
        eq_type = request.POST.get('eq_type', '').strip()
        model_type = request.POST.get('model_type', '').strip()
        status = request.POST.get('status', 'active').strip()
        model = request.POST.get('model', '').strip()
        location = request.POST.get('location', '').strip()
        install_date = request.POST.get('install_date', '').strip()
        position = request.POST.get('position', '0').strip() or '0'

        if rfid_card:
            if Equipment.objects.filter(rfid_card=rfid_card).exclude(pk=pk).exists():
                messages.error(request, '❌ 该RFID卡号已被其他设备使用！')
                return render(request, 'core/equipment_edit.html', context)

        equipment.name = name or equipment.name
        equipment.station = station
        equipment.line = line
        equipment.rfid_card = rfid_card if rfid_card else equipment.rfid_card
        equipment.area = area
        equipment.category = category
        equipment.eq_type = eq_type
        equipment.model_type = model_type
        equipment.status = status if status in ('active', 'inactive', 'maintenance') else equipment.status
        equipment.model = model
        equipment.location = location
        if install_date:
            equipment.install_date = install_date
        try:
            equipment.position = int(position)
        except Exception:
            equipment.position = equipment.position or 0

        # 上传照片
        if request.FILES.get('photo'):
            equipment.photo = request.FILES['photo']

        equipment.save()
        messages.success(request, '✅ 设备编辑成功！')
        return redirect('core:equipment_list')
    return render(request, 'core/equipment_edit.html', context)


@login_required
def equipment_delete(request, pk):
    """删除设备 - 加强权限控制 + 立即弹窗提示"""
    equipment = get_object_or_404(Equipment, pk=pk)

    # ==================== 权限判断 ====================
    try:
        profile = request.user.profile
        if profile.role != 'admin':
            messages.error(request, '❌ 普通用户没有删除设备的权限！')
            # 临时弹窗提示（确保用户能立刻看到）
            return redirect('core:equipment_list')
    except:
        messages.error(request, '❌ 权限验证失败，无法删除设备！')
        return redirect('core:equipment_list')

    # ==================== 执行删除（仅管理员可到这里） ====================
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA foreign_keys = OFF;")
            cursor.execute("DELETE FROM core_equipment WHERE id = %s", [pk])
            cursor.execute("PRAGMA foreign_keys = ON;")

        messages.success(request, f'✅ 设备 {equipment.name} 已成功删除！')

    except Exception as e:
        messages.error(request, f'❌ 删除失败：{str(e)}')

    return redirect('core:equipment_list')


@login_required
def equipment_detail(request, pk):
    """设备详情页 - 最终稳定版"""
    equipment = get_object_or_404(Equipment, pk=pk)

    # 计算补数（避免模板算术错误）
    health_complement = 100 - equipment.health_score

    context = {
        'equipment': equipment,
        'health_complement': health_complement,
    }

    return render(request, 'core/equipment_detail.html', context)


@login_required
def equipment_list(request):
    """设备总表视图 - 增加左侧 Sidebar（厂别 → 线别两级筛选） + 分页 + 许可证保护"""

    # ==================== 许可证检查（只加这一段） ====================
    license_ok, license_error = check_license()
    if not license_ok:
        return render(request, 'base.html', {
            'license_ok': False,
            'license_error': license_error
        })
    # ==================== 许可证检查结束 ====================

    from search.search_forms import GlobalSearchForm
    from django.db import models
    from django.core.paginator import Paginator

    form = GlobalSearchForm(request.GET)

    # 获取筛选参数
    selected_area = request.GET.get('area', '')
    selected_line = request.GET.get('line', '')
    selected_model_type = request.GET.get('model_type', '')

    equipments = Equipment.objects.select_related('design_info').all().order_by(
        'area', 'model_type', 'line', 'position', 'station'
    )

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
    if selected_model_type:
        equipments = equipments.filter(model_type=selected_model_type)

    # ====== 分页逻辑（每页50条）======
    paginator = Paginator(equipments, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # ==================== 正确构建左侧厂别 → 线别嵌套结构（修复版） ====================
    # 目的：每个厂别只显示自己真实存在的线别，不会把其他厂别的线别错误显示出来
    from collections import defaultdict

    area_to_lines = defaultdict(list)
    seen = set()
    for item in Equipment.objects.values('area', 'model_type', 'line').distinct():
        area = item['area'] if item['area'] else '未指定厂别'
        line = (item['line'] or '').strip()
        mt = (item['model_type'] or '').strip()
        if not line:
            continue
        key = (area, mt, line)
        if key in seen:
            continue
        seen.add(key)
        area_to_lines[area].append({'model_type': mt, 'line': line})

    area_line_list = []
    for area in sorted(area_to_lines.keys()):
        items = sorted(area_to_lines[area], key=lambda x: (x['model_type'], x['line']))
        area_line_list.append({'area': area, 'lines': items})

    area_list = [item['area'] for item in area_line_list]
    line_list = []

    return render(request, 'core/equipment_list.html', {
        'equipments': page_obj,
        'form': form,
        'area_line_list': area_line_list,  # ← 新增这个
        'area_list': area_list,  # 兼容保留
        'line_list': line_list,  # 兼容保留
        'selected_area': selected_area,
        'selected_line': selected_line,
        'selected_model_type': selected_model_type,
        'page_obj': page_obj,
        'paginator': paginator,
        'license_ok': True


    })


@login_required
def equipment_import(request):
    """
    从Excel导入设备
    - 工作表1，表头固定列名
    - code 唯一
    - 线别必须在产线配置表中，否则跳过（卡关）
    - 机种按配置表标准名纠正（Arias → ARIAS），对不上则跳过
    - 厂别自动去空格并转大写（F4 4f → F44F）
    """
    from django.contrib import messages
    from django.conf import settings
    from issues.issues_models import ProductionLineConfig
    import pandas as pd
    from datetime import date
    import os

    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        log = []
        success_count = 0
        skip_count = 0
        error_count = 0

        try:
            df = pd.read_excel(excel_file, sheet_name=0, header=0)

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

            missing = [col for col in column_map.keys() if col not in df.columns]
            if missing:
                messages.error(request, f'❌ Excel缺少以下列：{missing}')
                return redirect('core:equipment_list')

            # ---------- 线别白名单（产线配置表） ----------
            allowed_lines = set(
                ProductionLineConfig.objects.filter(is_active=True)
                .values_list('line', flat=True)
            )
            allowed_lines = {str(x).strip() for x in allowed_lines if x and str(x).strip()}
            log.append(f"✅ 成功读取 Excel，共 {len(df)} 行数据")
            log.append(f"📋 允许的线别（配置表）：{sorted(allowed_lines)}")

            if not allowed_lines:
                messages.error(request, '❌ 产线配置表没有启用的线别，请先在后台配置！')
                return redirect('core:equipment_list')

            # ---------- 机种白名单：Excel大小写不同也改成配置表标准名 ----------
            official_models = {}
            for name in ProductionLineConfig.objects.filter(is_active=True).values_list('model_type', flat=True):
                n = str(name).strip()
                if n:
                    official_models[n.lower()] = n
            log.append('📋 允许的机种（配置表）：' + str(sorted(set(official_models.values()))))

            for idx, row in df.iterrows():
                row_num = idx + 2
                raw_code = str(row.get('90流水號', '')).strip()
                if not raw_code or raw_code.lower() == 'nan':
                    log.append(f"行 {row_num}：code为空，跳过")
                    continue

                # 1. code 已存在
                if Equipment.objects.filter(code=raw_code).exists():
                    log.append(f"行 {row_num}：⚠️ code={raw_code} 已存在，跳过")
                    skip_count += 1
                    continue

                # 2. 线别必须在配置表中
                line_val = str(row.get('線別', '')).strip()
                if line_val.lower() == 'nan':
                    line_val = ''
                if line_val not in allowed_lines:
                    log.append(
                        f"行 {row_num}：❌ code={raw_code} 线别[{line_val}]不在配置表，跳过"
                    )
                    skip_count += 1
                    continue

                # 3. 机种必须能对上配置表（Arias → ARIAS）
                mt_raw = str(row.get('機種', '')).strip()
                if mt_raw.lower() == 'nan':
                    mt_raw = ''
                mt_std = official_models.get(mt_raw.lower(), '')
                if not mt_std:
                    log.append(
                        '行 %s：❌ code=%s 机种[%s]不在配置表，跳过' % (row_num, raw_code, mt_raw)
                    )
                    skip_count += 1
                    continue

                # 4. 组装并创建
                equipment_data = {
                    'code': raw_code,
                    'name': str(row.get('名稱', '')).strip() or '未命名设备',
                    'category': str(row.get('類別', '')).strip(),
                    'model_type': mt_std,
                    'line': line_val,
                    'area': normalize_area(str(row.get('區域', ''))),
                    'station': str(row.get('站別', '')).strip(),
                    'eq_type': str(row.get('类型', '')).strip(),
                    'install_date': date.today(),
                    'rfid_card': raw_code,
                    'status': 'active' if str(row.get('啟用狀態', '1')).strip() == '1' else 'active',
                }
                # 清理可能的 nan 字符串
                for k, v in list(equipment_data.items()):
                    if isinstance(v, str) and v.lower() == 'nan':
                        equipment_data[k] = ''

                try:
                    Equipment.objects.create(**equipment_data)
                    success_count += 1
                    log.append(f"行 {row_num}：✅ code={raw_code} 机种={mt_std} 线别={line_val} 导入成功")
                except Exception as e:
                    error_count += 1
                    log.append(f"行 {row_num}：❌ 导入失败 {str(e)}")

            messages.success(
                request,
                f'✅ 导入完成！成功 {success_count} 条，跳过 {skip_count} 条，失败 {error_count} 条'
            )

            log_path = os.path.join(settings.BASE_DIR, 'logs', 'equipment_import_log.txt')
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(log))
            messages.info(request, '📋 完整日志：logs/equipment_import_log.txt')

        except Exception as e:
            messages.error(request, f'❌ 读取Excel失败：{str(e)}')

        return redirect('core:equipment_list')

    return render(request, 'core/equipment_import.html', {'log': None})


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
import subprocess
import json
import os
from datetime import datetime

import threading
import time
from django.http import JsonResponse

# 全局变量存储进度（简单实现）
PREDICT_PROGRESS = {}


@login_required
def equipment_ai_predict(request, pk):
    """龙虾AI预测 - 超级调试版"""
    equipment = get_object_or_404(Equipment, pk=pk)

    print("="*60)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始为设备 {equipment.code} 执行龙虾AI预测...")
    print(f"设备ID: {pk}")
    print("="*60)

    try:
        test_csv = "test_data.csv"
        result_path = f"result_{equipment.code}.json"

        print(f"正在调用预测脚本: utils/predict_equipment.py --input {test_csv}")

        result = subprocess.run([
            "python", "utils/predict_equipment.py",
            "--input", test_csv,
            "--output", result_path
        ], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180)

        print(f"脚本返回码: {result.returncode}")
        print(f"脚本输出: {result.stdout[:500]}...")
        print(f"脚本错误: {result.stderr[:500]}...")

        if result.returncode != 0:
            raise Exception(f"脚本执行失败: {result.stderr}")

        # 读取结果
        with open(result_path, 'r', encoding='utf-8') as f:
            ai_result = json.load(f)

        print("预测结果:", ai_result)

        # 更新数据库
        equipment.ai_score = ai_result.get('ai_score', 70)
        equipment.ai_fault_prob = ai_result.get('fault_prob_next_week', 30)
        equipment.ai_remaining_life = ai_result.get('remaining_life_days', 45)
        equipment.ai_suggestion = ai_result.get('suggestion', '无建议')
        equipment.ai_top_risks = ai_result.get('top_risks', [])
        equipment.ai_last_predict = timezone.now()
        equipment.save()

        print("✅ 数据库更新成功")

        messages.success(request, f'✅ 龙虾AI预测完成！AI健康度：{ai_result.get("ai_score")} 分')

    except Exception as e:
        error_msg = str(e)
        print("❌ 预测异常:", error_msg)
        messages.error(request, f'❌ 龙虾AI预测失败：{error_msg[:150]}')

    print("="*60)
    return redirect('core:equipment_detail', pk=pk)


# ==================== 龙虾AI助手页面 ====================
@login_required
def ai_assistant_parse(request):
    """龙虾AI聊天助手 - 加强调试版"""
    import json
    import subprocess
    from datetime import datetime

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '').strip()

            # ==================== 调试打印 ====================
            print(f"\n{'=' * 80}")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [DEBUG] 收到前端消息 → {message}")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [DEBUG] 完整POST数据 → {data}")
            print(f"{'=' * 80}\n")

            if not message:
                print("[DEBUG] 消息为空，返回提示")
                return JsonResponse({'raw_output': '请输入消息'})

            # 调用 Ollama
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [DEBUG] 开始调用 Ollama...")
            result = subprocess.run(
                ["ollama", "run", "qwen2.5:7b", f"请用中文自然回复：{message}"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=90
            )

            raw_reply = result.stdout.strip()

            # ==================== Ollama 回应调试 ====================
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [DEBUG] Ollama返回长度: {len(raw_reply)}")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 【Ollama原始完整回复】\n{raw_reply}\n")

            return JsonResponse({'raw_output': raw_reply or '没有收到回复'})

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [ERROR] {str(e)}")
            return JsonResponse({'raw_output': f'错误: {str(e)}'})

    # 显示聊天页面
    return render(request, 'core/ai_assistant.html')


from datetime import datetime
import os
from django.conf import settings


def check_license():
    """检查许可证文件（方案1保护）"""
    license_path = os.path.join(settings.BASE_DIR, 'license.key')

    if not os.path.exists(license_path):
        return False, "❌ 系统许可证文件丢失！请联系原管理员（得铭）。"

    try:
        with open(license_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        lines = dict(line.split('=') for line in content.splitlines() if '=' in line)

        expiration_str = lines.get('EXPIRATION')
        signature = lines.get('SIGNATURE')

        if not expiration_str or not signature:
            return False, "❌ 许可证文件格式错误！"

        expiration_date = datetime.strptime(expiration_str, '%Y-%m-%d').date()
        today = datetime.now().date()

        if today > expiration_date:
            return False, f"❌ 系统已过期！有效期至 {expiration_str}。"

        if signature != 'perry_chen_2026':
            return False, "❌ 许可证签名验证失败！"

        return True, "许可证正常"

    except Exception as e:
        return False, f"❌ 许可证检查失败：{str(e)}"