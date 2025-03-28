import re
from .models import WBProduct, WBBrand, WBSeller
from apps.blog.models import Author
from django.http import HttpResponse
import apps.wb_checker.wb_explorer as wb_explorer
import cloudscraper
import json
import time
from functools import wraps


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
def check_repetitions_product(product_url, author_id):
    artikul = re.search(r'\/(\d+)\/', product_url).group(1)
    repeated_product = WBProduct.enabled_products.filter(artikul=artikul) #посмотреть, как сделать так, чтобы get - функция не выдавала исключения
    if repeated_product and len(repeated_product) == 1: #если нашел повторюшку
        repeated_product = repeated_product[0]
        authors_list = repeated_product.authors.all() #проверяет, нет ли уже того же автора у этой повторюшки
        authors_list = map(lambda x: x.id, authors_list)
        for elem in authors_list: #выводит ворнинг, если такой же автор
            if elem == author_id:
                print('Товар уже есть в отслеживании')
                return
        repeated_product.authors.add(Author.objects.get(id=author_id)) #если не нашел автора и не выкинуло из функции, то добавляет many-to-many связь
    else:
        wb_explorer.get_product_info(product_url, author_id)

#изменить имя функции во views
def get_repetitions_catalog_seller(seller_url, author_id):
    potential_repetitions = []
    seller_artikul = get_seller_artikul(seller_url)
    if WBSeller.objects.filter(wb_id=seller_artikul).first():
        potential_repetitions = WBProduct.enabled_products.filter(seller=WBSeller.objects.get(wb_id=seller_artikul))
        potential_repetitions = dict(map(lambda x: (x.artikul, x), potential_repetitions))
    return wb_explorer.get_catalog_of_seller(seller_url, author_id, potential_repetitions)

def check_repetitions_catalog(product_artikul, potential_repetitions):
    if str(product_artikul) in potential_repetitions.keys():
        return potential_repetitions[str(product_artikul)]


#проверяю на наличие бренда и продавца в БД
def check_existence_of_brand(brand_dict):
    brand_existence = WBBrand.objects.filter(wb_id=brand_dict['brand_id'])
    if not brand_existence:
        WBBrand.objects.create(name=brand_dict['brand_name'],
                               wb_id=brand_dict['brand_id'],
                               main_url=f'https://www.wildberries.ru/brands/{brand_dict['brand_id']}',
                               full_control = False)


def check_existence_of_seller(seller_dict):
    seller_existence = WBSeller.objects.filter(wb_id=seller_dict['seller_id'])
    if not seller_existence:
        WBSeller.objects.create(name=seller_dict['seller_name'],
                               wb_id=seller_dict['seller_id'],
                               main_url=f'https://www.wildberries.ru/seller/{seller_dict['seller_id']}',
                               full_control = False)

#https://www.wildberries.ru/seller/simaland-exclusive
#https://www.wildberries.ru/seller/simaland-exclusive?page=1&sort=priceup&fbrand=28172
def get_seller_artikul(seller_url):
    seller_artikul = re.search(r'(seller)\/([a-z]+?\-)?(\d+)(\?)?', seller_url)
    if seller_artikul:
        seller_artikul = seller_artikul.group(3)
    else:
        seller_slug_name = re.search(r'(seller\/)([a-z\-]+)(\?)?', seller_url).group(2)
        final_url = f'https://static-basket-01.wbbasket.ru/vol0/constructor-api/shops/{seller_slug_name}.json'
        headers = {"User-Agent": "Mozilla/5.0"}
        scraper = cloudscraper.create_scraper()
        response = scraper.get(final_url, headers=headers)
        json_data = json.loads(response.text)
        seller_artikul = json_data['supplierID']
    return seller_artikul



#изменить имя функции во views
def get_repetitions_catalog_brand(brand_url, author_id):
    brand_artikul = get_brand_artikul(brand_url)
    if WBSeller.objects.filter(wb_id=brand_artikul).first():
        potential_repetitions = WBProduct.enabled_products.filter(brand=WBSeller.objects.get(wb_id=brand_artikul))
        potential_repetitions = list(map(lambda x: {x.id: x}, potential_repetitions))
    return wb_explorer.get_catalog_of_brand(brand_url, author_id, potential_repetitions)

#Варианты урлов:
#https://www.wildberries.ru/brands/joonies
#https://www.wildberries.ru/brands/311409788-cotton-care
#https://static-basket-01.wbbasket.ru/vol0/data/brands/joonies.json
def get_brand_artikul(brand_url):
    brand_artikul = re.search(r'(brands)\/([a-z]+?\-)?(\d+)(\?)?', brand_url)
    if brand_artikul:
        brand_artikul = brand_artikul.group(3)
    else:
        brand_slug_name = re.search(r'(brands\/)([a-z\-]+)(\?)?', brand_url).group(2)
        final_url = f'https://static-basket-01.wbbasket.ru/vol0/data/brands/{brand_slug_name}.json'
        headers = {"User-Agent": "Mozilla/5.0"}
        scraper = cloudscraper.create_scraper()
        response = scraper.get(final_url, headers=headers)
        json_data = json.loads(response.text)
        brand_artikul = json_data['id']
    return brand_artikul

#изменения:
#1. добавил функцию для взятия всех потенциальных повторюшек по селлеру
#2. добавил функуию на проверку повторюшек внутри листа, который отдают функции на получение повторюшек от бренда и листа
#3. перенес функцию получения артикула селлера из урла + изменил ее для разных вариантов
#4. добавил функцию на получение потенциальных повторюшек у бренда
#5. добавил функцию получения артикула бренда из урла для разных вариантов
#6. потестить урл селлера и бренда с разными фильтрами еще