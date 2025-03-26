from django import forms

ACTION_TYPE=(('product', 'продукт'), 
             ('brand', 'бренд'), 
             ('seller', 'продавец'))

class WBProductForm(forms.Form):
    url = forms.CharField(max_length=100, required=True)
    action_type = forms.ChoiceField(choices=ACTION_TYPE)