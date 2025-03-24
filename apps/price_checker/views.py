from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from .forms import ProductForm
from .models import Product, Price, Shop
from .site_explorer import get_shop_of_product
from apps.blog.models import Author
import time
from functools import wraps
from .chart_builder import plot_price_history
# from .async_shit import process_sites
import asyncio

def time_count(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(end - start)
        return result
    return wrapper



def all_price_list(request):
    if request.method == 'POST':
        product_form = ProductForm(request.POST)
        if product_form.is_valid():
            product_data = get_shop_of_product(request.POST.get('url'))
            new_product = Product.objects.create(name=product_data['name'], 
                                                 author=Author.objects.get(id=2),
                                                 url=request.POST.get('url'),
                                                 latest_price=product_data['price_element'], 
                                                 shop=Shop.objects.get(regex_name=product_data['shop']),  
                                                 ref_url=request.POST.get('url'))
            Price.objects.create(product=new_product, price=product_data['price_element'])
            return HttpResponseRedirect('/price_checker')
        else:
            return HttpResponseBadRequest('Так себе ссылка')
    else:
        product_form = ProductForm()
        db_products = Product.objects.filter(enabled=True)
        return render(request, 'price_checker/index.html', context={'form': product_form, 'db_products': db_products})




def price_history(request, id):
    product_to_watch = Product.objects.get(id=id)
    prices_of_product = Price.objects.filter(product_id=id)
    dates = []
    prices = []
    for elem in prices_of_product:
        dates.append(elem.added_time)
        prices.append(elem.price)
    plot_price_history(dates, prices)
    return render(request, 'price_checker/price_history.html', context={'product_to_watch': product_to_watch, 
                                                                        'prices_of_product': prices_of_product, 
                                                                        'chart_url': 'apps/price_checker/static/price_checker/chart.png'})


def delete_product(request, id):
    Product.objects.get(id=id).delete()
    return HttpResponseRedirect('/price_checker')



def delete_price(request, id):
    product_to_redirect = Price.objects.get(id=id).product
    id_of_product = product_to_redirect.id
    Price.objects.get(id=id).delete()
    return HttpResponseRedirect(f'/price_checker/price_history/{id_of_product}')

# def update_prices(request):
#     asyncio.create_task(process_sites())

@time_count
def update_prices(request):
    all_prod = Product.enabled_products.all()
    exception_elems = []
    for elem in all_prod:
        try:
            maybe_new_price = get_shop_of_product(elem.url)['price_element']
        except:
            exception_elems.append(elem)
            continue
        if maybe_new_price != elem.latest_price:
            print(f'''
Цена изменилась!
Продукт: {elem.name}
Было: {elem.latest_price}
Стало: {maybe_new_price}
''')
            elem.latest_price = maybe_new_price
            elem.save()
            Price.objects.create(price=maybe_new_price, product=elem)
    broken_elems = []
    if exception_elems:
        print(f'''
    эти элементы не прошли с первой попытки: {[elem.name for elem in exception_elems]}
    ''')
        time.sleep(1)
        for elem in exception_elems:
            try:
                maybe_new_price = get_shop_of_product(elem.url)['price_element']
            except:
                broken_elems.append(elem)
                continue
            if maybe_new_price != elem.latest_price:
                print(f'''
    Цена изменилась!
    Продукт: {elem.name}
    Было: {elem.latest_price}
    Стало: {maybe_new_price}
    ''')
                elem.latest_price = maybe_new_price
                elem.save()
                Price.objects.create(price=maybe_new_price, product=elem)
        if broken_elems:
            print(f'Продукты, по которым не удалось обновить цену:')
            for elem in broken_elems: 
                print(f'id: {elem.id}, url: {elem.url}')
                answer = input('Что делаем с продуктом? (d - выключить, все остальное - пропустить) \n')
                if answer == 'd':
                    elem.enabled = False
                    elem.save()
                else:
                    continue
    return HttpResponseRedirect('/price_checker')
