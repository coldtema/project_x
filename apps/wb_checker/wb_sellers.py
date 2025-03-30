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
    def __init__(self, seller_url, author_id):
        self.seller_url = seller_url
        self.author_id = author_id
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
        '''Функция проверки селлера в БД, и, если селлер есть - берет все его продукты (потенциальные повторки)'''
        potential_repetitions = []
        #если селлер уже есть в БД, берет все продукты этого селлера вместе с их артикулами
        if self.seller_was_in_db:
            potential_repetitions = WBProduct.enabled_products.filter(seller=self.seller_object)
            potential_repetitions = dict(map(lambda x: (x.artikul, x), potential_repetitions))
        return potential_repetitions
    

    #https://www.wildberries.ru/seller/simaland-35167
    @utils.time_count
    def get_catalog_of_seller(self):
        '''Функция, которая:
        1. Парсит товар
        2. Проверяет его на повторку
        3. Проверяет наличие бренда (откладывает новые в кэш)
        4. Добавляет в кэш новые объекты цены и продукта, если они прошли проверку на повторки'''
        #делает первый запрос для определения количества продуктов (total) + определение количества страниц для полного отображения каталога (продуктов на странице - 100!!)
        #проверяет наличие продавца в БД
        for elem in range(1, self.number_of_pages + 1):
            self.seller_api_url = re.sub(pattern=r'page=\d+\&', repl=f'page={elem}&', string=self.seller_api_url)
            response = self.scraper.get(self.seller_api_url, headers=self.headers)
            json_data = json.loads(response.text)
            products_on_page = json_data['data']['products']
            for i in range(len(products_on_page)):
                #специально получаю артикул продукта для того, чтобы передать в функцию проверки на повторки
                product_artikul = products_on_page[i]['id']
                if self.potential_repetitions:
                    if self.check_repetition_in_catalog(product_artikul): continue
                #проверка бренда на наличие в БД плюс откладывание его в кэш (только бренд, тк селлер уже в базе)
                brand_artikul = products_on_page[i]['brandId']
                brand_name = products_on_page[i]['brand']
                brand_object = self.check_brand_existance(brand_artikul, brand_name) #отдает объект бренда без заходов в БД постоянных
                self.add_new_product_and_price(product_in_catalog=products_on_page[i], brand_object=brand_object, product_artikul = product_artikul)


    @transaction.atomic
    @utils.time_count
    def add_all_to_db(self):
        '''Функция добавления всех изменений в БД атомарной транзакцией'''
        WBBrand.objects.bulk_create(self.brands_to_add)
        WBProduct.objects.bulk_create(self.seller_products_to_add) #добавляю элементы одной командой
        WBPrice.objects.bulk_create(self.seller_prices_to_add) #добавляю элементы одной командой
        self.seller_products_to_add.extend(self.product_repetitions_list)
        Author.objects.get(id=self.author_id).wbproduct_set.add(*self.seller_products_to_add) #many-to-many связь через автора (вставляется сразу все) - обязательно распаковать список


    #https://www.wildberries.ru/seller/simaland-exclusive
    #https://www.wildberries.ru/seller/simaland-exclusive?page=1&sort=priceup&fbrand=28172
    def get_seller_artikul(self):
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
            try:
                category_wb_id = (WBCategory.objects.get(url=category.group(3))).wb_id
                addons.append(f'subject={category_wb_id}')
            except:
                addons.append(self.get_custom_links_of_brand()[category.group(3)])
        if addons: addons =f"&{'&'.join(list(filter(lambda x: True if 'page' not in x and 'sort' not in x and 'bid' not in x and 'erid' not in x else False, addons)))}"
        else: addons = ''
        return f'https://catalog.wb.ru/sellers/v2/catalog?ab_testing=false&appType=1&curr=rub&dest=-1257786&hide_dtype=13&lang=ru&spp=30&uclusters=0&page=1&supplier={self.seller_artikul}&sort={sorting}{addons}'


    def get_total_products_and_name_seller_in_catalog(self):
        response = self.scraper.get(self.seller_api_url, headers=self.headers)
        json_data = json.loads(response.text)
        total_products = json_data['data']['total']
        seller_name = json_data['data']['products'][0]['supplier']
        return total_products, seller_name


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
        
    def check_brand_existance(self, brand_artikul, brand_name):
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
                seller=self.seller_object,
                brand=brand_object)
        #добавляем объект прайса
        new_product_price = WBPrice(price=price_element,
                                added_time=timezone.now(),
                                product=new_product)
        self.seller_products_to_add.append(new_product)
        self.seller_prices_to_add.append(new_product_price)
        