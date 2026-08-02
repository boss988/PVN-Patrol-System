from django import forms

class GlobalSearchForm(forms.Form):
    """车间友好7字段搜索表单（严格按Equipment模型字段定义）"""
    id_search = forms.CharField(
        label="ID",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SOP4546-023 或 RFID'})
    )
    name = forms.CharField(
        label="设备名称",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'TDM对位'})
    )
    area = forms.CharField(
        label="厂别 / 区域",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'F44F'})
    )
    line = forms.CharField(
        label="线别",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'BB LINE01'})
    )
    model_type = forms.CharField(   # ← 严格按你定义：model_type = 机种
        label="机种名称",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'BNC 或 PRO'})
    )
    status = forms.ChoiceField(
        label="设备状态",
        required=False,
        choices=[
            ('all', '全部'),
            ('active', '活跃'),
            ('inactive', '停用'),
            ('maintenance', '保养中'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    station = forms.CharField(
        label="站别",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'p02'})
    )