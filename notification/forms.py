from django import forms
from .models import EmailGroup

class EmailGroupForm(forms.ModelForm):
    class Meta:
        model = EmailGroup
        fields = ['name', 'description', 'emails']
        widgets = {
            'emails': forms.Textarea(attrs={'rows': 5, 'placeholder': 'example@company.com\nanother@company.com'}),
        }