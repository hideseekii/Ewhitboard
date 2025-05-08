from django import forms
from .models import Board, BoardElement, BoardSubmission

class BoardForm(forms.ModelForm):
    class Meta:
        model = Board
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '輸入白板標題'}),
        }

class BoardSubmissionForm(forms.ModelForm):
    class Meta:
        model = BoardSubmission
        fields = ['recognized_text']
        widgets = {
            'recognized_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': '輸入辨識的文字內容'}),
        }