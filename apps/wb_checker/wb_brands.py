import os
import psutil
from requests import request
import re
import json
import cloudscraper
from datetime import datetime
import apps.wb_checker.utils as utils
from .models import WBProduct, WBSeller, WBPrice, WBCategory
from apps.blog.models import Author
from django.utils import timezone
import math
import time
from functools import wraps
from django.db import transaction



class Brand:
    def __init__(self, brand_url, author_id):
        self.brand_url = Brand.check_url_and_send_correct(brand_url)
        self.author_id = author_id
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.scraper = cloudscraper.create_scraper()
        self.brand_artikul, self.brand_siteId = self.get_brand_artikul_and_siteId()
        self.brandzone_url_api = self.get_brandzone_url_api()
        self.brand_api_url = self.construct_brand_api_url()
        self.total_products, self.brand_name = self.get_total_products_and_name_brand_in_catalog()
        self.number_of_pages = self.get_number_of_pages_in_catalog()
        self.brand_object, self.brand_was_in_db = utils.check_existence_of_brand(self.brand_name, self.brand_artikul)
        self.potential_repetitions = self.get_repetitions_catalog_brand()
        self.sellers_in_db = list(WBSeller.objects.all())
        self.seller_wb_id_in_db = list(map(lambda x: x.wb_id, self.sellers_in_db))
        self.product_repetitions_list = []
        self.sellers_to_add = []
        self.sellers_wb_ids_to_add = []
        self.brand_products_to_add = []
        self.brand_prices_to_add = []

    @utils.time_count
    def run(self):
        self.get_catalog_of_brand()
        self.add_all_to_db()


    @utils.time_count
    def get_repetitions_catalog_brand(self):
        potential_repetitions = []
        #если бренд уже есть в БД, берет все продукты этого селлера вместе с их артикулами
        if self.brand_was_in_db:
            potential_repetitions = WBProduct.enabled_products.filter(brand=self.brand_object)
            potential_repetitions = dict(map(lambda x: (x.artikul, x), potential_repetitions))
        return potential_repetitions
    

    #https://www.wildberries.ru/brand/simaland-35167
    @utils.time_count
    def get_catalog_of_brand(self):
        #делает первый запрос для определения количества продуктов (total) + определение количества страниц для полного отображения каталога (продуктов на странице - 100!!)
        #проверяет наличие продавца в БД
        for elem in range(1, self.number_of_pages + 1):
            self.brand_api_url = re.sub(pattern=r'page=\d+\&', repl=f'page={elem}&', string=self.brand_api_url)
            while True:
                try:
                    response = self.scraper.get(self.brand_api_url, headers=self.headers)
                    json_data = json.loads(response.text)
                    products_on_page = json_data['data']['products']
                    break
                except:
                    print(elem)
            for i in range(len(products_on_page)):
                #специально получаю артикул продукта для того, чтобы передать в функцию проверки на повторки
                product_artikul = products_on_page[i]['id']
                if self.potential_repetitions:
                    if self.check_repetition_in_catalog(product_artikul): continue
                #проверка селлера на наличие в БД плюс откладывание его в кэш (только селлера, тк бренд уже в базе)
                seller_artikul = products_on_page[i]['supplierId']
                seller_name = products_on_page[i]['supplier']
                seller_object = self.check_seller_existance(seller_artikul, seller_name)#отдает объект бренда без заходов в БД постоянных
                self.add_new_product_and_price(product_in_catalog=products_on_page[i], seller_object=seller_object, product_artikul = product_artikul)


    @transaction.atomic
    @utils.time_count
    def add_all_to_db(self):
        WBSeller.objects.bulk_create(self.sellers_to_add)
        WBProduct.objects.bulk_create(self.brand_products_to_add) #добавляю элементы одной командой
        WBPrice.objects.bulk_create(self.brand_prices_to_add) #добавляю элементы одной командой
        self.brand_products_to_add.extend(self.product_repetitions_list)
        Author.objects.get(id=self.author_id).wbproduct_set.add(*self.brand_products_to_add) #many-to-many связь через автора (вставляется сразу все) - обязательно распаковать список

    #Варианты урлов:
    #https://www.wildberries.ru/brands/joonies
    #https://www.wildberries.ru/brands/311409788-cotton-care
    #https://static-basket-01.wbbasket.ru/vol0/data/brands/joonies.json
    def get_brand_artikul_and_siteId(self):
        brand_slug_name = re.search(r'(brands\/)([a-z\-\d]+)(\?)?(\/)?(\#)?', self.brand_url).group(2)
        final_url = f'https://static-basket-01.wbbasket.ru/vol0/data/brands/{brand_slug_name}.json'
        response = self.scraper.get(final_url, headers=self.headers)
        json_data = json.loads(response.text)
        brand_artikul = json_data['id']
        brand_siteId = json_data['siteId']
        return brand_artikul, brand_siteId
    
    def get_brandzone_url_api(self):
        return f'https://brandzones.wildberries.ru/api/v1/site/brandzone?siteID={self.brand_siteId}&admin=false&contentID={self.brand_artikul}'

    def get_custom_links_of_brand(self):
        response = self.scraper.get(self.brandzone_url_api, headers=self.headers)
        json_data = json.loads(response.text)['sections'][2]['blocks'][0]['items']
        json_data = dict(map(lambda x: (x['url'].split('/')[-1].split('?')[0], x['query']), json_data))
        return json_data

    def construct_brand_api_url(self):
        clear_brand_url = re.sub(pattern=r'\#.+', repl='', string=self.brand_url)
        sorting = 'popular'
        addons = []
        if '?' in clear_brand_url:
            addons = clear_brand_url.split('?')[1]
            addons = addons.split('&')
            for elem in addons:
                if 'sort' in elem:
                    sorting = elem.split('=')[1]
        category = re.search(r'(brands\/)([a-z\-\d]+\/)([a-z\-]+)?(\?)?(\#)?', clear_brand_url) #выцепляю категорию
        if category: 
            try:
                category_wb_id = (WBCategory.objects.get(url=category.group(3))).wb_id
                addons.append(f'subject={category_wb_id}')
            except:
                addons.append(self.get_custom_links_of_brand()[category.group(3)])
        if addons: addons =f"&{'&'.join(list(filter(lambda x: True if 'page' not in x and 'sort' not in x and 'bid' not in x and 'erid' not in x else False, addons)))}"
        else: addons = ''
        return f'https://catalog.wb.ru/brands/v2/catalog?ab_testing=false&appType=1&curr=rub&dest=-1257786&hide_dtype=13&lang=ru&spp=30&uclusters=3&page=1&brand={self.brand_artikul}&sort={sorting}{addons}'


    def get_total_products_and_name_brand_in_catalog(self):
        response = self.scraper.get(self.brand_api_url, headers=self.headers)
        json_data = json.loads(response.text)
        total_products = json_data['data']['total']
        brand_name = json_data['data']['products'][0]['brand']
        return total_products, brand_name


    def get_number_of_pages_in_catalog(self):
        number_of_pages = math.ceil(self.total_products/100)
        if number_of_pages > 100: #так как максимально отдает вб 10к, а товаров на странице всегда <=100
            number_of_pages = 100
        return number_of_pages


    def check_repetition_in_catalog(self, product_artikul_to_check):
        potential_repetition = utils.check_repetitions_catalog(product_artikul_to_check, self.potential_repetitions)
        if potential_repetition:
            self.product_repetitions_list.append(potential_repetition)
            return True
        
    def check_seller_existance(self, seller_artikul, seller_name):
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


    def add_new_product_and_price(self, product_in_catalog, seller_object, product_artikul):
        #полностью собирает элемент
        product_url = f'https://www.wildberries.ru/catalog/{product_artikul}/detail.aspx'
        name = product_in_catalog['name'] #имя продукта в каталоге
        price_element = product_in_catalog['sizes'][0]['price']['product'] // 100
        #добавляем объект продукта
        new_product = WBProduct(name=name,
                artikul=product_artikul,
                latest_price=price_element,
                wb_cosh=True,
                url=product_url,
                enabled=True,
                brand=self.brand_object,
                seller=seller_object)
        #добавляем объект прайса
        new_product_price = WBPrice(price=price_element,
                                added_time=timezone.now(),
                                product=new_product)
        self.brand_products_to_add.append(new_product)
        self.brand_prices_to_add.append(new_product_price)
        
    @staticmethod
    def check_url_and_send_correct(url):
        if 'brands' in url:
            return url
        else:
            headers = {"User-Agent": "Mozilla/5.0"}
            scraper = cloudscraper.create_scraper()
            response = scraper.get(f'https://card.wb.ru/cards/v2/list?appType=1&curr=rub&dest=-1257786&spp=30&ab_testing=false&lang=ru&nm={re.search(r'\/(\d+)\/', url).group(1)}', headers=headers)
            json_data = json.loads(response.text)
            response = scraper.get(f'https://static-basket-01.wbbasket.ru/vol0/data/brands-by-id/{json_data['data']['products'][0]['brandId']}.json', headers=headers)
            json_data = json.loads(response.text)
            return f'https://www.wildberries.ru/brands/{json_data['url']}'

