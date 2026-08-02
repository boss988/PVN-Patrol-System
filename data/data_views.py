from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .data_models import EquipmentData
from core.core_models import Equipment
import pandas as pd

@login_required
def global_data_list(request):
    """
    全局设备数据列表
    输入：请求
    输出：最新数据 + 导入按钮
    """
    data = EquipmentData.objects.all().order_by('-record_date')
    return render(request, 'data/global_data_list.html', {'data': data})

# @login_required
# def import_data(request):
#     """
#     Excel导入设备数据
#     输入：上传文件
#     输出：成功条数
#     """
#     if request.method == 'POST' and 'excel_file' in request.FILES:
#         excel_file = request.FILES['excel_file']
#         try:
#             df = pd.read_excel(excel_file, sheet_name=0)
#             count = 0
#             for _, row in df.iterrows():
#                 equip_name = str(row.get('设备', ''))
#                 value = float(row.get('数值', 0))
#                 data_type = str(row.get('类型', 'vibration'))
#                 equipment = Equipment.objects.filter(name__icontains=equip_name).first()
#                 if equipment:
#                     EquipmentData.objects.create(
#                         equipment=equipment,
#                         data_type=data_type,
#                         value=value,
#                         note=str(row.get('备注', ''))
#                     )
#                     count += 1
#             return render(request, 'data/import_form.html', {'success': f'✅ 成功导入 {count} 条设备数据！'})
#         except Exception as e:
#             return render(request, 'data/import_form.html', {'error': str(e)})
#     return render(request, 'data/import_form.html', {})


@login_required
def import_data(request):
    """
    CT数据导入函数（已适配CTshow.xlsx）
    输入：上传文件
    输出：成功条数
    """
    if request.method == 'POST' and 'excel_file' in request.FILES:
        excel_file = request.FILES['excel_file']
        try:
            df = pd.read_excel(excel_file, sheet_name=0)
            print("=== 开始导入CT调试 ===")
            print(f"总行数: {len(df)}")
            print(f"实际列名: {list(df.columns)}")
            count = 0

            for idx, row in df.iterrows():
                if idx < 1: continue  # 跳过标题行

                serial = str(row.get('Serial Number', '')).strip()
                ct_value = float(row.get('CT', 0))

                if not serial or ct_value <= 0:
                    continue

                # 用 Serial Number 匹配设备
                equipment = Equipment.objects.filter(name__icontains=serial).first()
                if not equipment:
                    print(f"⚠️ 未匹配设备: {serial}")
                    continue

                EquipmentData.objects.create(
                    equipment=equipment,
                    data_type='ct',
                    value=ct_value,
                    unit='',
                    note=f"Serial: {serial} | Date: {row.get('Date', '')}"
                )
                count += 1

            return render(request, 'data/import_form.html', {
                'success': f'✅ 成功导入 {count} 条CT数据！'
            })
        except Exception as e:
            return render(request, 'data/import_form.html', {'error': f'导入失败：{str(e)}'})
    return render(request, 'data/import_form.html', {})