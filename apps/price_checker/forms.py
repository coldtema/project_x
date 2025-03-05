from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    url = forms.URLField(label='Вот сюда ссылку ->')

    class Meta:
        model = Product
        fields = ['url']