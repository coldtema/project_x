import math
import json
import time
import cloudscraper
import aiohttp
import asyncio
import json
from statistics import median
from datetime import datetime
from django.utils import timezone
from apps.wb_checker.utils.general_utils import time_count
from apps.wb_checker.models import TopWBProduct
from django.db import transaction


class TopBuilder:
    '''Класс для постоения топа продуктов исходя 
    из тех продуктов, которые в него переданы'''
    def __init__(self, dict_products_in_catalog):
        self.dict_products_in_catalog = dict_products_in_catalog
        self.feedbacks_median = self.get_feedbacks_median()
        self.price_history = None



    @time_count
    def build_top(self):
        '''Главная функция построения топа'''
        dict_artikuls_and_urls_to_make_tasks = {artikul:self.get_price_history_url(artikul) for artikul in self.dict_products_in_catalog.keys()}
        dict_artikuls_price_history = asyncio.run(group_all_histories(dict_artikuls_and_urls_to_make_tasks))
        for artikul, product_object in self.dict_products_in_catalog.items():
            try: #если вдруг истории цены нет
                self.price_history = dict_artikuls_price_history[artikul]
                self.price_history = list(map(lambda x: (x['dt'], x['price']['RUB']//100), self.price_history))
                self.price_history.append((timezone.now(), product_object.latest_price))
            except:
                self.price_history = [(timezone.now(), product_object.latest_price)]
            if len(self.price_history) < 4:
                product_object.score = 0
            else:
                self.prices_duration = self.get_duration_of_prices()
                score_of_product = self.get_score_of_product(product_object)
                product_object.score = score_of_product
        return self.dict_products_in_catalog



    def get_score_of_product(self, product_object):
        '''Получение внутренней оценки отдельного продукта'''
        prices_median = self.get_prices_median()
        true_discount = (prices_median - product_object.latest_price) / prices_median
        trust_score = min(1.0, product_object.feedbacks / self.feedbacks_median) * (product_object.rating / 5)
        score_of_product = true_discount * trust_score
        return score_of_product



    def get_prices_median(self):
        '''Получение весовой медианы цен отдельного продукта'''
        list_prices = []
        for elem in self.prices_duration:
            list_prices.extend([elem[1] for i in range(int(elem[0]))])
        return median(list_prices)




    def get_duration_of_prices(self):
        '''Получение списка цен в виде (цена*кол-во дней этой цены) для отдельного продукта'''
        prices_duration = []
        prices_duration.append((7, self.price_history[0][1]))#для первого
        for i in range(1, len(self.price_history)-1):
            price_duration = abs(self.price_history[i][0] - self.price_history[i-1][0]) / (60*60*24) #кол-во секунд в дне
            prices_duration.append((price_duration, self.price_history[i][1]))
        prices_duration.append((math.ceil(abs(datetime.timestamp(self.price_history[-1][0]) - self.price_history[-2][0]) / (60*60*24)), self.price_history[-1][1]))#для последнего
        return prices_duration


            

    def get_feedbacks_median(self):
        '''Получение медианы кол-ва отзывов по всей категории'''
        list_of_feedbacks = []
        for product_object in self.dict_products_in_catalog.values():
            list_of_feedbacks.append(product_object.feedbacks)
        list_of_feedbacks = sorted((list_of_feedbacks))
        if median(list_of_feedbacks) == 0:
            return math.ceil(sum(list_of_feedbacks) / len(list_of_feedbacks))
        return median(list_of_feedbacks)



    def get_price_history_url(self, artikul):
        '''Функция конструирования url-api для последующего обращения'''
        basket_num = TopBuilder.get_basket_num(artikul)
        artikul = str(artikul)
        if basket_num < 10:
            basket_num = f'0{basket_num}'
        price_history_searcher_url = ''
        if len(artikul) == 9:
            price_history_searcher_url = f'https://basket-{basket_num}.wbbasket.ru/vol{artikul[:4]}/part{artikul[:6]}/{artikul}/info/price-history.json'
        elif len(artikul) == 8:
            price_history_searcher_url = f'https://basket-{basket_num}.wbbasket.ru/vol{artikul[:3]}/part{artikul[:5]}/{artikul}/info/price-history.json'
        elif len(artikul) == 7:
            price_history_searcher_url = f'https://basket-{basket_num}.wbbasket.ru/vol{artikul[:2]}/part{artikul[:4]}/{artikul}/info/price-history.json'
        elif len(artikul) == 6:
            price_history_searcher_url = f'https://basket-{basket_num}.wbbasket.ru/vol{artikul[:1]}/part{artikul[:3]}/{artikul}/info/price-history.json'
        return price_history_searcher_url
    


    @staticmethod
    def get_basket_num(artikul: int):
        '''Определение сервера, на котором находится история цены по js скрипту на wb'''
        s = artikul // 100000  # Разделение артикулов на группы
        if s <= 143:
            return 1
        elif s <= 287:
            return 2
        elif s <= 431:
            return 3
        elif s <= 719:
            return 4
        elif s <= 1007:
            return 5
        elif s <= 1061:
            return 6
        elif s <= 1115:
            return 7
        elif s <= 1169:
            return 8
        elif s <= 1313:
            return 9
        elif s <= 1601:
            return 10
        elif s <= 1655:
            return 11
        elif s <= 1919:
            return 12
        elif s <= 2045:
            return 13
        elif s <= 2189:
            return 14
        elif s <= 2405:
            return 15
        elif s <= 2621:
            return 16
        elif s <= 2837:
            return 17
        elif s <= 3053:
            return 18
        elif s <= 3269:
            return 19
        elif s <= 3485:
            return 20
        elif s <= 3701:
            return 21
        elif s <= 3917:
            return 22
        elif s <= 4133:
            return 23
        elif s <= 4349:
            return 24
        elif s <= 4565:
            return 25
        else:
            return 26
        



async def get_price_history(session, artikul, url):
    '''Функция получения истории цены отдельного продукта'''
    try:
        async with session.get(url) as resp:
            data = await resp.json()
            return artikul, data
    except:
        return artikul, []
    

async def group_all_histories(artikuls_urls):
    '''Асинхронное получение историй цен всех переданных продуктов'''
    async with aiohttp.ClientSession() as session:
        tasks = [get_price_history(session, artikul, url) for artikul, url in artikuls_urls.items()]
        results = await asyncio.gather(*tasks)
        return dict(results)
        






class UpdaterInfoOfTop:
    def __init__(self):
        '''Инициализация необходимых атрибутов'''
        self.batch_size = 200
        self.len_all_top_wb_products_list = TopWBProduct.objects.all().count()
        self.batched_top_wb_products_list = []
        self.scraper = cloudscraper.create_scraper()
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.updated_top_prods = []
        self.top_prods_artikuls_to_delete = []
    
    def run(self):
        '''Запуск процесса обновления + разбиение всех продуктов на батчи'''
        for i in range(math.ceil(self.len_all_top_wb_products_list / self.batch_size)):
            self.batched_top_wb_products_list = TopWBProduct.objects.all()[i*self.batch_size:(i+1)*self.batch_size]
            self.get_new_info()
        self.save_update_prices()


    def get_new_info(self):
        '''Получение новой информации из запроса к api wb + 
        формирование правильных коллекций для обновления информации'''
        top_product_url_api = f'https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest={123589280}&spp=30&ab_testing=false&lang=ru&nm='
        if len(self.batched_top_wb_products_list) == 0:
            return
        final_url = top_product_url_api + ';'.join(map(lambda x: str(x.artikul), self.batched_top_wb_products_list))
        response = self.scraper.get(final_url, headers=self.headers)
        json_data = json.loads(response.text)
        products_on_page = json_data['data']['products']

        if len(products_on_page) != len(self.batched_top_wb_products_list):
            self.delete_not_existing_prods(products_on_page)

        products_on_page = sorted(products_on_page, key=lambda x: x['id'])
        self.batched_top_wb_products_list = sorted(self.batched_top_wb_products_list, key=lambda x: x.artikul)

        self.update_top_wb_product_info(products_on_page)
            

    def delete_not_existing_prods(self, products_on_page):
        '''Удаление товаров из списка временного, которые вообще
          удалились с сайта wb и не отображаются в api details'''
        prods_artikuls_to_delete = set(map(lambda x: x.artikul, self.batched_top_wb_products_list)) - set(map(lambda x: x['id'], products_on_page))
        self.top_prods_artikuls_to_delete.extend(prods_artikuls_to_delete)
        self.batched_top_wb_products_list = list(filter(lambda x: True if x.artikul not in prods_artikuls_to_delete else False, self.batched_top_wb_products_list))



    def update_top_wb_product_info(self, products_on_page):
        '''Обновление информации о продуктах с одной батчевой страницы'''
        for i in range(len(products_on_page)):
            if products_on_page[i]['id'] == self.batched_top_wb_products_list[i].artikul:
                if len(products_on_page[i]['sizes'][0]['stocks']) == 0:
                    self.top_prods_artikuls_to_delete.append(self.batched_top_wb_products_list[i].pk)
                else:
                    flag_change = False 
                    if products_on_page[i]['sizes'][0]['price']['product'] // 100 != self.batched_top_wb_products_list[i].latest_price:
                        self.batched_top_wb_products_list[i].latest_price = products_on_page[i]['sizes'][0]['price']['product'] // 100
                        flag_change = True
                    if products_on_page[i]['feedbacks'] != self.batched_top_wb_products_list[i].feedbacks:
                        self.batched_top_wb_products_list[i].feedbacks = products_on_page[i]['feedbacks']
                        flag_change = True
                    if flag_change == True:
                        self.updated_top_prods.append(self.batched_top_wb_products_list[i])
            else:
                raise Exception



    @transaction.atomic
    def save_update_prices(self):
        '''Занесение в БД всех обновлений после полного батчевого прохода'''
        TopWBProduct.objects.bulk_update(self.updated_top_prods, ['latest_price', 'feedbacks'])
        TopWBProduct.objects.filter(pk__in=self.top_prods_artikuls_to_delete).delete()