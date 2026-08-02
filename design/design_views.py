from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .design_models import DesignInfo
from core.core_models import Equipment
from django import forms
from search.search_forms import GlobalSearchForm
from django.db import models

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse   # ← 必须加上这一行！

from .design_models import DesignInfo
# from .design_forms import DesignInfoForm   # 如果你有单独的 forms 文件
from core.core_models import Equipment
from .design_models import DesignInfo, SharedFile   # ← 修改成这一行


class DesignInfoForm(forms.ModelForm):
    """
    设计信息表单。
    输入：POST请求数据 + 文件。
    输出：验证后的DesignInfo实例。
    功能：创建/更新设计信息，支持文件上传。
    """
    class Meta:
        model = DesignInfo
        fields = '__all__'

@login_required
def design_detail(request, equipment_pk):
    """
    设计详情视图。
    输入：HTTP请求 + equipment_pk。
    输出：渲染design_detail.html模板。
    功能：显示单个设备的设计信息和风险评分。
    """
    equipment = get_object_or_404(Equipment, pk=equipment_pk)
    design = get_object_or_404(DesignInfo, equipment=equipment)
    return render(request, 'design/design_detail.html', {
        'design': design,
        'equipment': equipment,
        'risk_score': design.design_risk_score
    })




@login_required
def global_design_list(request):
    """
    最终加强调试版 + 修复 equipment_id 参数问题
    """
    from search.search_forms import GlobalSearchForm
    from django.db import models

    print("=== global_design_list 被调用 ===")
    print("完整请求URL:", request.get_full_path())

    form = GlobalSearchForm(request.GET)
    designs = DesignInfo.objects.all().order_by('equipment__code')
    selected_equipment = None

    # ==================== 关键修复：同时支持 equipment_id 和 equipment_pk ====================
    equipment_pk = request.GET.get('equipment_pk') or request.GET.get('equipment_id')
    print(f"收到参数 equipment_pk/equipment_id: {equipment_pk}")

    if equipment_pk:
        selected_equipment = Equipment.objects.filter(pk=equipment_pk).first()
        print(f"✅ 成功选中设备: {selected_equipment} (ID={equipment_pk})")

    # ==================== 只有当没有从URL带设备时，才执行手动搜索 ====================
    if form.is_valid() and not selected_equipment:
        print("走手动搜索逻辑...")
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

    # 最终过滤
    if selected_equipment:
        designs = designs.filter(equipment=selected_equipment)
        print(f"最终 designs 数量: {designs.count()} 条（仅显示该设备）")

    return render(request, 'design/global_design_list.html', {
        'designs': designs,
        'form': form,
        'selected_equipment': selected_equipment,
    })


@login_required
def design_create(request, equipment_pk):
    """新增/编辑设计信息 - 最终修复版（已解决 design_detail reverse 报错）"""
    equipment = get_object_or_404(Equipment, pk=equipment_pk)
    print(f"design_create 被调用，设备: {equipment.name} (ID={equipment_pk})")

    # 如果已经存在设计信息，直接跳详情页（关键修复在这里）
    design_info = DesignInfo.objects.filter(equipment=equipment).first()
    if design_info:
        print("已有设计信息，跳转详情页")
        return redirect('design:design_detail', equipment_pk=design_info.equipment.pk)

    form = DesignInfoForm(request.POST or None, request.FILES or None)

    if request.method == 'POST':
        print("收到POST提交")
        if form.is_valid():
            instance = form.save(commit=False)
            instance.equipment = equipment
            instance.save()
            print("✅ 保存成功！")
            messages.success(request, f'✅ 设计信息保存成功！（{equipment.name}）')
            return redirect(f"{reverse('design:global_design_list')}?equipment_id={equipment.pk}")
        else:
            print("❌ 表单验证失败:", form.errors)

    return render(request, 'design/design_form.html', {
        'form': form,
        'selected_equipment': equipment,
    })


# ==================== 新增：文件临时共享中心视图 ====================
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator


# ==================== 文件临时共享中心视图（简单实用版） ====================
@login_required
def file_share_center(request):
    """文件临时共享中心 - 一个页面完成上传和下载"""

    # ==================== 处理文件上传 ====================
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']

        # 关键限制：最大 1GB
        MAX_SIZE = 1024 * 1024 * 1024  # 1GB = 1024MB

        if uploaded_file.size > MAX_SIZE:
            messages.error(request, f"❌ 文件太大！最大只能上传 1GB，您上传的文件大小是 {uploaded_file.size / (1024 * 1024):.1f} MB")
            return redirect('design:file_share_center')

        try:
            # 保存文件记录
            SharedFile.objects.create(
                uploader=request.user,
                file=uploaded_file,
                file_name=uploaded_file.name,
                file_size=uploaded_file.size,
            )

            messages.success(request, f"✅ 文件 “{uploaded_file.name}” 上传成功！")

        except Exception as e:
            messages.error(request, f"❌ 上传失败：{str(e)}")

        return redirect('design:file_share_center')

    # ==================== 显示所有已上传文件 ====================
    files = SharedFile.objects.all()

    return render(request, 'design/file_share_center.html', {
        'files': files,
    })


# ==================== 文件下载视图（强力强制下载） ====================
from django.http import FileResponse
import os


@login_required
def download_shared_file(request, file_id):
    """强制下载文件，解决浏览器直接打开的问题"""
    file_obj = get_object_or_404(SharedFile, pk=file_id)

    # 打开文件
    file_path = file_obj.file.path
    response = FileResponse(open(file_path, 'rb'), as_attachment=True)

    # 关键：强制浏览器下载，并使用正确的文件名
    response['Content-Disposition'] = f'attachment; filename="{file_obj.file_name}"'

    # 防止浏览器缓存
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'

    return response


# ==================== 删除共享文件视图 ====================
@login_required
def delete_shared_file(request, file_id):
    """删除上传的文件"""
    file_obj = get_object_or_404(SharedFile, pk=file_id)

    # 可选：只允许上传者本人或管理员删除（目前先允许所有人删除）
    # if file_obj.uploader != request.user and not request.user.is_staff:
    #     messages.error(request, "你没有权限删除此文件")
    #     return redirect('design:file_share_center')

    # 删除文件
    file_obj.file.delete()  # 删除实际文件
    file_obj.delete()  # 删除数据库记录

    messages.success(request, f"✅ 文件 “{file_obj.file_name}” 已删除！")
    return redirect('design:file_share_center')