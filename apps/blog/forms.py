from django import forms
from .models import Author

class UserForm(forms.Form):
    nickname = forms.CharField(max_length=20, label='Введите ваш никнейм')
    age = forms.IntegerField(max_value=100, min_value=0, label='Введите ваш возраст')
    # prof_author = forms.NullBooleanField(label='Профессиональный автор', required=True, help_text='gfb')
    # password = forms.CharField(widget=forms.widgets.PasswordInput)

class UserEditForm(forms.ModelForm):
    nickname = forms.CharField(max_length=20, label='Исправьте никнейм')
    age = forms.IntegerField(max_value=100, min_value=0, label='Исправьте возраст')
    id = forms.IntegerField(widget = forms.HiddenInput())
    class Meta:
        model = Author
        fields = ['nickname', 'age', 'id']