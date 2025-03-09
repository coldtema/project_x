from django import forms
from .models import Test

class AddTest(forms.Form):
    name = forms.CharField(max_length=100, label='Имя теста')
    text = forms.CharField(widget=forms.Textarea, label='Текст для анализа')
    class Meta:
        model = Test
        fields = ['name', 'text']