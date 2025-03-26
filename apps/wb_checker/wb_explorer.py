from requests import request
import re
import json
import cloudscraper
from datetime import datetime

#отслеживание цены
#https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest=-1257786&hide_dtype=10&spp=30&ab_testing=false&lang=ru&nm=
#https://card.wb.ru/cards/v2/list?appType=1&curr=rub&dest=-1257786&spp=30&ab_testing=false&lang=ru&nm=
def get_product_info(product_url):
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
    shop_name = json_data['data']['products'][0]['supplier'] #имя продавца
    shop_id = json_data['data']['products'][0]['supplierId'] #id продавца
    brand_name = json_data['data']['products'][0]['brand'] #имя бренда
    brand_id = json_data['data']['products'][0]['brandId'] #id бренда
    price_history = list(map(lambda x: (datetime.fromtimestamp(x['dt']), x['price']['RUB']//100), price_history))
    price_history.append((datetime.now(), price_element))
    return {'name': name,
            'artikul': artikul,
            'price_element': price_element,
            'wb_cosh': wb_cosh,
            'shop_name': shop_name,
            'shop_id': shop_id,
            'brand_name': brand_name,
            'brand_id': brand_id}




# if 201850 in promotions or 201858 in promotions:  # промо - вычислял по каунтеру промо (большая выборка)
#     wb_cosh = True

def get_price_history(product_url):
    artikul = re.search(r'\/(\d+)\/', product_url).group(1)
    if len(artikul) == 8:
        for basket_num in range(0, 30):
            try:
                price_history_searcher_url = f'https://basket-{str(basket_num)}.wbbasket.ru/vol{artikul[:5]}/part{artikul[:7]}/{artikul}/info/price-history.json'
                headers = {"User-Agent": "Mozilla/5.0"}
                scraper = cloudscraper.create_scraper()
                response = scraper.get(price_history_searcher_url, headers=headers)
                json_data = json.loads(response.text)
                return json_data
            except:
                continue
    else:
        for basket_num in range(0, 30):
            try:
                price_history_searcher_url = f'https://basket-{str(basket_num)}.wbbasket.ru/vol{artikul[:4]}/part{artikul[:6]}/{artikul}/info/price-history.json'
                headers = {"User-Agent": "Mozilla/5.0"}
                scraper = cloudscraper.create_scraper()
                response = scraper.get(price_history_searcher_url, headers=headers)
                json_data = json.loads(response.text)
                return json_data
            except:
                continue

#вроде как 100 товаров на странице
#https://www.wildberries.ru/seller/16105
# def get_catalog_of_supplier(dynamic_url):
#     sorting = 'popular'
#     addons = ''
#     if 'catalog' in dynamic_url:
#         seller = get_product_info(dynamic_url)['shop_id']
#     elif 'seller' in dynamic_url:
#         #дописать sorting
#         seller = re.search(r'(seller)\/(\d+)\?', dynamic_url).group(2)
#         addons = re.search(r'(page\=1\&)(.+)', dynamic_url).group(2)
#     final_url = f'https://catalog.wb.ru/sellers/v2/catalog?ab_testing=false&appType=1&curr=rub&dest=-1257786&hide_dtype=13&lang=ru&page={1}&sort={sorting}&spp=30&supplier={seller}&uclusters=0{addons}'
#     print(final_url)
#     headers = {"User-Agent": "Mozilla/5.0"}
#     scraper = cloudscraper.create_scraper()
#     response = scraper.get(final_url, headers=headers)
#     json_data = json.loads(response.text)
#     print(json_data['data']['total'])
    # try:
        # for
        # final_url = f'https://catalog.wb.ru/sellers/v2/catalog?ab_testing=false&appType=1&curr=rub&dest=-1257786&hide_dtype=13&lang=ru&page={page}&sort={sorting}&spp=30&supplier={seller}&uclusters=0{addons}'
