# projects/forms.py
from django import forms
from django.contrib.auth.models import User
from .models import Project, ProjectCollaborator

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class CollaboratorForm(forms.Form):
    username = forms.CharField(label="用戶名稱", max_length=150)
    role = forms.ChoiceField(label="角色", choices=ProjectCollaborator.ROLE_CHOICES)
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError("找不到該用戶")
        return username