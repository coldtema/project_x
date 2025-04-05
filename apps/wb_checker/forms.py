from django import forms

ACTION_TYPE=(('product', 'product'), 
             ('brand', 'brand'), 
             ('seller', 'seller'),
             ('promo', 'promo'))

class WBProductForm(forms.Form):
    url = forms.CharField(max_length=1000, required=True)
    # action_type = forms.ChoiceField(choices=ACTION_TYPE)


class WBDestForm(forms.Form):
    address = forms.CharField(max_length=1000)
