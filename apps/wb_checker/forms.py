from django import forms

ACTION_TYPE=(('product', 'product'), 
             ('brand', 'brand'), 
             ('seller', 'seller'))

class WBProductForm(forms.Form):
    url = forms.CharField(max_length=100, required=True)
    action_type = forms.ChoiceField(choices=ACTION_TYPE)