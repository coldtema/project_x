import time
from functools import wraps


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


def check_detailed_info_of_user(id_of_detailed_info, user):
    return user.wbdetailedinfo_set.filter(pk=id_of_detailed_info).select_related('product').first() #переписать, тк detailed_info - foreign key


def get_image_url(artikul):
    '''Функция конструирования url-api для последующего обращения'''
    basket_num = get_basket_num(int(artikul))
    artikul = str(artikul)
    if basket_num < 10:
        basket_num = f'0{basket_num}'
    img_url = ''
    if len(artikul) == 9:
        img_url = f'https://basket-{basket_num}.wbbasket.ru/vol{artikul[:4]}/part{artikul[:6]}/{artikul}/images/c516x688/1.webp'
    elif len(artikul) == 8:
        img_url = f'https://basket-{basket_num}.wbbasket.ru/vol{artikul[:3]}/part{artikul[:5]}/{artikul}/images/c516x688/1.webp'
    elif len(artikul) == 7:
        img_url = f'https://basket-{basket_num}.wbbasket.ru/vol{artikul[:2]}/part{artikul[:4]}/{artikul}/images/c516x688/1.webp'
    elif len(artikul) == 6:
        img_url = f'https://basket-{basket_num}.wbbasket.ru/vol{artikul[:1]}/part{artikul[:3]}/{artikul}/images/c516x688/1.webp'
    return img_url



def get_price_history_url(artikul):
    '''Функция конструирования url-api для последующего обращения'''
    basket_num = get_basket_num(artikul)
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


#пока не нужна эта функция, но не убираю
# @general_utils.time_count
# def load_test_data(request):
#     # author_object = Author.objects.get(pk=4)
#     # with open('wb_links.txt', 'r', encoding='utf-8') as file:
#     #     links_list = file.read().split('\n')
#     #     for link in links_list:
#     #         product = wb_products.Product(link, author_object)
#     #         product.get_product_info()
#     #         del product
#     all_cats = WBMenuCategory.objects.all()
#     author_object = Author.objects.get(pk=4)
#     for elem in all_cats:
#         url = 'https://www.wildberries.ru' + elem.main_url
#         if elem.shard_key != 'blackhole':
#             menu_category = wb_menu_categories.MenuCategory(url, author_object)
#             menu_category.run()
#             del menu_category
def get_brand_and_seller_from_prod(product_artikul):
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    product_url_api = f'https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest=-1257786&spp=30&ab_testing=false&lang=ru&nm={product_artikul}'
    response = scraper.get(product_url_api, headers=headers)
    json_data = json.loads(response.text)
    seller_name = json_data['data']['products'][0]['supplier'] #имя продавца
    seller_artikul = json_data['data']['products'][0]['supplierId'] #id продавца
    brand_name = json_data['data']['products'][0]['brand'] #имя бренда
    brand_artikul = json_data['data']['products'][0]['brandId'] #id бренда
    scraper.close()
    if brand_artikul != 0:
        seller_in_db, _ = WBSeller.objects.get_or_create(wb_id=seller_artikul, defaults={'name': seller_name,  
                                                                                       'main_url': f'https://www.wildberries.ru/seller/{seller_artikul}'})
        brand_in_db, _ = WBBrand.objects.get_or_create(wb_id=brand_artikul, defaults={'name': brand_name,  
                                                                                       'main_url': f'https://www.wildberries.ru/brands/{brand_artikul}'})
        return {'seller': seller_in_db, 'brand': brand_in_db}
    else:
        seller_in_db, _ = WBSeller.objects.get_or_create(wb_id=seller_artikul, defaults={'name': seller_name,  
                                                                                       'main_url': f'https://www.wildberries.ru/seller/{seller_artikul}'})
        return {'seller': seller_in_db}

def get_seller_from_link(seller_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    '''Получение артикула (wb_id) селлера'''
    seller_artikul = re.search(r'(seller)\/([a-z]+?\-)?(\d+)(\?)?', seller_url)
    #если артикул селлера указан сразу в url
    if seller_artikul:
        seller_artikul = seller_artikul.group(3)
    else:
        #если в url указано имя селлера в виде slug'a
        seller_slug_name = re.search(r'(seller\/)([a-z\-]+)(\?)?', seller_url).group(2)
        final_url = f'https://static-basket-01.wbbasket.ru/vol0/constructor-api/shops/{seller_slug_name}.json'
        response = scraper.get(final_url, headers=headers)
        json_data = json.loads(response.text)
        seller_artikul = json_data['supplierID']
    final_url = f'https://catalog.wb.ru/sellers/v2/catalog?ab_testing=false&appType=1&curr=rub&dest=-1257786&hide_dtype=13&lang=ru&page=1&sort=popular&spp=30&supplier={seller_artikul}'
    response = scraper.get(final_url, headers=headers)
    json_data = json.loads(response.text)
    seller_name = json_data['data']['products'][0]['supplier']
    seller_in_db, _ = WBSeller.objects.get_or_create(wb_id=seller_artikul, defaults={'name': seller_name,  
                                                                                    'main_url': f'https://www.wildberries.ru/seller/{seller_artikul}'})
    scraper.close()
    return {'seller': seller_in_db}
