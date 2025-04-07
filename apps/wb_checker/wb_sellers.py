import re
import json
import time
import cloudscraper
import apps.wb_checker.utils as utils
from .models import WBProduct, WBBrand, WBPrice, WBCategory, WBSeller, WBPreset
from apps.blog.models import Author
from django.utils import timezone
import math
from django.db import transaction



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
            self.number_of_pages = self.get_number_of_pages_in_catalog()
            self.seller_object = self.build_raw_seller_object()
            self.preset_object = self.build_raw_preset_object(raw_seller_url)
            self.potential_repetitions = self.get_repetitions_catalog_seller()
            self.brand_in_db_dict = dict(map(lambda x: (x.wb_id, x), WBBrand.objects.all()))
            self.product_repetitions_list = []
            self.brands_to_add = []
            self.seller_products_to_add = []



    @utils.time_count
    def run(self):
        '''Функция запуска процесса парсинга'''
        if self.dest_avaliable:
            self.get_catalog_of_seller()
            self.add_all_to_db()


    @utils.time_count
    def get_catalog_of_seller(self):
        '''Функция, которая:
        1. Парсит товар
        2. Проверяет его на повторку
        3. Проверяет наличие бренда (откладывает новые в кэш)
        4. Добавляет в кэш новые объекты цены и продукта, если они прошли проверку на повторки'''
        for elem in range(1, self.number_of_pages + 1):
            self.seller_api_url = re.sub(pattern=r'page=\d+\&', repl=f'page={elem}&', string=self.seller_api_url)
            response = self.scraper.get(self.seller_api_url, headers=self.headers)
            json_data = json.loads(response.text)
            products_on_page = json_data['data']['products']
            for i in range(len(products_on_page)):
                self.total_products -= 1
                product_artikul = products_on_page[i]['id'] #специально получаю артикул продукта для того, чтобы передать в функцию проверки на повторки
                if self.potential_repetitions:
                    if self.check_repetition_in_catalog(product_artikul): continue
                brand_artikul = products_on_page[i]['brandId']
                brand_name = products_on_page[i]['brand'] #проверка бренда на наличие в БД плюс откладывание его в кэш (только бренд, тк селлер уже в базе)
                brand_object = self.check_brand_existance(brand_artikul, brand_name) #отдает объект бренда без заходов в БД постоянных
                self.add_new_product(product_in_catalog=products_on_page[i], brand_object=brand_object, product_artikul = product_artikul)
                if self.total_products == 0: return
            if self.total_products == 0: return #как то получше написать надо






    @utils.time_count
    @transaction.atomic
    def add_all_to_db(self):
        '''Функция добавления всех изменений в БД атомарной транзакцией'''
        #добавляю селлеров, брендов и продукты
        WBSeller.objects.bulk_create([self.seller_object], update_conflicts=True, unique_fields=['wb_id'], update_fields=['name'])
        WBBrand.objects.bulk_create(self.brands_to_add, update_conflicts=True, unique_fields=['wb_id'], update_fields=['name'])
        WBProduct.objects.bulk_create(self.seller_products_to_add, update_conflicts=True, unique_fields=['artikul'], update_fields=['name']) #ссылается не на id а на wb_id добавленного бренда (тк оно уникальное)
        #добавляю цены
        artikuls_to_add_price = (list(map(lambda x: x.artikul, self.seller_products_to_add)))
        products_to_add_price = list(WBProduct.objects.filter(artikul__in=artikuls_to_add_price).prefetch_related('wbprice_set'))
        updated_prices = []
        for elem in products_to_add_price:
            if not elem.wbprice_set.exists():
                updated_prices.append(WBPrice(price=elem.latest_price,
                            added_time=timezone.now(),
                            product=elem))
        WBPrice.objects.bulk_create(updated_prices) #добавляю элементы одной командой
        #объединяю повторки с новыми продуктами для добавлеия many-to-many связи с автором и пресетом
        self.seller_products_to_add.extend(self.product_repetitions_list) #опять же, связи добавятся, потому что у этих продуктов есть уникальное поле артикула + расширяем повторками, которые процесс смог забрать
        self.preset_object.save()
        self.preset_object.products.set(self.seller_products_to_add)
        self.author_object.enabled_authors.add(*self.seller_products_to_add) #many-to-many связь через автора (вставляется сразу все) - обязательно распаковать список
        self.author_object.save() #для обновления слотов

    
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
        clear_seller_url = re.sub(pattern=r'\#.+', repl='', string=self.seller_url)
        sorting = 'popular'
        addons = []
        if '?' in clear_seller_url:
            addons = clear_seller_url.split('?')[1]
            addons = addons.split('&')
            for elem in addons:
                if 'sort' in elem:
                    sorting = elem.split('=')[1]
        category = re.search(r'(seller\/)([a-z\-\d]+\/)([a-z\-]+)(\?)?(\#)?', clear_seller_url) #выцепляю категорию
        if category: 
            category_wb_id = (WBCategory.objects.get(url=category.group(3))).wb_id
            addons.append(f'subject={category_wb_id}')
        if addons: addons =f"&{'&'.join(list(filter(lambda x: True if 'page' not in x and 'sort' not in x and 'bid' not in x and 'erid' not in x else False, addons)))}"
        else: addons = ''

        def repl_plus_4(match_obj):
            number = match_obj.group(1)
            number_in_str = str((int(number) + 4))
            return f'fdlvr={number_in_str}'
        
        if 'fdlvr' in addons:
            addons = re.sub(pattern=r'fdlvr\=(?P<number>\d+?)\&', repl=repl_plus_4, string=addons)
        return f'https://catalog.wb.ru/sellers/v2/catalog?ab_testing=false&appType=1&curr=rub&dest={self.author_object.dest_id}&hide_dtype=13&lang=ru&spp=30&uclusters=0&page=1&supplier={self.seller_artikul}&sort={sorting}{addons}'



    def get_total_products_and_name_seller_in_catalog(self):
        '''Получение количества продуктов для парсинга + 
        имя селлера (для создания объекта бренда при его отсутствии в БД)'''
        response = self.scraper.get(self.seller_api_url, headers=self.headers)
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
        return custom_total_products, seller_name



    def get_number_of_pages_in_catalog(self):
        '''Получение количества страниц для парсинга 
        плюс настройка ограничения в 100 страниц'''
        number_of_pages = math.ceil(self.total_products/100)
        if number_of_pages > 100:
            number_of_pages = 100
        return number_of_pages
    


    def build_raw_seller_object(self):
        '''Создание объекта селлера без занесения в БД и знания,
          есть ли уже такой объект в базе (если есть и будет конфликт => 
          все пройдет правильно из-за уникального wb_id)'''
        return WBSeller(wb_id=self.seller_artikul,
                        name=self.seller_name,
                        main_url=f'https://www.wildberries.ru/seller/{self.seller_artikul}')
    


    def build_raw_preset_object(self, raw_seller_url): #в атомарке засейвить плюс добавить связь
        '''Создание объекта пресета без лишнего обращения в БД (конфликтов нет - заносится в любом случае)'''
        return WBPreset(name=f'Товары продавца {self.seller_object.name} ({self.total_products} шт.)',
                        main_url = raw_seller_url,
                        max_elems = self.total_products,
                        author_id=self.author_id)



    @utils.time_count
    def get_repetitions_catalog_seller(self):
        '''Функция проверки селлера в БД, и, если селлер есть - 
        берет все его продукты (потенциальные повторки)'''
        potential_repetitions = []
        #поиск по индексируемому полю wb_id такой же быстрый как и по id
        potential_repetitions = WBProduct.objects.filter(seller__wb_id=self.seller_object.wb_id)
        potential_repetitions = dict(map(lambda x: (x.artikul, x), potential_repetitions))
        return potential_repetitions
    


    def check_repetition_in_catalog(self, product_artikul_to_check):
        '''Проверка на дубликат продукта в получаемом каталоге'''
        potential_repetition = self.potential_repetitions.get(product_artikul_to_check)
        if potential_repetition:
            self.product_repetitions_list.append(potential_repetition)
            return True
        


    def check_brand_existance(self, brand_artikul, brand_name):
        '''Проверка бренда на существование в БД + откладывание его в кэш при отсутствии'''
        if not self.brand_in_db_dict.get(brand_artikul):
            if brand_artikul == 0:
                brand_object = WBBrand(name='Без бренда',
                        wb_id=brand_artikul,
                        main_url=f'https://www.wildberries.ru/',
                        full_control = False)
            else:
                brand_object = WBBrand(name=brand_name,
                            wb_id=brand_artikul,
                            main_url=f'https://www.wildberries.ru/brands/{brand_artikul}',
                            full_control = False)
            self.brands_to_add.append(brand_object) #добавляем в список для добавления в БД
            self.brand_in_db_dict.update({brand_artikul:brand_object})
        else:
            brand_object = self.brand_in_db_dict[brand_artikul]#создаю нецелостный объект + при добавлении продукта все равно сработает, тк wb_id уникален
        return brand_object



    def add_new_product(self, product_in_catalog, brand_object, product_artikul):
        '''Сборка объекта продукта + добавление их в кэш'''
        product_url = f'https://www.wildberries.ru/catalog/{product_artikul}/detail.aspx'
        name = product_in_catalog['name']
        price_element = product_in_catalog['sizes'][0]['price']['product'] // 100
        new_product = WBProduct(name=name,
                artikul=product_artikul,
                latest_price=price_element,
                wb_cosh=True,
                url=product_url,
                seller=self.seller_object,
                brand=brand_object)
        self.seller_products_to_add.append(new_product)



    def check_url_and_send_correct(self, raw_url):
        '''Проверка url, отправленного пользователем, на предмет 
        парсинга бренда по продукту или парсинга бренда по прямой ссылке'''
        if 'seller' in raw_url:
            return raw_url
        else:
            response = self.scraper.get(f'https://card.wb.ru/cards/v2/list?appType=1&curr=rub&dest={self.author_object.dest_id}&spp=30&ab_testing=false&lang=ru&nm={re.search(r'\/(\d+)\/', raw_url).group(1)}', headers=self.headers)
            json_data = json.loads(response.text)
            return f'https://www.wildberries.ru/seller/{json_data['data']['products'][0]['supplierId']}'
        