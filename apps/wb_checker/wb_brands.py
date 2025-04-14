import os
import psutil
from requests import request
import re
import json
import cloudscraper
from datetime import datetime
import apps.wb_checker.utils as utils
from .models import WBProduct, WBSeller, WBPrice, WBCategory, WBBrand, WBPreset, TopWBProduct
from apps.blog.models import Author
from django.utils import timezone
import math
import time
from functools import wraps
from django.db import transaction
from statistics import median



class Brand:
    def __init__(self, raw_brand_url, author_object):
        '''Инициализация необходимых атрибутов'''
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.scraper = cloudscraper.create_scraper()
        self.author_object = author_object
        self.author_id = author_object.id
        self.dest_avaliable = True
        self.brand_url = self.check_url_and_send_correct(raw_brand_url)
        self.brand_artikul, self.brand_siteId = self.get_brand_artikul_and_siteId()
        self.brandzone_url_api = self.get_brandzone_url_api()
        self.brand_api_url = self.construct_brand_api_url()
        self.total_products, self.brand_name = self.get_total_products_and_name_brand_in_catalog()
        if self.dest_avaliable:
            self.brand_object = self.build_raw_brand_object()
            self.dict_brand_products_to_add = dict()
            self.dict_sellers_to_add = dict()
            self.list_brand_products_to_add_with_scores = []



    @utils.time_count
    def run(self):
        '''Запуск процесса парсинга'''
        if self.dest_avaliable:
            self.get_catalog_of_brand('popular')
            self.get_catalog_of_brand('benefit')
            self.get_catalog_of_brand('rate')
            self.build_top_prods()
            self.add_all_to_db()
    


    @utils.time_count
    def get_catalog_of_brand(self, sorting):
        '''Функция, которая:
        1. Парсит товар
        2. Проверяет его на повторку
        3. Проверяет наличие бренда (откладывает новые в кэш)
        4. Добавляет в кэш новые объекты цены и продукта, если они прошли проверку на повторки'''
        brand_api_url = self.brand_api_url + sorting
        response = self.scraper.get(brand_api_url, headers=self.headers)
        json_data = json.loads(response.text)
        products_on_page = json_data['data']['products']
        for i in range(len(products_on_page)):
            self.add_new_product(product_in_catalog=products_on_page[i])



    def build_top_prods(self):
        top_builder = TopBuilder(self.dict_brand_products_to_add)
        print('Вычисляю топ продуктов по цене/отзывам/рейтигу...')
        self.list_brand_products_to_add_with_scores = list(top_builder.build_top().values())
        self.list_brand_products_to_add_with_scores = sorted(self.list_brand_products_to_add_with_scores, key=lambda x: x.score)[-20:]
        if (len(self.list_brand_products_to_add_with_scores)) < 20:
            print(f'Топ {self.list_brand_products_to_add_with_scores} продуктов бренда:')
        else:
            print(f'Топ 20 продуктов бренда:')
        for product in self.list_brand_products_to_add_with_scores:
            print(f'Продукт: {product.url}')
            print(f'Цена: {product.latest_price}')
            print(f'Рейтинг: {product.rating}')
            print(f'Количество отзывов: {product.feedbacks}')
            print(f'Внутренний скор: {product.score}')
            print()
        



    @transaction.atomic
    @utils.time_count
    def add_all_to_db(self):
        '''Функция добавления всех изменений в БД атомарной транзакцией'''
        WBBrand.objects.bulk_create([self.brand_object], update_conflicts=True, unique_fields=['wb_id'], update_fields=['name'])
        WBSeller.objects.bulk_create(self.dict_sellers_to_add.values(), update_conflicts=True, unique_fields=['wb_id'], update_fields=['name'])
        TopWBProduct.objects.bulk_create(self.list_brand_products_to_add_with_scores, update_conflicts=True, unique_fields=['artikul'], update_fields=['name']) #ссылается не на id а на wb_id добавленного бренда (тк оно уникальное)
        # self.brand_products_to_add.extend(self.product_repetitions_list) #опять же, связи добавятся, потому что у этих продуктов есть уникальное поле артикула + 
        # self.author_object.enabled_connection.add(*self.brand_products_to_add) #many-to-many связь через автора (вставляется сразу все) - обязательно распаковать список
        # self.author_object.save()



    def get_brand_artikul_and_siteId(self):
        '''Получение артикула (wb_id) бренда + id мини-сайта этого бренда'''
        brand_slug_name = re.search(r'(brands\/)([a-z\-\d]+)(\?)?(\/)?(\#)?', self.brand_url).group(2)
        final_url = f'https://static-basket-01.wbbasket.ru/vol0/data/brands/{brand_slug_name}.json'
        response = self.scraper.get(final_url, headers=self.headers)
        json_data = json.loads(response.text)
        brand_artikul = json_data['id']
        brand_siteId = json_data['siteId']
        return brand_artikul, brand_siteId
    


    def get_brandzone_url_api(self):
        '''Конструирование url для доступа к api со всеми url-путями мини-сайта бренда'''
        return f'https://brandzones.wildberries.ru/api/v1/site/brandzone?siteID={self.brand_siteId}&admin=false&contentID={self.brand_artikul}'



    def get_custom_links_of_brand(self):
        '''Получение всех url-путей мини-сайта бренда'''
        response = self.scraper.get(self.brandzone_url_api, headers=self.headers)
        json_data = json.loads(response.text)['sections'][2]['blocks'][0]['items']
        json_data = dict(map(lambda x: (x['url'].split('/')[-1].split('?')[0], x['query']), json_data))
        return json_data



    def construct_brand_api_url(self):
        '''Построение url для доступа к api каталога бренда с 
        использованием всех фильтров, сортировок, категорий (путей кастомных)'''
        clear_brand_url = re.sub(pattern=r'\#.+', repl='', string=self.brand_url)
        addons = []
        if '?' in clear_brand_url:
            addons = clear_brand_url.split('?')[1]
            addons = addons.split('&')
        if addons: addons =f"&{'&'.join(list(filter(lambda x: True if 'page' not in x and 'sort' not in x and 'bid' not in x and 'erid' not in x else False, addons)))}"
        else: addons = ''
        #dest по топу товаров беру только на мск
        return f'https://catalog.wb.ru/brands/v2/catalog?ab_testing=false&appType=1&curr=rub&dest={-1257786}&hide_dtype=13&lang=ru&spp=30&uclusters=3&page=1&brand={self.brand_artikul}&sort='



    def get_total_products_and_name_brand_in_catalog(self):
        '''Получение количества продуктов для парсинга + 
        имя бренда (для создания объекта бренда при его отсутствии в БД)'''
        brand_api_url = self.brand_api_url + 'popular'
        response = self.scraper.get(brand_api_url, headers=self.headers)
        json_data = json.loads(response.text)
        try:
            total_products = json_data['data']['total']
            brand_name = json_data['data']['products'][0]['brand']
        except:
            print('Не найдено ни одного товара бренда (скорее всего они недоступны центральном регионе)')
            self.dest_avaliable = False
            return 0, None
        #точка входа для вопроса пользователю - сколько продуктов нужно взять, если их больше 10
        print(f'Товары обнаружены! Бренд - {brand_name}. Количество - {total_products}')
        print(f'Выполняется анализ топовых продуктов....')       
        return total_products, brand_name
    


    def build_raw_brand_object(self):
        '''Создание объекта бренда без занесения в БД и знания,
          есть ли уже такой объект в базе (если есть и будет конфликт => 
          все пройдет правильно из-за уникального wb_id)'''
        return WBBrand(wb_id=self.brand_artikul,
                    name=self.brand_name,
                    main_url=f'https://www.wildberries.ru/seller/{self.brand_artikul}')
        


    def build_raw_seller_object(self, seller_artikul, seller_name):
        '''Проверка продавца на существование в БД + откладывание его в кэш при отсутствии'''
        seller_object = WBSeller(name=seller_name,
                    wb_id=seller_artikul,
                    main_url=f'https://www.wildberries.ru/seller/{seller_artikul}', #баг только с самим вб
                    full_control = False)
        seller_object = self.dict_sellers_to_add.setdefault(seller_artikul, seller_object)
        return seller_object



    def add_new_product(self, product_in_catalog):
        '''Сборка объекта продукта и объекта цены + добавление их в кэш'''
        name = product_in_catalog['name']
        price_element = product_in_catalog['sizes'][0]['price']['product'] // 100
        product_artikul = product_in_catalog['id']
        product_url = f'https://www.wildberries.ru/catalog/{product_artikul}/detail.aspx'
        seller_artikul = product_in_catalog['supplierId']
        rating = product_in_catalog['reviewRating']
        feedbacks = product_in_catalog['feedbacks']
        seller_name = product_in_catalog['supplier']

        seller_object = self.build_raw_seller_object(seller_artikul, seller_name)
        new_product = TopWBProduct(name=name,
                artikul=product_artikul,
                latest_price = price_element,
                rating=rating,
                feedbacks=feedbacks,
                wb_cosh=True,
                url=product_url,
                brand=self.brand_object,
                seller=seller_object)
        new_product = {product_artikul: new_product}
        self.dict_brand_products_to_add.update(new_product)
        


    def check_url_and_send_correct(self, raw_url):
        '''Проверка url, отправленного пользователем, на предмет 
        парсинга бренда по продукту или парсинга бренда по прямой ссылке'''
        if 'brands' in raw_url:
            return raw_url
        else:
            response = self.scraper.get(f'https://card.wb.ru/cards/v2/list?appType=1&curr=rub&dest={self.author_object.dest_id}&spp=30&ab_testing=false&lang=ru&nm={re.search(r'\/(\d+)\/', raw_url).group(1)}', headers=self.headers)
            json_data = json.loads(response.text)
            response = self.scraper.get(f'https://static-basket-01.wbbasket.ru/vol0/data/brands-by-id/{json_data['data']['products'][0]['brandId']}.json', headers=self.headers)
            json_data = json.loads(response.text)
            return f'https://www.wildberries.ru/brands/{json_data['url']}'



class TopBuilder:
    def __init__(self, dict_products_in_catalog):
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.scraper = cloudscraper.create_scraper()
        self.dict_products_in_catalog = dict_products_in_catalog
        self.feedbacks_median = self.get_feedbacks_median()
        self.price_history = None



    @utils.time_count
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
            