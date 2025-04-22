from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from .forms import ProductForm
from .models import Product, Price, Shop
from .site_explorer import get_shop_of_product
from apps.blog.models import Author
import time
from functools import wraps
from .chart_builder import plot_price_history
# from .async_shit import process_sites
from django.urls import reverse
from apps.price_checker.utils import PriceUpdater
from apps.price_checker.utils import time_count
from django.core.paginator import Paginator



def all_price_list(request):
    '''Функция представления для отображения всех продуктов'''
    if request.method == 'POST':
        product_form = ProductForm(request.POST)
        if product_form.is_valid():
            product_data = get_shop_of_product(request.POST.get('url'))
            new_product = Product.objects.create(name=product_data['name'], 
                                                 url=request.POST.get('url'),
                                                 latest_price=product_data['price_element'], 
                                                 shop=Shop.objects.get(regex_name=product_data['shop']),  
                                                 ref_url=request.POST.get('url')) #прописать здесь get_or_create и вообще вынести в другое место
            Author.objects.get(id=2).product_set.add(new_product)
            Price.objects.create(product=new_product, price=product_data['price_element'])
            return HttpResponseRedirect(reverse('price_checker:all_price_list'))
        else:
            return HttpResponseBadRequest('Так себе ссылка')
    else:
        product_form = ProductForm()
        db_products = Product.objects.filter(enabled=True)
        paginator = Paginator(db_products, 10)
        page_number = request.GET.get('page', 1)
        db_products_page = paginator.get_page(page_number)
        page_number = db_products_page.number #исключение обработано строкой выше, а вот тип может быть строкой итд, поэтому беру номер еще раз уже из готового объекта класса Page
        number_of_pages = paginator.num_pages
        if page_number - 3 < 1:
            lowest_page = 1
        else:
            lowest_page = page_number - 3
        if page_number + 3 > number_of_pages:
            highest_page = number_of_pages
        else:
            highest_page = page_number + 3
        page_range = list(range(lowest_page, highest_page+1))
        return render(request, 'price_checker/index.html', context={'form': product_form, 
                                                                    'db_products_page': db_products_page,
                                                                    'page_range': page_range})




def price_history(request, id):
    '''Функция для открытия истории цены конкретного продукта'''
    product_to_watch = get_object_or_404(Product, id=id)
    prices_of_product = Price.objects.filter(product_id=id)
    dates = []
    prices = []
    for elem in prices_of_product:
        dates.append(elem.added_time)
        prices.append(elem.price)
    plot_price_history(dates, prices)
    return render(request, 'price_checker/price_history.html', context={'product_to_watch': product_to_watch, 
                                                                        'prices_of_product': prices_of_product})


def delete_product(request, id):
    '''Функция представления для удаления конкретного продукта'''
    Product.objects.get(id=id).delete()
    return HttpResponseRedirect(reverse('price_checker:all_price_list'))



def delete_price(request, id):
    '''Функция представления для удаления цены конкретного продукта'''
    product_to_redirect = Price.objects.get(id=id).product
    id_of_product = product_to_redirect.id
    Price.objects.get(id=id).delete()
    return HttpResponseRedirect(reverse('price_checker:price_history', args=[id_of_product]))

# def update_prices(request):
#     asyncio.create_task(process_sites())

@time_count
def update_prices(request):
    '''Функция представления для запуска обновления цен'''
    p_u = PriceUpdater()
    p_u.run()
    del p_u
    return HttpResponseRedirect(reverse('price_checker:all_price_list'))
