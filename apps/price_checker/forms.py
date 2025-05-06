from django import forms
from .models import Product


front_attrs = {'class': 'w-full px-3 py-2 rounded-md border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-neutral-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500'}

class ProductForm(forms.ModelForm):
    url = forms.URLField(label='Вот сюда ссылку ->', help_text='Введите ссылку на товар', widget=forms.TextInput(attrs=front_attrs))

    class Meta:
        model = Product
        fields = ['url']


class SendMailForm(forms.Form):
    comment = forms.CharField(max_length=1000, widget=forms.Textarea, label='Введите ваш комментарий (можно оставить пустым)', required=False)
    email_to = forms.EmailField(label='Введите email получателя')


class SearchForm(forms.Form):
    query = forms.CharField(max_length=100, label='', help_text='Введите сюда текст поиска', widget=forms.TextInput(attrs=front_attrs))