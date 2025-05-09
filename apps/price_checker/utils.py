from functools import wraps
import math
from .models import Product, Price
import time
from apps.price_checker.site_explorer import get_shop_of_product
from django.db import transaction
import asyncio
from .async_site_explorer import Parser
from django.utils import timezone


def time_count(func):
    '''Декоратор определения времени работы функции'''
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f'{func.__doc__} - {end - start}')
        return result
    return wrapper



def get_sparkline_points(prices, width=100, height=30):
    if not prices:
        return []

    n = len(prices)
    min_p, max_p = min(prices), max(prices)
    spread = max_p - min_p or 1
    step_x = width / max(n - 1, 1)

    return [
        ((round(i * step_x, 2), round(height - ((p - min_p) / spread * height), 2)), p)
        for i, p in enumerate(prices)
    ]



class PriceUpdater:

    def __init__(self):
        '''Инициализация всех необходимых атрибутов'''
        self.batch_size = 1000
        self.len_all_prod = Product.enabled_products.all().count()
        self.batched_prods = None
        self.batched_shop_prod_dict = None
        self.prods_to_go = ['']
        self.async_exeption_prods = []
        self.exception_prods = []
        self.broken_prods = []
        self.new_prices = []
        self.products_to_update = []
        


    def run(self):
        '''Запуск процесса обновления продуктов (на цену и наличие)'''
        for i in range(math.ceil(self.len_all_prod / self.batch_size)):
            self.batched_prods=Product.enabled_products.all()[i*self.batch_size:(i+1)*self.batch_size]
            self.batched_shop_prod_dict = self.build_all_shop_prod_dict()
            self.async_update_prices()
            if self.async_exeption_prods:
                print(f'Элементы, не прошедшие асинхронно: {len(self.async_exeption_prods)}')
                self.sync_update_prices()
                if self.exception_prods:
                    self.check_exception_prods()
                if self.broken_prods:
                    self.change_enable_of_broken_prods()
            self.save_all_to_db()
            self.products_to_update = []
            self.new_prices = []
            self.broken_prods = []
            self.exception_prods = []
            self.prods_to_go = ['']



    def build_all_shop_prod_dict(self):
        '''Функция для конструирования словаря типа (магазин: все его продукты)'''
        temp_dict = dict()
        for product in self.batched_prods:
            temp_dict.setdefault(product.shop.name, []).append(product)
        return temp_dict
        


    def fill_prods_to_go(self):
        '''Заполнение мини-стека продуктов (по 1му от каждого магазина)'''
        self.prods_to_go.clear()
        for shop, products in self.batched_shop_prod_dict.items():
            if len(products) != 0:
                self.prods_to_go.append(products[-1])
                self.batched_shop_prod_dict[shop].pop()


    @time_count
    def async_update_prices(self):
        '''Функция обновления цен'''
        while len(self.prods_to_go) != 0:
            self.fill_prods_to_go()
            parser = Parser()
            async_results = asyncio.run(parser.process_all_sites(self.prods_to_go))
            for i in range(len(async_results)):
                if isinstance(async_results[i], tuple):
                    self.async_exeption_prods.append(self.prods_to_go[i])
                    continue
                if async_results[i]['price_element'] != self.prods_to_go[i].latest_price:
                    self.updating_plus_notification(async_results[i]['price_element'], self.prods_to_go[i])



    @time_count
    def sync_update_prices(self):
        '''Функция обновления цен'''
        for product in self.async_exeption_prods:
            try:
                maybe_new_price = get_shop_of_product(product.url)['price_element']
            except TimeoutError:
                print(product, '- завершился по таймауту')
            except:
                self.exception_prods.append(product)
                continue
            if maybe_new_price != product.latest_price:
                self.updating_plus_notification(maybe_new_price, product)



    @time_count
    def check_exception_prods(self):
            time.sleep(10)
            '''Функция проверки тех элементов, которые не прошли проверку с 1го раза'''
            print(f'''
        эти элементы не прошли с первой попытки: {[elem.name for elem in self.exception_prods]}
        ''')
            for product in self.exception_prods:
                try:
                    maybe_new_price = get_shop_of_product(product.url)['price_element']
                except:
                    self.broken_prods.append(product)
                    continue
                if maybe_new_price != product.latest_price:
                    self.updating_plus_notification(maybe_new_price, product)



    def updating_plus_notification(self, maybe_new_price, product):
        '''Функция-точка входа для уведомления пользователя + изменения продукта (при изменении его цены)'''
        print(f'''
Цена изменилась!
Продукт: {product.url}
Было: {product.latest_price}
Стало: {maybe_new_price}
''')
        product.latest_price = maybe_new_price
        product.updated = timezone.now()
        self.new_prices.append(Price(price=maybe_new_price, product=product))
        self.products_to_update.append(product)



    def change_enable_of_broken_prods(self):
        '''Функция-точка входа для уведомления пользователя + изменения продукта (при невозможности получить его цену)'''
        print(f'Продукты, по которым не удалось обновить цену:')
        for product in self.broken_prods: 
            print(f'id: {product.id}, url: {product.url}')
            answer = input('Что делаем с продуктом? (d - выключить, все остальное - пропустить) \n')
            if answer == 'd':
                product.enabled = False
                product.updated = timezone.now()
            else:
                continue

    @time_count
    @transaction.atomic
    def save_all_to_db(self):
        '''Занесение всех изменений в БД одной атомарной транзакцией'''
        Product.enabled_products.all().bulk_update(self.products_to_update, fields=['latest_price', 'updated'])
        Price.objects.all().bulk_create(self.new_prices)
        Product.objects.all().bulk_update(self.broken_prods, fields = ['enabled', 'updated'])