import time
from functools import wraps
from .models import WBBrand, WBSeller

def time_count(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f'{func.__doc__} - {end - start}')
        return result
    return wrapper


def check_repetitions_catalog(product_artikul_to_check, potential_repetitions):
    if str(product_artikul_to_check) in potential_repetitions.keys():
        return potential_repetitions[str(product_artikul_to_check)]


#проверяю на наличие бренда и продавца в БД (возможно можно как то засунуть в одну атомарную транзакцию, чтобы не обращаться к БД для создания несуществующего бренда/селлера)
#Вторым параметром передаю, был ли бренд/селлер уже в бд или нет
def check_existence_of_brand(brand_name, brand_artikul):
    brand_existence = WBBrand.objects.filter(wb_id=brand_artikul)
    if not brand_existence:
        brand_object = (WBBrand.objects.create(name=brand_name,
                               wb_id=brand_artikul,
                               main_url=f'https://www.wildberries.ru/brands/{brand_artikul}',
                               full_control = False), False)
    else:
        brand_object = (brand_existence[0], True)
    return brand_object


def check_existence_of_seller(seller_name, seller_artikul):
    seller_existence = WBSeller.objects.filter(wb_id=seller_artikul)
    if not seller_existence:
        seller_object = (WBSeller.objects.create(name=seller_name,
                               wb_id=seller_artikul,
                               main_url=f'https://www.wildberries.ru/brands/{seller_artikul}',
                               full_control = False), False)
    else:
        seller_object = (seller_existence[0], True)
    return seller_object