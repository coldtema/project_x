import os
import psutil
from requests import request
import re
import json
import cloudscraper
from datetime import datetime
import apps.wb_checker.utils as utils
from .models import WBProduct, WBSeller, WBBrand, WBPrice
from apps.blog.models import Author
from django.utils import timezone
import math
from .utils import time_count
from django.db import transaction



class Product:
    def __init__(self, product_url, author_id):
        self.product_url = product_url
        self.author_id = author_id
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.scraper = cloudscraper.create_scraper()
        self.artikul = re.search(r'\/(\d+)\/', product_url).group(1)
        self.product_url_api = f'https://card.wb.ru/cards/v2/list?appType=1&curr=rub&dest=-1257786&spp=30&ab_testing=false&lang=ru&nm={self.artikul}'

    @time_count
    def get_repetition_or_run(self):
        '''Проверка на повторки среди считываемых продуктов и продуктов бренда, которые уже существуют в БД'''
        repeated_product = WBProduct.enabled_products.filter(artikul=self.artikul) #посмотреть, как сделать так, чтобы get - функция не выдавала исключения
        if repeated_product and len(repeated_product) == 1: #если нашел повторюшку
            repeated_product = repeated_product[0]
            authors_list = repeated_product.authors.all() #проверяет, нет ли уже того же автора у этой повторюшки
            authors_list = map(lambda x: x.id, authors_list)
            for elem in authors_list: #выводит ворнинг, если такой же автор
                if elem == self.author_id:
                    print('Товар уже есть в отслеживании')
                    return
            repeated_product.authors.add(Author.objects.get(id=self.author_id)) #если не нашел автора и не выкинуло из функции, то добавляет many-to-many связь (попробовать написать через автора)
        else:
            self.get_product_info()


    def get_product_info(self):
        #полностью собирает элемент
        response = self.scraper.get(self.product_url_api, headers=self.headers)
        json_data = json.loads(response.text)
        name = json_data['data']['products'][0]['name']
        price_element = json_data['data']['products'][0]['sizes'][0]['price']['product'] // 100
        try: #если вдруг истории цены нет
            price_history = self.get_price_history(self.product_url)
            price_history = list(map(lambda x: (timezone.make_aware(datetime.fromtimestamp(x['dt'])), x['price']['RUB']//100), price_history))
            price_history.append((timezone.now(), price_element))
        except:
            price_history = [(timezone.now(), price_element)]
        seller_name = json_data['data']['products'][0]['supplier'] #имя продавца
        seller_artikul = json_data['data']['products'][0]['supplierId'] #id продавца
        brand_name = json_data['data']['products'][0]['brand'] #имя бренда
        brand_artikul = json_data['data']['products'][0]['brandId'] #id бренда
        #проверяет наличие этого бренда и продавца в БД (если нет, то создает их, если есть - не трогает)
        brand_object = utils.check_existence_of_brand(seller_name, seller_artikul)[0]
        seller_object = utils.check_existence_of_seller(brand_name, brand_artikul)[0]
        #добавляем элемент
        new_product = WBProduct(name=name,
                artikul=self.artikul,
                latest_price=price_element,
                wb_cosh=True,
                url=self.product_url,
                enabled=True,
                seller=seller_object,
                brand=brand_object)
        price_history = list(map(lambda x: WBPrice(price=x[1], added_time=x[0], product=new_product), price_history))
        self.add_product_to_db(new_product, price_history)


    def get_price_history(self):
        basket_num = Product.get_basket_num(int(self.artikul))
        if basket_num < 10:
            basket_num = f'0{basket_num}'
        if len(self.artikul) == 9:
            price_history_searcher_url = f'https://basket-{basket_num}.wbbasket.ru/vol{self.artikul[:4]}/part{self.artikul[:6]}/{self.artikul}/info/price-history.json'
        else:
            price_history_searcher_url = f'https://basket-{basket_num}.wbbasket.ru/vol{self.artikul[:3]}/part{self.artikul[:5]}/{self.artikul}/info/price-history.json'
        response = self.scraper.get(price_history_searcher_url, headers=self.headers)
        json_data = json.loads(response.text)
        return json_data
    

    @transaction.atomic
    def add_product_to_db(self, new_product, price_history):
        #сохраняем элемент
        new_product.save()
        #добавляем many-to-many связь (почему то через автора всегда быстрее)
        Author.objects.get(id=self.author_id).wbproduct_set.add(new_product)
        WBPrice.objects.bulk_create(price_history)
    

    #js скрипт на wb для определения сервера
    @staticmethod
    def get_basket_num(artikul: int):
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

