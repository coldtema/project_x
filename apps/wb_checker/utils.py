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
from statistics import median
import datetime


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
        self.current_detail_to_check = None


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
                self.current_detail_to_check = details_of_prods_to_check[j]
                if products_on_page[j]['id'] == self.current_detail_to_check.product.artikul: #по хорошему вот тут надо добавить исключение какое то
                    if self.current_detail_to_check.size == None:
                        self.check_nonsize_product(products_on_page[j])
                    else:
                        self.check_size_product(products_on_page[j])                      
                else:
                    print(products_on_page[j]['id'])
                    print(self.current_detail_to_check.product.artikul)
                    print('Не сходится товар и запрос по индексам')



    def check_nonsize_product(self, product_on_page):
        '''Функция проверки изменений товара для продукта, у которого нет размера'''
        self.test_counter += 1
        stocks = product_on_page['sizes'][0]['stocks']
        if len(stocks) != 0:
            volume = 0
            for stock in stocks:
                volume += stock['qty']
            price_of_detail = int(product_on_page['sizes'][0]['price']['product'] // 100)
            #точка входа для уведомления пользователя
            self.updating_plus_notification(price_of_detail, volume)
        else:
            self.disable_product()
            


    def disable_product(self):
        print(f'Продукта больше нет в наличии!\nПродукт: {self.current_detail_to_check.product.url}\n')
        self.current_detail_to_check.enabled = False
        self.current_detail_to_check.volume = 0
        self.updated_details.append(self.current_detail_to_check)   



    def check_size_product(self, product_on_page):
        '''Функция проверки изменений товара для продукта, у которого есть размер'''
        self.test_counter += 1
        sizes = product_on_page['sizes']
        for size in sizes:
            if size['origName'] == self.current_detail_to_check.size:
                stocks = size['stocks']
                if len(stocks) != 0:
                    volume = 0
                    for stock in stocks:
                        volume += stock['qty']
                    price_of_detail = size['price']['product'] // 100
                    #точка входа для уведомления пользователя
                    self.updating_plus_notification(price_of_detail, volume)
                break      



    def updating_plus_notification(self, price_of_detail, volume): 
        flag_change = False           
        if self.current_detail_to_check.latest_price != price_of_detail:
            print(f'Цена изменилась!\nПродукт: {self.current_detail_to_check.product.url}\nБыло: {self.current_detail_to_check.latest_price}\nСтало: {price_of_detail}\n')
            flag_change = True
            self.current_detail_to_check.latest_price = price_of_detail
            self.new_prices.append(WBPrice(price=price_of_detail,
                                        added_time=timezone.now(),
                                        detailed_info=self.current_detail_to_check))
            if self.current_detail_to_check.volume != volume: #по количеству постоянные изменения - просто пишу в бд без уведомлений (пока что)
                flag_change = True
                self.current_detail_to_check.volume = volume
            if flag_change: self.updated_details.append(self.current_detail_to_check)             


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
        self.test_counter = 0
        self.current_detail_to_check = None


    def run(self):
        '''Запуск скрипта обновления'''
        self.update_avaliability()     
        self.save_update_avaliability()
        print(f'Товаров проверено:{self.test_counter}')


    @time_count
    def update_avaliability(self):
        '''Обновление наличия продуктов, которых нет в наличии'''
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
                self.current_detail_to_check = details_of_prods_to_check[j]
                if products_on_page[j]['id'] == self.current_detail_to_check.product.artikul: #по хорошему вот тут надо добавить исключение какое то
                    if self.current_detail_to_check.size == None:
                        self.check_nonsize_product(products_on_page[j])
                    else:
                        self.check_size_product(products_on_page[j])                      
                else:
                    print('Не сходится товар и запрос по индексам')



    def check_nonsize_product(self, product_on_page):
        '''Функция проверки наличия продукта, у которого нет размеров'''
        self.test_counter += 1
        stocks = product_on_page['sizes'][0]['stocks']
        if len(stocks) != 0:
            #точка входа для уведомления пользователя о том, что товар в наличии
            volume = 0
            for stock in stocks:
                volume += stock['qty']
            price_of_detail = product_on_page['sizes'][0]['price']['product'] // 100
            #проверять тут нужно на разницу цены до "нет в наличии" и после
            self.enable_product(price_of_detail, volume)
            



    def check_size_product(self, product_on_page):
        '''Функция проверки наличия продукта, у которого есть размер'''
        self.test_counter += 1
        sizes = product_on_page['sizes']
        for size in sizes:
            if size['origName'] == self.current_detail_to_check.size:
                stocks = size['stocks']
                if len(stocks) != 0:
                    #точка входа для уведомления пользователя о том, что товар в наличии
                    volume = 0
                    for stock in stocks:
                        volume += stock['qty']
                    price_of_detail = size['price']['product'] // 100
                    self.enable_product(price_of_detail, volume) #добавить кастомизацию по размеру (вдруг его не было в наличии)
                break                      
                


    def enable_product(self, price_of_detail, volume):
        self.current_detail_to_check.latest_price = price_of_detail
        self.current_detail_to_check.volume = volume
        self.current_detail_to_check.enabled = True
        self.updated_details.append(self.current_detail_to_check)
        self.new_prices.append(WBPrice(price=price_of_detail,
                                        added_time=timezone.now(),
                                        detailed_info=self.current_detail_to_check))
        print(f'Продукт снова в наличии!\nПродукт: {self.current_detail_to_check.product.url}\n')



    @time_count
    @transaction.atomic
    def save_update_avaliability(self):
        '''Занесение в БД обновления наличия'''
        WBDetailedInfo.objects.bulk_update(self.updated_details, ['latest_price', 'volume', 'enabled'])
        WBPrice.objects.bulk_create(self.new_prices)





class TopBuilder:
    def __init__(self, dict_products_in_catalog):
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.scraper = cloudscraper.create_scraper()
        self.dict_products_in_catalog = dict_products_in_catalog
        self.feedbacks_median = self.get_feedbacks_median()
        self.price_history = None



    @time_count
    def build_top(self):
        for artikul, product_object in self.dict_products_in_catalog.items():
            try: #если вдруг истории цены нет
                self.price_history = self.get_price_history(artikul)
                #price_history = list(map(lambda x: (timezone.make_aware(datetime.fromtimestamp(x['dt'])), x['price']['RUB']//100), price_history))
                self.price_history = list(map(lambda x: (x['dt'], x['price']['RUB']//100), self.price_history))
                self.price_history.append((timezone.now(), product_object.latest_price))
            except:
                self.price_history = [(timezone.now(), product_object.latest_price)]
            if len(self.price_history) < 4:
                product_object.score = 0
            else:
                self.prices_duration = self.get_duration_of_prices()
                score_of_product = self.get_score_of_product(product_object)
                product_object.score = score_of_product
        return self.dict_products_in_catalog



    def get_score_of_product(self, product_object):
        prices_median = self.get_prices_median()
        true_discount = (prices_median - product_object.latest_price) / prices_median
        trust_score = min(1.0, product_object.feedbacks / self.feedbacks_median) * (product_object.rating / 5)
        score_of_product = true_discount * trust_score
        return score_of_product



    def get_prices_median(self):
        list_prices = []
        for elem in self.prices_duration:
            list_prices.extend([elem[1] for i in range(int(elem[0]))])
        return median(list_prices)




    def get_duration_of_prices(self):
        prices_duration = []
        prices_duration.append((7, self.price_history[0][1]))#для первого
        for i in range(1, len(self.price_history)-1):
            price_duration = abs(self.price_history[i][0] - self.price_history[i-1][0]) / (60*60*24) #кол-во секунд в дне
            prices_duration.append((price_duration, self.price_history[i][1]))
        prices_duration.append((math.ceil(abs(datetime.timestamp(self.price_history[-1][0]) - self.price_history[-2][0]) / (60*60*24)), self.price_history[-1][1]))#для последнего
        return prices_duration


            

    def get_feedbacks_median(self):
        list_of_feedbacks = []
        for product_object in self.dict_products_in_catalog.values():
            list_of_feedbacks.append(product_object.feedbacks)
        list_of_feedbacks = sorted((list_of_feedbacks))
        return median(list_of_feedbacks)



    def get_price_history(self, artikul):
        '''Функция получения истории цены продукта'''
        basket_num = TopBuilder.get_basket_num(artikul)
        artikul = str(artikul)
        if basket_num < 10:
            basket_num = f'0{basket_num}'
        price_history_searcher_url = ''
        if len(artikul) == 9:
            price_history_searcher_url = f'https://basket-{basket_num}.wbbasket.ru/vol{artikul[:4]}/part{artikul[:6]}/{artikul}/info/price-history.json'
        elif len(artikul) == 9:
            price_history_searcher_url = f'https://basket-{basket_num}.wbbasket.ru/vol{artikul[:3]}/part{artikul[:5]}/{artikul}/info/price-history.json'
        elif len(artikul) == 7:
            price_history_searcher_url = f'https://basket-{basket_num}.wbbasket.ru/vol{artikul[:2]}/part{artikul[:4]}/{artikul}/info/price-history.json'
        elif len(artikul) == 6:
            price_history_searcher_url = f'https://basket-{basket_num}.wbbasket.ru/vol{artikul[:1]}/part{artikul[:3]}/{artikul}/info/price-history.json'
        response = self.scraper.get(price_history_searcher_url, headers=self.headers)
        json_data = json.loads(response.text)
        return json_data
    


    @staticmethod
    def get_basket_num(artikul: int):
        '''Определение сервера, на котором находится история цены по js скрипту на wb'''
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