import math
import time
from functools import wraps
from .models import WBBrand, WBSeller, WBProduct, WBPrice
import cloudscraper
import json
from django.utils import timezone
from django.db import transaction
from collections import Counter


def time_count(func):
    '''Декоратор определения времени работы функции'''
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f'{func.__doc__} - {end - start}')
        return result
    return wrapper


def check_repetitions_catalog(product_artikul_to_check, potential_repetitions):
    '''Простая функция на проверку повторок в кэше процесса парсинга'''
    if product_artikul_to_check in potential_repetitions.keys():
        return potential_repetitions[product_artikul_to_check]


#проверяю на наличие бренда и продавца в БД (возможно можно как то засунуть в одну атомарную транзакцию, чтобы не обращаться к БД для создания несуществующего бренда/селлера)
#Вторым параметром передаю, был ли бренд/селлер уже в бд или нет
def check_existence_of_brand(brand_name, brand_artikul):
    '''Проверка бренда на наличие в БД (аналог get or create, 
    только еще отдается был ли бренд в бд до этого или нет)'''
    with transaction.atomic():
        brand_object = WBBrand.objects.update_or_create(wb_id=brand_artikul, defaults={'name':brand_name,
                                                                                    'main_url':f'https://www.wildberries.ru/brands/{brand_artikul}',
                                                                                    'full_control':False}) #true - создан, false - обновлен
    return brand_object[0], brand_object[1]


def check_existence_of_seller(seller_name, seller_artikul):
    '''Проверка селлера на наличие в БД (аналог get or create, 
    только еще отдается был ли бренд в бд до этого или нет)'''
    with transaction.atomic():
        seller_object = WBSeller.objects.update_or_create(wb_id=seller_artikul, defaults={'name':seller_name,
                                                                                    'main_url':f'https://www.wildberries.ru/brands/{seller_artikul}',
                                                                                    'full_control':False})
    return seller_object[0], seller_object[1]

def update_categories():
    '''Обновление базы категорий от самого wb (не кастомные бренда, а именно база wb)'''
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




class PriceUpdater:
    def __init__(self):
        self.product_url_api = f'https://card.wb.ru/cards/v2/list?appType=1&curr=rub&dest=-1257786&spp=30&ab_testing=false&lang=ru&nm='
        self.detail_product_url_api = 'https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest=123589280&hide_dtype=13&spp=30&ab_testing=false&lang=ru&nm='
        self.scraper = cloudscraper.create_scraper()
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.all_prods = tuple(WBProduct.enabled_products.all())
        self.all_prods_artikuls = tuple(map(lambda x: str(x.artikul), self.all_prods))
        self.dict_all_prods = dict(zip(self.all_prods_artikuls, self.all_prods))
        self.potential_disabled_products = []
        self.potential_disabled_products_artikuls = []
        self.disabled_products = []
        self.updated_prods = []
        self.updated_prices = []


    def run(self):
        self.update_prices()     
        self.check_disabled_prods()
        self.save_update_prices()


    @time_count
    def update_prices(self):
        '''Обновление цен всей БД'''
        #максимум в листе 512 элементов
        updated_info = []
        for i in range(math.ceil(len(self.all_prods) / 512)):
            print(i)
            temp_prods_artikuls_from_db = tuple(self.all_prods_artikuls[512*i:512*(i+1)])
            final_url = self.product_url_api + ';'.join(temp_prods_artikuls_from_db)
            response = self.scraper.get(final_url, headers=self.headers)
            json_data = json.loads(response.text)
            products_on_page = json_data['data']['products']
            enabled_products_artikuls = []
            for j in range(len(products_on_page)):
                product_artikul = products_on_page[j]['id']
                product_price = products_on_page[j]['sizes'][0]['price']['product'] // 100
                product_to_check = self.dict_all_prods[str(product_artikul)]
                enabled_products_artikuls.append(str(product_artikul))
                if product_to_check.latest_price != product_price: #проверить на всякий случай на типы здесь
                    updated_info.append(f'''Цена изменилась!
Продукт: {product_to_check.url}
Было: {product_to_check.latest_price}
Стало: {product_price}
Время:{timezone.now()}

''')
                    product_to_check.latest_price = product_price
                    self.updated_prods.append(product_to_check)
                    self.updated_prices.append(WBPrice(price=product_price,
                            added_time=timezone.now(),
                            product=product_to_check)) 
                #сверяем количество полученных продуктов и переданных продуктов
            if len(enabled_products_artikuls) != len(temp_prods_artikuls_from_db):
                self.potential_disabled_products_artikuls.extend(set(temp_prods_artikuls_from_db) - set(enabled_products_artikuls))        
        self.potential_disabled_products = list(map(lambda x: self.dict_all_prods[x], self.potential_disabled_products_artikuls))
        with open('updated_info.txt', 'w', encoding='utf-8') as file:
            file.write(''.join(updated_info))


    def check_disabled_prods(self):
        if len(self.potential_disabled_products_artikuls) != 0:
            final_url = self.detail_product_url_api + ';'.join(self.potential_disabled_products_artikuls)
            print(final_url)
            response = self.scraper.get(final_url, headers=self.headers)
            json_data = json.loads(response.text)
            products_on_page = json_data['data']['products']
            for i in range(len(products_on_page)):
                try:
                    product_artikul = products_on_page[i]['id']
                    product_price = products_on_page[i]['sizes'][0]['price']['product'] // 100
                    product_to_check = self.dict_all_prods[str(product_artikul)]
                    if product_to_check.latest_price != product_price: #проверить на всякий случай на типы здесь
                        product_to_check.latest_price = product_price
                        self.updated_prods.append(product_to_check)
                        self.updated_prices.append(WBPrice(price=product_price,
                                added_time=timezone.now(),
                                product=product_to_check)) 
                except:
                    self.potential_disabled_products[i].enabled = False
                    self.disabled_products.append(self.potential_disabled_products[i])


    @time_count
    @transaction.atomic
    def save_update_prices(self):
        '''Занесение в БД обновления всех цен'''
        WBProduct.objects.bulk_update(self.updated_prods, ['latest_price'])
        WBPrice.objects.bulk_create(self.updated_prices)
        WBProduct.objects.bulk_update(self.disabled_products, ['enabled'])



#добавить функцию, если dest не прошел на мск + если dest не прошел на list

