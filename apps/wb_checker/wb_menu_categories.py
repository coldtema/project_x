import re
import json
import cloudscraper
from datetime import datetime
from django.db import transaction
from apps.wb_checker.utils.top_prods import TopBuilder
from .models import WBSeller, WBBrand, TopWBProduct, WBMenuCategory
from apps.accounts.models import CustomUser
from apps.wb_checker.utils.general_utils import get_image_url



class MenuCategory:
    '''Класс для формирования топовых продуктов из любой категории wb (~2500)'''
    
    def __init__(self, category_url, author_object):
        '''Инициализация необходимых атрибутов'''
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.scraper = cloudscraper.create_scraper()
        self.author_object = author_object
        self.author_id = author_object.id
        self.dest_avaliable = True
        self.category_url = category_url
        self.category_object = self.get_category_object()
        self.category_api_url = self.construct_category_api_url()
        self.total_products = self.get_total_products_in_catalog()
        if self.dest_avaliable:
            self.dict_category_products_to_add = dict()
            self.dict_sellers_to_add = dict()
            self.dict_brands_to_add = dict()
            self.final_dict_brands_to_add = dict()
            self.final_dict_sellers_to_add = dict()
            self.list_category_products_to_add_with_scores = []



    def run(self):
        '''Запуск процесса построения топа продуктов'''
        if self.dest_avaliable:
            self.get_catalog_of_category('popular')
            self.get_catalog_of_category('benefit')
            self.get_catalog_of_category('rate')
            self.build_top_prods()
            self.add_all_to_db()
        self.scraper.close()
    


    def get_catalog_of_category(self, sorting):
        '''Функция, которая берет первую страницу категории по разным сортировкам, 
        достает оттуда информацию о товарах, и вызывает функцию добавления этих 
        товаров в список для построения будущего топа'''
        category_api_url = self.category_api_url + sorting
        response = self.scraper.get(category_api_url, headers=self.headers)
        json_data = json.loads(response.text)
        products_on_page = json_data['data']['products']
        for i in range(len(products_on_page)):
            self.add_new_product(product_in_catalog=products_on_page[i])



    def build_top_prods(self):
        '''Построение финального топа товаров с использованием класса TopBuilder'''
        top_builder = TopBuilder(self.dict_category_products_to_add)
        print('Вычисляю топ продуктов категории по цене/отзывам/рейтигу...')
        self.list_category_products_to_add_with_scores = list(top_builder.build_top().values())
        self.list_category_products_to_add_with_scores = sorted(self.list_category_products_to_add_with_scores, key=lambda x: x.score)[-20:]
        del top_builder 
        for product in self.list_category_products_to_add_with_scores:
            self.final_dict_sellers_to_add.setdefault(product.seller.wb_id, self.dict_sellers_to_add[product.seller.wb_id])
            self.final_dict_brands_to_add.setdefault(product.brand.wb_id, self.dict_brands_to_add[product.brand.wb_id])




    @transaction.atomic
    def add_all_to_db(self):
        '''Функция добавления всех изменений в БД атомарной транзакцией'''
        WBBrand.objects.bulk_create(self.final_dict_brands_to_add.values(), update_conflicts=True, unique_fields=['wb_id'], update_fields=['name'])
        WBSeller.objects.bulk_create(self.final_dict_sellers_to_add.values(), update_conflicts=True, unique_fields=['wb_id'], update_fields=['name'])
        TopWBProduct.objects.bulk_create(self.list_category_products_to_add_with_scores, ignore_conflicts=True) #ссылается не на id а на wb_id добавленного бренда (тк оно уникальное)
        self.author_object.wbmenucategory_set.add(self.category_object)



    def get_category_object(self):
        '''Получение объекта категории из БД, 
        и оформление подписки на нее пользователем'''
        clear_category_url = self.category_url.split('?')[0].split('#')[0]
        category_slug_name = re.search(r'(catalog\/)(.+)', clear_category_url).group(2)
        category_slug_name = '/catalog/' + category_slug_name
        category_object = WBMenuCategory.objects.filter(main_url=category_slug_name).first() #тк есть дубли в БД (дочерняя категория может вставиться в другой blackhole)

        if category_object.subs.exists() and self.author_object.is_superuser == False:
            self.dest_avaliable=False
            self.author_object.wbmenucategory_set.add(category_object)
        return category_object



    def construct_category_api_url(self):
        '''Построение url для доступа к api каталога категории'''
        return f'https://catalog.wb.ru/catalog/{self.category_object.shard_key}/v2/catalog?ab_testing=false&appType=1&curr=rub&dest=123589280&hide_dtype=13&lang=ru&page=1&spp=30&{self.category_object.query}&uclusters=3&sort='



    def get_total_products_in_catalog(self):
        '''Получение количества продуктов для парсинга категории'''
        category_api_url = self.category_api_url  + 'popular'
        response = self.scraper.get(category_api_url, headers=self.headers)
        json_data = json.loads(response.text)
        try:
            total_products = json_data['data']['total']
            br = json_data['data']['products'][0]['brand'] #просто заглушка для keyerror если вдруг в категории пусто
        except:
            print('Не найдено ни одного товара категории (скорее всего они недоступны центральном регионе)')
            self.dest_avaliable = False
            return 0, None
        print(f'Товары обнаружены! Категория - {self.category_object.name}. Количество - {total_products}')
        print(f'Выполняется анализ топовых продуктов....')       
        return total_products
    


    def build_raw_brand_object(self, brand_artikul, brand_name):
        '''Проверка бренда (который фигурировал внутри категории) на существование в БД + откладывание его в кэш при отсутствии'''
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
        


    def build_raw_seller_object(self, seller_artikul, seller_name):
        '''Проверка продавца (который фигурировал внутри категории) на существование в БД + откладывание его в кэш при отсутствии'''
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
        seller_name = product_in_catalog['supplier']
        brand_artikul = product_in_catalog['brandId']
        brand_name = product_in_catalog['brand']
        rating = product_in_catalog['reviewRating']
        feedbacks = product_in_catalog['feedbacks']

        seller_object = self.build_raw_seller_object(seller_artikul, seller_name)
        brand_object = self.build_raw_brand_object(brand_artikul, brand_name)
        image_url = get_image_url(product_artikul)
        new_product = TopWBProduct(name=name,
                artikul=product_artikul,
                latest_price = price_element,
                rating=rating,
                feedbacks=feedbacks,
                wb_cosh=True,
                url=product_url,
                brand=brand_object,
                seller=seller_object,
                menu_category=self.category_object,
                created=datetime.today(),
                source='CATEGORY',
                image_url = image_url)
        new_product = {product_artikul: new_product}
        self.dict_category_products_to_add.update(new_product)



class TopWBProductMenuCategoryUpdater():
    def __init__(self):
        self.all_categories = WBMenuCategory.objects.all()
        

    def run(self):
        author_object = CustomUser.objects.get(username='coldtema')
        for category in self.all_categories:
            if category.shard_key != 'blackhole':
                TopWBProduct.objects.filter(source='CATEGORY', menu_category=category).delete()
                MenuCategory(f'https://www.wildberries.ru{category.main_url}', author_object).run()