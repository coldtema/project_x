from django import forms

class WBProductForm(forms.Form):
    url = forms.CharField(max_length=1000, required=True)


class WBDestForm(forms.Form):
    address = forms.CharField(max_length=1000)
