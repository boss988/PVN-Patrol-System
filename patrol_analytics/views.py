from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
from issues.issues_models import PatrolIssue
import json
import os
from django.conf import settings
from collections import defaultdict
from .models import PatrolSummaryRecord   # ← 新增这一行
from issues.issues_views import PATROL_EDIT_DELETE_USERS # ← 导入白名单

SUMMARY_FILE = os.path.join(settings.BASE_DIR, 'patrol_summary.json')



@login_required
def patrol_analytics_dashboard(request):
    """点检问题汇总看板主页面"""
    print("=== patrol_analytics_dashboard 被调用 ===")

    # ==================== 日期范围（扩大到60天，避免漏掉历史记录） ====================
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=14)  # ← 可改成41或55，根据需要调整

    if request.method == 'POST':
        start_str = request.POST.get('start_date')
        end_str = request.POST.get('end_date')
        if start_str and end_str:
            start_date = timezone.datetime.strptime(start_str, '%Y-%m-%d').date()
            end_date = timezone.datetime.strptime(end_str, '%Y-%m-%d').date()

    date_range = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    print(f"【DEBUG】日期范围: {start_date} 到 {end_date}，共 {len(date_range)} 天")

    # ==================== 主管名称规范化函数（和前端、下拉框完全一致） ====================
    def normalize_supervisor_name(name):
        if not name:
            return ""
        n = str(name).strip()
        # 去掉常见后缀和空格
        n = n.replace("_PVN", "").replace(" PVN", "").replace(" ", "")
        # 简繁体转换
        n = n.replace("風", "风").replace("華", "华").replace("興", "兴").replace("劉", "刘")
        # 统一成下拉框里的标准名称
        if "windwang" in n.lower() or "王海风" in n or "王海風" in n:
            return "Wind Wang(王海风_PVN)"
        if "xhli" in n.lower() or "李興恒" in n or "李兴恒" in n:
            return "Xh Li(李興恒_PVN)"
        if "zhengping" in n.lower() or "劉正平" in n or "刘正平" in n:
            return "Zheng-ping Liu(劉正平_PVN)"
        if "guanghua" in n.lower() or "彭光華" in n or "彭光华" in n:
            return "Guang-hua Peng(彭光華_PVN)"
        return name.strip()  # 如果都没匹配，就保留原始名称

    # ==================== 统计 Open / Closed（使用规范化后的名称） ====================
    per_supervisor_counts = defaultdict(lambda: {'open': 0, 'closed': 0})
    queryset = PatrolIssue.objects.filter(date__range=[start_date, end_date])

    print(f"【DEBUG】查询到符合日期范围的记录共 {queryset.count()} 条")

    for issue in queryset:
        raw_sup = getattr(issue, 'supervisor', '').strip()
        normalized_sup = normalize_supervisor_name(raw_sup)

        if normalized_sup:
            if issue.status == 'Open':
                per_supervisor_counts[normalized_sup]['open'] += 1
            elif issue.status == 'Closed':
                per_supervisor_counts[normalized_sup]['closed'] += 1

            # 打印每一条记录，方便你看到到底哪些被统计了
            print(f"   → 日期:{issue.date} | 原始主管:'{raw_sup}' → 规范化后:'{normalized_sup}' | 状态:{issue.status}")

    print("📊 【DEBUG】最终统计结果（已规范化）：")
    for sup, cnt in per_supervisor_counts.items():
        print(f"   → '{sup}'  Open: {cnt['open']} | Closed: {cnt['closed']}")

    saved_data = load_summary_data()

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'date_range': date_range,
        'total': queryset.count(),
        'open_count': sum(c['open'] for c in per_supervisor_counts.values()),
        'closed_count': sum(c['closed'] for c in per_supervisor_counts.values()),
        'saved_data': saved_data,
        'per_supervisor_counts': dict(per_supervisor_counts),
        'patrol_edit_users': PATROL_EDIT_DELETE_USERS,  # ← 新增这一行白名单
    }

    print("【DEBUG】传递给模板的 per_supervisor_counts keys:", list(per_supervisor_counts.keys()))
    return render(request, 'patrol_analytics/dashboard.html', context)


# ==================== 从数据库读取最新汇总数据 ====================
def load_summary_data():
    """从数据库读取最新保存的汇总数据"""
    record = PatrolSummaryRecord.objects.order_by('-save_date').first()
    if record:
        print(f"✅ [DEBUG] 从数据库成功加载最新汇总数据 (ID: {record.id})")
        return record.data
    else:
        print("⚠️ [DEBUG] 数据库中还没有保存的汇总数据")
        return None



# ==================== 保存数据到数据库 ====================
@csrf_exempt
@login_required
def save_summary(request):
    """保存手动填写的汇总数据到数据库 —— 增加权限控制"""

    # ==================== 权限检查 ====================
    if request.user.username not in PATROL_EDIT_DELETE_USERS:
        return JsonResponse({
            'success': False,
            'error': '你没有权限保存数据！'
        }, status=403)
    # =================================================


    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # ==================== 修复日期格式 ====================
            dates = data.get('dates', [])
            start_date_str = dates[0] if dates else None
            end_date_str = dates[-1] if dates else None

            # 把 "04/25" 这种格式转为 "2026-04-25"
            def parse_table_date(date_str):
                if not date_str:
                    return None
                try:
                    # 处理 m/d 格式 → 2026-m-d
                    if '/' in date_str:
                        month, day = date_str.strip().split('/')
                        return f"2026-{month.zfill(2)}-{day.zfill(2)}"
                    return date_str
                except:
                    return None

            start_date = parse_table_date(start_date_str)
            end_date = parse_table_date(end_date_str)

            # 保存到数据库
            record = PatrolSummaryRecord.objects.create(
                start_date=start_date,
                end_date=end_date,
                data=data
            )

            print(f"✅ [DEBUG] 数据已成功保存到数据库！记录ID: {record.id}")
            return JsonResponse({'success': True, 'record_id': record.id})

        except Exception as e:
            print("❌ [DEBUG] 保存失败：", str(e))
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'success': False}, status=400)