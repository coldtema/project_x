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