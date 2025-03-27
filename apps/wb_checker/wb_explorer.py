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

def time_count(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(end - start)
        return result
    return wrapper


@time_count
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
    try: #если вдруг истории цены нет
        price_history = get_price_history(product_url)
        price_history = list(map(lambda x: (timezone.make_aware(datetime.fromtimestamp(x['dt'])), x['price']['RUB']//100), price_history))
        price_history.append((timezone.now(), price_element))
    except:
        price_history = [(timezone.now(), price_element)]
    seller_name = json_data['data']['products'][0]['supplier'] #имя продавца
    seller_id = json_data['data']['products'][0]['supplierId'] #id продавца
    brand_name = json_data['data']['products'][0]['brand'] #имя бренда
    brand_id = json_data['data']['products'][0]['brandId'] #id бренда
    #проверяет наличие этого бренда и продавца в БД (если нет, то создает их, если есть - не трогает)
    seller_dict = {'seller_name': seller_name, 'seller_id': seller_id}
    brand_dict = {'brand_name': brand_name, 'brand_id': brand_id}
    backend_explorer.check_existence_of_brand(brand_dict=brand_dict)
    backend_explorer.check_existence_of_seller(seller_dict=seller_dict)
    #добавляем элемент
    new_product = WBProduct.objects.create(name=name,
            artikul=artikul,
            latest_price=price_element,
            wb_cosh=True,
            url=product_url,
            enabled=True,
            seller=WBSeller.objects.get(wb_id=seller_id),
            brand=WBBrand.objects.get(wb_id=brand_id))
    #добавляем many-to-many связь (почему то через автора всегда быстрее)
    Author.objects.get(id=author_id).wbproduct_set.add(new_product)
    #добавляем все прайсы
    price_history = list(map(lambda x: WBPrice(price=x[1], added_time=x[0], product=new_product), price_history))
    WBPrice.objects.bulk_create(price_history)




# if 201850 in promotions or 201858 in promotions:  # промо - вычислял по каунтеру промо (большая выборка)
#     wb_cosh = True


#js скрипт на wb для определения сервера
def get_basket_num(artikul: int) -> int:
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
    

def get_price_history(product_url):
    artikul = (re.search(r'\/(\d+)\/', product_url).group(1))
    basket_num = get_basket_num(int(artikul))
    print(basket_num)
    if basket_num < 10:
        basket_num = f'0{basket_num}'
    if len(artikul) == 9:
        price_history_searcher_url = f'https://basket-{basket_num}.wbbasket.ru/vol{artikul[:4]}/part{artikul[:6]}/{artikul}/info/price-history.json'
    else:
        price_history_searcher_url = f'https://basket-{basket_num}.wbbasket.ru/vol{artikul[:3]}/part{artikul[:5]}/{artikul}/info/price-history.json'
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(price_history_searcher_url, headers=headers)
    json_data = json.loads(response.text)
    return json_data



#надо проверить повторюшки еще потом перед этим
def get_product_info_seller_catalog(author_id, product_in_catalog):
    #полностью собирает элемент
    artikul = product_in_catalog['id']
    product_url = f'https://www.wildberries.ru/catalog/{artikul}/detail.aspx'
    name = product_in_catalog['name'] #имя продукта в каталоге
    price_element = product_in_catalog['sizes'][0]['price']['product'] // 100
    # price_history = [(timezone.now(), price_element)] #не берем историю цены - слишком долго (1.5 сек)
    seller_id = product_in_catalog['supplierId'] #id продавца
    brand_name = product_in_catalog['brand'] #имя бренда
    brand_id = product_in_catalog['brandId'] #id бренда
    #проверяет наличие в БД только по бренду, потому что seller один и тот же (если нет, то создает его, если есть - не трогает)
    brand_dict = {'brand_name': brand_name, 'brand_id': brand_id}
    #проверяет наличие только по бренду, потому что seller один и тот же
    backend_explorer.check_existence_of_brand(brand_dict=brand_dict)
    #добавляем объект продукта
    new_product = WBProduct(name=name,
            artikul=artikul,
            latest_price=price_element,
            wb_cosh=True,
            url=product_url,
            enabled=True,
            seller=WBSeller.objects.get(wb_id=seller_id),
            brand=WBBrand.objects.get(wb_id=brand_id))
    #добавляем объект прайса
    new_product_price = WBPrice(price=price_element,
                               added_time=timezone.now(),
                               product=new_product)
    return new_product, new_product_price



def get_catalog_of_seller(seller_url, author_id):
    #конструирует url
    seller_id = re.search(r'(seller)\/(\d+)\?', seller_url).group(2)
    addons = re.search(r'(page\=1\&)(.+)', seller_url).group(2)
    sorting = re.search(r'\&(sort)\=(.+?)\&', seller_url).group(2)
    if not addons: addons = ''
    if not sorting: sorting = 'popular'
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