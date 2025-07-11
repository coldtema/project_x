import math
import time
import cloudscraper
import json
from django.utils import timezone
from django.db import transaction
from django.db.models import Prefetch
from apps.accounts.models import CustomUser
from apps.wb_checker.utils.general_utils import time_count
from ..models import WBPrice, WBDetailedInfo, WBProduct
from apps.core.models import Notification
from apps.core import tasks



class PriceUpdater:
    def __init__(self):
        '''Инициализация необходимых атрибутов'''
        self.batch_size = 50
        self.len_all_authors_list = CustomUser.objects.all().count()
        self.batched_authors_list = []
        self.scraper = cloudscraper.create_scraper()
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.new_prices = []
        self.updated_details = []
        self.test_counter = 0
        self.current_detail_to_check = None
        self.detail_product_url_api = None
        self.prods_artikuls_to_delete = []
        self.notifications_to_save = []
    
    def run(self):
        '''Запуск процесса обновления цен + батчинг по авторам'''
        for i in range(math.ceil(self.len_all_authors_list / self.batch_size)):
            self.batched_authors_list = CustomUser.objects.all().prefetch_related(Prefetch('wbdetailedinfo_set', 
                                                                            queryset=WBDetailedInfo.objects.filter(enabled=True).select_related('product')))[i*self.batch_size:(i+1)*self.batch_size]
            self.go_through_all_authors()
            self.save_update_prices()
            self.send_tg_notifications()
            self.new_prices = []
            self.updated_details = []
            self.prods_artikuls_to_delete = []
            self.notifications_to_save = []
        print(f'Товаров проверено:{self.test_counter}')


    def go_through_all_authors(self):
        '''Функция, в которой идет проход по одному автору из батча'''
        for i in range(len(self.batched_authors_list)):
            author_object = self.batched_authors_list[i]
            self.detail_product_url_api = f'https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest={author_object.dest_id}&spp=30&ab_testing=false&lang=ru&nm='
            details_of_prods_to_check = self.batched_authors_list[i].wbdetailedinfo_set.all()
            if len(details_of_prods_to_check) == 0:
                continue
            self.go_through_all_details(details_of_prods_to_check)


    def go_through_all_details(self, details_of_prods_to_check):
        '''Подготовка списка для обновления цены'''
        for j in range(math.ceil(len(details_of_prods_to_check) / 200)):
            self.batched_details_of_prods_to_check = details_of_prods_to_check[j*200:(j+1)*200]
            final_url = self.detail_product_url_api + ';'.join(map(lambda x: str(x.product.artikul), self.batched_details_of_prods_to_check))
            response = self.scraper.get(final_url, headers=self.headers)
            json_data = json.loads(response.text)
            products_on_page = json_data['data']['products']

            if len(products_on_page) != len(self.batched_details_of_prods_to_check):
                self.delete_not_existing_prods(products_on_page)


            products_on_page = sorted(products_on_page, key=lambda x: x['id'])
            self.batched_details_of_prods_to_check = sorted(self.batched_details_of_prods_to_check, key=lambda x: x.product.artikul)
            self.update_info(products_on_page)




    
    def update_info(self, products_on_page):
        '''Обновление цен продуктов, которые есть наличии + 
        разведение по тем, у кого есть размер, и тем, у кого нет'''
        for j in range(len(products_on_page)):
            self.current_detail_to_check = self.batched_details_of_prods_to_check[j]
            if products_on_page[j]['id'] == self.current_detail_to_check.product.artikul:
                if self.current_detail_to_check.size == None:
                    self.check_nonsize_product(products_on_page[j])
                else:
                    self.check_size_product(products_on_page[j])                      
            else: #по факту до этого никогда не должно доходить (оставил на всякий случай)
                print(products_on_page[j]['id'])
                print(self.current_detail_to_check.product.artikul)
                print('Не сходится товар и запрос по индексам')
                raise Exception



    def delete_not_existing_prods(self, products_on_page):
        '''Удаление товаров из списка временного, которые вообще
          удалились с сайта wb и не отображаются в api details'''
        prods_artikuls_to_delete = set(map(lambda x: x.product.artikul, self.batched_details_of_prods_to_check)) - set(map(lambda x: x['id'], products_on_page))
        self.prods_artikuls_to_delete.extend(prods_artikuls_to_delete)
        self.batched_details_of_prods_to_check = list(filter(lambda x: True if x.product.artikul not in prods_artikuls_to_delete else False, self.batched_details_of_prods_to_check))



    def check_nonsize_product(self, product_on_page):
        '''Функция проверки изменений товара для продукта, у которого нет размера'''
        self.test_counter += 1
        stocks = product_on_page['sizes'][0]['stocks']
        if len(stocks) != 0:
            volume = 0
            for stock in stocks:
                volume += stock['qty']
            price_of_detail = int(product_on_page['sizes'][0]['price']['product'] // 100)
            #точка входа для уведомления пользователя
            self.updating_plus_notification(price_of_detail, volume)
        else:
            self.disable_product()
            


    def disable_product(self):
        '''Отключение товара (тк его больше нет в наличии)'''
        self.notifications_to_save.append(Notification(text=f'<i>🛒WildBerries</i> <br> <b>📦{self.current_detail_to_check.product.name}</b> <br> <b> ❌ Нет в наличии! </b>  Добавлен во вкладку "Нет в наличии".',
                                                        tg_text=f'<i>🛒WildBerries</i>\n<a href="{self.current_detail_to_check.product.url}"><b>📦{self.current_detail_to_check.product.name}</b></a>\n<b> ❌ Нет в наличии! </b>',
                                                        wb_product=self.current_detail_to_check,
                                                        user=self.current_detail_to_check.author))
        self.current_detail_to_check.enabled = False
        self.current_detail_to_check.volume = 0
        self.updated_details.append(self.current_detail_to_check)   



    def check_size_product(self, product_on_page):
        '''Функция проверки изменений товара для продукта, у которого есть размер'''
        self.test_counter += 1
        sizes = product_on_page['sizes']
        for size in sizes:
            if size['origName'] == self.current_detail_to_check.size:
                stocks = size['stocks']
                if len(stocks) != 0:
                    volume = 0
                    for stock in stocks:
                        volume += stock['qty']
                    price_of_detail = size['price']['product'] // 100
                    #точка входа для уведомления пользователя
                    self.updating_plus_notification(price_of_detail, volume)
                break      



    def updating_plus_notification(self, price_of_detail, volume):
        '''Точка входа для уведомления пользователя + изменение полей товара
        добавление товара в общую коллекцию обновления'''
        flag_change = False           
        if self.current_detail_to_check.latest_price != price_of_detail: #and abs(self.current_detail_to_check.latest_price - price_of_detail) /self.current_detail_to_check.latest_price > 0.03: #сделать потом поле у пользователя (на сколько отслеживаем цену)
            # print(abs(self.current_detail_to_check.latest_price - price_of_detail) /self.current_detail_to_check.latest_price)
            self.make_notification(price_of_detail)
            flag_change = True
            self.current_detail_to_check.latest_price = price_of_detail
            self.current_detail_to_check.updated = timezone.now()
            self.new_prices.append(WBPrice(price=price_of_detail,
                                        added_time=timezone.now(),
                                        detailed_info=self.current_detail_to_check))
        if self.current_detail_to_check.volume != volume: #по количеству постоянные изменения - просто пишу в бд без уведомлений (пока что)
            if self.current_detail_to_check.volume >= 10 and volume < 10:
                self.notifications_to_save.append(Notification(text=f'<i>🛒WildBerries</i> <br> <b>📦{self.current_detail_to_check.product.name}</b> <br>  ❗️<b>Менее 10 штук в наличии!</b> Успейте купить :)',
                                                               tg_text=f'<i>🛒WildBerries</i>\n<a href="{self.current_detail_to_check.product.url}"><b>📦{self.current_detail_to_check.product.name}</b></a>\n❗️<b>Менее 10 штук в наличии!</b> Успейте купить :)',
                                                                wb_product=self.current_detail_to_check,
                                                                user=self.current_detail_to_check.author))
            flag_change = True
            self.current_detail_to_check.volume = volume
        if flag_change: self.updated_details.append(self.current_detail_to_check) 


    def make_notification(self, price_of_detail):
        if abs(self.current_detail_to_check.latest_price - price_of_detail) > self.current_detail_to_check.author.notification_discount_price or abs(int((self.current_detail_to_check.latest_price-price_of_detail)/(self.current_detail_to_check.latest_price/100))) > self.current_detail_to_check.author.notification_discount:
            if self.current_detail_to_check.latest_price > price_of_detail and self.current_detail_to_check.author.pricedown_notification is True:
                self.current_detail_to_check.last_notified_price = price_of_detail
                self.notifications_to_save.append(Notification(text=f'<i>🛒WildBerries</i> <br> <b>📦{self.current_detail_to_check.product.name}</b> <br> 🟢 Цена <b>упала</b> на <b>{self.current_detail_to_check.latest_price - price_of_detail} ₽</b>! (-{int((self.current_detail_to_check.latest_price-price_of_detail)/(self.current_detail_to_check.latest_price/100))}%)',
                                                                tg_text=f'<i>🛒WildBerries</i>\n<a href="{self.current_detail_to_check.product.url}"><b>📦{self.current_detail_to_check.product.name}</b></a>\n🟢 Цена <b>упала</b> на <b>{self.current_detail_to_check.latest_price - price_of_detail} ₽</b>! (-{int((self.current_detail_to_check.latest_price-price_of_detail)/(self.current_detail_to_check.latest_price/100))}%)',
                                                                wb_product=self.current_detail_to_check,
                                                                user=self.current_detail_to_check.author))
            elif self.current_detail_to_check.author.priceup_notification is True:
                self.current_detail_to_check.last_notified_price = price_of_detail
                self.notifications_to_save.append(Notification(text=f'<i>🛒WildBerries</i> <br> <b>📦{self.current_detail_to_check.product.name}</b> <br> 🔴 Цена <b>поднялась</b> на <b> {price_of_detail - self.current_detail_to_check.latest_price} ₽</b>! (+{int((price_of_detail-self.current_detail_to_check.latest_price)/(self.current_detail_to_check.latest_price/100))}%)',
                                                                tg_text=f'<i>🛒WildBerries</i>\n<a href="{self.current_detail_to_check.product.url}"><b>📦{self.current_detail_to_check.product.name}</b></a>\n🔴 Цена <b>поднялась</b> на <b> {price_of_detail - self.current_detail_to_check.latest_price} ₽</b>! (+{int((price_of_detail-self.current_detail_to_check.latest_price)/(self.current_detail_to_check.latest_price/100))}%)',
                                                                wb_product=self.current_detail_to_check,
                                                                user=self.current_detail_to_check.author))


    
    @transaction.atomic
    def save_update_prices(self):
        '''Занесение в БД обновления наличия'''
        WBDetailedInfo.objects.bulk_update(self.updated_details, ['latest_price', 'volume', 'enabled', 'updated', 'last_notified_price'])
        WBPrice.objects.bulk_create(self.new_prices)
        WBProduct.objects.filter(artikul__in=self.prods_artikuls_to_delete).delete()
        Notification.objects.bulk_create(self.notifications_to_save)



    def send_tg_notifications(self):
        for notif in self.notifications_to_save:
            if notif.user.tg_user:
                tasks.send_tg_notification.delay(notif.user.tg_user.tg_id, notif.tg_text)









class AvaliabilityUpdater:
    def __init__(self):
        '''Инициализация необходимых атрибутов'''
        self.batch_size = 50
        self.len_all_authors_list = CustomUser.objects.all().count()
        self.batched_authors_list = []
        self.scraper = cloudscraper.create_scraper()
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.new_prices = []
        self.updated_details = []
        self.test_counter = 0
        self.current_detail_to_check = None
        self.detail_product_url_api = None
        self.prods_artikuls_to_delete = []
        self.notifications_to_save = []


    def run(self):
        '''Запуск процесса обновления цен + батчинг по авторам'''
        for i in range(math.ceil(self.len_all_authors_list / self.batch_size)):
            self.batched_authors_list = CustomUser.objects.all().prefetch_related(Prefetch('wbdetailedinfo_set', 
                                                                            queryset=WBDetailedInfo.objects.filter(enabled=False).select_related('product')))[i*self.batch_size:(i+1)*self.batch_size]
            self.go_through_all_authors()     
            self.save_update_avaliability()
            self.send_tg_notifications()
            self.new_prices = []
            self.updated_details = []
            self.prods_artikuls_to_delete = []
            self.notifications_to_save = []
        print(f'Товаров проверено:{self.test_counter}')



    def go_through_all_authors(self):
        '''Функция, в которой идет проход по одному автору из батча'''
        for i in range(len(self.batched_authors_list)):
            author_object = self.batched_authors_list[i]
            self.detail_product_url_api = f'https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest={author_object.dest_id}&spp=30&ab_testing=false&lang=ru&nm='
            details_of_prods_to_check = self.batched_authors_list[i].wbdetailedinfo_set.all()
            if len(details_of_prods_to_check) == 0:
                continue
            self.go_through_all_details(details_of_prods_to_check)


    def go_through_all_details(self, details_of_prods_to_check):
        '''Подготовка списка для обновления цены'''
        for j in range(math.ceil(len(details_of_prods_to_check) / 200)):
            self.batched_details_of_prods_to_check = details_of_prods_to_check[j*200:(j+1)*200]
            final_url = self.detail_product_url_api + ';'.join(map(lambda x: str(x.product.artikul), self.batched_details_of_prods_to_check))
            response = self.scraper.get(final_url, headers=self.headers)
            json_data = json.loads(response.text)
            products_on_page = json_data['data']['products']

            if len(products_on_page) != len(self.batched_details_of_prods_to_check):
                self.delete_not_existing_prods(products_on_page)


            products_on_page = sorted(products_on_page, key=lambda x: x['id'])
            self.batched_details_of_prods_to_check = sorted(self.batched_details_of_prods_to_check, key=lambda x: x.product.artikul)
            self.update_avaliability(products_on_page)



    def delete_not_existing_prods(self, products_on_page):
        '''Удаление товаров из списка временного, которые вообще
          удалились с сайта wb и не отображаются в api details'''
        prods_artikuls_to_delete = set(map(lambda x: x.product.artikul, self.batched_details_of_prods_to_check)) - set(map(lambda x: x['id'], products_on_page))
        self.prods_artikuls_to_delete.extend(prods_artikuls_to_delete)
        self.batched_details_of_prods_to_check = list(filter(lambda x: True if x.product.artikul not in prods_artikuls_to_delete else False, self.batched_details_of_prods_to_check))



    
    def update_avaliability(self, products_on_page):
        '''Обновление наличия продуктов, которые были не в наличии в БД + 
        разведение по тем, у кого есть размер, и тем, у кого нет'''
        for j in range(len(products_on_page)):
            self.current_detail_to_check = self.batched_details_of_prods_to_check[j]
            if products_on_page[j]['id'] == self.current_detail_to_check.product.artikul: #по хорошему вот тут надо добавить исключение какое то
                if self.current_detail_to_check.size == None:
                    self.check_nonsize_product(products_on_page[j])
                else:
                    self.check_size_product(products_on_page[j])                      
            else:
                print('Не сходится товар и запрос по индексам')



    def check_nonsize_product(self, product_on_page):
        '''Функция проверки наличия продукта, у которого нет размера'''
        self.test_counter += 1
        stocks = product_on_page['sizes'][0]['stocks']
        if len(stocks) != 0:
            #точка входа для уведомления пользователя о том, что товар в наличии
            volume = 0
            for stock in stocks:
                volume += stock['qty']
            price_of_detail = product_on_page['sizes'][0]['price']['product'] // 100
            #проверять тут нужно на разницу цены до "нет в наличии" и после
            self.enable_product(price_of_detail, volume)
            



    def check_size_product(self, product_on_page):
        '''Функция проверки наличия продукта, у которого есть размер'''
        self.test_counter += 1
        sizes = product_on_page['sizes']
        for size in sizes:
            if size['origName'] == self.current_detail_to_check.size:
                stocks = size['stocks']
                if len(stocks) != 0:
                    #точка входа для уведомления пользователя о том, что товар в наличии
                    volume = 0
                    for stock in stocks:
                        volume += stock['qty']
                    price_of_detail = size['price']['product'] // 100
                    self.enable_product(price_of_detail, volume) #добавить кастомизацию по размеру (вдруг его не было в наличии)
                break                      
                


    def enable_product(self, price_of_detail, volume):
        '''Точка входа для уведомления пользователя + изменение полей товара
        добавление товара в общую коллекцию обновления'''
        if int(self.current_detail_to_check.first_price) == 0:
            self.current_detail_to_check.first_price = price_of_detail
        self.current_detail_to_check.latest_price = price_of_detail
        self.current_detail_to_check.volume = volume
        self.current_detail_to_check.enabled = True
        self.current_detail_to_check.updated = timezone.now()
        self.updated_details.append(self.current_detail_to_check)
        self.new_prices.append(WBPrice(price=price_of_detail,
                                        added_time=timezone.now(),
                                        detailed_info=self.current_detail_to_check))
        self.notifications_to_save.append(Notification(text=f'<i>🛒WildBerries</i> <br> <b>📦{self.current_detail_to_check.product.name}</b> <br> <b> ✅ Появился в наличии! </b> Успейте купить!',
                                                        tg_text=f'<i>🛒WildBerries</i>\n<a href="{self.current_detail_to_check.product.url}"><b>📦{self.current_detail_to_check.product.name}</b></a>\n<b> ✅ Появился в наличии! </b> Успейте купить!',                
                                                        wb_product=self.current_detail_to_check,
                                                        user=self.current_detail_to_check.author))
        

    def make_deletion_notification(self):
        prods_to_delete =  WBProduct.objects.filter(artikul__in=self.prods_artikuls_to_delete).prefetch_related('wbdetailedinfo_set')
        for prod in prods_to_delete:
            if prod.wbdetailedinfo_set.exists():
                for detailed_info in prod.wbdetailedinfo_set:
                    self.notifications_to_save.append(Notification(text=f'<i>🛒WildBerries</i> <br> <b>📦{detailed_info.name}</b> <br> <b> ❗️Больше нет на сайте WB.</b> <br> Нам пришлось его полностью удалить. Если это ошибка, то напишите нам в поддержку.',
                                                                   tg_text=f'<i>🛒WildBerries</i>\n<a href="{detailed_info.product.url}"><b>📦{detailed_info.name}</b></a>\n<b> ❗️Больше нет на сайте WB.</b>\nНам пришлось его полностью удалить. Если это ошибка, то напишите нам в поддержку.',
                                                                        additional_link = prod.url,
                                                                        user=detailed_info.author))


    
    @transaction.atomic
    def save_update_avaliability(self):
        '''Занесение в БД обновления наличия'''
        WBDetailedInfo.objects.bulk_update(self.updated_details, ['latest_price', 'volume', 'enabled', 'updated', 'first_price'])
        WBPrice.objects.bulk_create(self.new_prices)
        WBProduct.objects.filter(artikul__in=self.prods_artikuls_to_delete).delete()
        Notification.objects.bulk_create(self.notifications_to_save)


    def send_tg_notifications(self):
        for notif in self.notifications_to_save:
            if notif.user.tg_user:
                tasks.send_tg_notification.delay(notif.user.tg_user.tg_id, notif.tg_text)



class WBPriceClearer:
    def __init__(self):
        '''Инициализация необходимых атрибутов'''
        self.batch_size = 1000
        self.len_all_details_list = WBDetailedInfo.objects.all().count()
        self.batched_details_list = []
        self.wbprice_ids_to_delete = []


    def run(self):
        '''Запуск процесса удаления лишних цен + батчинг по авторам'''
        for i in range(math.ceil(self.len_all_details_list / self.batch_size)):
            self.batched_details_list = WBDetailedInfo.objects.all().prefetch_related('wbprice_set')[i*self.batch_size:(i+1)*self.batch_size]
            self.go_through_all_details()     
            self.delete_notif_in_db()
            self.wbprice_ids_to_delete = []


    def go_through_all_details(self):
        '''Функция, в которой идет проход по одной детали из батча'''
        for i in range(len(self.batched_details_list)):
            if self.batched_details_list[i].wbprice_set.count() > 15:
                self.wbprice_ids_to_delete.extend(list(map(lambda x: x['pk'], self.batched_details_list[i].wbprice_set.order_by('-added_time')[14:].values('pk'))))
                self.wbprice_ids_to_delete.pop()


    @transaction.atomic
    def delete_notif_in_db(self):
        '''Занесение в БД обновления наличия'''
        WBPrice.objects.filter(pk__in=self.wbprice_ids_to_delete).delete()