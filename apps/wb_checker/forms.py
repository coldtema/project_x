from django import forms


front_attrs = {'class': 'w-full px-3 py-2 rounded-md border-2 border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-neutral-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500'}

class WBProductForm(forms.Form):
    url = forms.CharField(max_length=1000, required=True, help_text='Введите ссылку/артикул на товар с Wildberries', widget=forms.TextInput(attrs=front_attrs))


class SearchForm(forms.Form):
    query = forms.CharField(max_length=100, label='', help_text='Введите сюда текст поиска', widget=forms.TextInput(attrs=front_attrs))