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
    categories_list = get_menu_cats()
    new_categories_list = []
    for elem in categories_list:
        new_categories_list.append(WBMenuCategory(wb_id=elem[0], main_url=elem[1], shard_key=elem[2], name=elem[3], query=elem[4]))
    WBMenuCategory.objects.bulk_create(new_categories_list, ignore_conflicts=True)


def get_menu_cats():
    '''Обновление базы категорий меню от самого wb'''
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
                try:
                    shard = elem['shard']
                    if not shard: continue
                    categories_list.append((elem['id'], elem['url'], shard, elem['name'], elem['query']))
                except:
                    continue
            elif type(elem) == dict and 'childs' in elem.keys():
                try:
                    shard = elem['shard']
                    if not shard: continue
                    categories_list.append((elem['id'], elem['url'], shard, elem['name'], elem['query']))
                except:
                    wrapper(elem['childs'])
                    continue
                wrapper(elem['childs'])
        return categories_list
    return wrapper(json_data)