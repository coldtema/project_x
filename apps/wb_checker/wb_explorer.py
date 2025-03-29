import os
import psutil
from requests import request
import re
import json
import cloudscraper
from datetime import datetime
import apps.wb_checker.backend_explorer as backend_explorer
from .models import WBProduct, WBSeller, WBBrand, WBPrice
from apps.blog.models import Author
from django.utils import timezone
import math
import time
from functools import wraps

#отслеживание цены
#https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest=-1257786&hide_dtype=10&spp=30&ab_testing=false&lang=ru&nm=
#https://card.wb.ru/cards/v2/list?appType=1&curr=rub&dest=-1257786&spp=30&ab_testing=false&lang=ru&nm=

def time_count(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(end - start)
        return result
    return wrapper



def get_product_info(product_url, author_id):
    #полностью собирает элемент
    artikul = re.search(r'\/(\d+)\/', product_url).group(1)
    product_url_api = f'https://card.wb.ru/cards/v2/list?appType=1&curr=rub&dest=-1257786&spp=30&ab_testing=false&lang=ru&nm={artikul}'
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url_api, headers=headers)
    json_data = json.loads(response.text)
    name = json_data['data']['products'][0]['name']
    price_element = json_data['data']['products'][0]['sizes'][0]['price']['product'] // 100
    try: #если вдруг истории цены нет
        price_history = get_price_history(product_url)
        price_history = list(map(lambda x: (timezone.make_aware(datetime.fromtimestamp(x['dt'])), x['price']['RUB']//100), price_history))
        price_history.append((timezone.now(), price_element))
    except:
        price_history = [(timezone.now(), price_element)]
    seller_name = json_data['data']['products'][0]['supplier'] #имя продавца
    seller_id = json_data['data']['products'][0]['supplierId'] #id продавца
    brand_name = json_data['data']['products'][0]['brand'] #имя бренда
    brand_id = json_data['data']['products'][0]['brandId'] #id бренда
    #проверяет наличие этого бренда и продавца в БД (если нет, то создает их, если есть - не трогает)
    seller_dict = {'seller_name': seller_name, 'seller_id': seller_id}
    brand_dict = {'brand_name': brand_name, 'brand_id': brand_id}
    backend_explorer.check_existence_of_brand(brand_dict=brand_dict)
    backend_explorer.check_existence_of_seller(seller_dict=seller_dict)
    #добавляем элемент
    new_product = WBProduct.objects.create(name=name,
            artikul=artikul,
            latest_price=price_element,
            wb_cosh=True,
            url=product_url,
            enabled=True,
            seller=WBSeller.objects.get(wb_id=seller_id),
            brand=WBBrand.objects.get(wb_id=brand_id))
    #добавляем many-to-many связь (почему то через автора всегда быстрее)
    Author.objects.get(id=author_id).wbproduct_set.add(new_product)
    #добавляем все прайсы
    price_history = list(map(lambda x: WBPrice(price=x[1], added_time=x[0], product=new_product), price_history))
    WBPrice.objects.bulk_create(price_history)




# if 201850 in promotions or 201858 in promotions:  # промо - вычислял по каунтеру промо (большая выборка)
#     wb_cosh = True


#js скрипт на wb для определения сервера
def get_basket_num(artikul: int):
    s = artikul // 100000  # Разделение артикулов на группы
    if s <= 143:
        return 1
    elif s <= 287:
        return 2
    elif s <= 431:
        return 3
    elif s <= 719:
        return 4
    elif s <= 1007:
        return 5
    elif s <= 1061:
        return 6
    elif s <= 1115:
        return 7
    elif s <= 1169:
        return 8
    elif s <= 1313:
        return 9
    elif s <= 1601:
        return 10
    elif s <= 1655:
        return 11
    elif s <= 1919:
        return 12
    elif s <= 2045:
        return 13
    elif s <= 2189:
        return 14
    elif s <= 2405:
        return 15
    elif s <= 2621:
        return 16
    elif s <= 2837:
        return 17
    elif s <= 3053:
        return 18
    elif s <= 3269:
        return 19
    elif s <= 3485:
        return 20
    elif s <= 3701:
        return 21
    elif s <= 3917:
        return 22
    elif s <= 4133:
        return 23
    elif s <= 4349:
        return 24
    elif s <= 4565:
        return 25
    else:
        return 26
    

def get_price_history(product_url):
    artikul = (re.search(r'\/(\d+)\/', product_url).group(1))
    basket_num = get_basket_num(int(artikul))
    if basket_num < 10:
        basket_num = f'0{basket_num}'
    if len(artikul) == 9:
        price_history_searcher_url = f'https://basket-{basket_num}.wbbasket.ru/vol{artikul[:4]}/part{artikul[:6]}/{artikul}/info/price-history.json'
    else:
        price_history_searcher_url = f'https://basket-{basket_num}.wbbasket.ru/vol{artikul[:3]}/part{artikul[:5]}/{artikul}/info/price-history.json'
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(price_history_searcher_url, headers=headers)
    json_data = json.loads(response.text)
    return json_data




def get_product_info_seller_catalog(author_id, product_in_catalog, brand_object, seller_object):
    #полностью собирает элемент
    artikul = product_in_catalog['id']
    product_url = f'https://www.wildberries.ru/catalog/{artikul}/detail.aspx'
    name = product_in_catalog['name'] #имя продукта в каталоге
    price_element = product_in_catalog['sizes'][0]['price']['product'] // 100
    #добавляем объект продукта
    new_product = WBProduct(name=name,
            artikul=artikul,
            latest_price=price_element,
            wb_cosh=True,
            url=product_url,
            enabled=True,
            seller=seller_object,
            brand=brand_object)
    #добавляем объект прайса
    new_product_price = WBPrice(price=price_element,
                               added_time=timezone.now(),
                               product=new_product)
    return new_product, new_product_price



#!!!максимальное количество товаров - 10к, дальше вб сам не отдает их
#https://www.wildberries.ru/seller/simaland-35167
@time_count
def get_catalog_of_seller(seller_url, author_id, potential_repetitions):
    process = psutil.Process(os.getpid())
    print(f"Используется памяти: {process.memory_info().rss / 1024 ** 2:.2f} MB")
    #кэш на проверку брендов в виде wb_id брендов
    brands_to_add = []
    brands_wb_ids_to_add = []
    brand_object = ''
    brands_in_db = list(WBBrand.objects.all())
    brand_wb_id_in_db = list(map(lambda x: x.wb_id, brands_in_db))
    #конструирует url
    addons = re.search(r'(page\=\d+?)(\&.+)', seller_url) #посмотреть немного на измененный regex
    sorting = re.search(r'\&(sort)\=(.+?)\&', seller_url)
    seller_artikul = backend_explorer.get_seller_artikul(seller_url) #еще понаблюдать
    if not addons: addons = ''
    else: addons = addons.group(2)
    if not sorting: sorting = 'popular'
    else: sorting = sorting.group(2)
    final_url = f'https://catalog.wb.ru/sellers/v2/catalog?ab_testing=false&appType=1&curr=rub&dest=-1257786&hide_dtype=13&lang=ru&page={1}&sort={sorting}&spp=30&supplier={seller_artikul}&uclusters=0{addons}'
    #делает первый запрос для определения количества продуктов (total) + определение количества страниц для полного отображения каталога (продуктов на странице - 100!!)
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(final_url, headers=headers)
    json_data = json.loads(response.text)
    total_products = json_data['data']['total']
    number_of_pages = math.ceil(total_products/100)
    if number_of_pages > 100:
        number_of_pages = 100
    #проверяет наличие продавца в БД
    seller_name = json_data['data']['products'][0]['supplier']
    backend_explorer.check_existence_of_seller(seller_dict={'seller_id':seller_artikul, 'seller_name':seller_name})
    seller_object = WBSeller.objects.get(wb_id=seller_artikul)
    all_products = []
    all_prices = []
    repetitions_list = []
    for elem in range(1, number_of_pages + 1):
        final_url = f'https://catalog.wb.ru/sellers/v2/catalog?ab_testing=false&appType=1&curr=rub&dest=-1257786&hide_dtype=13&lang=ru&page={elem}&sort={sorting}&spp=30&supplier={seller_artikul   }&uclusters=0{addons}'
        response = scraper.get(final_url, headers=headers)
        try:
            json_data = json.loads(response.text)
        except:
            continue
        products_on_page = json_data['data']['products']
        for i in range(len(products_on_page)):
            #специально получаю артикул для того, чтобы передать в функцию проверки на повторки
            if potential_repetitions:
                product_artikul = products_on_page[i]['id']
                potential_repetition = backend_explorer.check_repetitions_catalog(product_artikul, potential_repetitions)
                if potential_repetition:
                    repetitions_list.append(potential_repetition)
                    continue
            #проверка бренда на наличие в БД плюс откладывание его в кэш (только бренд, тк селлер уже в базе)
            brand_id = products_on_page[i]['brandId']
            if brand_id not in brand_wb_id_in_db:
                if brand_id == 0:
                    brand_object = WBBrand(name='Без бренда',
                               wb_id=products_on_page[i]['brandId'],
                               main_url=f'https://www.wildberries.ru/',
                               full_control = False)
                else:
                    brand_dict = {'brand_name': products_on_page[i]['brand'], 'brand_id': brand_id}
                    brand_object = WBBrand(name=products_on_page[i]['brand'],
                                wb_id=products_on_page[i]['brandId'],
                                main_url=f'https://www.wildberries.ru/brands/{brand_dict['brand_id']}',
                                full_control = False)
                brands_to_add.append(brand_object)
                brands_in_db.append(brand_object)
                brand_wb_id_in_db.append(brand_id)
            else:
                # print(brand_id)
                # print(brand_wb_id_in_db)
                # print(brand_wb_id_in_db.index(brand_id))
                brand_object = brands_in_db[brand_wb_id_in_db.index(brand_id)]
            new_product, new_product_price = get_product_info_seller_catalog(author_id=author_id, product_in_catalog=products_on_page[i], brand_object=brand_object, seller_object=seller_object)
            all_products.append(new_product)
            all_prices.append(new_product_price)
    process = psutil.Process(os.getpid())
    print(f"Используется памяти: {process.memory_info().rss / 1024 ** 2:.2f} MB")
    WBBrand.objects.bulk_create(brands_to_add)
    WBProduct.objects.bulk_create(all_products) #добавляю элементы одной командой
    WBPrice.objects.bulk_create(all_prices) #добавляю элементы одной командой
    all_products.extend(repetitions_list)
    Author.objects.get(id=author_id).wbproduct_set.set(all_products) #many-to-many связь через автора (вставляется сразу все)




#https://www.wildberries.ru/seller/simaland-35167
def get_catalog_of_brand(brand_url, author_id, potential_repetitions):
    ...
#     #конструирует url
#     brand_artikul = backend_explorer.get_brand_artikul()
#     addons = re.search(r'(page\=1)(\&.+)', brand_url)
#     sorting = re.search(r'\&(sort)\=(.+?)\&', brand_url)
#     if not addons: addons = ''
#     else: addons = addons.group(2)
#     if not sorting: sorting = 'popular'
#     else: sorting = sorting.group(2)
#     final_url = f'https://catalog.wb.ru/sellers/v2/catalog?ab_testing=false&appType=1&curr=rub&dest=-1257786&hide_dtype=13&lang=ru&page={1}&sort={sorting}&spp=30&supplier={seller_artikul}&uclusters=0{addons}'
#     #делает первый запрос для определения количества продуктов (total) + определение количества страниц для полного отображения каталога (продуктов на странице - 100!!)
#     print(final_url)
#     headers = {"User-Agent": "Mozilla/5.0"}
#     scraper = cloudscraper.create_scraper()
#     response = scraper.get(final_url, headers=headers)
#     json_data = json.loads(response.text)
#     total_products = json_data['data']['total']
#     number_of_pages = math.ceil(total_products/100)
#     #проверяет наличие продавца в БД
#     seller_name = json_data['data']['products'][0]['supplier']
#     backend_explorer.check_existence_of_seller(seller_dict={'seller_id':seller_id, 'seller_name':seller_name})
#     all_products = []
#     all_prices = []
#     repetitions_list = []
#     for elem in range(1, number_of_pages + 1):
#         final_url = f'https://catalog.wb.ru/sellers/v2/catalog?ab_testing=false&appType=1&curr=rub&dest=-1257786&hide_dtype=13&lang=ru&page={elem}&sort={sorting}&spp=30&supplier={seller_id}&uclusters=0{addons}'
#         response = scraper.get(final_url, headers=headers)
#         json_data = json.loads(response.text)
#         products_on_page = json_data['data']['products']
#         for i in range(len(products_on_page)):
#             #специально получаю артикул для того, чтобы передать в функцию проверки на повторки
#             if potential_repetitions:
#                 product_artikul = products_on_page[i]['id']
#                 potential_repetition = backend_explorer.check_repetitions_catalog(product_artikul, potential_repetitions)
#                 if potential_repetition:
#                     repetitions_list.append(potential_repetition)
#                     continue
#             new_product, new_product_price = get_product_info_seller_catalog(author_id=author_id, product_in_catalog=products_on_page[i])
#             all_products.append(new_product)
#             all_prices.append(new_product_price)
#     WBProduct.objects.bulk_create(all_products) #добавляю элементы одной командой
#     WBPrice.objects.bulk_create(all_prices) #добавляю элементы одной командой
#     all_products.extend(repetitions_list)
#     Author.objects.get(id=author_id).wbproduct_set.set(all_products) #many-to-many связь через автора (вставляется сразу все)



#изменения:
#1. перенес функцию получения артикула селлера в backend explorer
#2. теперь еще передаю potential repetitions в get catalog of seller
#3. проверяю внутри цикла на потенциальную повторюшку
#4. прибавляю повторюшки, если они есть к добавлению many-to-many связи
#5. думаю разнести все по папкам по типу wb_explorer_seller/product/brand (еще подумать, как разнести грамотно)
#6. изменил немного regex для addonov
#7. перенес получение артикула селлера в отдельную функцию (полный процесс)
#8. вынести функцию конструкции url в отдельную