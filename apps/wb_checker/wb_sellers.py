import re
import json
import cloudscraper
import apps.wb_checker.utils as utils
from .models import WBProduct, WBBrand, WBPrice, WBCategory
from apps.blog.models import Author
from django.utils import timezone
import math
from django.db import transaction



class Seller:
    def __init__(self, seller_url, author_object):
        '''Инициализация необходимых атрибутов'''
        self.seller_url = self.check_url_and_send_correct(seller_url)
        self.author_object = author_object
        self.author_id = author_object.id #не стал везде в коде менять, оставил автор айди (просто взял из объекта)
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.scraper = cloudscraper.create_scraper()
        self.seller_artikul = self.get_seller_artikul()
        self.seller_api_url = self.construct_seller_api_url()
        self.total_products, self.seller_name = self.get_total_products_and_name_seller_in_catalog()
        self.number_of_pages = self.get_number_of_pages_in_catalog()
        self.seller_object, self.seller_was_in_db = utils.check_existence_of_seller(self.seller_name, self.seller_artikul)
        self.potential_repetitions = self.get_repetitions_catalog_seller()
        self.brands_in_db = list(WBBrand.objects.all())
        self.brand_wb_id_in_db = list(map(lambda x: x.wb_id, self.brands_in_db))
        self.product_repetitions_list = []
        self.brands_to_add = []
        self.brands_wb_ids_to_add = []
        self.seller_products_to_add = []
        self.seller_prices_to_add = []



    @utils.time_count
    def run(self):
        '''Функция запуска процесса парсинга'''
        self.get_catalog_of_seller()
        self.add_all_to_db()



    @utils.time_count
    def get_repetitions_catalog_seller(self):
        '''Функция проверки селлера в БД, и, если селлер есть - 
        берет все его продукты (потенциальные повторки)'''
        potential_repetitions = []
        #если селлер уже есть в БД, берет все продукты этого селлера вместе с их артикулами
        if self.seller_was_in_db:
            potential_repetitions = WBProduct.enabled_products.filter(seller=self.seller_object)
            potential_repetitions = dict(map(lambda x: (x.artikul, x), potential_repetitions))
        return potential_repetitions
    


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
                product_artikul = products_on_page[i]['id'] #специально получаю артикул продукта для того, чтобы передать в функцию проверки на повторки
                if self.potential_repetitions:
                    if self.check_repetition_in_catalog(product_artikul): continue
                brand_artikul = products_on_page[i]['brandId']
                brand_name = products_on_page[i]['brand'] #проверка бренда на наличие в БД плюс откладывание его в кэш (только бренд, тк селлер уже в базе)
                brand_object = self.check_brand_existance(brand_artikul, brand_name) #отдает объект бренда без заходов в БД постоянных
                self.add_new_product_and_price(product_in_catalog=products_on_page[i], brand_object=brand_object, product_artikul = product_artikul)



    @transaction.atomic
    @utils.time_count
    def add_all_to_db(self):
        '''Функция добавления всех изменений в БД атомарной транзакцией'''
        WBBrand.objects.bulk_create(self.brands_to_add)
        WBProduct.objects.bulk_create(self.seller_products_to_add) #добавляю элементы одной командой
        WBPrice.objects.bulk_create(self.seller_prices_to_add) #добавляю элементы одной командой
        self.seller_products_to_add.extend(self.product_repetitions_list) #возможно можно как то проверять повторки, были ли они уже в остлеживании или нет именно у этого автора
        Author.objects.get(id=self.author_id).wbproduct_set.add(*self.seller_products_to_add) #many-to-many связь через автора (вставляется сразу все) - обязательно распаковать список


    
    def get_seller_artikul(self):
        '''Получение арттикула (wb_id) селлера'''
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
        return f'https://catalog.wb.ru/sellers/v2/catalog?ab_testing=false&appType=1&curr=rub&dest={self.author_object.dest_id}&hide_dtype=13&lang=ru&spp=30&uclusters=0&page=1&supplier={self.seller_artikul}&sort={sorting}{addons}'



    def get_total_products_and_name_seller_in_catalog(self):
        '''Получение количества продуктов для парсинга + 
        имя селлера (для создания объекта бренда при его отсутствии в БД)'''
        response = self.scraper.get(self.seller_api_url, headers=self.headers)
        json_data = json.loads(response.text)
        total_products = json_data['data']['total']
        seller_name = json_data['data']['products'][0]['supplier']
        return total_products, seller_name



    def get_number_of_pages_in_catalog(self):
        '''Получение количества страниц для парсинга 
        плюс настройка ограничения в 100 страниц'''
        number_of_pages = math.ceil(self.total_products/100)
        if number_of_pages > 100:
            number_of_pages = 100
        return number_of_pages



    def check_repetition_in_catalog(self, product_artikul_to_check):
        '''Проверка на дубликат продукта в получаемом каталоге'''
        potential_repetition = utils.check_repetitions_catalog(product_artikul_to_check, self.potential_repetitions)
        if potential_repetition:
            self.product_repetitions_list.append(potential_repetition)
            return True
        


    def check_brand_existance(self, brand_artikul, brand_name):
        '''Проверка бренда на существование в БД + откладывание его в кэш при отсутствии'''
        if brand_artikul not in self.brand_wb_id_in_db:
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
            self.brands_in_db.append(brand_object) #чтобы уже не повторялся (если попадется бренд, который еще не добавлен в БД, но добавлен в кэш)
            self.brand_wb_id_in_db.append(brand_artikul)
        else:
            brand_object = self.brands_in_db[self.brand_wb_id_in_db.index(brand_artikul)]
        return brand_object


    def add_new_product_and_price(self, product_in_catalog, brand_object, product_artikul):
        '''Сборка объекта продукта и объекта цены + добавление их в кэш'''
        product_url = f'https://www.wildberries.ru/catalog/{product_artikul}/detail.aspx'
        name = product_in_catalog['name']
        price_element = product_in_catalog['sizes'][0]['price']['product'] // 100
        new_product = WBProduct(name=name,
                artikul=product_artikul,
                latest_price=price_element,
                wb_cosh=True,
                url=product_url,
                enabled=True,
                seller=self.seller_object,
                brand=brand_object)
        new_product_price = WBPrice(price=price_element,
                                added_time=timezone.now(),
                                product=new_product)
        self.seller_products_to_add.append(new_product)
        self.seller_prices_to_add.append(new_product_price)

    def check_url_and_send_correct(self, url):
        '''Проверка url, отправленного пользователем, на предмет 
        парсинга бренда по продукту или парсинга бренда по прямой ссылке'''
        if 'seller' in url:
            return url
        else:
            response = self.scraper.get(f'https://card.wb.ru/cards/v2/list?appType=1&curr=rub&dest={self.author_object.dest_id}&spp=30&ab_testing=false&lang=ru&nm={re.search(r'\/(\d+)\/', url).group(1)}', headers=self.headers)
            json_data = json.loads(response.text)
            return f'https://www.wildberries.ru/seller/{json_data['data']['products'][0]['supplierId']}'
        