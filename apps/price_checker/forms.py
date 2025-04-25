from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    url = forms.URLField(label='Вот сюда ссылку ->')

    class Meta:
        model = Product
        fields = ['url']


class SendMailForm(forms.Form):
    comment = forms.CharField(max_length=1000, widget=forms.Textarea, label='Введите ваш комментарий (можно оставить пустым)', required=False)
    email_to = forms.EmailField(label='Введите email получателя')


class SearchForm(forms.Form):
    query = forms.CharField(max_length=100, label='', help_text='Введите сюда текст поиска')