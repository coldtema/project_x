from functools import wraps
import math
from .models import Product, Price
import time
from apps.price_checker.site_explorer import get_shop_of_product
from django.db import transaction
import asyncio
from .async_site_explorer import Parser
from django.utils import timezone
from apps.core.models import Notification
from apps.core import tasks
# from apps.core.models import Notification


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
    def __init__(self, enabled):
        '''Инициализация всех необходимых атрибутов'''
        self.batch_size = 1000
        self.enabled = enabled
        self.len_all_prod = Product.objects.filter(enabled=self.enabled, repeated=False).count()
        self.batched_prods = None
        self.batched_shop_prod_dict = None
        self.prods_to_go = ['']
        self.async_exeption_prods = []
        self.exception_prods = []
        self.broken_prods = []
        self.new_prices = []
        self.products_to_update = []
        self.notifications_to_save = []
        


    def run(self):
        '''Запуск процесса обновления продуктов (на цену и наличие)'''
        for i in range(math.ceil(self.len_all_prod / self.batch_size)):
            self.batched_prods=Product.objects.filter(enabled=self.enabled, repeated=False).select_related('shop', 'author')[i*self.batch_size:(i+1)*self.batch_size]
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
            self.send_tg_notifications()
            self.products_to_update = []
            self.new_prices = []
            self.broken_prods = []
            self.exception_prods = []
            self.prods_to_go = ['']
            self.notifications_to_save = []



    def build_all_shop_prod_dict(self):
        '''Функция для конструирования словаря типа (магазин: все его продукты)'''
        temp_dict = dict()
        for product in self.batched_prods:
            temp_dict.setdefault(product.shop.regex_name, []).append(product)
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
        '''Асинхронно обновляем цены'''
        while len(self.prods_to_go) != 0:
            self.fill_prods_to_go()
            parser = Parser()
            async_results = asyncio.run(parser.process_all_sites(self.prods_to_go))
            for i in range(len(async_results)):
                print(async_results[i])
                if isinstance(async_results[i], tuple) and async_results[i][0] == 'timeout':
                    self.batched_shop_prod_dict[async_results[i][1]].clear()
                    print(async_results[i][1]) #точка входа для написания лога
                    continue
                if isinstance(async_results[i], tuple):
                    self.async_exeption_prods.append(self.prods_to_go[i])
                    continue
                if async_results[i]['price_element'] != self.prods_to_go[i].latest_price and self.enabled==True:
                    self.updating_plus_notification(async_results[i]['price_element'], self.prods_to_go[i])
                elif self.enabled==False:
                    self.disabled_updating_plus_notification(async_results[i]['price_element'], self.prods_to_go[i])
					





    @time_count
    def sync_update_prices(self):
        '''Синхронно обновляем цены'''
        for product in self.async_exeption_prods:
            try:
                maybe_new_price = get_shop_of_product(product.url)['price_element']
            except TimeoutError:
                print(product, '- завершился по таймауту')
            except:
                self.exception_prods.append(product)
                continue
            if maybe_new_price != product.latest_price and self.enabled == True:
                self.updating_plus_notification(maybe_new_price, product)
            elif self.enabled==False:
                self.disabled_updating_plus_notification(maybe_new_price, product)



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
                    if self.enabled == True:
                        self.broken_prods.append(product)
                    continue
                if maybe_new_price != product.latest_price and self.enabled == True:
                    self.updating_plus_notification(maybe_new_price, product)
                elif self.enabled==False:
                    self.disabled_updating_plus_notification(maybe_new_price, product)




    def updating_plus_notification(self, maybe_new_price, product):
        '''Функция-точка входа для уведомления пользователя об изменении цены отслеживаемого продукта который в наличии + изменения продукта (при изменении его цены)'''
        detailed_text = ''
        if maybe_new_price < product.first_price:
            detailed_text = f' (↓ {abs(product.first_price-maybe_new_price)}₽)'
        elif maybe_new_price > product.first_price:
            detailed_text = f' (↑ {abs(product.first_price-maybe_new_price)}₽)'


        if abs(product.latest_price - maybe_new_price) > product.author.notification_discount_price or abs(int((product.latest_price-maybe_new_price)/(product.latest_price/100))) > product.author.notification_discount:
            if product.latest_price > maybe_new_price and product.author.pricedown_notification is True:
                product.last_notified_price = maybe_new_price
                self.notifications_to_save.append(Notification(text=f'<i>🛒{product.shop.name}</i> <br> <b>📦{product.name}</b> <br> 🟢 Цена <b>упала</b> на <b>{product.latest_price - maybe_new_price} ₽</b>! (-{int((product.latest_price-maybe_new_price)/(product.latest_price/100))}%)',
                                                               tg_text=f'<a href="{product.shop.main_url}"><i>🛒{product.shop.name}</i></a>\n<a href="{product.ref_url}"><b>📦{product.name}</b></a>\n🟢 Цена <b>упала</b> на <b>{product.latest_price - maybe_new_price} ₽</b>! (-{int((product.latest_price-maybe_new_price)/(product.latest_price/100))}%)\n💵<b>Текущая цена:</b> {maybe_new_price}₽{detailed_text}',
                                                                    product=product,
                                                                    user=product.author))
            elif product.author.priceup_notification is True:
                product.last_notified_price = maybe_new_price
                self.notifications_to_save.append(Notification(text=f'<i>🛒{product.shop.name}</i> <br> <b>📦{product.name}</b> <br> 🔴 Цена <b>поднялась</b> на <b> {maybe_new_price - product.latest_price} ₽</b>! (+{int((maybe_new_price-product.latest_price)/(product.latest_price/100))}%)',
                                                                    tg_text=f'<a href="{product.shop.main_url}"><i>🛒{product.shop.name}</i></a>\n<a href="{product.ref_url}"><b>📦{product.name}</b></a>\n🔴 Цена <b>поднялась</b> на <b> {maybe_new_price - product.latest_price} ₽</b>! (+{int((maybe_new_price-product.latest_price)/(product.latest_price/100))}%)\n💵<b>Текущая цена:</b> {maybe_new_price}₽{detailed_text}',
                                                                    product=product,
                                                                    user=product.author))
        product.latest_price = maybe_new_price
        product.updated = timezone.now()
        self.new_prices.append(Price(price=maybe_new_price, product=product))
        self.products_to_update.append(product)

  

    def disabled_updating_plus_notification(self, maybe_new_price, product):
        '''Функция-точка входа для уведомления пользователя о том что продукт снова в наличии + изменения продукта (при изменении его цены)'''
        detailed_text = ''
        if maybe_new_price < product.first_price:
            detailed_text = f' (↓ {abs(product.first_price-maybe_new_price)}₽)'
        elif maybe_new_price > product.first_price:
            detailed_text = f' (↑ {abs(product.first_price-maybe_new_price)}₽)'
        self.notifications_to_save.append(Notification(text=f'<i>🛒{product.shop.name}</i> <br> <b>📦{product.name}</b> <br> <b> ✅ Появился в наличии! </b> Успейте купить!',
                                                       tg_text=f'<a href="{product.shop.main_url}"><i>🛒{product.shop.name}</i></a>\n<a href="{product.ref_url}"><b>📦{product.name}</b></a>\n<b>✅ Появился в наличии! </b> Успейте купить!\n💵<b>Текущая цена:</b> {maybe_new_price}₽{detailed_text}',
                                                        product=product,
                                                        user=product.author))
        if product.latest_price != maybe_new_price:
            product.latest_price = maybe_new_price
            self.new_prices.append(Price(price=maybe_new_price, product=product))
        product.updated = timezone.now()
        product.enabled = True
        self.products_to_update.append(product)


    def change_enable_of_broken_prods(self):
        '''Функция-точка входа для уведомления пользователя + изменения продукта (при невозможности получить его цену)'''
        print(f'Продукты, по которым не удалось обновить цену:')
        for product in self.broken_prods: 
            # self.notifications_to_save.append(Notification(text=f'<i>🛒{product.shop.name}</i> <br> <b>📦{product.name}</b> <br> <b> ❌ Нет в наличии! </b> Добавлен во вкладку "Нет в наличии".',
            #                                                 product=product,
            #                                                 user=product.author))
            product.enabled = False
            product.updated = timezone.now()


    @transaction.atomic
    def save_all_to_db(self):
        '''Занесение всех изменений в БД одной атомарной транзакцией'''
        Product.objects.all().bulk_update(self.products_to_update, fields=['latest_price', 'updated', 'enabled', 'last_notified_price'])
        Price.objects.all().bulk_create(self.new_prices)
        Product.objects.all().bulk_update(self.broken_prods, fields = ['enabled', 'updated'])
        Notification.objects.bulk_create(self.notifications_to_save)

    def send_tg_notifications(self):
        for notif in self.notifications_to_save:
            if notif.user.tg_user:
                tasks.send_tg_notification.delay(notif.user.tg_user.tg_id, notif.tg_text)





class RepetitionsPriceUpdater:
    def __init__(self, enabled):
        '''Инициализация всех необходимых атрибутов'''
        self.batch_size = 10000
        self.enabled = enabled
        self.len_all_prod = Product.objects.filter(enabled=self.enabled, repeated=True).count()
        self.batched_prods = None
        self.batched_shop_prod_dict = None
        self.prods_to_go = ['']
        self.async_exeption_prods = []
        self.exception_prods = []
        self.broken_prods = []
        self.new_prices = []
        self.products_to_update = []
        self.notifications_to_save = []
        


    def run(self):
        '''Запуск процесса обновления продуктов (на цену и наличие)'''
        for i in range(math.ceil(self.len_all_prod / self.batch_size)):
            self.batched_prods=Product.objects.filter(enabled=self.enabled, repeated=True)[i*self.batch_size:(i+1)*self.batch_size]
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
            self.send_tg_notifications()
            self.products_to_update = []
            self.new_prices = []
            self.broken_prods = []
            self.exception_prods = []
            self.prods_to_go = ['']
            self.notifications_to_save = []



    def build_all_shop_prod_dict(self):
        '''Функция для конструирования словаря типа (магазин: все его продукты)'''
        temp_dict = dict()

        for product in self.batched_prods:
            temp_dict.setdefault(product.url, product)
            
        self.batched_prods = temp_dict.values()
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
                print(async_results[i])
                if isinstance(async_results[i], tuple) and async_results[i][0] == 'timeout':
                    self.batched_shop_prod_dict[async_results[i][1]].clear()
                    print(async_results[i][1]) #точка входа для написания лога
                    continue
                if isinstance(async_results[i], tuple):
                    self.async_exeption_prods.append(self.prods_to_go[i])
                    continue
                if async_results[i]['price_element'] != self.prods_to_go[i].latest_price and self.enabled==True:
                    self.updating_plus_notification(async_results[i]['price_element'], self.prods_to_go[i])
                elif self.enabled==False:
                    self.disabled_updating_plus_notification(async_results[i]['price_element'], self.prods_to_go[i])
					





    @time_count
    def sync_update_prices(self):
        '''Функция обновления цен'''
        for product in self.async_exeption_prods:
            try:
                maybe_new_price = get_shop_of_product(product.url)['price_element']
            except:
                self.exception_prods.append(product)
                continue
            if maybe_new_price != product.latest_price and self.enabled == True:
                self.updating_plus_notification(maybe_new_price, product)
            elif self.enabled==False:
                self.disabled_updating_plus_notification(maybe_new_price, product)



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
                    if self.enabled == True:
                        self.broken_prods.append(product)
                    continue
                if maybe_new_price != product.latest_price and self.enabled == True:
                    self.updating_plus_notification(maybe_new_price, product)
                elif self.enabled==False:
                    self.disabled_updating_plus_notification(maybe_new_price, product)




    def updating_plus_notification(self, maybe_new_price, product):
        '''Функция-точка входа для уведомления пользователя об изменении цены отслеживаемого продукта который в наличии + изменения продукта (при изменении его цены)'''
        #сделать уведомления для всех пользователей, у кого этот продукт есть
        repetitions = Product.objects.filter(url=product.url).select_related('author', 'shop')
        for repetition in repetitions:

            detailed_text = ''
            if maybe_new_price < repetition.first_price:
                detailed_text = f' (↓ {abs(repetition.first_price-maybe_new_price)}₽)'
            elif maybe_new_price > repetition.first_price:
                detailed_text = f' (↑ {abs(repetition.first_price-maybe_new_price)}₽)'

            if abs(repetition.latest_price - maybe_new_price) > repetition.author.notification_discount_price or abs(int((repetition.latest_price-maybe_new_price)/(repetition.latest_price/100))) > repetition.author.notification_discount:
                if repetition.latest_price > maybe_new_price and repetition.author.pricedown_notification is True:
                    repetition.last_notified_price = maybe_new_price
                    self.notifications_to_save.append(Notification(text=f'<i>🛒{repetition.shop.name}</i> <br> <b>📦{repetition.name}</b> <br> 🟢 Цена <b>упала</b> на <b>{repetition.latest_price - maybe_new_price} ₽</b>! (-{int((repetition.latest_price-maybe_new_price)/(repetition.latest_price/100))}%)',
                                                                    tg_text=f'<a href="{repetition.shop.main_url}"><i>🛒{repetition.shop.name}</i></a>\n<a href="{repetition.ref_url}"><b>📦{repetition.name}</b></a>\n🟢 Цена <b>упала</b> на <b>{repetition.latest_price - maybe_new_price} ₽</b>! (-{int((repetition.latest_price-maybe_new_price)/(repetition.latest_price/100))}%)\n💵<b>Текущая цена:</b> {maybe_new_price}₽{detailed_text}',
                                                                    product=repetition,
                                                                    user=repetition.author))
                elif repetition.author.priceup_notification is True:
                    repetition.last_notified_price = maybe_new_price
                    self.notifications_to_save.append(Notification(text=f'<i>🛒{repetition.shop.name}</i> <br> <b>📦{repetition.name}</b> <br> 🔴 Цена <b>поднялась</b> на <b> {maybe_new_price - repetition.latest_price} ₽</b>! (+{int((maybe_new_price-repetition.latest_price)/(repetition.latest_price/100))}%)',
                                                                    tg_text=f'<a href="{repetition.shop.main_url}"><i>🛒{repetition.shop.name}</i></a>\n<a href="{repetition.ref_url}"><b>📦{repetition.name}</b></a>\n🔴 Цена <b>поднялась</b> на <b> {maybe_new_price - repetition.latest_price} ₽</b>! (+{int((maybe_new_price-repetition.latest_price)/(repetition.latest_price/100))}%)\n💵<b>Текущая цена:</b> {maybe_new_price}₽{detailed_text}',
                                                                    product=repetition,
                                                                    user=repetition.author))
            repetition.latest_price = maybe_new_price
            repetition.updated = timezone.now()
            self.new_prices.append(Price(price=maybe_new_price, product=repetition))
            self.products_to_update.append(repetition)


    def disabled_updating_plus_notification(self, maybe_new_price, product):
        '''Функция-точка входа для уведомления пользователя о том что продукт снова в наличии + изменения продукта (при изменении его цены)'''
        repetitions = Product.objects.filter(url=product.url).select_related('author', 'shop')
        for repetition in repetitions:
            self.notifications_to_save.append(Notification(text=f'<i>🛒{repetition.shop.name}</i> <br> <b>📦{repetition.name}</b> <br> <b> ✅ Появился в наличии! </b> Успейте купить!',
                                                           tg_text=f'<a href="{repetition.shop.main_url}"><i>🛒{repetition.shop.name}</i></a>\n<a href="{repetition.ref_url}"><b>📦{repetition.name}</b></a>\n<b> ✅ Появился в наличии! </b> Успейте купить!',
                                                            product=repetition,
                                                            user=repetition.author))
            if repetition.latest_price != maybe_new_price:
                repetition.latest_price = maybe_new_price
                self.new_prices.append(Price(price=maybe_new_price, product=repetition))
            repetition.updated = timezone.now()
            repetition.enabled = True
            self.products_to_update.append(repetition)


    def change_enable_of_broken_prods(self):
        '''Функция-точка входа для уведомления пользователя + изменения продукта (при невозможности получить его цену)'''
        print(f'Продукты, по которым не удалось обновить цену:')
        urls_of_broken_prods = list(*map(lambda x: x.url, self.broken_prods))
        broken_repetitions = Product.objects.filter(url__in=urls_of_broken_prods).select_related('author', 'shop')
        for product in broken_repetitions:
            # self.notifications_to_save.append(Notification(text=f'<i>🛒{product.shop.name}</i> <br> <b>📦{product.name}</b> <br> <b> ❌ Нет в наличии! </b> Добавлен во вкладку "Нет в наличии".',
            #                                                 product=product,
            #                                                 user=product.author))
            product.enabled = False
            product.updated = timezone.now()


    @transaction.atomic
    def save_all_to_db(self):
        '''Занесение всех изменений в БД одной атомарной транзакцией'''
        Product.objects.all().bulk_update(self.products_to_update, fields=['latest_price', 'updated', 'enabled', 'last_notified_price'])
        Price.objects.all().bulk_create(self.new_prices)
        Product.objects.all().bulk_update(self.broken_prods, fields = ['enabled', 'updated'])
        Notification.objects.bulk_create(self.notifications_to_save)

    def send_tg_notifications(self):
        for notif in self.notifications_to_save:
            if notif.user.tg_user:
                tasks.send_tg_notification.delay(notif.user.tg_user.tg_id, notif.tg_text)



class PriceClearer:
    def __init__(self):
        '''Инициализация необходимых атрибутов'''
        self.batch_size = 1000
        self.len_all_prods_list = Product.objects.all().count()
        self.batched_prods_list = []
        self.price_ids_to_delete = []


    def run(self):
        '''Запуск процесса удаления лишних цен + батчинг по продуктам'''
        for i in range(math.ceil(self.len_all_prods_list / self.batch_size)):
            self.batched_prods_list = Product.objects.all().prefetch_related('price_set')[i*self.batch_size:(i+1)*self.batch_size]
            self.go_through_all_prods()     
            self.delete_notif_in_db()
            self.price_ids_to_delete = []


    def go_through_all_prods(self):
        '''Функция, в которой идет проход по одному продукту из батча'''
        for i in range(len(self.batched_prods_list)):
            if self.batched_prods_list[i].price_set.count() > 15:
                self.price_ids_to_delete.extend(list(map(lambda x: x['pk'], self.batched_prods_list[i].price_set.order_by('-added_time')[14:].values('pk'))))
                self.price_ids_to_delete.pop()


    @transaction.atomic
    def delete_notif_in_db(self):
        '''Занесение в БД обновления наличия'''
        Price.objects.filter(pk__in=self.price_ids_to_delete).delete()