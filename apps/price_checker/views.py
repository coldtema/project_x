from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest
from .forms import ProductForm
from .models import Product
from .site_explorer import get_product_brandshop, get_shop_of_product
import time

def all_price_list(request):
    if request.method == 'POST':
        product_form = ProductForm(request.POST)
        print(request.POST)
        if product_form.is_valid():
            product_data = get_shop_of_product(request.POST.get('url'))
            return render(request, 'price_checker/temp_view_prod.html', context={'product_data': product_data})
        else:
            return HttpResponseBadRequest('Так себе ссылка')
    else:
        product_form = ProductForm()
        return render(request, 'price_checker/index.html', context={'form': product_form})
