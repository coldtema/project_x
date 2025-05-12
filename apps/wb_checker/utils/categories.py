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
    '''Обновление базы категорий меню от самого wb в самой БД (лучше переписать в виде класса)'''
    categories_list = get_menu_cats()
    new_categories_list = []
    for elem in categories_list:
        new_categories_list.append(WBMenuCategory(wb_id=elem[0], main_url=elem[1], shard_key=elem[2], name=elem[3], query=elem[4], parent=elem[5]))
    for elem in new_categories_list:
        list_path = elem.main_url.split('/')
        if len(list_path) == 3 and list_path[1] == 'catalog' and  elem.shard_key == 'blackhole':
            continue
        elif len(list_path) >= 3 and list_path[1] == 'catalog':
            list_ru_path_part = []
            for path_part in list_path[2:-1]:
                ru_path_part = get_ru_path(path_part, new_categories_list)
                list_ru_path_part.append(ru_path_part)
            list_ru_path_part.append(elem.name)
            elem.ru_path=' / '.join(list_ru_path_part)
    WBMenuCategory.objects.bulk_create(new_categories_list, ignore_conflicts=True)


def get_ru_path(path_part, prods):
    path_dict = {'podarki-zhenshchinam': 'Подарки женщинам',
                 'dom':'Дом',
                 'vidy-sporta': 'Виды спорта',
                 'dlya-remonta': 'Для ремонта',
                 'sad-i-dacha': 'Сад и дача',
                 'podarki': 'Подарки',
                 'podarki-': 'Подарки',
                 'bokaly-i-kruzhki': 'Бокалы и кружки',
                 'hozyaystvennye-tovary': 'Хозяйственные товары',
                 'noutbuki-pereferiya': 'Ноутбуки и периферия',
                 'foto-i-video-tehnika': 'Фото и Видео техника',
                 'produkty': 'Продукты',
                 'asksseuary':'Аксессуары',
                 'turizm-kemping': 'Туризм и кемпинг',
                 'tantsy': 'Танцы',
                 'nehudozhestvennaya-literatura': 'Нехудожественная литература',
                 'podguzniki': 'Подгузники',
                 'podarki-muzhchinam': 'Подарки мужчинам',
                 'gorshki-opory-i-vse-dlya-rassady': 'Горшки, опоры, и все для рассады',
                 'sportivniy-inventar': 'Спортивный инвентарь',
                 'stirka': 'Стирка',
                 'makiyazh-brovey': 'Макияж бровей',
                 'professionalnaya-kosmetika': 'Профессиональная косметика',
                 'udalenie-volos': 'Удаление волос',
                 'hozyaystvennye-sumki': 'Хозяйственные сумки',
                 'igry-i-razvlecheniya': 'Игры и развлечения',
                 'igrovye-konsoli-i-igry': 'Игровые консоли и игры',
                 'noutbuki-i-kompyutery': 'Ноутбуки и компьютеры',
                 'periferiynye-ustroystva': 'Периферийные устройства',
                 'telefony-i-gadzhety': 'Телефоны и гаджеты',
                 'zootovary': 'Зоотовары',
                 'fitnes-i-trenazhery': 'Фитнес и тренажеры',
                 'instrumenty-i-osnastka': 'Инструменты и оснастка',
                 'knigi-i-diski': 'Книги и диски',
                 'tovary-dlya-bani-i-sauny': 'Товары для бани и сауны',
                 'stroitelstvo-i-remont': 'Строительство и ремонт',
                 'tovary-dlya-remonta': 'Товары для ремонта',
                 'yuvelirnye-izdeliya': 'Ювелирные изделия',
                 'avtokosmetika-i-avtohimiya': 'Автокосметика и автохимия',
                 'straykbol-i-peyntbol': 'Страйкбол и пейнтбол',
                 'skalolazanie': 'Скалолазание',
                 'lyzhnyy-sport': 'Лыжный спорт',
                 'sportivniy-inventar-i-aksessuary': 'Спортивный инвентарь и аксессуары',
                 'pohody': 'Походы',
                 'turizm': 'Туризм',
                 'spalnye-meshki-matrasy': 'Спальный мешки и матрасы',
                 'professionalnaya-parikmaherskaya-tehnika': 'Профессиональная парикмахерская техника',
                 'knigi-dlya-detey': 'Книги для детей',
                 'raskraski-i-risovanie': 'Раскраски и рисование',
                 'detskiy-dosug': 'Детский досуг',
                 'detskaya-literatura': 'Детская литература',
                 'kraski-i-gruntovki': 'Краски и грунтовки',
                 'bilyard': 'Бильярд',
                 'snoubord': 'Сноуборд',
                 'plavanie-i-snorkeling': 'Плавание и сноркелинг',
                 'roliki-samokaty-skeytbordy': 'Ролики, самокаты, скейтборды',
                 'sportivniy-tovar': 'Спортивные товары',
                 'ohota-i-rybalka': 'Охота и рыбалка',
                 'tovary-dlya-sobak': 'Товары для собак',
                 'produkty-pitaniya': 'Продукты питания',
                 'dlya-prazdnika': 'Для праздника',
                 'kontratseptivy': 'Контрацептивы',
                 }
    result = path_dict.get(path_part, None)
    if not result:
        for elem in prods:
            list_path = elem.main_url.split('/')
            if list_path[1] == 'catalog' and list_path[-1] == path_part:
                return elem.name
        print(path_part) #если вдруг какая то категория не нашлась
    else:
        return result

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