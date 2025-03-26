import re
from .models import WBProduct, WBBrand, WBSeller
from apps.blog.models import Author
from django.http import HttpResponse
import apps.wb_checker.wb_explorer as wb_explorer 

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

#проверяю на наличие бренда и продавца в БД
def check_existence_of_brand_and_seller(seller_dict, brand_dict):
    brand_existence = WBBrand.objects.filter(wb_id=brand_dict['brand_id'])
    seller_existence = WBSeller.objects.filter(wb_id=seller_dict['seller_id'])
    if not brand_existence:
        WBBrand.objects.create(name=brand_dict['brand_name'],
                               wb_id=brand_dict['brand_id'],
                               main_url=f'https://www.wildberries.ru/brands/{brand_dict['brand_id']}',
                               full_control = False)
    if not seller_existence:
        WBSeller.objects.create(name=seller_dict['seller_name'],
                               wb_id=seller_dict['seller_id'],
                               main_url=f'https://www.wildberries.ru/seller/{seller_dict['seller_id']}',
                               full_control = False)

def check_repetitions_seller(product_url, author_id):
    ...

def check_repetitions_brand(product_url, author_id):
    ...