import math
import time
from functools import wraps
from .models import WBBrand, WBSeller, WBProduct, WBPrice, WBDetailedInfo
import cloudscraper
import json
from django.utils import timezone
from django.db import transaction
from collections import Counter
from apps.blog.models import Author
from django.db.models import Prefetch


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
        self.all_authors_list = Author.objects.all().prefetch_related(Prefetch('wbdetailedinfo_set', 
                                                 queryset=WBDetailedInfo.objects.filter(enabled=True).select_related('product')))
        self.scraper = cloudscraper.create_scraper()
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.new_prices = []
        self.updated_details = []
        self.test_counter = 0


    def run(self):
        '''Запуск скрипта обновления'''
        self.update_prices()     
        self.save_update_prices()
        print(f'Товаров проверено:{self.test_counter}')


    @time_count
    def update_prices(self):
        '''Обновление цен продуктов, которые есть наличии'''
        for i in range(len(self.all_authors_list)):
            author_object = self.all_authors_list[i]
            detail_product_url_api = f'https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest={author_object.dest_id}&spp=30&ab_testing=false&lang=ru&nm='
            details_of_prods_to_check = self.all_authors_list[i].wbdetailedinfo_set.all()
            if len(details_of_prods_to_check) == 0:
                continue
            final_url = detail_product_url_api + ';'.join(map(lambda x: str(x.product.artikul), details_of_prods_to_check))
            response = self.scraper.get(final_url, headers=self.headers)
            json_data = json.loads(response.text)
            products_on_page = json_data['data']['products']

            products_on_page = sorted(products_on_page, key=lambda x: x['id'])
            details_of_prods_to_check = sorted(details_of_prods_to_check, key=lambda x: x.product.artikul)

            for j in range(len(products_on_page)):
                current_detail_to_check = details_of_prods_to_check[j]
                if products_on_page[j]['id'] == current_detail_to_check.product.artikul: #по хорошему вот тут надо добавить исключение какое то
                    if current_detail_to_check.size == None:
                        self.check_nonsize_product(current_detail_to_check, products_on_page[j])
                    else:
                        self.check_size_product(current_detail_to_check, products_on_page[j])                      
                else:
                    print(products_on_page[j]['id'])
                    print(current_detail_to_check.product.artikul)
                    print('Не сходится товар и запрос по индексам')



    def check_nonsize_product(self, current_detail_to_check, product_on_page):
        self.test_counter += 1
        stocks = product_on_page['sizes'][0]['stocks']
        flag_change = False
        if len(stocks) != 0:
            volume = 0
            for stock in stocks:
                volume += stock['qty']
            price_of_detail = int(product_on_page['sizes'][0]['price']['product'] // 100)
            #точка входа для уведомления пользователя
            if current_detail_to_check.latest_price != price_of_detail:
                print(f'Цена изменилась!\nПродукт: {current_detail_to_check.product.url}\nБыло: {current_detail_to_check.latest_price}\nСтало: {price_of_detail}\n')
                flag_change = True
                current_detail_to_check.latest_price = price_of_detail
                self.new_prices.append(WBPrice(price=price_of_detail,
                                            added_time=timezone.now(),
                                            detailed_info=current_detail_to_check))
            if current_detail_to_check.volume != volume: #по количеству постоянные изменения - просто пишу в бд без уведомлений (пока что)
                flag_change = True
                current_detail_to_check.volume = volume
            if flag_change: self.updated_details.append(current_detail_to_check)
        else:
            print(f'Продукта больше нет в наличии!\nПродукт: {current_detail_to_check.product.url}')
            current_detail_to_check.enabled = False
            current_detail_to_check.volume = 0
            self.updated_details.append(current_detail_to_check)
            


    def check_size_product(self, current_detail_to_check, product_on_page):
        self.test_counter += 1
        sizes = product_on_page['sizes']
        flag_change = False
        for size in sizes:
            if size['origName'] == current_detail_to_check.size:
                stocks = size['stocks']
                if len(stocks) != 0:
                    volume = 0
                    for stock in stocks:
                        volume += stock['qty']
                    price_of_detail = size['price']['product'] // 100
                    #точка входа для уведомления пользователя
                    if current_detail_to_check.latest_price != price_of_detail:
                        print(f'Цена изменилась!\nПродукт: {current_detail_to_check.product.url}\nБыло: {current_detail_to_check.latest_price}\nСтало: {price_of_detail}\n')
                        flag_change = True
                        current_detail_to_check.latest_price = price_of_detail
                        self.new_prices.append(WBPrice(price=price_of_detail,
                                                    added_time=timezone.now(),
                                                    detailed_info=current_detail_to_check))
                    if current_detail_to_check.volume != volume:
                        print(f'Кол-во изменилось!\nПродукт: {current_detail_to_check.product.url}\nБыло: {current_detail_to_check.volume}\nСтало: {volume}\n') 
                        flag_change = True
                        current_detail_to_check.volume = volume
                    if flag_change: self.updated_details.append(current_detail_to_check)
                else:
                    print(f'Продукта больше нет в наличии!\nПродукт: {current_detail_to_check.product.url}')
                    current_detail_to_check.enabled = False
                    current_detail_to_check.volume = 0
                    self.updated_details.append(current_detail_to_check)
                break                      


    @time_count
    @transaction.atomic
    def save_update_prices(self):
        '''Занесение в БД обновления наличия'''
        WBDetailedInfo.objects.bulk_update(self.updated_details, ['latest_price', 'volume', 'enabled'])
        WBPrice.objects.bulk_create(self.new_prices)





class AvaliabilityUpdater:
    def __init__(self):
        '''Инициализация необходимых атрибутов'''
        self.all_authors_list = Author.objects.all().prefetch_related(Prefetch('wbdetailedinfo_set', 
                                                 queryset=WBDetailedInfo.objects.filter(enabled=False).select_related('product')))
        self.scraper = cloudscraper.create_scraper()
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.new_prices = []
        self.updated_details = []


    def run(self):
        '''Запуск скрипта обновления'''
        self.update_avaliability()     
        self.save_update_prices()


    @time_count
    def update_avaliability(self):
        '''Обновление наличия продуктов, которых нет в наличии'''
        #максимум в листе 512 элементов
        for i in range(len(self.all_authors_list)):
            author_object = self.all_authors_list[i]
            detail_product_url_api = f'https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest={author_object.dest_id}&spp=30&ab_testing=false&lang=ru&nm='
            details_of_prods_to_check = self.all_authors_list[i].wbdetailedinfo_set.all()
            if len(details_of_prods_to_check) == 0:
                continue
            artikuls_of_details = list(map(lambda x: str(x.product.artikul), details_of_prods_to_check))
            final_url = detail_product_url_api + ';'.join(artikuls_of_details)
            print(final_url)
            response = self.scraper.get(final_url, headers=self.headers)
            json_data = json.loads(response.text)
            products_on_page = json_data['data']['products']

            products_on_page = sorted(products_on_page, key=lambda x: x['id'])
            details_of_prods_to_check = sorted(details_of_prods_to_check, key=lambda x: x.product.artikul)

            for j in range(len(products_on_page)):
                current_detail_to_check = details_of_prods_to_check[j]
                if products_on_page[i]['id'] == current_detail_to_check.product.id: #по хорошему вот тут надо добавить исключение какое то
                    if current_detail_to_check.size == None:
                        self.check_nonsize_product(current_detail_to_check, products_on_page[j])
                    else:
                        self.check_size_product(current_detail_to_check, products_on_page[j])                      
                else:
                    print('Не сходится товар и запрос по индексам')



    def check_nonsize_product(self, current_detail_to_check, product_on_page):
        stocks = product_on_page['sizes'][0]['stocks']
        if len(stocks) != 0:
            volume = 0
            for stock in stocks:
                volume += stock['qty']
            price_of_detail = product_on_page['sizes'][0]['price']['product'] // 100
            current_detail_to_check.latest_price = price_of_detail
            current_detail_to_check.volume = volume
            current_detail_to_check.enabled = True
            self.updated_details.append(current_detail_to_check)
            self.new_prices.append(WBPrice(price=price_of_detail,
                                            added_time=timezone.now(),
                                            detailed_info=current_detail_to_check))
            



    def check_size_product(self, current_detail_to_check, product_on_page):
        sizes = product_on_page['sizes']
        for size in sizes:
            if size['origName'] == current_detail_to_check.size:
                stocks = size['stocks']
                if len(stocks) != 0:
                    #точка входа для уведомления пользователя о том, что товар в наличии
                    volume = 0
                    for stock in stocks:
                        volume += stock['qty']
                    price_of_detail = size['price']['product'] // 100
                    current_detail_to_check.latest_price = price_of_detail
                    current_detail_to_check.volume = volume
                    current_detail_to_check.enabled = True
                    self.updated_details.append(current_detail_to_check)
                    self.new_prices.append(WBPrice(price=price_of_detail,
                                                    added_time=timezone.now(),
                                                    detailed_info=current_detail_to_check))
                break                      



    @time_count
    @transaction.atomic
    def save_update_prices(self):
        '''Занесение в БД обновления наличия'''
        WBDetailedInfo.objects.bulk_update(self.updated_details, ['latest_price', 'volume', 'enabled'])
        WBPrice.objects.bulk_create(self.new_prices)
        



#добавить функцию, если dest не прошел на мск

