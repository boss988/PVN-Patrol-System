from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import os
import pandas as pd
from .models import LaserCheckConfig, AIComparison
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.urls import reverse
from django.http import FileResponse, Http404, JsonResponse, HttpResponse
import base64
from django.core.files.base import ContentFile


# ==================== 全局配置 ====================
# meerk40t 导入（保留备用）
MEERK40T_AVAILABLE = False
MEERK40T_ERROR = None
try:
    from meerk40t.core.laserjob import LaserJob
    MEERK40T_AVAILABLE = True
    print("[DEBUG] ✅ meerk40t 导入成功！")
except Exception as e:
    MEERK40T_ERROR = str(e)
    print(f"[ERROR] ❌ meerk40t 导入失败：{MEERK40T_ERROR}")


# ==================== 视图函数 ====================

@login_required
def search_page(request):
    """搜索首页 - 接收料号并跳转到详情页"""
    if request.method == 'POST':
        part_number = request.POST.get('part_number', '').strip().upper()
        if part_number:
            print(f"[DEBUG] 搜索页收到输入料号: {part_number} → 跳转到详情页")
            return redirect('laser_check:check_detail', part_number=part_number)
        else:
            messages.error(request, "请输入料号")

    config = LaserCheckConfig.objects.first()
    return render(request, 'laser_check/search.html', {'config': config})


@login_required
def settings_page(request):
    """设置页面 - 配置产品图文件夹、镭雕图文件夹、Excel映射文件路径"""
    config = LaserCheckConfig.objects.first() or LaserCheckConfig()
    if request.method == 'POST':
        config.product_folder = request.POST.get('product_folder', '').strip()
        config.laser_folder = request.POST.get('laser_folder', '').strip()
        config.mapping_excel = request.POST.get('mapping_excel', '').strip()
        config.save()
        messages.success(request, "路径设置已保存")
        return redirect('laser_check:search_page')
    return render(request, 'laser_check/settings.html', {'config': config})


@login_required
def check_detail(request, part_number):
    """镭雕图检查详情页 - 核心搜索逻辑 + 详细调试信息"""
    config = LaserCheckConfig.objects.first()
    if not config:
        messages.error(request, "请先在后台设置文件夹路径")
        return redirect('laser_check:search_page')

    part_number = (part_number or request.GET.get('part_number', '')).strip().upper()
    if not part_number:
        messages.error(request, "料号不能为空")
        return redirect('laser_check:search_page')

    print(f"[DEBUG] ==================== 开始处理料号: {part_number} ====================")

    # ====================== Excel 映射 ======================
    spec_from_excel = None
    if config.mapping_excel and os.path.exists(config.mapping_excel):
        try:
            df = pd.read_excel(config.mapping_excel)
            df.columns = [str(col).strip() for col in df.columns]
            for _, row in df.iterrows():
                key = str(row.get('料號', row.get('料号', ''))).strip().upper()
                if key == part_number:
                    spec_from_excel = str(row.get('規格', row.get('规格', ''))).strip()
                    print(f"[DEBUG] Excel映射成功: {part_number} -> {spec_from_excel}")
                    break
        except Exception as e:
            print(f"[DEBUG] Excel读取失败: {e}")

    # ====================== 产品图搜索 ======================
    product_path = None
    product_relative_path = None
    search_keywords = [part_number]
    if spec_from_excel:
        search_keywords.append(spec_from_excel.upper())

    if os.path.exists(config.product_folder):
        for root, dirs, files in os.walk(config.product_folder):
            for file in files:
                if file.upper().endswith(('.PDF', '.PDT')) and any(kw in file.upper() for kw in search_keywords):
                    product_path = os.path.join(root, file)
                    product_relative_path = os.path.relpath(product_path, config.product_folder).replace('\\', '/')
                    print(f"[DEBUG] 找到产品图: {product_path}")
                    break
            if product_path:
                break

    # ====================== 镭雕图搜索（支持多个版本） ======================
    laser_files = []
    if os.path.exists(config.laser_folder):
        for root, dirs, files in os.walk(config.laser_folder):
            for file in files:
                if part_number in file.upper() and file.upper().endswith('.EZD'):
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, config.laser_folder).replace('\\', '/')
                    laser_files.append({
                        'filename': file,
                        'relative_path': relative_path,
                    })
                    print(f"[DEBUG] 找到镭雕图: {file}")

    print(f"[DEBUG] 共找到 {len(laser_files)} 个 .ezd 文件")

    context = {
        'part_number': part_number,
        'product_folder': config.product_folder,
        'laser_folder': config.laser_folder,
        'product_path': product_path,
        'product_relative_path': product_relative_path,
        'laser_files': laser_files,
        'spec_from_excel': spec_from_excel,

        'pdf_absolute_url': request.build_absolute_uri(
            reverse('laser_check:serve_pdf', args=[product_relative_path])
        ) if product_relative_path else None,
    }
    return render(request, 'laser_check/check_detail.html', context)


# ==================== 文件服务视图 ====================

@login_required
def serve_file(request, file_type, filename):
    """通用文件下载服务（PDF 和 .ezd）"""
    config = LaserCheckConfig.objects.first()
    if not config:
        raise Http404("配置不存在")

    if file_type == 'pdf':
        folder = config.product_folder
    elif file_type == 'ezd':
        folder = config.laser_folder
    else:
        raise Http404("类型错误")

    full_path = os.path.join(folder, filename)
    if not os.path.exists(full_path):
        print(f"[ERROR] 文件不存在: {full_path}")
        raise Http404("文件不存在")

    print(f"[DEBUG] 成功下载文件: {full_path}")

    if file_type == 'pdf':
        content_type = 'application/pdf'
    else:
        content_type = 'application/octet-stream'

    response = FileResponse(open(full_path, 'rb'), content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
@xframe_options_sameorigin
def serve_pdf(request, filename):
    """PDF 文件服务 - 用于网页直接预览"""
    config = LaserCheckConfig.objects.first()
    if not config:
        raise Http404("配置不存在")

    filename = filename.rstrip('/')
    full_path = os.path.join(config.product_folder, filename)
    if not os.path.exists(full_path):
        print(f"[ERROR] PDF文件不存在: {full_path}")
        raise Http404("文件不存在")

    print(f"[DEBUG] 成功服务 PDF: {full_path}")

    response = FileResponse(open(full_path, 'rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{os.path.basename(filename)}"'
    response['X-Content-Type-Options'] = 'nosniff'
    return response


# ==================== AI 检测视图 ====================

@login_required
def ai_check(request, part_number):
    """AI 检测页面 - 产品图 vs 镭雕图对比（带完整调试）"""
    if request.method == 'POST':
        product_base64 = request.POST.get('product_image', '')
        laser_base64 = request.POST.get('laser_image', '')

        print(f"[AI DEBUG] === 开始处理料号: {part_number} ===")
        print(f"[AI DEBUG] product_base64 总长度: {len(product_base64)}")
        print(f"[AI DEBUG] laser_base64 总长度: {len(laser_base64)}")

        if not product_base64 or not laser_base64:
            print("[AI DEBUG] 错误: 图片数据为空")
            return JsonResponse({'status': 'error', 'message': '请上传两张图片'})

        try:
            def clean_base64(data):
                if ',' in data:
                    data = data.split(',', 1)[1]
                return data.strip()

            product_clean = clean_base64(product_base64)
            laser_clean = clean_base64(laser_base64)

            print(f"[AI DEBUG] 清理后 product_clean 长度: {len(product_clean)}")
            print(f"[AI DEBUG] 清理后 laser_clean 长度: {len(laser_clean)}")

            prompt = """你现在收到两张图片：

左边图片是【产品图（标准参考图）】
右边图片是【镭雕图（实际要打标的图）】

请你先分别描述两张图片的主要内容，然后再仔细对比。

重点检查右边的镭雕图是否存在以下问题：
1. 漏字、缺字、字符不完整
2. 字符变形、模糊、重叠、错位
3. 多余的字符或标点
4. 任何与左边产品图不一致的地方

请严格、仔细检查，不要遗漏。
如果完全一致，请回复“完全一致，无任何差异”。
如果有任何差异，请逐条列出，并说明具体位置。"""

            import requests
            print("[AI DEBUG] 正在调用 Ollama API...")

            response = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "qwen2.5vl:7b",
                    "messages": [
                        {"role": "user", "content": prompt},
                        {"role": "user", "images": [product_clean, laser_clean]}
                    ],
                    "stream": False
                },
                timeout=580
            )

            print(f"[AI DEBUG] Ollama 返回状态码: {response.status_code}")
            print(f"[AI DEBUG] Ollama 返回原始内容前500字符: {response.text[:500]}...")

            result = response.json()
            ai_result = result.get('message', {}).get('content', str(result))

            AIComparison.objects.create(
                part_number=part_number,
                result_text=ai_result,
                created_by=request.user
            )

            print("[AI DEBUG] AI 检测成功完成")
            return JsonResponse({'status': 'success', 'result': ai_result})

        except Exception as e:
            print(f"[AI ERROR] 发生异常: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)})

    context = {'part_number': part_number}
    return render(request, 'laser_check/ai_check.html', context)


# ==================== AI 历史记录视图 ====================

@login_required
def ai_history(request, part_number):
    """查看某个料号的 AI 检测历史记录"""
    records = AIComparison.objects.filter(part_number=part_number).order_by('-created_at')
    context = {
        'part_number': part_number,
        'records': records,
    }
    return render(request, 'laser_check/ai_history.html', context)


# ==================== 保留 serve_ezd_svg（避免 urls.py 报错） ====================
@login_required
@xframe_options_sameorigin
def serve_ezd_svg(request, filename):
    """保留此函数，避免 urls.py 报错（当前不使用 SVG 预览）"""
    return HttpResponse("<h3 style='text-align:center;margin-top:100px;color:#666;'>SVG 预览暂未启用</h3>", status=200)