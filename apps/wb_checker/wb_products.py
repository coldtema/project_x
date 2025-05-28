import re
import json
import cloudscraper
from .models import WBProduct, WBSeller, WBBrand, WBPrice, WBDetailedInfo
from django.utils import timezone
from django.db import transaction
from apps.wb_checker.utils.general_utils import get_image_url



class Product:
    def __init__(self, product_url, author_object, sizes_to_save=None):
        '''Инициализация необходимых атрибутов'''
        self.sizes_to_save = sizes_to_save
        self.author_object = author_object
        self.author_id = author_object.id
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.scraper = cloudscraper.create_scraper()
        self.artikul = re.search(r'\/(\d+)\/', product_url).group(1)
        self.product_url = f'https://www.wildberries.ru/catalog/{self.artikul}/detail.aspx'
        self.product_url_api = f'https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest={self.author_object.dest_id}&spp=30&ab_testing=false&lang=ru&nm={self.artikul}'
        self.product_name, self.product_sizes, self.product_volume, self.product_price, self.sizes_dict = self.get_product_detailed_info()
        self.image_url = get_image_url(self.artikul)




    def get_product_info(self):
        '''Функция сборки продукта'''
        response = self.scraper.get(self.product_url_api, headers=self.headers)
        json_data = json.loads(response.text)
        seller_name = json_data['data']['products'][0]['supplier'] #имя продавца
        seller_artikul = json_data['data']['products'][0]['supplierId'] #id продавца
        brand_name = json_data['data']['products'][0]['brand'] #имя бренда
        brand_artikul = json_data['data']['products'][0]['brandId'] #id бренда
        brand_object = Product.build_raw_brand_object(brand_name, brand_artikul)
        seller_object = Product.build_raw_seller_object(seller_name, seller_artikul)  
        new_product = WBProduct(name=self.product_name,
                artikul=self.artikul,
                wb_cosh=True,
                url=self.product_url.split('?')[0],
                seller=seller_object,
                brand=brand_object,
                image_url=self.image_url)
        detailed_info_list = []
        prices_list = []
        for i in range(len(self.product_price)):
            #добавляем элемент
            if self.product_volume[i] == '0' or self.product_volume[i] == 0: 
                enabled = False 
            else: enabled = True
            new_detailed_info = WBDetailedInfo(latest_price=self.product_price[i],
                                                size=self.product_sizes[i],
                                                volume=self.product_volume[i],
                                                enabled=enabled,
                                                author_id=self.author_id,
                                                product=new_product)
            new_price = WBPrice(price=self.product_price[i],
                                added_time=timezone.now(),
                                detailed_info=new_detailed_info)
            detailed_info_list.append(new_detailed_info)
            prices_list.append(new_price) 
        self.add_product_to_db(new_product, detailed_info_list, prices_list)


    @staticmethod
    def build_raw_seller_object(seller_name, seller_artikul):
        '''Создание объекта селлера без лишнего обращения в БД'''
        return WBSeller(wb_id=seller_artikul,
                        name=seller_name,
                        main_url=f'https://www.wildberries.ru/seller/{seller_artikul}')
    

    @staticmethod
    def build_raw_brand_object(brand_name, brand_artikul):
        '''Создание объекта бренда без лишнего обращения в БД'''
        if brand_artikul == 0:
            return WBBrand(wb_id=brand_artikul,
                    name='Без бренда',
                    main_url=f'https://www.wildberries.ru/')
        
        return WBBrand(wb_id=brand_artikul,
                    name=brand_name,
                    main_url=f'https://www.wildberries.ru/brands/{brand_artikul}')
    


    def get_product_detailed_info(self): 
        response = self.scraper.get(self.product_url_api, headers=self.headers)
        json_data = json.loads(response.text)
        name = json_data['data']['products'][0]['name']
        if self.sizes_to_save:
            return name, list(self.sizes_to_save.keys()), list(map(lambda x: x[0], self.sizes_to_save.values())), list(map(lambda x: x[1], self.sizes_to_save.values())), None
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
            return name, [None], [sizes_dict['0'][0]], [sizes_dict['0'][1]], None
        
        
        print(f'Товар обнаружен!\nНазвание: {name}.\nДоступные варианты:')
        return name, None, None, None, sizes_dict
    


    @transaction.atomic
    def add_product_to_db(self, new_product, new_detailed_info, new_price):
        '''Функция добавления всех изменений в БД атомарной транзакцией'''
        #сохраняем элемент
        WBBrand.objects.bulk_create([new_product.brand], update_conflicts=True, unique_fields=['wb_id'], update_fields=['name'])
        WBSeller.objects.bulk_create([new_product.seller], update_conflicts=True, unique_fields=['wb_id'], update_fields=['name'])
        WBProduct.objects.bulk_create([new_product], update_conflicts=True, unique_fields=['artikul'], update_fields=['name'])
        for i in range(len(new_detailed_info)):
            new_detailed_info[i], was_not_in_db = WBDetailedInfo.objects.get_or_create(size=new_detailed_info[i].size,
                                                                                        enabled=new_detailed_info[i].enabled,
                                                                                        author_id=self.author_id,
                                                                                        product=new_product,
                                                                                        defaults={'volume':new_detailed_info[i].volume,
                                                                                                'latest_price':new_detailed_info[i].latest_price,
                                                                                                'first_price':new_detailed_info[i].latest_price}) #возможно в defaults убрать volume из за постоянных изменений (убрал - посмотреть, как ведет)
            if was_not_in_db:
                new_price[i].detailed_info = new_detailed_info[i]
                new_price[i].save()
                self.author_object.slots -= 1
                self.author_object.save()
            else:
                new_detailed_info[i].updated = timezone.now()
                new_detailed_info[i].save()
                print('Товар уже есть в отслеживании')