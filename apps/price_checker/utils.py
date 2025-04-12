from functools import wraps
from .models import Product, Price
import time
from apps.price_checker.site_explorer import get_shop_of_product
from django.db import transaction



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



class PriceUpdater:

    def __init__(self):
        '''Инициализация всех необходимых атрибутов'''
        self.all_prod = Product.enabled_products.all().select_related('shop')
        self.all_shop_prod_dict = self.build_all_shop_prod_dict()
        self.prods_to_go = ['']
        self.exception_prods = []
        self.broken_prods = []
        self.new_prices = []
        self.products_to_update = []
        


    def run(self):
        '''Запуск процесса обновления продуктов (на цену и наличие)'''
        self.update_prices()
        if self.exception_prods:
            self.check_exception_prods()
        if self.broken_prods:
            self.change_enable_of_broken_prods()
        self.save_all_to_db()


    def build_all_shop_prod_dict(self):
        '''Функция для конструирования словаря типа (магазин: все его продукты)'''
        temp_dict = dict()
        for product in self.all_prod:
            temp_dict.setdefault(product.shop.name, []).append(product)
        return temp_dict
        


    def fill_prods_to_go(self):
        '''Заполнение мини-стека продуктов (по 1му от каждого магазина)'''
        self.prods_to_go.clear()
        for shop, products in self.all_shop_prod_dict.items():
            if len(products) != 0:
                self.prods_to_go.append(products[-1])
                self.all_shop_prod_dict[shop].pop()


    @time_count
    def update_prices(self):
        '''Функция обновления цен'''
        while len(self.prods_to_go) != 0:
            self.fill_prods_to_go()
            for product in self.prods_to_go:
                try:
                    maybe_new_price = get_shop_of_product(product.url)['price_element']
                except:
                    self.exception_prods.append(product)
                    continue
                if maybe_new_price != product.latest_price:
                    self.updating_plus_notification(maybe_new_price, product)


    @time_count
    def check_exception_prods(self):
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
        '''Функция-точка входяа для уведомления пользователя + изменения продукта (при изменении его цены)'''
        print(f'''
Цена изменилась!
Продукт: {product.name}
Было: {product.latest_price}
Стало: {maybe_new_price}
''')
        product.latest_price = maybe_new_price
        self.new_prices.append(Price(price=maybe_new_price, product=product))
        self.products_to_update.append(product)



    def change_enable_of_broken_prods(self):
        '''Функция-точка входяа для уведомления пользователя + изменения продукта (при невозможности получить его цену)'''
        print(f'Продукты, по которым не удалось обновить цену:')
        for product in self.broken_prods: 
            print(f'id: {product.id}, url: {product.url}')
            answer = input('Что делаем с продуктом? (d - выключить, все остальное - пропустить) \n')
            if answer == 'd':
                product.enabled = False
            else:
                continue

    @time_count
    @transaction.atomic
    def save_all_to_db(self):
        '''Занесение всех изменений в БД одной атомарной транзакцией'''
        Product.enabled_products.all().bulk_update(self.products_to_update, fields=['latest_price'])
        Price.objects.all().bulk_create(self.new_prices)
        Product.objects.all().bulk_update(self.broken_prods, fields = ['enabled'])