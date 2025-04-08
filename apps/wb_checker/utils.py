import math
import time
from functools import wraps
from .models import WBBrand, WBSeller, WBProduct, WBPrice
import cloudscraper
import json
from django.utils import timezone
from django.db import transaction
from collections import Counter
from apps.blog.models import Author


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
        '''Инициализация необходимых атрибутов'''
        self.all_authors_list = Author.objects.all().prefetch_related('enabled_connection', 'disabled_connection')
        self.scraper = cloudscraper.create_scraper()
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.disabled_products_artikuls = []
        self.disabled_products = []
        self.updated_prods = []
        self.dict_update_avaliability = dict()
        self.updated_prices = []


    def run(self):
        '''Запуск скрипта обновления'''
        self.update_prices()     
        self.save_update_prices()


    @time_count
    def update_prices(self):
        '''Обновление цен всей БД'''
        #максимум в листе 512 элементов
        updated_info = []
        for i in range(len(self.all_authors_list)):
            author_object = self.all_authors_list[i]
            detail_product_url_api = f'https://card.wb.ru/cards/v2/list?appType=1&curr=rub&dest={author_object.dest_id}&spp=30&ab_testing=false&lang=ru&nm='
            author_prods_to_check = self.all_authors_list[i].enabled_connection.all()
            dict_author_prods_to_check = dict(map(lambda x: (str(x.artikul), x), author_prods_to_check))
            for i in range(math.ceil(len(author_prods_to_check) / 512)):
                print(i)
                temp_prods_artikuls_from_db = tuple(tuple(dict_author_prods_to_check.keys())[512*i:512*(i+1)])
                final_url = detail_product_url_api + ';'.join(temp_prods_artikuls_from_db)
                response = self.scraper.get(final_url, headers=self.headers)
                json_data = json.loads(response.text)
                products_on_page = json_data['data']['products']
                enabled_products_artikuls = []
                for j in range(len(products_on_page)):
                    product_artikul = products_on_page[j]['id']
                    product_price = products_on_page[j]['sizes'][0]['price']['product'] // 100
                    product_to_check = dict_author_prods_to_check[str(product_artikul)]
                    enabled_products_artikuls.append(str(product_artikul))
                    if product_to_check.latest_price != product_price: #проверить на всякий случай на типы здесь
                        updated_info.append(f'''Цена изменилась!
Автор: {author_object}
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
                        


                if len(enabled_products_artikuls) != len(temp_prods_artikuls_from_db):
                    self.disabled_products_artikuls.extend(set(temp_prods_artikuls_from_db) - set(enabled_products_artikuls))
                    self.disabled_products = list(map(lambda x: dict_author_prods_to_check[x], self.disabled_products_artikuls)) #получил продукты для автора, которых нет в наличии        
                    self.dict_update_avaliability.update({author_object: self.disabled_products})   

        with open('updated_info.txt', 'w', encoding='utf-8') as file:
            file.write(''.join(updated_info))

    @time_count
    @transaction.atomic
    def save_update_prices(self):
        '''Занесение в БД обновления всех цен'''
        WBProduct.objects.bulk_update(self.updated_prods, ['latest_price'])
        WBPrice.objects.bulk_create(self.updated_prices)
        for author_object, disabled_prods in self.dict_update_avaliability.items():
            author_object.enabled_connection.remove(*disabled_prods)
            author_object.disabled_connection.add(*disabled_prods)










class AvaliabilityUpdater:
    def __init__(self):
        '''Инициализация необходимых атрибутов'''
        self.all_authors_list = Author.objects.all().prefetch_related('enabled_connection', 'disabled_connection')
        self.scraper = cloudscraper.create_scraper()
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.updated_prods = []
        self.updated_enabled_prods = dict()
        self.updated_prices = []


    def run(self):
        '''Запуск скрипта обновления'''
        self.update_prices()     
        self.save_update_prices()


    @time_count
    def update_prices(self):
        '''Обновление наличия прподуктов, которых нет в наличии'''
        #максимум в листе 512 элементов
        updated_info = []
        for i in range(len(self.all_authors_list)):
            author_object = self.all_authors_list[i]
            detail_product_url_api = f'https://card.wb.ru/cards/v2/list?appType=1&curr=rub&dest={author_object.dest_id}&spp=30&ab_testing=false&lang=ru&nm='
            author_prods_to_check = self.all_authors_list[i].disabled_connection.all()
            dict_author_prods_to_check = dict(map(lambda x: (str(x.artikul), x), author_prods_to_check))
            self.updated_prods = []
            for i in range(math.ceil(len(author_prods_to_check) / 512)):
                print(i)
                temp_prods_artikuls_from_db = tuple(tuple(dict_author_prods_to_check.keys())[512*i:512*(i+1)])
                final_url = detail_product_url_api + ';'.join(temp_prods_artikuls_from_db)
                response = self.scraper.get(final_url, headers=self.headers)
                json_data = json.loads(response.text)
                products_on_page = json_data['data']['products']
                enabled_products_artikuls = []
                for j in range(len(products_on_page)):
                    product_artikul = products_on_page[j]['id']
                    product_price = products_on_page[j]['sizes'][0]['price']['total'] // 100
                    product_to_check = dict_author_prods_to_check[str(product_artikul)]
                    enabled_products_artikuls.append(str(product_artikul))
                    updated_info.append(f'''Продукт снова в наличии!
Автор: {author_object}
Продукт: {product_to_check.url}
Время:{timezone.now()}

''')
                    self.updated_prods.append(product_to_check)
                    if product_to_check.latest_price != product_price:
                        product_to_check.latest_price = product_price
                        self.updated_prices.append(WBPrice(price=product_price,
                                added_time=timezone.now(),
                                product=product_to_check))                        
            self.updated_enabled_prods.update({author_object: self.updated_prods})
        with open('updated_enabled.txt', 'w', encoding='utf-8') as file:
            file.write(''.join(updated_info))

    @time_count
    @transaction.atomic
    def save_update_prices(self):
        '''Занесение в БД обновления наличия'''
        WBProduct.objects.bulk_update(self.updated_prods, ['latest_price'])
        WBPrice.objects.bulk_create(self.updated_prices)
        for author_object, enabled_prods in self.updated_enabled_prods.items():
            author_object.enabled_connection.add(*enabled_prods)
            author_object.disabled_connection.remove(*enabled_prods)
        



#добавить функцию, если dest не прошел на мск

