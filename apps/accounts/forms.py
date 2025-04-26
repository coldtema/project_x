from django import forms
from apps.accounts.models import CustomUser
from django.contrib.auth.forms import UserCreationForm

class SignUpForm(UserCreationForm):
    # username = forms.CharField(max_length=30)
    # email = forms.EmailField(max_length=200)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2'] #как бы расширили поля, которые могут быть 