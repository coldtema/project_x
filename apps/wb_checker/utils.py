import math
import time
from functools import wraps
from .models import WBBrand, WBSeller, WBProduct, WBPrice
import cloudscraper
import json
from django.utils import timezone
from django.db import transaction


def time_count(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f'{func.__doc__} - {end - start}')
        return result
    return wrapper


def check_repetitions_catalog(product_artikul_to_check, potential_repetitions):
    if str(product_artikul_to_check) in potential_repetitions.keys():
        return potential_repetitions[str(product_artikul_to_check)]


#проверяю на наличие бренда и продавца в БД (возможно можно как то засунуть в одну атомарную транзакцию, чтобы не обращаться к БД для создания несуществующего бренда/селлера)
#Вторым параметром передаю, был ли бренд/селлер уже в бд или нет
def check_existence_of_brand(brand_name, brand_artikul):
    brand_existence = WBBrand.objects.filter(wb_id=brand_artikul)
    if not brand_existence:
        brand_object = (WBBrand.objects.create(name=brand_name,
                               wb_id=brand_artikul,
                               main_url=f'https://www.wildberries.ru/brands/{brand_artikul}',
                               full_control = False), False)
    else:
        brand_object = (brand_existence[0], True)
    return brand_object


def check_existence_of_seller(seller_name, seller_artikul):
    seller_existence = WBSeller.objects.filter(wb_id=seller_artikul)
    if not seller_existence:
        seller_object = (WBSeller.objects.create(name=seller_name,
                               wb_id=seller_artikul,
                               main_url=f'https://www.wildberries.ru/brands/{seller_artikul}',
                               full_control = False), False)
    else:
        seller_object = (seller_existence[0], True)
    return seller_object

def update_categories():
    categories_list = []
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    final_url = f'https://static-basket-01.wbbasket.ru/vol0/data/subject-base.json'
    response = scraper.get(final_url, headers=headers)
    json_data = json.loads(response.text)
    def wrapper(json_data):
        for elem in json_data:
            if type(elem) == dict and 'childs' not in elem.keys():
                categories_list.append((elem['id'], elem['url']))
            elif type(elem) == dict and 'childs' in elem.keys():
                categories_list.append((elem['id'], elem['url']))
                wrapper(elem['childs'])
        return categories_list
    return wrapper(json_data)

@transaction.atomic
def save_update_prices(updated_prods, updated_prices):
    WBProduct.objects.bulk_update(updated_prods, ['latest_price'])
    WBPrice.objects.bulk_create(updated_prices)



def update_prices():
    product_url_api = f'https://card.wb.ru/cards/v2/list?appType=1&curr=rub&dest=-1257786&spp=30&ab_testing=false&lang=ru&nm='
    #получает все продукиы в виде артикул:продукт
    all_prods = list(WBProduct.enabled_products.all())
    all_prods_artikuls = list(map(lambda x: x.artikul, WBProduct.enabled_products.all()))
    updated_prods = []
    updated_prices = []
    #максимум в листе 512 элементов
    for i in range(math.ceil(len(all_prods) / 512)):
        temp_prods_from_db = list(map(lambda x: x.artikul, all_prods[512*i:512*(i+1)]))
        final_url = product_url_api + ';'.join(temp_prods_from_db)
        headers = {"User-Agent": "Mozilla/5.0"}
        scraper = cloudscraper.create_scraper()
        response = scraper.get(final_url, headers=headers)
        json_data = json.loads(response.text)
        products_on_page = json_data['data']['products']
        for j in range(len(products_on_page)):
            product_artikul = products_on_page[j]['id']
            product_price = products_on_page[j]['sizes'][0]['price']['product'] // 100
            if str(product_artikul) in all_prods_artikuls:
                product_to_check = all_prods[all_prods_artikuls.index(str(product_artikul))]
                if product_to_check.latest_price != product_price: #проверить на всякий случай на типы здесь
                    product_to_check.latest_price = product_price
                    updated_prods.append(product_to_check)
                    updated_prices.append(WBPrice(price=product_price,
                            added_time=timezone.now(),
                            product=product_to_check))
        #сверяем количество полученных продуктов и переданных продуктов
        if len(products_on_page) != len(temp_prods_from_db):
            # check_disabled_prods()
            ...
    save_update_prices(updated_prods, updated_prices)




