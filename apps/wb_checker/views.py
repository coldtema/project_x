from django.shortcuts import render
from django.urls import reverse
from .forms import WBProductForm, WBDestForm
from django.http import HttpResponseRedirect, HttpResponse
from .models import WBBrand, WBPrice, WBProduct, WBSeller, WBCategory, WBDetailedInfo, WBMenuCategory
from apps.blog.models import Author
from .utils import time_count
from apps.wb_checker import wb_menu_categories, wb_products, wb_brands, wb_sellers, wb_pickpoints
from django.db import transaction
import apps.wb_checker.utils as utils
import re


def all_price_list(request):
    '''Temp view-функция для представления начальной страницы wb_checker'a'''
    form_parse = WBProductForm()
    form_get_dest = WBDestForm()
    author_id = 4 #пока не знаю, как точно передавать author_id в функцию, но это как-то через аунтефикацию надо делать (пока эмулирую)
            #проверяем поле action_type, чтобы понять какую функцию юзать (можно как альтернативу сделать regex's по урлу, но пока проще так)
    if request.method == 'POST':
        form = WBProductForm(request.POST)
        if form.is_valid():
            author_object = Author.objects.get(pk=author_id)
            url_dispatcher(request.POST['url'], author_object)
            return HttpResponseRedirect(reverse('all_price_list'))
        elif WBDestForm(request.POST).is_valid():
                author_object = Author.objects.get(pk=author_id)
                author_object.dest_id, author_object.dest_name = wb_pickpoints.get_dest(request.POST['address'])    
                author_object.save()

    return render(request, 'index.html', context={'form_parse': form_parse, 'form_get_dest':form_get_dest})


def clear_db(request):
    '''Полная очистка таблиц, связанных с вб'''
    authors = Author.objects.all()
    WBPrice.objects.all().delete()
    WBProduct.objects.all().delete()
    WBSeller.objects.all().delete()
    WBBrand.objects.all().delete()
    WBDetailedInfo.objects.all().delete()
    return HttpResponseRedirect(reverse('all_price_list'))


@utils.time_count
@transaction.atomic
def update_brands_categories(request):
    '''Обновление slug - категорий для брендов и селлеров из общей базы wb'''
    new_categories_list = []
    WBCategory.objects.all().delete()
    data = utils.update_categories()
    for elem in data:
        new_categories_list.append(WBCategory(wb_id=elem[0], url=elem[1]))
    WBCategory.objects.bulk_create(new_categories_list)
    return HttpResponseRedirect(reverse('all_price_list'))



@utils.time_count
@transaction.atomic
def update_menu_categories(request):
    '''Обновление категорий общего меню wb'''
    all_categories_list = []
    data = utils.update_menu_categories()
    for elem in data:
        all_categories_list.append(WBMenuCategory(wb_id=elem[0], main_url=elem[1], shard_key=elem[2], name=elem[3], query=elem[4]))
    WBMenuCategory.objects.bulk_create(all_categories_list, ignore_conflicts=True)
    return HttpResponseRedirect(reverse('all_price_list'))




@utils.time_count
def update_prices(request):
    '''Обновление цен на продукты и их наличия'''
    utils.PriceUpdater().run()
    return HttpResponseRedirect(reverse('all_price_list'))


@utils.time_count
def url_dispatcher(url, author_object):
    '''Функция разведения по разным модулям парсинга исходя из введенного текста'''
    if re.search(pattern=r'catalog\/\d+\/detail', string=url):
        product = wb_products.Product(url, author_object)
        product.get_product_info()
        del product
    elif re.search(pattern=r'\/(seller)\/', string=url):
        seller = wb_sellers.Seller(url, author_object)
        seller.run()
        del seller
    elif re.search(pattern=r'\/(brands)\/', string=url):
        brand = wb_brands.Brand(url, author_object)
        brand.run()
        del brand
    elif re.search(pattern=r'catalog\/\D+\/', string=url):
        menu_category = wb_menu_categories.MenuCategory(url, author_object)
        menu_category.run()
        del menu_category



@utils.time_count
def update_avaliability(request):
    '''Проверка наличия продуктов, которых не было в наличии'''
    utils.AvaliabilityUpdater().run()
    return HttpResponseRedirect(reverse('all_price_list'))



@utils.time_count
def load_test_data(request):
    # author_object = Author.objects.get(pk=4)
    # with open('wb_links.txt', 'r', encoding='utf-8') as file:
    #     links_list = file.read().split('\n')
    #     for link in links_list:
    #         product = wb_products.Product(link, author_object)
    #         product.get_product_info()
    #         del product
    all_cats = WBMenuCategory.objects.all()
    author_object = Author.objects.get(pk=4)
    for elem in all_cats:
        url = 'https://www.wildberries.ru' + elem.main_url
        if elem.shard_key != 'blackhole':
            menu_category = wb_menu_categories.MenuCategory(url, author_object)
            menu_category.run()
            del menu_category
            

