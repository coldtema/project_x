import time
from ..models import WBMenuCategory, WBCategory
import cloudscraper
import json



def update_custom_cats():
    '''Обновление базы категорий от самого wb которые используются внутри фильтров бренда и селлера
    сейчас не используется, но не удаляю'''
    categories_list = []
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    final_url = f'https://static-basket-01.wbbasket.ru/vol0/data/subject-base.json'
    response = scraper.get(final_url, headers=headers)
    json_data = json.loads(response.text)
    def wrapper(json_data):
        for elem in json_data:
            if type(elem) == dict and 'childs' not in elem.keys():
                categories_list.append((elem['id'], elem['url']))
            elif type(elem) == dict and 'childs' in elem.keys():
                categories_list.append((elem['id'], elem['url']))
                wrapper(elem['childs'])
        scraper.close()
        new_categories_list = []
        WBCategory.objects.all().delete()
        for elem in categories_list:
            new_categories_list.append(WBCategory(wb_id=elem[0], url=elem[1]))
        WBCategory.objects.bulk_create(new_categories_list)
    return wrapper(json_data)



def update_menu_cats():
    '''Обновление базы категорий меню от самого wb в самой БД'''
    categories_list = get_menu_cats()
    WBMenuCategory.objects.all().delete()
    new_categories_list = []
    for elem in categories_list:
        new_categories_list.append(WBMenuCategory(wb_id=elem[0], main_url=elem[1], shard_key=elem[2], name=elem[3], query=elem[4], parent=elem[5]))
    # new_categories_list.append(WBMenuCategory(wb_id=131450, main_url="/catalog/sdelano-v-rossii", shard_key="blackhole", name="Сделано в России", query='', parent=None)) #костыль, но по вине WB (нет query в единственном при наличии sharda)
    WBMenuCategory.objects.bulk_create(new_categories_list, ignore_conflicts=True)


def get_menu_cats():
    '''Получение свежей базы категорий меню от самого wb'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    final_url = f'https://static-basket-01.wbbasket.ru/vol0/data/main-menu-ru-ru-v3.json'
    response = scraper.get(final_url, headers=headers)
    json_data = json.loads(response.text)
    scraper.close()
    categories_list = []
    def wrapper(json_data):
        for elem in json_data:
            if type(elem) == dict and 'childs' not in elem.keys():
                shard = elem.get('shard', None)
                id = elem.get('id', None)
                url = elem.get('url', None)
                name = elem.get('name', None)
                query = elem.get('query', None)
                parent = elem.get('parent', None)
                categories_list.append((id, url, shard, name, query, parent))
            elif type(elem) == dict and 'childs' in elem.keys():
                shard = elem.get('shard', None)
                id = elem.get('id', None)
                url = elem.get('url', None)
                name = elem.get('name', None)
                query = elem.get('query', None)
                parent = elem.get('parent', None)
                categories_list.append((id, url, shard, name, query, parent))
                wrapper(elem['childs'])
        return categories_list
    return wrapper(json_data)