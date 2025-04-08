import os
import psutil
from requests import request
import re
import json
import cloudscraper
from datetime import datetime
import apps.wb_checker.utils as utils
from .models import WBProduct, WBSeller, WBPrice, WBCategory, WBBrand, WBsearchtion
from apps.blog.models import Author
from django.utils import timezone
import math
import time
from functools import wraps
from django.db import transaction



class Search:
    def __init__(self, search_url, author_object):
        '''Инициализация необходимых атрибутов'''
        self.search_url = search_url
        self.author_object = author_object
        self.author_id = author_object.id
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.scraper = cloudscraper.create_scraper()
        self.search_slug_name = self.search_url.split('?')[0].split('/')[-1]
        self.search_object = self.get_object_of_search()
        self.search_api_url = self.construct_search_api_url()
        self.total_products = self.get_total_products_in_catalog()
        self.number_of_pages = self.get_number_of_pages_in_catalog()

        self.sellers_in_db = list(WBSeller.objects.all())
        self.seller_wb_id_in_db = list(map(lambda x: x.wb_id, self.sellers_in_db))
        self.brands_in_db = list(WBBrand.objects.all())
        self.brand_wb_id_in_db = list(map(lambda x: x.wb_id, self.brands_in_db))

        self.sellers_to_add = []
        self.sellers_wb_ids_to_add = []
        self.sellers_wb_id_in_search = []

        self.brands_to_add = []
        self.brands_wb_ids_to_add = []

        self.products_to_add = []
        self.prices_to_add = []

        self.repetition_products_to_change = []
        #это кэш на проверку самой категории (есть ли продукты этой категории уже в БД)
        # self.potential_repetitions = self.get_repetitions_catalog_brand()
        self.product_repetitions_list = []



    @utils.time_count
    def run(self):
        '''Запуск процесса парсинга'''
        self.get_catalog_of_search()
        self.get_repetitions_catalog_search()
        self.add_all_to_db()



    @utils.time_count
    def get_repetitions_catalog_search(self):
        '''Функция взятия всех продуктов + артикулов из БД тех селлеров, 
        которые были в промоакции (если они уже были в БД), 
        + редактирование кэшированных объектов для добавления/изменения в БД'''
        #находит повторки по фигурирующим продавцам из промоакции, которые лежали в БД до этого + берет их артикулы
        potential_repetitions_products = list(WBProduct.enabled_products.filter(seller__wb_id__in=self.sellers_wb_id_in_search))
        potential_repetitions_products_artikul = list(map(lambda x: x.artikul, potential_repetitions_products))
        new_products_to_delete_indexes = []
        #если нашел повторки
        if potential_repetitions_products:
            for i in range(len(self.products_to_add)):
                #если артикул продукта уже лежит в БД, то добавляем индекс для удаления нового продукта в кэш + 
                #добавляем продукт в кэш на добавление новой связи с автором и изменение графы промо в БД (продукта, который уже в ней лежал)
                if self.products_to_add[i].artikul in potential_repetitions_products_artikul:
                    new_products_to_delete_indexes.append(i)
                    self.repetition_products_to_change.append(potential_repetitions_products[potential_repetitions_products_artikul.index(self.products_to_add[i].artikul)])
        #если повторки нашлись, то удаляем их из изначального списка продуктов на добавление + удаляем сопряженную цену 
        #+добавляем связь с продуктов старых из БД, которые были дубликатами + обновляем у них поле промо
        if new_products_to_delete_indexes:
            self.products_to_add = list(filter(lambda x: True if self.products_to_add.index(x) not in new_products_to_delete_indexes else False, self.products_to_add))
            self.prices_to_add = list(filter(lambda x: True if self.prices_to_add.index(x) not in new_products_to_delete_indexes else False, self.prices_to_add))
    


    @utils.time_count
    def get_catalog_of_search(self):
        '''Функция, которая:
        1. Парсит товар
        2. Проверяет его на повторку
        3. Проверяет наличие бренда (откладывает новые в кэш)
        4. Добавляет в кэш новые объекты цены и продукта, если они прошли проверку на повторки'''
        for elem in range(1, self.number_of_pages + 1):
            self.search_api_url = re.sub(pattern=r'page=\d+\&', repl=f'page={elem}&', string=self.search_api_url)
            while True:
                try:
                    response = self.scraper.get(self.search_api_url, headers=self.headers)
                    json_data = json.loads(response.text)
                    products_on_page = json_data['data']['products']
                    break
                except:
                    print(elem)
            for i in range(len(products_on_page)):
                seller_artikul = products_on_page[i]['supplierId']
                seller_name = products_on_page[i]['supplier']
                brand_artikul = products_on_page[i]['brandId']
                brand_name = products_on_page[i]['brand']
                #проверка селлера и бренда на наличие в БД + откладывание его в кэш 
                seller_object = self.check_seller_existance(seller_artikul, seller_name)
                brand_object = self.check_brand_existance(brand_artikul, brand_name)
                self.add_new_product_and_price(product_in_catalog=products_on_page[i], seller_object=seller_object, brand_object=brand_object)



    @transaction.atomic
    @utils.time_count
    def add_all_to_db(self):
        '''Функция добавления всех изменений в БД атомарной транзакцией'''
        self.search_object.save()
        WBBrand.objects.bulk_create(self.brands_to_add)
        WBSeller.objects.bulk_create(self.sellers_to_add)
        WBProduct.objects.bulk_create(self.products_to_add) #добавляю элементы одной командой
        WBPrice.objects.bulk_create(self.prices_to_add) #добавляю элементы одной командой
        self.products_to_add.extend(self.repetition_products_to_change)
        Author.objects.get(id=self.author_id).wbproduct_set.add(*self.products_to_add) #many-to-many связь через автора (вставляется сразу все) - обязательно распаковать список
        for elem in self.repetition_products_to_change:
            elem.searchtion = self.search_object
        WBProduct.objects.bulk_update(self.repetition_products_to_change, ['searchtion'])
            




    def get_object_of_search(self):
        '''Получение объекта промо + проверка на уникальность'''
        response = self.scraper.get(f'https://static-basket-01.wbbasket.ru/vol0/data/searchtions/{self.search_slug_name}-v3.json', headers=self.headers)
        json_data = json.loads(response.text)['search']
        potential_search_object = WBsearchtion.objects.filter(wb_id=json_data['id']).first()
        if not potential_search_object:
            clear_shard_key = '/'.join(json_data['shardKey'].split('/')[1:])
            return WBsearchtion(name=json_data['name'],
                            wb_id=json_data['id'],
                            main_url=self.search_url,
                            shard_key=clear_shard_key,
                            query=json_data['query'])
        else:
            return potential_search_object



    def construct_search_api_url(self):
        '''Построение url для доступа к api каталога промо с 
        использованием всех фильтров, сортировок, пресетов промо'''
        clear_search_url = re.sub(pattern=r'\#.+', repl='', string=self.search_url)
        sorting = 'popular'
        addons = []
        if '?' in clear_search_url:
            addons = clear_search_url.split('?')[1]
            addons = addons.split('&')
            for elem in addons:
                if 'sort' in elem:
                    sorting = elem.split('=')[1]
        if addons: addons =f"&{'&'.join(list(filter(lambda x: True if 'page' not in x and 'sort' not in x and 'bid' not in x and 'erid' not in x else False, addons)))}"
        else: addons = ''
        return f'https://search.wb.ru/{self.search_object.shard_key}/v2/catalog?ab_testing=false&appType=1&curr=rub&dest={self.author_object.dest_id}&hide_dtype=13&lang=ru&{self.search_object.query}&spp=30&uclusters=3&page=1&sort={sorting}{addons}'



    def get_total_products_in_catalog(self):
        '''Получение количества продуктов для парсинга'''
        response = self.scraper.get(self.search_api_url, headers=self.headers)
        json_data = json.loads(response.text)
        total_products = json_data['data']['total']
        return total_products



    def get_number_of_pages_in_catalog(self):
        '''Получение количества страниц для парсинга 
        плюс настройка ограничения в 100 страниц'''
        number_of_pages = math.ceil(self.total_products/100)
        if number_of_pages > 100:
            number_of_pages = 100
        return number_of_pages
        


    def check_seller_existance(self, seller_artikul, seller_name):
        '''Проверка продавца на существование в БД + откладывание его в кэш при отсутствии'''
        if seller_artikul not in self.sellers_wb_id_in_search:
            self.sellers_wb_id_in_search.append(seller_artikul)
        if seller_artikul not in self.seller_wb_id_in_db:
            seller_object = WBSeller(name=seller_name,
                        wb_id=seller_artikul,
                        main_url=f'https://www.wildberries.ru/seller/{seller_artikul}',
                        full_control = False)
            self.sellers_to_add.append(seller_object) #добавляем в список для добавления в БД
            self.sellers_in_db.append(seller_object) #чтобы уже не повторялся
            self.seller_wb_id_in_db.append(seller_artikul)
        else:
            seller_object = self.sellers_in_db[self.seller_wb_id_in_db.index(seller_artikul)]
        return seller_object
    


    def check_brand_existance(self, brand_artikul, brand_name):
        '''Проверка бренда на существование в БД + откладывание его в кэш при отсутствии'''
        if brand_artikul not in self.brand_wb_id_in_db:
            brand_object = WBBrand(name=brand_name,
                        wb_id=brand_artikul,
                        main_url=f'https://www.wildberries.ru/brands/{brand_artikul}',
                        full_control = False)
            self.brands_to_add.append(brand_object) #добавляем в список для добавления в БД
            self.brands_in_db.append(brand_object) #чтобы уже не повторялся
            self.brand_wb_id_in_db.append(brand_artikul)
        else:
            brand_object = self.brands_in_db[self.brand_wb_id_in_db.index(brand_artikul)]
        return brand_object



    def add_new_product_and_price(self, product_in_catalog, seller_object, brand_object):
        '''Сборка объекта продукта и объекта цены + добавление их в кэш'''
        product_artikul = product_in_catalog['id']
        product_url = f'https://www.wildberries.ru/catalog/{product_artikul}/detail.aspx'
        name = product_in_catalog['name']
        price_element = product_in_catalog['sizes'][0]['price']['product'] // 100
        new_product = WBProduct(name=name,
                artikul=product_artikul,
                latest_price=price_element,
                wb_cosh=True,
                url=product_url,
                enabled=True,
                brand=brand_object,
                seller=seller_object,
                searchtion=self.search_object)
        new_product_price = WBPrice(price=price_element,
                                added_time=timezone.now(),
                                product=new_product)
        self.products_to_add.append(new_product)
        self.prices_to_add.append(new_product_price)
        

