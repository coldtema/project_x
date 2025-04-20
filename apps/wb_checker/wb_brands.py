import re
import json
import cloudscraper
from datetime import datetime
from django.db import transaction
from .models import WBSeller, WBBrand, TopWBProduct
from apps.wb_checker.utils.top_prods import TopBuilder
from apps.blog.models import Author



class Brand:
    '''Класс для формирования списка топовых продуктов от определенного бренда с вб'''

    def __init__(self, brand_url, author_object):
        '''Инициализация необходимых атрибутов'''
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.scraper = cloudscraper.create_scraper()
        self.author_object = author_object
        self.author_id = author_object.id
        self.dest_avaliable = True
        self.brand_url = brand_url
        self.brand_artikul, self.brand_slug_name = self.get_brand_artikul_and_slug_name() 
        self.brand_api_url = self.construct_brand_api_url()
        self.total_products, self.brand_name = self.get_total_products_and_name_brand_in_catalog()
        if self.dest_avaliable:
            self.brand_object = self.build_raw_brand_object()
            self.dict_brand_products_to_add = dict()
            self.dict_sellers_to_add = dict()
            self.list_brand_products_to_add_with_scores = []
            self.final_dict_sellers_to_add = dict()



    def run(self):
        '''Запуск процесса построения топа продуктов'''
        if self.dest_avaliable:
            self.get_catalog_of_brand('popular')
            self.get_catalog_of_brand('benefit')
            self.get_catalog_of_brand('rate')
            self.build_top_prods()
            self.add_all_to_db()
        self.scraper.close()
    


    def get_catalog_of_brand(self, sorting):
        '''Функция, которая берет первую страницу бренда по разным сортировкам, 
        достает оттуда информацию о товарах, и вызывает функцию добавления этих 
        товаров в список для построения будущего топа'''
        brand_api_url = self.brand_api_url + sorting
        response = self.scraper.get(brand_api_url, headers=self.headers)
        json_data = json.loads(response.text)
        products_on_page = json_data['data']['products']
        for i in range(len(products_on_page)):
            self.add_new_product(product_in_catalog=products_on_page[i])



    def build_top_prods(self):
        '''Построение финального топа товаров с использованием класса TopBuilder'''
        top_builder = TopBuilder(self.dict_brand_products_to_add)
        print('Вычисляю топ продуктов бренда по цене/отзывам/рейтигу...')
        self.list_brand_products_to_add_with_scores = list(top_builder.build_top().values())
        self.list_brand_products_to_add_with_scores = sorted(self.list_brand_products_to_add_with_scores, key=lambda x: x.score)[-20:] 
        del top_builder
        for product in self.list_brand_products_to_add_with_scores:
            self.final_dict_sellers_to_add.setdefault(product.seller.wb_id, self.dict_sellers_to_add[product.seller.wb_id])



    @transaction.atomic
    def add_all_to_db(self):
        '''Функция добавления всех изменений в БД атомарной транзакцией'''
        WBBrand.objects.bulk_create([self.brand_object], update_conflicts=True, unique_fields=['wb_id'], update_fields=['name'])
        WBSeller.objects.bulk_create(self.final_dict_sellers_to_add.values(), update_conflicts=True, unique_fields=['wb_id'], update_fields=['name'])
        TopWBProduct.objects.bulk_create(self.list_brand_products_to_add_with_scores, ignore_conflicts=True) #ссылается не на id а на wb_id добавленного бренда (тк оно уникальное)
        self.author_object.wbbrand_set.add(self.brand_object)



    def get_brand_artikul_and_slug_name(self):
        '''Получение артикула (wb_id) бренда + id мини-сайта этого бренда'''
        brand_slug_name = re.search(r'(brands\/)([a-z\-\d]+)(\?)?(\/)?(\#)?', self.brand_url).group(2)
        final_url = f'https://static-basket-01.wbbasket.ru/vol0/data/brands/{brand_slug_name}.json'
        response = self.scraper.get(final_url, headers=self.headers)
        json_data = json.loads(response.text)
        brand_artikul = json_data['id']
        return brand_artikul, brand_slug_name



    def construct_brand_api_url(self):
        '''Построение url для доступа к api каталога бренда'''
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
        '''Создание объекта бренда с занесением в БД, и, 
        если бренд был в базе, и, если у него были подписчики, 
        то просто создается подписка на него у пользователя, вместо конструирования топа'''
        brand_object, was_not_in_db = WBBrand.objects.get_or_create(wb_id=self.brand_artikul, defaults={'name': self.brand_name,  
                                                                                                        'main_url': f'https://www.wildberries.ru/brands/{self.brand_slug_name}'})
        if not was_not_in_db and brand_object.subs.exists() and self.author_id != 4: #вот здесь надо поменять на админа потом или как то (тк это разграничитель между добавлением нового и обновлением)
            self.dest_avaliable = False
            self.author_object.wbbrand_set.add(brand_object)
        return brand_object
        


    def build_raw_seller_object(self, seller_artikul, seller_name):
        '''Проверка продавца на существование в БД + откладывание его в кэш при отсутствии'''
        seller_object = WBSeller(name=seller_name,
                    wb_id=seller_artikul,
                    main_url=f'https://www.wildberries.ru/seller/{seller_artikul}') #баг только с самим вб
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
                seller=seller_object,
                created=datetime.today(),
                source='BRAND')
        new_product = {product_artikul: new_product}
        self.dict_brand_products_to_add.update(new_product)
        



class TopWBProductBrandUpdater():
    def __init__(self):
        self.brands_with_subs = WBBrand.objects.filter(subs__isnull=False)
        

    def run(self):
        author_object = Author.objects.get(pk=4)
        for brand in self.brands_with_subs:
            TopWBProduct.objects.filter(source='BRAND', brand=brand).delete()
            Brand(brand.main_url, author_object).run()