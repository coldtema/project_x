from django import forms
from apps.accounts.models import CustomUser
from django.contrib.auth.forms import UserCreationForm


front_attrs = {'class': 'w-full px-3 py-2 rounded-md border border-gray-300 dark:border-neutral-700 bg-gray-100 dark:bg-neutral-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500'}

class SignUpForm(UserCreationForm):
    # username = forms.CharField(max_length=30)
    # email = forms.EmailField(max_length=200)
    error_messages = {
        "password_mismatch": "Пароли не совпадают.",
    }

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2'] #как бы расширили поля, которые могут быть 
        error_messages = {
            'username': {
                'unique': "Пользователь с таким именем уже существует.",
                'mismatch': "Пожалуйста, введите корректное имя пользователя.",
            },
            'email': {
                'unique': "Пользователь с такой почтой уже существует.",
                'mismatch': "Пожалуйста, введите корректный адрес электронной почты.",
            },
        }

class WBDestForm(forms.Form):
    address = forms.CharField(required=True, max_length=1000, widget=forms.TextInput(attrs=front_attrs), help_text='Местоположение')