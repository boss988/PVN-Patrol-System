from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .issues_models import EquipmentIssue
from core.core_models import Equipment
from django import forms
import pandas as pd  # 用于Excel导入
from datetime import datetime
from .issues_models import EquipmentIssue, PatrolIssue   # ← 新增这一行
from django.contrib import messages   # ← 新增这一行
from notification.models import EmailGroup   # ← 新增这一行
from datetime import date
import json
from django.http import JsonResponse
from .issues_models import PatrolIssue, PatrolCategory
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

class IssueForm(forms.ModelForm):
    class Meta:
        model = EquipmentIssue
        fields = ['desc', 'occur_date', 'abnormal_work_time', 'work_time_type', 'severity']  # 排除 issue_code


# ==================== 新增：主管下拉列表（以后要加主管只改这里） ====================
SUPERVISOR_CHOICES = [
    "Wind Wang(王海风_PVN)",
    "Xh Li(李興恒_PVN)",
    "Zheng-ping Liu(劉正平_PVN)",
    "Guang-hua Peng(彭光華_PVN)",
]
# ==================== 允许编辑/删除点检记录的用户（白名单） ====================
# 只有这些用户名可以看到并操作“编辑”和“删除”按钮
# 以后想加人或删人，只改这里就行
PATROL_EDIT_DELETE_USERS = [
    'V25020512',
    's20038978',
    'V25018772',
    'perry_chen',
    # 以后可以继续往这里加

]
# 公屏通知权限白名单（可发布/关闭跑马灯公屏信息）
MARQUEE_NOTICE_USERS = [
    'V25020512',
    's20038978',
    'V25018772',
    'perry_chen',
    # 以后要加账号，直接写在这里
]


# ==================== 新增：跑马灯日志辅助函数（只在新增记录时使用） ====================
def append_to_marquee_log(request, line):
    """点检记录新增成功后，自动在跑马灯追加一条记录"""
    from django.conf import settings
    import os
    from datetime import datetime

    try:
        # 优先使用用户姓名，没有姓名就用登录账号
        if hasattr(request.user, 'profile') and request.user.profile.name:
            display_name = request.user.profile.name.strip()
        else:
            display_name = request.user.username

        # 构建显示内容
        if line and line.strip():
            log_text = f"{display_name} 在 {line.strip()} 线 点检Điểm kiểm trên dây chuyền"
        else:
            log_text = f"{display_name} 点检记录已上传Ghi chép điểm kiểm đã tải lên"

        # 加上时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        full_line = f"{timestamp} | {log_text}"

        # 写入 maintenance_log.txt（追加模式）
        log_path = os.path.join(settings.BASE_DIR, 'static', 'maintenance_log.txt')
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(full_line + '\n')

        print(f"[跑马灯] 已成功追加：{full_line}")   # 调试信息
    except Exception as e:
        print(f"[跑马灯] 追加失败：{e}")



@login_required
def issues_list(request, equipment_pk):
    """
    问题列表视图。
    输入：请求和equipment_pk。
    输出：渲染模板。
    功能：显示设备的问题列表，支持过滤。
    交互：通过pk拉取equipment.issues.all()。
    """
    equipment = get_object_or_404(Equipment, pk=equipment_pk)
    issues = equipment.issues.all()
    return render(request, 'issues/issues_list.html', {'issues': issues, 'equipment': equipment})



@login_required
def patrol_list(request):
    """点检问题点记录列表（支持日期 + 主管 + 状态筛选 + 分页）"""

    # ==================== 1. 获取筛选参数 ====================
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    supervisor = request.GET.get('supervisor', '').strip()
    status = request.GET.get('status', '').strip()
    category = request.GET.get('category', '').strip()  # ← 新增类别大饼跳转用

    # ==================== 2. 构建查询 ====================
    issues = PatrolIssue.objects.all().order_by('-date')

    if start_date:
        issues = issues.filter(date__gte=start_date)
    if end_date:
        issues = issues.filter(date__lte=end_date)

    # 新增：主管筛选（支持模糊匹配，兼容各种写法）
    if supervisor:
        issues = issues.filter(supervisor__icontains=supervisor)
    if status:
        issues = issues.filter(status__iexact=status)
    if category:
        # 支持按类别名称筛选（也兼容「未分类」）
        if category == '未分类':
            issues = issues.filter(category__isnull=True)
        else:
            issues = issues.filter(category__name=category)

    # 新增：状态筛选
    if status:
        issues = issues.filter(status__iexact=status)

    # ==================== 3. 分页 ====================
    from django.core.paginator import Paginator
    paginator = Paginator(issues, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    groups = EmailGroup.objects.all().order_by('name')

    return render(request, 'issues/patrol_list.html', {
        'issues': page_obj,
        'groups': groups,
        'today': date.today(),
        'page_obj': page_obj,
        'start_date': start_date,
        'end_date': end_date,
        'selected_supervisor': supervisor,
        'selected_status': status,
        'patrol_edit_users': PATROL_EDIT_DELETE_USERS,  # 保持之前的
        'selected_category': category, # 类别大饼跳用
    })


@login_required
def patrol_create(request):
    """新增点检问题点记录（支持多张照片 + 正确保存到 media 文件夹）"""
    if request.method == 'POST':
        photos = request.FILES.getlist('photos')   # 获取所有上传的文件
        photo_urls = []

        # 获取用户选择的类别ID
        category_id = request.POST.get('category')

        issue = PatrolIssue.objects.create(
            sequence=request.POST.get('sequence'),
            date=request.POST.get('date'),
            line=request.POST.get('line'),
            station=request.POST.get('station'),
            problem_desc=request.POST.get('problem_desc'),
            op_responsible=request.POST.get('op_responsible'),
            supervisor=request.POST.get('supervisor'),
            status=request.POST.get('status'),
            category_id=category_id if category_id else None,  # ← 新增这一行
        )

        # 保存每张照片到磁盘，并记录URL
        for photo in photos:
            if photo:
                # 保存文件
                issue.photo = photo   # 先用单文件字段保存
                issue.save()          # 保存一次
                photo_urls.append(issue.photo.url)   # 记录URL

        issue.photos = photo_urls   # 保存到多照片字段
        issue.save()

        # ==================== 新增：更新跑马灯（只在新增时执行） ====================
        append_to_marquee_log(request, issue.line)

        messages.success(request, f'✅ 点检记录已保存！共上传 {len(photos)} 张照片')
        return redirect('issues:patrol_list')

    # 获取所有启用的类别，按排序显示
    categories = PatrolCategory.objects.filter(is_active=True).order_by('order')

    return render(request, 'issues/patrol_form.html', {
        'supervisor_choices': SUPERVISOR_CHOICES,
        'categories': categories,  # ← 新增
    })


@login_required
def patrol_edit(request, pk):
    """编辑点检问题点记录（支持删除已有照片）—— 增加权限控制"""

    # ==================== 权限检查 ====================
    if request.user.username not in PATROL_EDIT_DELETE_USERS:
        messages.error(request, '❌ 你没有权限编辑点检记录！')
        return redirect('issues:patrol_list')
    # =================================================

    issue = get_object_or_404(PatrolIssue, pk=pk)
    if request.method == 'POST':
        photos_to_delete = request.POST.get('photos_to_delete', '').strip()
        new_photos = request.FILES.getlist('photos')

        # 删除选中的照片
        if photos_to_delete:
            delete_list = [u.strip() for u in photos_to_delete.split(',') if u.strip()]
            issue.photos = [url for url in issue.photos if url not in delete_list]

        # 保存新上传的照片
        for photo in new_photos:
            if photo:
                issue.photo = photo          # 先用单文件字段保存
                issue.save()
                if issue.photo.url not in issue.photos:
                    issue.photos.append(issue.photo.url)

        # 更新其他字段
        issue.date = request.POST.get('date')
        issue.line = request.POST.get('line')
        issue.station = request.POST.get('station')
        issue.problem_desc = request.POST.get('problem_desc')
        issue.op_responsible = request.POST.get('op_responsible')
        issue.supervisor = request.POST.get('supervisor')
        issue.status = request.POST.get('status')
        # 更新类别
        category_id = request.POST.get('category')
        issue.category_id = category_id if category_id else None

        issue.save()

        messages.success(request, f'✅ 编辑成功！已删除 {len(delete_list) if photos_to_delete else 0} 张照片')
        return redirect('issues:patrol_list')

    categories = PatrolCategory.objects.filter(is_active=True).order_by('order')

    return render(request, 'issues/patrol_form.html', {
        'issue': issue,
        'edit': True,
        'supervisor_choices': SUPERVISOR_CHOICES,
        'categories': categories,  # ← 新增
    })



@login_required
def patrol_import(request):
    """点检问题点 Excel 导入（完全匹配你提供的格式）"""
    if request.method == 'POST' and 'excel_file' in request.FILES:
        excel_file = request.FILES['excel_file']
        try:
            df = pd.read_excel(excel_file, sheet_name="问题记录 2026")
            count = 0

            for idx, row in df.iterrows():
                if idx < 1: continue  # 跳过标题行

                date_str = str(row.get('日期', '')).strip()
                if not date_str or date_str in ['日期', 'nan', 'NaN', '']:
                    continue

                try:
                    issue_date = pd.to_datetime(date_str).date()
                except:
                    continue

                PatrolIssue.objects.create(
                    sequence=row.get('顺序'),
                    date=issue_date,
                    line=str(row.get('线别', '')).strip(),
                    station=str(row.get('站别', '')).strip(),
                    problem_desc=str(row.get('问题要改善', '')).strip(),
                    op_responsible=str(row.get('越南负责人（OP）', '')).strip(),
                    supervisor=str(row.get('责任单位主管', '')).strip(),
                    status=str(row.get('情况', 'Open')).strip(),
                    # 照片暂时不支持批量导入（可后续手动编辑上传）
                )
                count += 1

            messages.success(request, f'✅ 成功导入 {count} 条点检问题记录！')
            return redirect('issues:patrol_list')

        except Exception as e:
            messages.error(request, f'❌ 导入失败：{str(e)}')
            return redirect('issues:patrol_list')

    return render(request, 'issues/patrol_import.html', {})


@login_required
def patrol_delete(request, pk):
    """删除一条点检记录 —— 增加权限控制"""

    # ==================== 权限检查 ====================
    if request.user.username not in PATROL_EDIT_DELETE_USERS:
        messages.error(request, '❌ 你没有权限删除点检记录！')
        return redirect('issues:patrol_list')
    # =================================================

    from django.shortcuts import get_object_or_404
    from django.contrib import messages
    issue = get_object_or_404(PatrolIssue, pk=pk)
    issue.delete()
    messages.success(request, f'✅ 记录 {pk} 已删除！')
    return redirect('issues:patrol_list')


@login_required
def global_issues_list(request):
    """
    全局问题点列表 - 已改成和设计模块完全一致的风格
    支持搜索 + 绿条 + 从设备详情页自动选中当前设备
    """
    from search.search_forms import GlobalSearchForm
    from django.db import models

    print("=== global_issues_list 被调用 ===")
    print("完整请求URL:", request.get_full_path())

    form = GlobalSearchForm(request.GET)
    issues = EquipmentIssue.objects.all().order_by('-occur_date')
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

    # 如果选中了设备，只显示该设备的问题点
    if selected_equipment:
        issues = issues.filter(equipment=selected_equipment)
        print(f"过滤后 issues 数量: {issues.count()} 条")

    return render(request, 'issues/global_issues_list.html', {
        'issues': issues,
        'form': form,
        'selected_equipment': selected_equipment,
    })


@login_required
def issue_create(request, equipment_pk):
    """新增问题点 - 自动生成 issue_code"""
    equipment = get_object_or_404(Equipment, pk=equipment_pk)

    if request.method == 'POST':
        form = IssueForm(request.POST)
        photos = request.FILES.getlist('photos')

        if form.is_valid():
            issue = form.save(commit=False)
            issue.equipment = equipment

            # 自动生成问题码：20260318-001
            today = datetime.now().strftime('%Y%m%d')
            last = EquipmentIssue.objects.filter(issue_code__startswith=today).order_by('-issue_code').first()
            seq = int(last.issue_code.split('-')[-1]) + 1 if last and last.issue_code else 1
            issue.issue_code = f"{today}-{seq:03d}"

            issue.save()

            # 保存照片
            photo_urls = []
            for photo in photos:
                if photo:
                    issue.photo = photo
                    issue.save()
                    photo_urls.append(issue.photo.url)

            issue.photos = photo_urls
            issue.save()

            messages.success(request, f'✅ 保存成功！问题码：{issue.issue_code}')
            return redirect('issues:global_issues_list')
        else:
            print("❌ 表单验证失败:", form.errors)

    else:
        form = IssueForm()

    return render(request, 'issues/issue_form.html', {
        'form': form,
        'equipment': equipment,
    })

@login_required
def import_issues(request):
    """
    最终修正版 - 强制读取 'LapTop BB Auto Downtime' sheet
    """
    if request.method == 'POST' and 'excel_file' in request.FILES:
        excel_file = request.FILES['excel_file']
        try:
            # 强制使用正确的 sheet
            sheet_name = 'LapTop BB Auto Downtime'
            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=0)

            print("=== Excel 文件信息 ===")
            print(f"文件名称: {excel_file.name}")
            print(f"强制读取 sheet: {sheet_name}")
            print(f"实际列名列表: {list(df.columns)}")
            print(f"总行数: {len(df)}")

            print("\n=== 开始导入调试（前5行） ===")
            count = 0
            failed = []

            for idx, row in df.iterrows():
                # 打印前5行关键数据
                if idx < 5:
                    print(f"行{idx+2}: 站別='{row.get('站別', '')}' | 設備='{row.get('設備', '')}' | 日期='{row.get('日期', '')}' | 異常現象='{row.get('異常現象及原因', '')}'")

                station = str(row.get('站別', '')).strip()
                equip_name = str(row.get('設備', '')).strip()
                raw_date = str(row.get('日期', '')).strip()
                desc = str(row.get('異常現象及原因', '')).strip()

                if not station or not desc or raw_date in ['日期', 'nan', '', 'NaN']:
                    continue

                # 优先用站別匹配设备
                equipment = Equipment.objects.filter(station__iexact=station).first()

                # 如果站別没找到，再用设备名称模糊匹配
                if not equipment and equip_name:
                    equipment = Equipment.objects.filter(name__icontains=equip_name).first()

                if not equipment:
                    failed.append(f"行{idx+2}: 未找到设备（站別={station}, 名称={equip_name}）")
                    continue

                # 日期解析
                clean_date = raw_date.split('N')[0].split('D')[0].strip()
                try:
                    occur_date = pd.to_datetime(f"2026-{clean_date}", format='%Y-%m/%d').date()
                except:
                    failed.append(f"行{idx+2}: 日期格式错误 ({raw_date})")
                    continue

                time_str = str(row.get('異常時間\n(min)', row.get('異常時間(min)', '0'))).strip()
                minutes = float(time_str) if time_str.replace('.', '', 1).isdigit() else 0

                EquipmentIssue.objects.create(
                    equipment=equipment,
                    issue_code=f"EX-{datetime.now().strftime('%Y%m%d')}-{count+1:03d}",
                    desc=desc,
                    occur_date=occur_date,
                    abnormal_work_time=int(minutes),
                    work_time_type=str(row.get('异常工时甄别（硬件/软件/其它)', '')),
                    can_import_maintenance=str(row.get('可否导入保养', '')) == 'OK',
                    risk_id=f"RISK-{datetime.now().strftime('%Y%m%d')}-{count+1:03d}",
                    source_excel=excel_file.name
                )
                count += 1

            msg = f'✅ 成功导入 {count} 条问题点！'
            if failed:
                msg += f'\n⚠️ 失败 {len(failed)} 条（见下方）'
                for f in failed[:15]:
                    print(f)
                if len(failed) > 15:
                    print(f"... 还有 {len(failed)-15} 条失败记录")

            return render(request, 'issues/import_form.html', {'success': msg})

        except Exception as e:
            return render(request, 'issues/import_form.html', {'error': f'导入失败：{str(e)}'})

    return render(request, 'issues/import_form.html', {})


@login_required
def patrol_update_problem(request, pk):
    """只更新“问题要改善”字段（双击编辑专用）"""
    if request.method == 'POST':
        issue = get_object_or_404(PatrolIssue, pk=pk)

        # 支持 POST 表单和 JSON 两种方式
        new_desc = request.POST.get('problem_desc')
        if not new_desc and request.body:
            try:
                data = json.loads(request.body)
                new_desc = data.get('problem_desc')
            except:
                pass

        if new_desc is not None:
            issue.problem_desc = new_desc
            issue.save()
            return JsonResponse({'success': True})

    return JsonResponse({'success': False})


@login_required
def patrol_export(request):
    """导出Excel - 只导出勾选的行 + 照片/视频做成可点击超链接"""
    from django.http import HttpResponse
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill
    from openpyxl.utils import get_column_letter

    if request.method != 'POST':
        return redirect('issues:patrol_list')

    selected_ids_str = request.POST.get('selected_ids', '')
    if not selected_ids_str:
        return redirect('issues:patrol_list')

    selected_ids = [int(x) for x in selected_ids_str.split(',') if x.strip().isdigit()]
    issues = PatrolIssue.objects.filter(id__in=selected_ids).order_by('-date')

    wb = Workbook()
    ws = wb.active
    ws.title = "点检问题点记录"

    # 列顺序与网页完全一致
    headers = ['日期', '线别', '站别', '问题要改善', '照片/视频', 'OP负责人', '主管', '状态']

    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for row_idx, issue in enumerate(issues, start=2):
        ws.cell(row=row_idx, column=1, value=issue.date.strftime('%Y-%m-%d') if issue.date else '')
        ws.cell(row=row_idx, column=2, value=issue.line)
        ws.cell(row=row_idx, column=3, value=issue.station)
        ws.cell(row=row_idx, column=4, value=issue.problem_desc)

        # 第5列：照片/视频 → 做成超链接
        if issue.photos and len(issue.photos) > 0:
            url = issue.photos[0]  # 取第一张作为链接
            cell = ws.cell(row=row_idx, column=5, value="查看图片/视频")
            cell.hyperlink = url
            cell.style = "Hyperlink"
        elif issue.photo:
            cell = ws.cell(row=row_idx, column=5, value="查看图片/视频")
            cell.hyperlink = issue.photo.url
            cell.style = "Hyperlink"
        else:
            ws.cell(row=row_idx, column=5, value="无")

        ws.cell(row=row_idx, column=6, value=issue.op_responsible)
        ws.cell(row=row_idx, column=7, value=issue.supervisor)
        ws.cell(row=row_idx, column=8, value=issue.status)

        ws.row_dimensions[row_idx].height = 150

    # 列宽调整
    column_widths = [12, 12, 10, 60, 25, 18, 18, 12]
    for i, width in enumerate(column_widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = width

    ws.freeze_panes = "A2"

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=点检问题点记录_{len(issues)}条.xlsx'

    wb.save(response)
    return response

# ==================== 公屏通知管理 ====================
@login_required
def marquee_notice_manage(request):
    """
    公屏通知发布/关闭页面
    只有白名单用户可以访问
    """
    from .issues_models import MarqueeNotice

    # 权限检查
    if request.user.username not in MARQUEE_NOTICE_USERS:
        messages.error(request, '你没有权限管理公屏通知！')
        return redirect('issues:patrol_list')

    # 获取当前启用的通知（最多一条）
    current_notice = MarqueeNotice.objects.filter(is_active=True).order_by('-created_at').first()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'publish':
            content = request.POST.get('content', '').strip()
            if not content:
                messages.error(request, '通知内容不能为空！')
            else:
                # 先把旧的全部关闭
                MarqueeNotice.objects.filter(is_active=True).update(is_active=False)
                # 创建新通知
                MarqueeNotice.objects.create(
                    content=content,
                    is_active=True,
                    created_by=request.user.username
                )
                messages.success(request, f'公屏通知已发布：{content}')
                return redirect('issues:marquee_notice_manage')

        elif action == 'close':
            MarqueeNotice.objects.filter(is_active=True).update(is_active=False)
            messages.success(request, '公屏通知已关闭，跑马灯恢复显示点检日志')
            return redirect('issues:marquee_notice_manage')

    return render(request, 'issues/marquee_notice.html', {
        'current_notice': current_notice,
        'marquee_users': MARQUEE_NOTICE_USERS,
    })


@login_required
def marquee_content_api(request):
    """
    跑马灯内容接口（方案B：公屏优先，没有才显示点检日志）
    返回纯文本，给 base.html 的 JS 调用
    """
    from .issues_models import MarqueeNotice
    from django.conf import settings
    import os

    # 1. 优先查启用中的公屏通知
    notice = MarqueeNotice.objects.filter(is_active=True).order_by('-created_at').first()
    if notice:
        time_str = notice.created_at.strftime('%m-%d %H:%M')
        msg = f"📢 {notice.content}　|　发布人：{notice.created_by}　|　时间：{time_str}"
        return HttpResponse(msg, content_type='text/plain; charset=utf-8')

    # 2. 没有公屏通知 → 读原来的点检日志
    log_path = os.path.join(settings.BASE_DIR, 'static', 'maintenance_log.txt')
    try:
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
            if lines:
                return HttpResponse('🚨 ' + lines[-1], content_type='text/plain; charset=utf-8')
    except Exception:
        pass

    return HttpResponse('🚨 系统运行正常 | 等待最新信息...', content_type='text/plain; charset=utf-8')