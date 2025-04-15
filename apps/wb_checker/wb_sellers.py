import re
import json
import time
import cloudscraper
import apps.wb_checker.utils.utils as utils
from .models import WBProduct, WBBrand, WBPrice, WBCategory, WBSeller, TopWBProduct
from apps.blog.models import Author
from django.utils import timezone
import math
from django.db import transaction
from apps.wb_checker.utils.utils import TopBuilder
from datetime import datetime



class Seller:
    def __init__(self, raw_seller_url, author_object):
        '''Инициализация необходимых атрибутов'''
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.scraper = cloudscraper.create_scraper()
        self.author_object = author_object
        self.author_id = author_object.id #не стал везде в коде менять, оставил автор айди (просто взял из объекта)
        self.dest_avaliable = True
        self.seller_url = self.check_url_and_send_correct(raw_seller_url)
        self.seller_artikul = self.get_seller_artikul()
        self.seller_api_url = self.construct_seller_api_url()
        self.total_products, self.seller_name = self.get_total_products_and_name_seller_in_catalog()
        if self.dest_avaliable:
            self.seller_object = self.build_raw_seller_object()
            self.dict_brands_to_add = dict()
            self.dict_seller_products_to_add = dict()
            self.list_seller_products_to_add_with_scores = []


    @utils.time_count
    def run(self):
        '''Функция запуска процесса парсинга'''
        if self.dest_avaliable:
            self.get_catalog_of_seller('popular')
            self.get_catalog_of_seller('benefit')
            self.get_catalog_of_seller('rate')
            self.build_top_prods()
            self.add_all_to_db()


    @utils.time_count
    def get_catalog_of_seller(self, sorting):
        '''Функция, которая:
        1. Парсит товар
        2. Проверяет его на повторку
        3. Проверяет наличие бренда (откладывает новые в кэш)
        4. Добавляет в кэш новые объекты цены и продукта, если они прошли проверку на повторки'''
        seller_api_url = self.seller_api_url + sorting
        response = self.scraper.get(self.seller_api_url, headers=self.headers)
        json_data = json.loads(response.text)
        products_on_page = json_data['data']['products']
        for i in range(len(products_on_page)):
            self.add_new_product(product_in_catalog=products_on_page[i])



    def build_top_prods(self):
        top_builder = TopBuilder(self.dict_seller_products_to_add)
        print('Вычисляю топ продуктов продавца по цене/отзывам/рейтигу...')
        self.list_seller_products_to_add_with_scores = list(top_builder.build_top().values())
        self.list_seller_products_to_add_with_scores = sorted(self.list_seller_products_to_add_with_scores, key=lambda x: x.score)[-20:]
        if (len(self.list_seller_products_to_add_with_scores)) < 20:
            print(f'Топ {self.list_seller_products_to_add_with_scores} продуктов продавца:')
        else:
            print(f'Топ 20 продуктов бренда:')
        for product in self.list_seller_products_to_add_with_scores:
            print(f'Продукт: {product.url}')
            print(f'Цена: {product.latest_price}')
            print(f'Рейтинг: {product.rating}')
            print(f'Количество отзывов: {product.feedbacks}')
            print(f'Внутренний скор: {product.score}')
            print()






    @utils.time_count
    @transaction.atomic
    def add_all_to_db(self):
        '''Функция добавления всех изменений в БД атомарной транзакцией'''
        WBSeller.objects.bulk_create([self.seller_object], update_conflicts=True, unique_fields=['wb_id'], update_fields=['name'])
        WBBrand.objects.bulk_create(self.dict_brands_to_add.values(), update_conflicts=True, unique_fields=['wb_id'], update_fields=['name'])
        TopWBProduct.objects.bulk_create(self.list_seller_products_to_add_with_scores, ignore_conflicts=True) #ссылается не на id а на wb_id добавленного бренда (тк оно уникальное)
        self.author_object.wbseller_set.add(self.seller_object)

    
    def get_seller_artikul(self):
        '''Получение артикула (wb_id) селлера'''
        seller_artikul = re.search(r'(seller)\/([a-z]+?\-)?(\d+)(\?)?', self.seller_url)
        #если артикул селлера указан сразу в url
        if seller_artikul:
            seller_artikul = seller_artikul.group(3)
        else:
            #если в url указано имя селлера в виде slug'a
            seller_slug_name = re.search(r'(seller\/)([a-z\-]+)(\?)?', self.seller_url).group(2)
            final_url = f'https://static-basket-01.wbbasket.ru/vol0/constructor-api/shops/{seller_slug_name}.json'
            response = self.scraper.get(final_url, headers=self.headers)
            json_data = json.loads(response.text)
            seller_artikul = json_data['supplierID']
        return seller_artikul
    


    def construct_seller_api_url(self):
        '''Построение url для доступа к api каталога селлера с 
        использованием всех фильтров, сортировок, категорий (путей кастомных)'''
        return f'https://catalog.wb.ru/sellers/v2/catalog?ab_testing=false&appType=1&curr=rub&dest={self.author_object.dest_id}&hide_dtype=13&lang=ru&spp=30&uclusters=0&page=1&supplier={self.seller_artikul}&sort='



    def get_total_products_and_name_seller_in_catalog(self):
        '''Получение количества продуктов для парсинга + 
        имя селлера (для создания объекта бренда при его отсутствии в БД)'''
        seller_api_url = self.seller_api_url + 'popular'
        response = self.scraper.get(seller_api_url, headers=self.headers)
        json_data = json.loads(response.text)
        try:
            total_products = json_data['data']['total']
            seller_name = json_data['data']['products'][0]['supplier']
        except:
            print('Не найдено ни одного товара продавца (скорее всего они недоступны в вашем регионе)')
            self.dest_avaliable = False
            return 0, None
        #точка входа для вопроса пользователю - сколько продуктов нужно взять, если их больше 10
        print(f'Товары обнаружены! Продавец - {seller_name}. Количество - {total_products}')
        print(f'Доступных слотов для отслеживания продуктов: {self.author_object.slots}')
        return total_products, seller_name
    


    def build_raw_seller_object(self):
        '''Создание объекта селлера без занесения в БД и знания,
          есть ли уже такой объект в базе (если есть и будет конфликт => 
          все пройдет правильно из-за уникального wb_id)'''
        seller_object, was_not_in_db = WBSeller.objects.get_or_create(wb_id=self.seller_artikul,
                                                                      name=self.seller_name,
                                                                      main_url=f'https://www.wildberries.ru/seller/{self.seller_artikul}')
        
        if not was_not_in_db and seller_object.subs.exists():
            self.dest_avaliable = False
            self.author_object.wbseller_set.add(seller_object)
        return seller_object

    def build_raw_brand_object(self, brand_artikul, brand_name):
        '''Проверка бренда на существование в БД + откладывание его в кэш при отсутствии'''
        if brand_artikul == 0:
            brand_object = WBBrand(name='Без бренда',
                    wb_id=brand_artikul,
                    main_url=f'https://www.wildberries.ru/')
        else:
            brand_object = WBBrand(name=brand_name,
                        wb_id=brand_artikul,
                        main_url=f'https://www.wildberries.ru/brands/{brand_artikul}')
        brand_object = self.dict_brands_to_add.setdefault(brand_artikul, brand_object)
        return brand_object



    def add_new_product(self, product_in_catalog):
        '''Сборка объекта продукта + добавление их в кэш'''
        name = product_in_catalog['name']
        price_element = product_in_catalog['sizes'][0]['price']['product'] // 100
        product_artikul = product_in_catalog['id']
        product_url = f'https://www.wildberries.ru/catalog/{product_artikul}/detail.aspx'
        brand_artikul = product_in_catalog['brandId']
        rating = product_in_catalog['reviewRating']
        feedbacks = product_in_catalog['feedbacks']
        brand_name = product_in_catalog['brand']

        brand_object = self.build_raw_brand_object(brand_artikul, brand_name)
        new_product = TopWBProduct(name=name,
                artikul=product_artikul,
                latest_price = price_element,
                rating=rating,
                feedbacks=feedbacks,
                wb_cosh=True,
                url=product_url,
                brand=brand_object,
                seller=self.seller_object,
                created=datetime.today(),
                source='SELLER')
        new_product = {product_artikul: new_product}
        self.dict_seller_products_to_add.update(new_product)



    def check_url_and_send_correct(self, raw_url):
        '''Проверка url, отправленного пользователем, на предмет 
        парсинга бренда по продукту или парсинга бренда по прямой ссылке'''
        if 'seller' in raw_url:
            return raw_url
        else:
            response = self.scraper.get(f'https://card.wb.ru/cards/v2/list?appType=1&curr=rub&dest={self.author_object.dest_id}&spp=30&ab_testing=false&lang=ru&nm={re.search(r'\/(\d+)\/', raw_url).group(1)}', headers=self.headers)
            json_data = json.loads(response.text)
            return f'https://www.wildberries.ru/seller/{json_data['data']['products'][0]['supplierId']}'
        