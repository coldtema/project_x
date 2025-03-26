from requests import request
import re
import json
import cloudscraper
from datetime import datetime
import apps.wb_checker.backend_explorer as backend_explorer
from .models import WBProduct, WBSeller, WBBrand, WBPrice
from apps.blog.models import Author
from django.utils import timezone

#отслеживание цены
#https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest=-1257786&hide_dtype=10&spp=30&ab_testing=false&lang=ru&nm=
#https://card.wb.ru/cards/v2/list?appType=1&curr=rub&dest=-1257786&spp=30&ab_testing=false&lang=ru&nm=


def get_product_info(product_url, author_id):
    #полностью собирает элемент
    artikul = re.search(r'\/(\d+)\/', product_url).group(1)
    product_url_api = f'https://card.wb.ru/cards/v2/list?appType=1&curr=rub&dest=-1257786&spp=30&ab_testing=false&lang=ru&nm={artikul}'
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url_api, headers=headers)
    json_data = json.loads(response.text)
    name = json_data['data']['products'][0]['name']
    price_element = json_data['data']['products'][0]['sizes'][0]['price']['product'] // 100
    price_history = get_price_history(product_url)
    wb_cosh = True
    seller_name = json_data['data']['products'][0]['supplier'] #имя продавца
    seller_id = json_data['data']['products'][0]['supplierId'] #id продавца
    brand_name = json_data['data']['products'][0]['brand'] #имя бренда
    brand_id = json_data['data']['products'][0]['brandId'] #id бренда
    price_history = list(map(lambda x: (timezone.make_aware(datetime.fromtimestamp(x['dt'])), x['price']['RUB']//100), price_history))
    price_history.append((timezone.now(), price_element))
    #проверяет наличие этого бренда и продавца в БД (если нет, то создает их, если есть - не трогает)
    seller_dict = {'seller_name': seller_name, 'seller_id': seller_id}
    brand_dict = {'brand_name': brand_name, 'brand_id': brand_id}
    backend_explorer.check_existence_of_brand_and_seller(seller_dict=seller_dict, brand_dict=brand_dict)
    #добавляем элемент
    new_product = WBProduct.objects.create(name=name,
            artikul=artikul,
            latest_price=price_element,
            wb_cosh=wb_cosh,
            url=product_url,
            enabled=True,
            seller=WBSeller.objects.get(wb_id=seller_id),
            brand=WBBrand.objects.get(wb_id=brand_id))
    #добавляем many-to-many связь
    new_product.authors.add(Author.objects.get(id=author_id))
    #добавляем все прайсы
    for elem in price_history:
        WBPrice.objects.create(price=elem[1],
                               added_time=elem[0],
                               product_id=new_product.id)




# if 201850 in promotions or 201858 in promotions:  # промо - вычислял по каунтеру промо (большая выборка)
#     wb_cosh = True
#https://basket-02.wbbasket.ru/vol158/part15851/15851117/info/price-history.json
def get_price_history(product_url):
    artikul = re.search(r'\/(\d+)\/', product_url).group(1)
    if len(artikul) == 9:
        for basket_num in range(1, 30):
            try:
                if basket_num < 10:
                    basket_num = f'0{basket_num}'
                price_history_searcher_url = f'https://basket-{str(basket_num)}.wbbasket.ru/vol{artikul[:4]}/part{artikul[:6]}/{artikul}/info/price-history.json'
                headers = {"User-Agent": "Mozilla/5.0"}
                scraper = cloudscraper.create_scraper()
                response = scraper.get(price_history_searcher_url, headers=headers)
                json_data = json.loads(response.text)
                return json_data
            except:
                continue
    else:
        for basket_num in range(1, 30):
            try:
                if basket_num < 10:
                    basket_num = f'0{basket_num}'
                price_history_searcher_url = f'https://basket-{str(basket_num)}.wbbasket.ru/vol{artikul[:3]}/part{artikul[:5]}/{artikul}/info/price-history.json'
                headers = {"User-Agent": "Mozilla/5.0"}
                scraper = cloudscraper.create_scraper()
                response = scraper.get(price_history_searcher_url, headers=headers)
                json_data = json.loads(response.text)
                return json_data
            except:
                continue

#вроде как 100 товаров на странице
#https://www.wildberries.ru/seller/16105
def get_catalog_of_seller(dynamic_url):
    sorting = 'popular'
    addons = ''
    if 'catalog' in dynamic_url:
        seller = get_product_info(dynamic_url)['shop_id']
    elif 'seller' in dynamic_url:
        #дописать sorting
        seller = re.search(r'(seller)\/(\d+)\?', dynamic_url).group(2)
        addons = re.search(r'(page\=1\&)(.+)', dynamic_url).group(2)
    final_url = f'https://catalog.wb.ru/sellers/v2/catalog?ab_testing=false&appType=1&curr=rub&dest=-1257786&hide_dtype=13&lang=ru&page={1}&sort={sorting}&spp=30&supplier={seller}&uclusters=0{addons}'
    print(final_url)
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(final_url, headers=headers)
    json_data = json.loads(response.text)
    print(json_data['data']['total'])
    # try:
        # for
        # final_url = f'https://catalog.wb.ru/sellers/v2/catalog?ab_testing=false&appType=1&curr=rub&dest=-1257786&hide_dtype=13&lang=ru&page={page}&sort={sorting}&spp=30&supplier={seller}&uclusters=0{addons}'



def get_catalog_of_brand():
    ...