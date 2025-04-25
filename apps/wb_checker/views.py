from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect
from apps.blog.models import Author
from apps.wb_checker.utils.general_utils import time_count
from apps.wb_checker.utils.pickpoints import load_dest_to_author
from apps.wb_checker.utils.single_prods import PriceUpdater, AvaliabilityUpdater
from apps.wb_checker.utils.categories import update_menu_cats
from apps.wb_checker.utils.top_prods import UpdaterInfoOfTop
from apps.wb_checker import wb_menu_categories, wb_products, wb_brands, wb_sellers
from .forms import WBProductForm, WBDestForm
from .models import WBBrand, WBSeller, TopWBProduct
import re


def all_price_list(request):
    '''Temp view-функция для представления начальной страницы wb_checker'a'''
    form_parse = WBProductForm()
    form_get_dest = WBDestForm()
    author_id = 2 #пока не знаю, как точно передавать author_id в функцию, но это как-то через аунтефикацию надо делать (пока эмулирую)
    if request.method == 'POST':
        form = WBProductForm(request.POST)
        if form.is_valid():
            author_object = Author.objects.get(pk=author_id)
            url_dispatcher(request.POST['url'], author_object)
            return HttpResponseRedirect(reverse('wb_checker:all_price_list'))
        elif WBDestForm(request.POST).is_valid():
            load_dest_to_author(author_id, request.POST['address'])
    return render(request, 'index.html', context={'form_parse': form_parse, 'form_get_dest':form_get_dest})



def clear_db(request):
    '''Полная очистка таблиц, связанных с вб'''
    WBSeller.objects.all().delete()
    WBBrand.objects.all().delete()
    TopWBProduct.objects.all().delete()
    return HttpResponseRedirect(reverse('wb_checker:all_price_list'))



@time_count
def update_menu_categories(request):
    '''Обновление категорий общего меню wb'''
    update_menu_cats()
    return HttpResponseRedirect(reverse('wb_checker:all_price_list'))



@time_count
def update_prices(request):
    '''Обновление цен на продукты и их наличия'''
    price_updater = PriceUpdater()
    price_updater.run()
    del price_updater
    return HttpResponseRedirect(reverse('wb_checker:all_price_list'))



@time_count
def update_avaliability(request):
    '''Проверка наличия продуктов, которых не было в наличии'''
    avaliability_updater = AvaliabilityUpdater()
    avaliability_updater.run()
    del avaliability_updater
    return HttpResponseRedirect(reverse('wb_checker:all_price_list'))



@time_count
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
    elif re.search(pattern=r'catalog\/\D+\/?', string=url):
        menu_category = wb_menu_categories.MenuCategory(url, author_object)
        menu_category.run()
        del menu_category
            



@time_count
def update_top_prods(request):
    # author_object = Author.objects.get(pk=4)
    # with open('wb_links.txt', 'r', encoding='utf-8') as file:
    #     links_list = file.read().split('\n')
    #     for link in links_list:
    #         product = wb_products.Product(link, author_object)
    #         product.get_product_info()
    #         del product
    wb_brands.TopWBProductBrandUpdater().run()
    wb_sellers.TopWBProductSellerUpdater().run()
    wb_menu_categories.TopWBProductMenuCategoryUpdater().run()
    # all_cats = WBMenuCategory.objects.all()
    # author_object = Author.objects.get(pk=4)
    # for elem in all_cats:
    #     url = 'https://www.wildberries.ru' + elem.main_url
    #     if elem.shard_key != 'blackhole':
    #         menu_category = wb_menu_categories.MenuCategory(url, author_object)
    #         menu_category.run()
    #         del menu_category
    return HttpResponseRedirect(reverse('wb_checker:all_price_list'))




@time_count
def update_top_prods_info(request):
    updater_info_of_top = UpdaterInfoOfTop()
    updater_info_of_top.run()
    del updater_info_of_top
    return HttpResponseRedirect(reverse('wb_checker:all_price_list'))