import cloudscraper
import json
from django.utils import timezone
from django.db import transaction
from django.db.models import Prefetch
from apps.blog.models import Author
from apps.wb_checker.utils.general_utils import time_count
from ..models import WBPrice, WBDetailedInfo



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