from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import EmailGroup
from .forms import EmailGroupForm
from issues.issues_models import PatrolIssue   # 点检模型
from django.conf import settings
import os
from django.http import JsonResponse   # ← 新增这一行


@login_required
def patrol_send_email(request):
    """调试版 - 发送点检邮件（已修复 selected_ids 拆分问题）"""
    print("=== 邮件发送视图被调用 ===")
    print("请求方法:", request.method)
    print("POST 数据:", dict(request.POST))

    if request.method == 'POST':
        # 关键修复：处理逗号分隔的字符串
        selected_str = request.POST.get('selected_ids', '')
        if selected_str:
            selected_ids = [int(x.strip()) for x in selected_str.split(',') if x.strip().isdigit()]
        else:
            selected_ids = []

        group_id = request.POST.get('group_id')
        subject = request.POST.get('subject', '点检问题点记录通知')

        print("处理后的选中记录ID:", selected_ids)
        print("群组ID:", group_id)

        if not selected_ids:
            messages.error(request, '❌ 请至少选择一条记录')
            print("错误：没有选中记录")
            return redirect('issues:patrol_list')

        if not group_id:
            messages.error(request, '❌ 请选择邮件群组')
            print("错误：没有选择群组")
            return redirect('issues:patrol_list')

        try:
            group = EmailGroup.objects.get(id=group_id)
            issues = PatrolIssue.objects.filter(id__in=selected_ids)
            print(f"找到 {issues.count()} 条记录，将发送给群组: {group.name}")

            # 生成HTML邮件
            html_content = render_to_string('notification/patrol_email.html', {
                'issues': issues,
                'site_url': 'http://127.0.0.1:8000',
            })

            # 发送（console模式会直接打印到终端）
            email = EmailMultiAlternatives(
                subject=subject,
                body="纯文本版本",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=group.emails.replace('\n', ',').split(','),
            )
            email.attach_alternative(html_content, "text/html")
            email.send()

            print("✅ 邮件已成功发送（console模式）")
            messages.success(request, f'✅ 邮件已发送至 {group.name}！（console模式已打印内容）')

        except Exception as e:
            print("发送异常:", str(e))
            messages.error(request, f'❌ 发送失败：{str(e)}')

        return redirect('issues:patrol_list')

    # GET 请求（显示模态框）
    print("GET 请求，显示模态框")
    today_issues = PatrolIssue.objects.filter(date__date__today=True)
    groups = EmailGroup.objects.all()
    return render(request, 'notification/patrol_send_modal.html', {
        'today_issues': today_issues,
        'groups': groups,
    })

@login_required
def create_email_group(request):
    """普通用户新建邮件群组（使用普通表单提交 + redirect）"""
    if request.method == 'POST':
        form = EmailGroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.created_by = request.user
            group.save()
            messages.success(request, f'✅ 群组 "{group.name}" 创建成功！')
            return redirect('issues:patrol_list')   # 保存后返回列表页
        else:
            messages.error(request, '❌ 保存失败，请检查填写内容')
    else:
        form = EmailGroupForm()

    return render(request, 'notification/email_group_form.html', {'form': form})