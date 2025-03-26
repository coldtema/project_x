import re
from .models import WBProduct, WBBrand, WBSeller
from apps.blog.models import Author
from django.http import HttpResponse
from wb_explorer import get_product_info

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
        get_product_info(product_url, author_id)


def check_repetitions_seller(product_url, author_id):
    ...

def check_repetitions_brand(product_url, author_id):
    ...