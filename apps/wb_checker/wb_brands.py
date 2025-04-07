import os
import psutil
from requests import request
import re
import json
import cloudscraper
from datetime import datetime
import apps.wb_checker.utils as utils
from .models import WBProduct, WBSeller, WBPrice, WBCategory, WBBrand, WBPreset
from apps.blog.models import Author
from django.utils import timezone
import math
import time
from functools import wraps
from django.db import transaction



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
            self.number_of_pages = self.get_number_of_pages_in_catalog()
            self.brand_object = self.build_raw_brand_object()
            self.preset_object = self.build_raw_preset_object(raw_brand_url)
            self.potential_repetitions = self.get_repetitions_catalog_brand()
            self.sellers_in_db_dict = dict(map(lambda x: (x.wb_id, x), WBSeller.objects.all()))
            self.product_repetitions_list = []
            self.sellers_to_add = []
            self.brand_products_to_add = []



    @utils.time_count
    def run(self):
        '''Запуск процесса парсинга'''
        if self.dest_avaliable:
            self.get_catalog_of_brand()
            self.add_all_to_db()
    


    @utils.time_count
    def get_catalog_of_brand(self):
        '''Функция, которая:
        1. Парсит товар
        2. Проверяет его на повторку
        3. Проверяет наличие бренда (откладывает новые в кэш)
        4. Добавляет в кэш новые объекты цены и продукта, если они прошли проверку на повторки'''
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
                self.total_products -= 1
                product_artikul = products_on_page[i]['id'] #специально получаю артикул продукта здесь для того, чтобы передать в функцию проверки на повторки
                if self.potential_repetitions:
                    if self.check_repetition_in_catalog(product_artikul): continue
                seller_artikul = products_on_page[i]['supplierId']
                seller_name = products_on_page[i]['supplier']
                seller_object = self.check_seller_existance(seller_artikul, seller_name) #проверка селлера на наличие в БД + откладывание его в кэш (только селлера, тк бренд уже в базе)
                self.add_new_product(product_in_catalog=products_on_page[i], seller_object=seller_object, product_artikul = product_artikul)
                if self.total_products == 0: return
            if self.total_products == 0: return



    @transaction.atomic
    @utils.time_count
    def add_all_to_db(self):
        '''Функция добавления всех изменений в БД атомарной транзакцией'''
        WBBrand.objects.bulk_create([self.brand_object], update_conflicts=True, unique_fields=['wb_id'], update_fields=['name'])
        WBSeller.objects.bulk_create(self.sellers_to_add, update_conflicts=True, unique_fields=['wb_id'], update_fields=['name'])
        WBProduct.objects.bulk_create(self.brand_products_to_add, update_conflicts=True, unique_fields=['artikul'], update_fields=['name']) #ссылается не на id а на wb_id добавленного бренда (тк оно уникальное)
        artikuls_to_add_price = (list(map(lambda x: x.artikul, self.brand_products_to_add))) #вытаскиваем артикулы, которые точно нужно добавить (независимо от процессов)
        products_to_add_price = list(WBProduct.objects.filter(artikul__in=artikuls_to_add_price).prefetch_related('wbprice_set')) #вытаскиваем из бд продукты, которые несуществуют для этого процесса
        updated_prices = []
        for elem in products_to_add_price:
            if not elem.wbprice_set.exists(): #проверяем, не проставили ли другие процессы цену у этого продукта => продукт уже полностью добавлен другим процессом, и цена не нужна
                updated_prices.append(WBPrice(price=elem.latest_price,
                            added_time=timezone.now(),
                            product=elem))
        WBPrice.objects.bulk_create(updated_prices) #добавляю элементы одной командой
        self.brand_products_to_add.extend(self.product_repetitions_list) #опять же, связи добавятся, потому что у этих продуктов есть уникальное поле артикула + 
        self.preset_object.save()
        self.preset_object.products.set(self.brand_products_to_add)
        self.author_object.enabled_authors.add(*self.brand_products_to_add) #many-to-many связь через автора (вставляется сразу все) - обязательно распаковать список
        self.author_object.save()


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

        def repl_plus_4(match_obj):
            number = match_obj.group(1)
            number_in_str = str((int(number) + 4))
            return f'fdlvr={number_in_str}'
        
        if 'fdlvr' in addons:
            addons = re.sub(pattern=r'fdlvr\=(?P<number>\d+?)\&', repl=repl_plus_4, string=addons)
        return f'https://catalog.wb.ru/brands/v2/catalog?ab_testing=false&appType=1&curr=rub&dest={self.author_object.dest_id}&hide_dtype=13&lang=ru&spp=30&uclusters=3&page=1&brand={self.brand_artikul}&sort={sorting}{addons}'



    def get_total_products_and_name_brand_in_catalog(self):
        '''Получение количества продуктов для парсинга + 
        имя бренда (для создания объекта бренда при его отсутствии в БД)'''
        response = self.scraper.get(self.brand_api_url, headers=self.headers)
        json_data = json.loads(response.text)
        try:
            total_products = json_data['data']['total']
            brand_name = json_data['data']['products'][0]['brand']
        except:
            print('Не найдено ни одного товара (скорее всего они недоступны в вашем регионе)')
            self.dest_avaliable = False
            return 0, None
        #точка входа для вопроса пользователю - сколько продуктов нужно взять, если их больше 10
        print(f'Товары обнаружены! Бренд - {brand_name}. Количество - {total_products}')
        print(f'Доступных слотов для отслеживания продуктов: {self.author_object.slots}')
        if total_products > 10:
            while True:
                print('Введите количество продуктов, которые нужно сохранить (первые N)')
                try:
                    custom_total_products = int(input())
                    if custom_total_products > total_products:
                        print('Введено число, превышающее количество найденных продуктов, попробуйте снова')
                        continue
                    if custom_total_products > self.author_object.slots:
                        print(f'Недостаточно слотов для отслеживания продуктов. Доступных слотов - {self.author_object.slots}')
                        continue
                    break
                except:
                    print('Введено некорректное число, попробуйте снова')
        else:
            custom_total_products = total_products
        self.author_object.slots = self.author_object.slots-custom_total_products
        return custom_total_products, brand_name



    def get_number_of_pages_in_catalog(self):
        '''Получение количества страниц для парсинга 
        плюс настройка ограничения в 100 страниц'''
        number_of_pages = math.ceil(self.total_products/100)
        if number_of_pages > 100:
            number_of_pages = 100
        return number_of_pages
    


    def build_raw_brand_object(self):
        '''Создание объекта бренда без занесения в БД и знания,
          есть ли уже такой объект в базе (если есть и будет конфликт => 
          все пройдет правильно из-за уникального wb_id)'''
        return WBBrand(wb_id=self.brand_artikul,
                    name=self.brand_name,
                    main_url=f'https://www.wildberries.ru/seller/{self.brand_artikul}')
    


    def build_raw_preset_object(self, raw_brand_url):
        '''Создание объекта пресета без лишнего обращения в БД (конфликтов нет - заносится в любом случае)'''
        return WBPreset(name=f'Товары бренда {self.brand_object.name} ({self.total_products} шт.)',
                        main_url = raw_brand_url,
                        max_elems = self.total_products,
                        author_id=self.author_id)
    


    @utils.time_count
    def get_repetitions_catalog_brand(self):
        '''Функция взятия всех продуктов + артикулов в БД бренда, 
        по которому будет производиться парсинг (при его наличии)'''
        potential_repetitions = []
        potential_repetitions = WBProduct.objects.filter(brand__wb_id=self.brand_object.wb_id)
        potential_repetitions = dict(map(lambda x: (x.artikul, x), potential_repetitions))
        return potential_repetitions



    def check_repetition_in_catalog(self, product_artikul_to_check):
        '''Проверка на дубликат продукта в получаемом каталоге'''
        potential_repetition = self.potential_repetitions.get(product_artikul_to_check)
        if potential_repetition:
            self.product_repetitions_list.append(potential_repetition)
            return True
        


    def check_seller_existance(self, seller_artikul, seller_name):
        '''Проверка продавца на существование в БД + откладывание его в кэш при отсутствии'''
        if not self.sellers_in_db_dict.get(seller_artikul):
            seller_object = WBSeller(name=seller_name,
                        wb_id=seller_artikul,
                        main_url=f'https://www.wildberries.ru/seller/{seller_artikul}', #баг только с самим вб
                        full_control = False)
            self.sellers_to_add.append(seller_object) #добавляем в список для добавления в БД
            self.sellers_in_db_dict.update({seller_artikul:seller_object})
        else:
            seller_object = self.sellers_in_db_dict[seller_artikul]
        return seller_object



    def add_new_product(self, product_in_catalog, seller_object, product_artikul):
        '''Сборка объекта продукта и объекта цены + добавление их в кэш'''
        product_url = f'https://www.wildberries.ru/catalog/{product_artikul}/detail.aspx'
        name = product_in_catalog['name']
        price_element = product_in_catalog['sizes'][0]['price']['product'] // 100
        new_product = WBProduct(name=name,
                artikul=product_artikul,
                latest_price=price_element,
                wb_cosh=True,
                url=product_url,
                brand=self.brand_object,
                seller=seller_object)
        self.brand_products_to_add.append(new_product)
        


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

