from django.urls import path
from .design_views import (
    design_detail,
    design_create,
    global_design_list,
    file_share_center, # ← 新增这一行
    download_shared_file,
    delete_shared_file,
)

app_name = 'design'

urlpatterns = [
    path('designs/', global_design_list, name='global_design_list'),
    path('designs/<int:equipment_pk>/', design_detail, name='design_detail'),
    path('designs/<int:equipment_pk>/create/', design_create, name='design_create'),

    # 新增：文件临时共享中心
    path('file-share/', file_share_center, name='file_share_center'),
    # 新增：下载文件
    path('file-share/download/<int:file_id>/', download_shared_file, name='download_shared_file'),
# 新增：删除文件
    path('file-share/delete/<int:file_id>/', delete_shared_file, name='delete_shared_file'),
]