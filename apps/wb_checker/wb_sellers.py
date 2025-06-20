import re
import json
import cloudscraper
from django.db import transaction
from datetime import datetime
from apps.wb_checker.utils.top_prods import TopBuilder
from .models import WBBrand, WBSeller, TopWBProduct
from apps.accounts.models import CustomUser
from apps.wb_checker.utils.general_utils import get_image_url



class Seller:
    '''Класс для формирования списка топовых продуктов от определенного селлера с вб'''

    def __init__(self, seller_url, author_object, celery_task=False):
        '''Инициализация необходимых атрибутов'''
        self.celery_task = celery_task
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.scraper = cloudscraper.create_scraper()
        self.author_object = author_object
        self.author_id = author_object.id
        self.dest_avaliable = True
        self.seller_url = seller_url
        self.seller_artikul = self.get_seller_artikul()
        self.seller_api_url = self.construct_seller_api_url()
        self.total_products, self.seller_name = self.get_total_products_and_name_seller_in_catalog()
        if self.dest_avaliable:
            self.seller_object = self.build_raw_seller_object()
            self.dict_brands_to_add = dict()
            self.dict_seller_products_to_add = dict()
            self.list_seller_products_to_add_with_scores = []
            self.final_dict_brands_to_add = dict()


    def run(self):
        '''Запуск процесса построения топа продуктов'''
        if self.dest_avaliable:
            self.get_catalog_of_seller('popular')
            self.get_catalog_of_seller('benefit')
            self.get_catalog_of_seller('rate')
            self.build_top_prods()
            self.add_all_to_db()
        self.scraper.close()



    def get_catalog_of_seller(self, sorting):
        '''Функция, которая берет первую страницу селлера по разным сортировкам, 
        достает оттуда информацию о товарах, и вызывает функцию добавления этих 
        товаров в список для построения будущего топа'''
        seller_api_url = self.seller_api_url + sorting
        response = self.scraper.get(seller_api_url, headers=self.headers)
        json_data = json.loads(response.text)
        products_on_page = json_data['data']['products']
        for i in range(len(products_on_page)):
            self.add_new_product(product_in_catalog=products_on_page[i])



    def build_top_prods(self):
        '''Построение финального топа товаров с использованием класса TopBuilder'''
        top_builder = TopBuilder(self.dict_seller_products_to_add)
        print('Вычисляю топ продуктов продавца по цене/отзывам/рейтигу...')
        self.list_seller_products_to_add_with_scores = list(top_builder.build_top().values())
        self.list_seller_products_to_add_with_scores = sorted(self.list_seller_products_to_add_with_scores, key=lambda x: x.score)[-20:]
        del top_builder
        for product in self.list_seller_products_to_add_with_scores:
            self.final_dict_brands_to_add.setdefault(product.brand.wb_id, self.dict_brands_to_add[product.brand.wb_id])


    @transaction.atomic
    def add_all_to_db(self):
        '''Функция добавления всех изменений в БД атомарной транзакцией'''
        WBSeller.objects.bulk_create([self.seller_object], update_conflicts=True, unique_fields=['wb_id'], update_fields=['name'])
        WBBrand.objects.bulk_create(self.final_dict_brands_to_add.values(), update_conflicts=True, unique_fields=['wb_id'], update_fields=['name'])
        TopWBProduct.objects.bulk_create(self.list_seller_products_to_add_with_scores, ignore_conflicts=True) #ссылается не на id а на wb_id добавленного бренда (тк оно уникальное)
        if self.celery_task == False:
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
        '''Построение url для доступа к api каталога селлера'''
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
        print(f'Выполняется анализ топовых продуктов....')   
        return total_products, seller_name
    


    def build_raw_seller_object(self):
        '''Создание объекта селлера с занесением в БД, и, 
        если селлер был в базе, и, если у него были подписчики, 
        то просто создается подписка на него у пользователя, вместо конструирования топа'''
        seller_object, was_not_in_db = WBSeller.objects.get_or_create(wb_id=self.seller_artikul,
                                                                      name=self.seller_name,
                                                                      main_url=f'https://www.wildberries.ru/seller/{self.seller_artikul}')
        
        if not was_not_in_db and seller_object.subs.exists() and self.author_object.is_staff == False:
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
                source='SELLER',
                image_url = get_image_url(product_artikul))
        new_product = {product_artikul: new_product}
        self.dict_seller_products_to_add.update(new_product)
        


class TopWBProductSellerUpdater():
    def __init__(self):
        self.sellers_with_subs = WBSeller.objects.filter(subs__isnull=False)
        

    def run(self):
        author_object = CustomUser.objects.get(username='coldtema')
        TopWBProduct.objects.filter(source='SELLER').delete()
        for seller in self.sellers_with_subs:
            TopWBProduct.objects.filter(source='SELLER', seller=seller).delete()
            Seller(seller.main_url, author_object, celery_task=True).run()