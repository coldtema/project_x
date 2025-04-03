from django.shortcuts import render
from django.urls import reverse
from .forms import WBProductForm, WBDestForm
from django.http import HttpResponseRedirect, HttpResponse
from .models import WBBrand, WBPrice, WBProduct, WBSeller, WBCategory, WBPromotion
from apps.blog.models import Author
from .utils import time_count
from apps.wb_checker import wb_products, wb_brands, wb_sellers, wb_promos, wb_pickpoints
from django.db import transaction
import apps.wb_checker.utils as utils


def all_price_list(request):
    form_parse = WBProductForm()
    form_get_dest = WBDestForm()
    author_id = 4 #пока не знаю, как точно передавать author_id в функцию, но это как-то через аунтефикацию надо делать (пока эмулирую)
            #проверяем поле action_type, чтобы понять какую функцию юзать (можно как альтернативу сделать regex's по урлу, но пока проще так)
    if request.method == 'POST':
        form = WBProductForm(request.POST)
        if form.is_valid():
            author_object = Author.objects.get(pk=author_id)
            action_type=request.POST['action_type']
            if action_type == 'product':
                product = wb_products.Product(request.POST['url'], author_object)
                product.get_repetition_or_run()
                del product
            elif action_type == 'seller':
                seller = wb_sellers.Seller(request.POST['url'], author_object)
                seller.run()
                del seller
            elif action_type == 'brand':
                brand = wb_brands.Brand(request.POST['url'], author_object)
                brand.run()
                del brand
            elif action_type == 'promo':
                promo = wb_promos.Promo(request.POST['url'], author_object)
                promo.run()
                del promo
            return HttpResponseRedirect(reverse('all_price_list'))
        elif WBDestForm(request.POST).is_valid():
                author_object = Author.objects.get(pk=author_id)
                author_object.dest_id, author_object.dest_name = wb_pickpoints.get_dest(request.POST['address'])    
                author_object.save()

    return render(request, 'index.html', context={'form_parse': form_parse, 'form_get_dest':form_get_dest})


def clear_db(request):
    '''Полная очистка таблиц, связанных с вб'''
    authors = Author.objects.all()
    for author in authors:
        author.wbproduct_set.all().delete()
    WBPrice.objects.all().delete()
    WBProduct.objects.all().delete()
    WBSeller.objects.all().delete()
    WBBrand.objects.all().delete()
    WBPromotion.objects.all().delete()
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
def update_prices(request):
    '''Обновление цен на продукты'''
    utils.PriceUpdater().run()
    return HttpResponseRedirect(reverse('all_price_list'))

