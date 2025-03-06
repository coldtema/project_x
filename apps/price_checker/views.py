from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from .forms import ProductForm
from .models import Product, Price
from .site_explorer import get_product_brandshop, get_shop_of_product
from apps.blog.models import Author

def all_price_list(request):
    if request.method == 'POST':
        product_form = ProductForm(request.POST)
        if product_form.is_valid():
            product_data = get_shop_of_product(request.POST.get('url'))
            new_product = Product.objects.create(name=product_data['name'], latest_price=product_data['price_element'], url=request.POST.get('url'), author=Author.objects.get(id=2))
            Price.objects.create(product=new_product, price=product_data['price_element'])
            return HttpResponseRedirect('/price_checker')
        else:
            return HttpResponseBadRequest('Так себе ссылка')
    else:
        product_form = ProductForm()
        db_products = Product.objects.all()
        return render(request, 'price_checker/index.html', context={'form': product_form, 'db_products': db_products})
