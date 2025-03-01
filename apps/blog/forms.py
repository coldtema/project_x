from django import forms

class UserForm(forms.Form):
    name = forms.CharField(max_length=20, label='Введите ваше имя')
    age = forms.IntegerField(max_value=100, min_value=0, label='Введите ваш возраст')