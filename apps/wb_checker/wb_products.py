import os
import time
import psutil
from requests import request
import re
import json
import cloudscraper
from datetime import datetime
import apps.wb_checker.utils as utils
from .models import WBProduct, WBSeller, WBBrand, WBPrice, WBDetailedInfo
from apps.blog.models import Author
from django.utils import timezone
import math
from .utils import time_count
from django.db import transaction



class Product:
    def __init__(self, product_url, author_object):
        '''Инициализация необходимых атрибутов'''
        self.product_url = product_url
        self.author_object = author_object
        self.author_id = author_object.id
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.scraper = cloudscraper.create_scraper()
        self.artikul = re.search(r'\/(\d+)\/', product_url).group(1)
        self.product_url_api = f'https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest={self.author_object.dest_id}&spp=30&ab_testing=false&lang=ru&nm={self.artikul}'
        self.product_name, self.product_size, self.product_volume, self.product_price = self.get_product_detailed_info()

    @utils.time_count
    def get_product_info(self):
        '''Функция сборки продукта'''
        if self.product_volume == 0: enabled = False 
        else: enabled = True
        response = self.scraper.get(self.product_url_api, headers=self.headers)
        json_data = json.loads(response.text)
        seller_name = json_data['data']['products'][0]['supplier'] #имя продавца
        seller_artikul = json_data['data']['products'][0]['supplierId'] #id продавца
        brand_name = json_data['data']['products'][0]['brand'] #имя бренда
        brand_artikul = json_data['data']['products'][0]['brandId'] #id бренда
        brand_object = Product.build_raw_brand_object(brand_name, brand_artikul)
        seller_object = Product.build_raw_seller_object(seller_name, seller_artikul)  
        #добавляем элемент
        new_product = WBProduct(name=self.product_name,
                artikul=self.artikul,
                wb_cosh=True,
                url=self.product_url.split('?')[0],
                seller=seller_object,
                brand=brand_object)
        new_detailed_info = WBDetailedInfo(latest_price=self.product_price,
                                           size=self.product_size,
                                           volume=self.product_volume,
                                           enabled=enabled,
                                           author_id=self.author_id,
                                           product=new_product)
        new_price = WBPrice(price=self.product_price,
                            added_time=timezone.now(),
                            detailed_info=new_detailed_info)
        self.add_product_to_db(new_product, new_detailed_info, new_price)


    @staticmethod
    def build_raw_seller_object(seller_name, seller_artikul):
        '''Создание объекта селлера без лишнего обращения в БД'''
        return WBSeller(wb_id=seller_artikul,
                        name=seller_name,
                        main_url=f'https://www.wildberries.ru/seller/{seller_artikul}')
    

    @staticmethod
    def build_raw_brand_object(brand_name, brand_artikul):
        '''Создание объекта бренда без лишнего обращения в БД'''
        return WBBrand(wb_id=brand_artikul,
                    name=brand_name,
                    main_url=f'https://www.wildberries.ru/seller/{brand_artikul}')
    


    def get_product_detailed_info(self):
        response = self.scraper.get(self.product_url_api, headers=self.headers)
        json_data = json.loads(response.text)
        name = json_data['data']['products'][0]['name']
        sizes = json_data['data']['products'][0]['sizes']
        sizes_dict = dict()
        for size in sizes:
            volume_of_size = 0
            price_of_size = 0
            if len(size['stocks']) != 0:
                price_of_size = size['price']['product']//100
            for stock in size['stocks']:
                volume_of_size += stock['qty']
            sizes_dict.update({size['origName']: (volume_of_size, price_of_size)})
        if len(list(sizes_dict.keys())) == 1 and list(sizes_dict.keys())[0] == '0':
            print(f'Товар обнаружен!\nНазвание: {name}.\nПрисутствует только 1 вариант.')
            return name, None, sizes_dict['0'][0], sizes_dict['0'][1]
        print(f'Товар обнаружен!\nНазвание: {name}.\nДоступные варианты:')
        for size, volume_and_price in sizes_dict.items():
            print(f'Вариант: {size}. Количество: {volume_and_price[0]}. Цена: {volume_and_price[1]}')
        print('Введите имя варианта, который нужно выбрать')
        while True:
            user_size = input()
            if sizes_dict.get(user_size) is None: 
                print('Введено неправильное имя варианта, попробуйте снова')
                continue
            break
        return name, user_size, sizes_dict[user_size][0], sizes_dict[user_size][1]
    
    @utils.time_count
    @transaction.atomic
    def add_product_to_db(self, new_product, new_detailed_info, new_price):
        '''Функция добавления всех изменений в БД атомарной транзакцией'''
        #сохраняем элемент
        WBBrand.objects.bulk_create([new_product.brand], update_conflicts=True, unique_fields=['wb_id'], update_fields=['name'])
        WBSeller.objects.bulk_create([new_product.seller], update_conflicts=True, unique_fields=['wb_id'], update_fields=['name'])
        WBProduct.objects.bulk_create([new_product], update_conflicts=True, unique_fields=['artikul'], update_fields=['name'])
        new_detailed_info, was_not_in_db = WBDetailedInfo.objects.get_or_create(latest_price=self.product_price,
                                           size=self.product_size,
                                           volume=self.product_volume,
                                           enabled=new_detailed_info.enabled,
                                           author_id=self.author_id,
                                           product=new_product)
        if was_not_in_db:
            new_price.detailed_info = new_detailed_info
            new_price.save()
            self.author_object.slots -= 1
            self.author_object.save()
        else:
            print('Товар уже есть в отслеживании')
    


    # @staticmethod
    # def get_basket_num(artikul: int):
    #     '''Определение сервера, на котором находится история цены по js скрипту на wb'''
    #     s = artikul // 100000  # Разделение артикулов на группы
    #     if s <= 143:
    #         return 1
    #     elif s <= 287:
    #         return 2
    #     elif s <= 431:
    #         return 3
    #     elif s <= 719:
    #         return 4
    #     elif s <= 1007:
    #         return 5
    #     elif s <= 1061:
    #         return 6
    #     elif s <= 1115:
    #         return 7
    #     elif s <= 1169:
    #         return 8
    #     elif s <= 1313:
    #         return 9
    #     elif s <= 1601:
    #         return 10
    #     elif s <= 1655:
    #         return 11
    #     elif s <= 1919:
    #         return 12
    #     elif s <= 2045:
    #         return 13
    #     elif s <= 2189:
    #         return 14
    #     elif s <= 2405:
    #         return 15
    #     elif s <= 2621:
    #         return 16
    #     elif s <= 2837:
    #         return 17
    #     elif s <= 3053:
    #         return 18
    #     elif s <= 3269:
    #         return 19
    #     elif s <= 3485:
    #         return 20
    #     elif s <= 3701:
    #         return 21
    #     elif s <= 3917:
    #         return 22
    #     elif s <= 4133:
    #         return 23
    #     elif s <= 4349:
    #         return 24
    #     elif s <= 4565:
    #         return 25
    #     else:
    #         return 26



    # @time_count
    # def get_repetition_or_run(self):
    #     '''Проверка на повторки среди считываемых продуктов и продуктов бренда, которые уже существуют в БД'''

    #     repeated_product = WBProduct.objects.filter(artikul=self.artikul) #посмотреть, как сделать так, чтобы get - функция не выдавала исключения
    #     if repeated_product and len(repeated_product) == 1: #если нашел повторюшку
    #         repeated_product = repeated_product[0]
    #         authors_list = repeated_product.enabled_connection.all() #проверяет, нет ли уже того же автора у этой повторюшки
    #         for elem in authors_list: #выводит ворнинг, если такой же автор
    #             if elem.id == self.author_id:
    #                 print('Товар уже есть в отслеживании')
    #                 return
    #             if elem.dest_id == self.author_object.dest_id:
    #                 repeated_product.enabled_connection.add(Author.objects.get(id=self.author_id)) #если не нашел автора и не выкинуло из функции, то добавляет many-to-many связь (попробовать написать через автора)
    #                 return
    #     self.get_product_info()

    # def get_price_history(self):
    #     '''Функция получения истории цены продукта'''
    #     basket_num = Product.get_basket_num(int(self.artikul))
    #     if basket_num < 10:
    #         basket_num = f'0{basket_num}'
    #     if len(self.artikul) == 9:
    #         price_history_searcher_url = f'https://basket-{basket_num}.wbbasket.ru/vol{self.artikul[:4]}/part{self.artikul[:6]}/{self.artikul}/info/price-history.json'
    #     elif len(self.artikul) == 9:
    #         price_history_searcher_url = f'https://basket-{basket_num}.wbbasket.ru/vol{self.artikul[:3]}/part{self.artikul[:5]}/{self.artikul}/info/price-history.json'
    #     elif len(self.artikul) == 7:
    #         price_history_searcher_url = f'https://basket-{basket_num}.wbbasket.ru/vol{self.artikul[:2]}/part{self.artikul[:4]}/{self.artikul}/info/price-history.json'
    #     elif len(self.artikul) == 6:
    #         price_history_searcher_url = f'https://basket-{basket_num}.wbbasket.ru/vol{self.artikul[:1]}/part{self.artikul[:3]}/{self.artikul}/info/price-history.json'
    #     response = self.scraper.get(price_history_searcher_url, headers=self.headers)
    #     json_data = json.loads(response.text)
    #     return json_data