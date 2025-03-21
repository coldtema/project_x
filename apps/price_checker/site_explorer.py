import time
from requests import request
from bs4 import BeautifulSoup
import re
import json
import httpx
import cloudscraper


def get_shop_of_product(product_url):
    '''Функция, определяющая, какому магазину принадлежит ссылка'''
    regex = r'://(www\.)?(ru\.)?(mytishchi\.)?(moscow\.)?(msk\.)?(moskva\.)?(outlet\.)?(shop\.)?([\w-]+)\.(\w+)/'
    print(re.search(pattern=regex, string=product_url).group(9).strip())
    return shop_to_func.get(re.search(pattern=regex, string=product_url).group(9).strip())(product_url)

    

def get_product_brandshop(product_url):
    '''Функция для парсинга товара из brandshop'a'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    try:
        price_element = soup_engine.find("div", class_="product-order__price_new").text.strip()
    except:
        price_element = soup_engine.find("div", class_="product-order__price-wrapper").text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element.split())))) #добавление только цифр в поле price
    brand = soup_engine.find("div", class_="product-page__header font font_title-l").text.strip()
    category, model = map(lambda x: x.text.strip(), soup_engine.find_all("div", class_="product-page__subheader font font_m font_grey")) #модель не добавляю
    return {'price_element': price_element, 'name': brand + ' ' + category, 'shop': 'brandshop', 'category': shop_to_category['brandshop']}



def get_product_superstep(product_url):
    '''Функция для парсинга товара из superstep'a'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    try:
        price_element = soup_engine.find("div", class_="product-detail__sale-price--black").text.strip()
    except:
        price_element = soup_engine.find("div", class_="price").text.strip()
        price_element = price_element.split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element.split()))))
    name = soup_engine.find("div", class_="detail__info-wrapper")
    name = ' '.join(list(name.stripped_strings)) #переделанный в строку генератор отредактированных строк
    name = re.search(pattern=r'(.+?) Цвет', string=name).group(1)
    return {'price_element': price_element, 'name': name, 'shop': 'superstep', 'category': shop_to_category['superstep']}



def get_product_rendez_vous(product_url):
    '''Функция для парсинга товара из rendez-vous'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("span", class_="item-price-value").text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element.split()))))
    category_plus_brand = soup_engine.find("span", class_="item-name-title").text.strip()
    brand = ''
    category = ''
    for elem in category_plus_brand.split():
        if elem.upper() == elem:
            brand += f' {elem}'
        else:
            category += f' {elem}'
    brand = brand.strip()
    category = category.strip()
    return {'price_element': price_element, 'name': brand + ' ' + category, 'shop': 'rendez-vous', 'category': shop_to_category['rendez-vous']}



def get_product_tsum_outlet(product_url):
    '''Функция для парсинга товара из tsum_outlet'a'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("div", class_=re.compile(r'Price__wrapper___\w+')).text.strip()
    price_element = price_element.split('₽')
    if price_element[1]:
        price_element = price_element[1]
    else:
        price_element = price_element[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element.split()))))
    name = soup_engine.find("title").text.strip()
    name = re.search(pattern=r'(.+?)( купить)', string=name).group(1)
    return {'price_element': int(str(price_element)), 'name': name, 'shop': 'tsum-outlet', 'category': shop_to_category['tsum-outlet']}




def get_product_tsum(product_url):
    '''Функция для парсинга товара из tsum'a'''
    if 'outlet' in product_url:
        return get_product_tsum_outlet(product_url)
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("p", class_=re.compile(r'Price__price___\w+')).text.strip()
    price_element = price_element.split('₽')
    if price_element[1]:
        price_element = price_element[1]
    else:
        price_element = price_element[0]
    brand = soup_engine.find("div", class_=re.compile(r'ColumnView__infoBlocksRow___\w+')).text.strip()
    brand = re.search(pattern=r'Бренд: (.+?)С', string=brand).group(1)
    category = soup_engine.find("h1", class_=re.compile(r'description__productName___\w+')).text.strip()
    category = re.search(pattern=r'[А-Я].+', string=category).group(0)
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element.split()))))
    return {'price_element': int(str(price_element)), 'name': brand + ' ' + category, 'shop': 'tsum', 'category': shop_to_category['tsum']}



def get_product_street_beat(product_url):
    '''Функция для парсинга товара из street beat'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    digital_data_dict = re.search(r'window\.digitalData\s*=\s*(\{.*?\});', response.text)
    json_data = json.loads(digital_data_dict.group(1))
    name = json_data['product']['name']
    price_element = json_data['product']['unitPrice']
    return {'price_element': price_element, 'name': name, 'shop': 'street-beat', 'category': shop_to_category['street-beat']}


def get_product_lacoste(product_url):
    '''Функция для парсинга товара из lacoste'a'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("div", class_="nl-product-price nl-product-configuration__price").text.strip().split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element.split()))))
    name = soup_engine.find("h4", class_="nl-product-configuration__title").text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'lacoste', 'category': shop_to_category['lacoste']}



def get_product_sv77(product_url):
    '''Функция для парсинга товара из sv77'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("button", class_="button button-bordered items-center button-rect w-100 db fade button-hover-black").text.strip().split('руб.')
    if price_element[1] != '':
        price_element = price_element[1]
    else:
        price_element = price_element[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element.split()))))
    name = soup_engine.find("h1", class_="product-view-title uppercase").text.strip()
    name = ' '.join(name.split('\n'))
    return {'price_element': price_element, 'name': name, 'shop': 'sv77', 'category': shop_to_category['sv77']}



def get_product_elyts(product_url):
    '''Функция для парсинга товара из elyts'a'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("div", class_="final-price-block").text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element.split()))))
    name = soup_engine.find("h1").text
    return {'price_element': price_element, 'name': name, 'shop': 'elyts', 'category': shop_to_category['elyts']}



def get_product_vipavenue(product_url):
    '''Функция для парсинга товара из vipavenue'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("div", class_="product__card--price-actual").text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element.split()))))
    name = soup_engine.find("div", class_="product__card--title").text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'vipavenue', 'category': shop_to_category['vipavenue']}



def get_product_aimclo(product_url):
    '''Функция для парсинга товара из aimclo'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    try:
        price_element = soup_engine.find("div", class_="product-information__price js-element-price").text.strip()
    except:
        price_element = soup_engine.find("div", class_="product-information__price product-information__sale js-element-price").text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("h1", class_="product-information__title").text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'aimclo', 'category': shop_to_category['aimclo']}



def get_product_befree(product_url):
    '''Функция для парсинга товара из befree'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("div", class_=re.compile(r'.+(digi-product-price)')).text.strip()
    price_element = price_element.split('₽')[0]
    name = soup_engine.find("span", class_=re.compile(r'.+( title)')).text.strip()
    return {'price_element': int(price_element), 'name': name, 'shop': 'befree', 'category': shop_to_category['befree']}


def get_product_loverepublic(product_url):
    '''Функция для парсинга товара из love republic'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("div", class_='item-prices').text.strip()
    price_element = price_element.split('₽')
    if price_element[1]:
        price_element = price_element[1].split('%')[1]
    else:
        price_element = price_element[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("h1", class_='catalog-element__title').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'love republic', 'category': shop_to_category['loverepublic']}



def get_product_youstore(product_url):
    '''Функция для парсинга товара из youstore'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("div", class_='product-view-price').text.strip()
    price_element = price_element.split('₽')[0].strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("h1").text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'youstore', 'category': shop_to_category['youstore']}



def get_product_gate31(product_url): #вообще не увидел раздел скидок
    '''Функция для парсинга товара из gate31'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("div", class_='product-price__default').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("div", class_='ProductPage__title').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'gate31', 'category': shop_to_category['gate31']}



def get_product_incanto(product_url):
    '''Функция для парсинга товара из incanto'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    full = soup_engine.find("title").text.strip()
    price_element = re.search(pattern=r'(цене )(.+?)( ₽)', string=full).group(2)
    name = re.search(pattern=r'(.+)( Incanto)', string=full).group(1)
    return {'price_element': int(float(price_element)), 'name': name, 'shop': 'incanto', 'category': shop_to_category['incanto']}



def get_product_sportcourt(product_url):
    '''Функция для парсинга товара из sportcourt'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    response.encoding = response.apparent_encoding #свойство, которое угадывает кодировку на основе содержимого
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("div", class_='p_price').text.strip()
    if price_element.split('₽')[1]:
        price_element = price_element.split('₽')[1]
    else:
        price_element = price_element.split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("div", class_='model_name').text.strip()
    return {'price_element': int(float(price_element)), 'name': name, 'shop': 'sportcourt', 'category': shop_to_category['sportcourt']}




def get_product_1811stores(product_url):
    '''Функция для парсинга товара из 1811stores'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    full = soup_engine.find("title").text.strip()
    price_element = re.search(pattern=r'(за )(.+?)( руб.)', string=full).group(2)
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = re.search(pattern=r'(.+?)( купить)', string=full).group(1)
    return {'price_element': int(float(price_element)), 'name': name, 'shop': '1811stores', 'category': shop_to_category['1811stores']}



def get_product_bask(product_url):
    '''Функция для парсинга товара из bask'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("span", class_='avail-b').text.strip()
    price_element = re.search(pattern=r'(.+?)(Доступно)', string=price_element).group(1)
    if price_element.split('₽')[1]:
        price_element = price_element.split('₽')[1]
    else:
        price_element = price_element.split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("title").text.strip()
    name = re.search(pattern=r'(.+?)( - )', string=name).group(1)
    return {'price_element': int(float(price_element)), 'name': name, 'shop': 'bask', 'category': shop_to_category['bask']}



def get_product_noone(product_url):
    '''Функция для парсинга товара из noone'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("div", class_='item-price').text.strip()
    price_element = price_element.split('RUB')[0].strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("title").text.strip()
    name = re.search(pattern=r'(.+?)( купить)', string=name).group(1)
    return {'price_element': price_element, 'name': name, 'shop': 'noone', 'category': shop_to_category['noone']}


def get_product_elis(product_url):
    '''Функция для парсинга товара из elis'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = httpx.get(url=product_url, headers=headers, verify=False) #пока выключил проверку SSL-сертификатов - что-то с ними случилось
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("span", class_='price').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("h1", class_='item-detail__title').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'elis', 'category': shop_to_category['elis']}



def get_product_afinabags(product_url):
    '''Функция для парсинга товара из afinabags'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("div", class_='item-card__price').text.strip()
    price_element = price_element.split('₽')
    if price_element[1]:
        price_element = price_element[1]
    else:
        price_element = price_element[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("title").text.strip()
    try:
        name = re.search(pattern=r'(.+?)( по \d)', string=name).group(1)
    except:
        name = re.search(pattern=r'(.+?)( купить)', string=name).group(1)
    return {'price_element': price_element, 'name': name, 'shop': 'afinabags', 'category': shop_to_category['afinabags']}



def get_product_crockid(product_url):
    '''Функция для парсинга товара из crockid'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("div", class_=re.compile(r'(cost)(.+)?')).text.strip()
    price_element = price_element.split('р.')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("h1", class_='name').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'crockid', 'category': shop_to_category['crockid']}



def get_product_bungly(product_url):
    '''Функция для парсинга товара из bungly'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("div", class_='price-first-load').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("div", class_='product-title').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'bungly', 'category': shop_to_category['bungly']}



def get_product_aupontrouge(product_url):
    '''Функция для парсинга товара из aupontrouge'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("div", class_='product-price').text.strip()
    price_element = price_element.split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("title").text.strip()
    name = re.search(pattern=r'(.+?)( купить)', string=name).group(1)
    return {'price_element': price_element, 'name': name, 'shop': 'aupontrouge', 'category': shop_to_category['aupontrouge']}



def get_product_sohoshop(product_url):
    '''Функция для парсинга товара из sohoshop'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("div", class_='prices_block').text.strip()
    price_element = price_element.split('руб')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("div", class_='topic__inner').text.strip()
    name = name.split('\n')[-1]
    return {'price_element': price_element, 'name': name, 'shop': 'sohoshop', 'category': shop_to_category['sohoshop']}



def get_product_lichi(product_url):
    '''Функция для парсинга товара из lichi'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("div", class_=re.compile(r'(product-content_price_box__).+')).text.strip()
    price_element = price_element.split('₽')
    if price_element[2]:
        price_element = price_element[1]
    else:
        price_element=price_element[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("h1").text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'lichi', 'category': shop_to_category['lichi']}



def get_product_askent(product_url):
    '''Функция для парсинга товара из askent'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("div", class_='product__currentPrice').text.strip()
    price_element = price_element.split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("div", class_='productName').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'askent', 'category': shop_to_category['askent']}



def get_product_darsi(product_url):
    '''Функция для парсинга товара из darsi'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    full = soup_engine.find("title").text.strip()
    price_element = re.search(pattern=r'(цене )(.+?)( руб)', string=full).group(2)
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = re.search(pattern=r'(.+?)( купить)', string=full).group(1)
    return {'price_element': price_element, 'name': name, 'shop': 'darsi', 'category': shop_to_category['darsi']}



def get_product_cocos_moscow(product_url):
    '''Функция для парсинга товара из cocos-moscow'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("div", class_='product-item-detail-price').text.strip()
    price_element = price_element.split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("div", class_='product_card__title').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'cocos-moscow', 'category': shop_to_category['cocos-moscow']}



def get_product_inspireshop(product_url):
    '''Функция для парсинга товара из inspireshop'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("div", class_='product-page__item-price-container').text.strip()
    price_element = price_element.split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("h1", class_='product-page__item-name').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'inspireshop', 'category': shop_to_category['inspireshop']}



def get_product_respect_shoes(product_url):
    '''Функция для парсинга товара из respect-shoes'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("div", class_='price-div-flex').text.strip()
    price_element = price_element.split('р.')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("h1", class_='h1-cart').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'respect-shoes', 'category': shop_to_category['respect-shoes']}



def get_product_pompa(product_url):
    '''Функция для парсинга товара из pompa'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("span", class_='current_price').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("h1", class_='detail-item-title d-sm-block d-none').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'pompa', 'category': shop_to_category['pompa']}



def get_product_bunnyhill(product_url):
    '''Функция для парсинга товара из bunnyhill'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("span", class_='price price_to_change').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("h1", class_='name js-ga-name').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'bunnyhill', 'category': shop_to_category['bunnyhill']}



def get_product_annapekun(product_url):
    '''Функция для парсинга товара из annapekun'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("div", class_='catalog-item__price').text.strip()
    price_element = price_element.split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('title').text.strip()
    name = re.search(pattern=r'(.+?)( - купить)', string=name).group(1)
    return {'price_element': price_element, 'name': name, 'shop': 'annapekun', 'category': shop_to_category['annapekun']}



def get_product_amazingred(product_url):
    '''Функция для парсинга товара из amazingred'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = httpx.get(product_url, headers=headers)
    digital_data_dict = re.search(r'window\.digitalData\s*=\s*(\{.*?\});', response.text)
    json_data = json.loads(digital_data_dict.group(1))
    price_element = json_data['product']['unitSalePrice']
    name = json_data['product']['name']
    return {'price_element': price_element, 'name': name, 'shop': 'amazingred', 'category': shop_to_category['amazingred']}



def get_product_m_reason(product_url):
    '''Функция для парсинга товара из m-reason'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("div", class_='price-card__price').text.strip()
    price_element = price_element.split('i')
    if price_element[1]:
        price_element = price_element[1]
    else:
        price_element = price_element[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('div', class_='product-detail__title').text.strip()
    name = ' '.join(name.split())
    return {'price_element': price_element, 'name': name, 'shop': 'm-reason', 'category': shop_to_category['m-reason']}



def get_product_voishe(product_url):
    '''Функция для парсинга товара из voishe'''
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://www.voishe.ru/",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}
    response = httpx.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("div", class_='js-product-price js-store-prod-price-val t-store__prod-popup__price-value').text.strip()
    price_element = price_element.split(',')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('title').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'voishe', 'category': shop_to_category['voishe']}



def get_product_choux(product_url):
    '''Функция для парсинга товара из choux'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    full = soup_engine.find('title').text.strip()
    price_element = re.search(pattern=r'(цене )(.+?)( ₽)', string=full).group(2)
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = re.search(pattern=r'(.+?)( купить)', string=full).group(1)
    return {'price_element': price_element, 'name': name, 'shop': 'choux', 'category': shop_to_category['choux']}



def get_product_fablestore(product_url):
    '''Функция для парсинга товара из fablestore'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='product-result__price body-text').text.strip()
    price_element = price_element.split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1', class_='product-info__title').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'fablestore', 'category': shop_to_category['fablestore']}



def get_product_selfmade(product_url):
    '''Функция для парсинга товара из selfmade'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='product-price').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1', class_='product-name').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'selfmade', 'category': shop_to_category['selfmade']}



def get_product_kanzler_style(product_url):
    '''Функция для парсинга товара из kanzler-style'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='product__price-wrapper').text.strip()
    price_element = price_element.split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1', class_='product__title').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'kanzler-style', 'category': shop_to_category['kanzler-style']}



def get_product_belleyou(product_url):
    '''Функция для парсинга товара из belleyou'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('span', class_='current-price').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1', class_='product-desc-title').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'belleyou', 'category': shop_to_category['belleyou']}



def get_product_zolla(product_url):
    '''Функция для парсинга товара из zolla'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='catalog-detail--redesign__aside-price-current').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1', class_='catalog-detail--redesign__aside-title').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'zolla', 'category': shop_to_category['zolla']}



def get_product_danielonline(product_url):
    '''Функция для парсинга товара из danielonline'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='item-price__value').text.strip()
    price_element = price_element.split('руб.')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'danielonline', 'category': shop_to_category['danielonline']}



def get_product_zarina(product_url):
    '''Функция для парсинга товара из zarina'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='product__price-current').text.strip()
    price_element = price_element.split('руб.')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'zarina', 'category': shop_to_category['zarina']}



def get_product_alexanderbogdanov(product_url):
    '''Функция для парсинга товара из alexanderbogdanov'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='product-card-info__prices').text.strip()
    price_element = price_element.split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('p', class_='product-card-info__title').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'alexanderbogdanov', 'category': shop_to_category['alexanderbogdanov']}



def get_product_werfstore(product_url): #не нашел скидок
    '''Функция для парсинга товара из werfstore'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('p', class_='price').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1', class_='product_title entry-title').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'werfstore', 'category': shop_to_category['werfstore']}



def get_product_koffer(product_url):
    '''Функция для парсинга товара из koffer'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='product-info__buy-block').text.strip()
    price_element = price_element.split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'koffer', 'category': shop_to_category['koffer']}



def get_product_age_of_innocence(product_url):
    '''Функция для парсинга товара из age-of-innocence'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find_all('div', class_='v-stack')
    price_element = ''.join(list(map(lambda x: x.text.strip(), price_element)))
    price_element = re.search(pattern=r'(₽)(.+?)\,', string=price_element).group(2)
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('title').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'age-of-innocence', 'category': shop_to_category['age-of-innocence']}



def get_product_nice_one(product_url):
    '''Функция для парсинга товара из nice-one'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='price').text.strip()
    price_element = price_element.split('руб.')
    if price_element[1]:
        price_element = price_element[1]
    else:
        price_element = price_element[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'nice-one', 'category': shop_to_category['nice-one']}



def get_product_alpindustria(product_url):
    '''Функция для парсинга товара из alpindustria'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='product__price-wrap').text.strip()
    price_element = price_element.split('руб.')
    if price_element[1]:
        price_element = price_element[1]
    else:
        price_element = price_element[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'alpindustria', 'category': shop_to_category['alpindustria']}



def get_product_indiwd(product_url):
    '''Функция для парсинга товара из indiwd'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='h3 product__page-price').text.strip()
    price_element = price_element.split('₽')
    price_element = price_element[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'indiwd', 'category': shop_to_category['indiwd']}



def get_product_biggeek(product_url):
    '''Функция для парсинга товара из biggeek'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('span', class_='total-prod-price').text.strip()
    price_element = price_element.split('₽')
    price_element = price_element[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'biggeek', 'category': shop_to_category['biggeek']}



def get_product_tefal(product_url):
    '''Функция для парсинга товара из tefal'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    full = soup_engine.find('title').text.strip()
    price_element = int(float(re.search(pattern=r'(цена )(.+)( руб)', string=full).group(2)))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'tefal', 'category': shop_to_category['tefal']}



def get_product_yves_rocher(product_url):
    '''Функция для парсинга товара из yves-rocher'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('span', class_='bold text_size_20 tab_text_size_24').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'yves-rocher', 'category': shop_to_category['yves-rocher']}



def get_product_galaxystore(product_url):
    '''Функция для парсинга товара из galaxystore'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    digital_data_dict = re.search(r'window\.digitalData\s*=\s*(\{.*?\});', response.text)
    json_data = json.loads(digital_data_dict.group(1))
    price_element = int(json_data['product']['unitSalePrice'])
    name = json_data['product']['name']
    return {'price_element': price_element, 'name': name, 'shop': 'galaxystore', 'category': shop_to_category['galaxystore']}



def get_product_megafon(product_url):
    '''Функция для парсинга товара из megafon'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_=re.compile(r'(Price_text__).+')).text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'megafon', 'category': shop_to_category['megafon']}



def get_product_ecco(product_url):
    '''Функция для парсинга товара из ecco'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('span', class_='price').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'ecco', 'category': shop_to_category['ecco']}



def get_product_xcom_shop(product_url):
    '''Функция для парсинга товара из xcom-shop'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='card-content-total-price__current').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'xcom-shop', 'category': shop_to_category['xcom-shop']}



def get_product_epldiamond(product_url):
    '''Функция для парсинга товара из epldiamond'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('title').text.strip()
    price_element = re.search(pattern=r'(цене )(.+)( руб)', string=price_element).group(2)
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'epldiamond', 'category': shop_to_category['epldiamond']}



def get_product_doctorslon(product_url):
    '''Функция для парсинга товара из doctorslon'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='product-price').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'doctorslon', 'category': shop_to_category['doctorslon']}



def get_product_randewoo(product_url): #пока добавляется последний элемент, если там список ароматов, подумать, как предложить выбор
    '''Функция для парсинга товара из randewoo'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    try:
        price_element = soup_engine.find_all('span', class_='s-productType__priceNewValue')
        price_element = tuple(map(lambda x: x.text, price_element))
        first_name = soup_engine.find('title').text.strip()
        first_name = re.search(pattern=r'(.+?)( купить)', string=first_name).group(1).strip(' -')
        last_name = soup_engine.find_all('div', class_='s-productType__title')
        name = tuple(map(lambda x: first_name + ' ' + x.text.strip('? \r\n'), last_name))
        if not name: raise Exception
        dict_prices = dict(zip(name, price_element))
        name = tuple(dict_prices.keys())[-1]
        price_element = tuple(dict_prices.values())[-1]
    except:
        price_element = soup_engine.find('strong', class_='b-productSummary__priceNew').text.strip()
        name = soup_engine.find('title').text.strip()
        name = re.search(pattern=r'(.+?)( купить)', string=name).group(1).strip(' -')
    return {'price_element': int(price_element), 'name': name, 'shop': 'randewoo', 'category': shop_to_category['randewoo']}



def get_product_babor(product_url):
    '''Функция для парсинга товара из babor'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='productCard-price').text.strip()
    price_element = price_element.split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'babor', 'category': shop_to_category['babor']}



def get_product_mir_kubikov(product_url):
    '''Функция для парсинга товара из mir-kubikov'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    try:
        price_element = soup_engine.find('p', class_='product__info__price g-h2 m-old').text.strip()
        price_element = price_element.split('\n')[0]
    except:
        price_element = soup_engine.find('p', class_='product__info__price g-h2').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('title').text.strip()
    name = re.search(pattern=r'(.+)( \- купить)', string=name).group(1)
    return {'price_element': price_element, 'name': name, 'shop': 'mir-kubikov', 'category': shop_to_category['mir-kubikov']}



def get_product_bombbar(product_url): #может отлетать - надо давать таймаут
    '''Функция для парсинга товара из bombbar'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='price').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'bombbar', 'category': shop_to_category['bombbar']}



def get_product_iledebeaute(product_url): 
    '''Функция для парсинга товара из iledebeaute'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', itemprop='price').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'iledebeaute', 'category': shop_to_category['iledebeaute']}



def get_product_shop_polaris(product_url): 
    '''Функция для парсинга товара из shop-polaris'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='price d-flex').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'shop-polaris', 'category': shop_to_category['shop-polaris']}



def get_product_patchandgo(product_url):
    '''Функция для парсинга товара из patchandgo'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='product-page__controls__price').text.strip()
    price_element = price_element.split('р.')
    if price_element[1]:
        price_element = price_element[1].strip()
    else:
        price_element = price_element[0].strip()
    price_element = int(float(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element)))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'patchandgo', 'category': shop_to_category['patchandgo']}



def get_product_madwave(product_url):
    '''Функция для парсинга товара из madwave'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find_all('span', class_='target-price')
    price_element = list(map(lambda x: x.text, price_element))[-1].strip(' .')
    price_element = int(float(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element)))))
    name = soup_engine.find('title').text.strip()
    name = re.search(pattern=r'((.+)\s\|\s(.+))\|', string=name).group(1)
    return {'price_element': price_element, 'name': name, 'shop': 'madwave', 'category': shop_to_category['madwave']}



def get_product_apple_avenue(product_url):
    '''Функция для парсинга товара из apple-avenue'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='price font-price-large bold').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'apple-avenue', 'category': shop_to_category['apple-avenue']}



def get_product_re_store(product_url):
    '''Функция для парсинга товара из re-store'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    full = str(soup_engine.find('meta', attrs={'name':'description'}))
    full = re.search(pattern=r'(\<meta content\=\")(.+)(от официального магазина)', string=full).group(2)
    price_element = re.search(pattern=r'(по цене )(.+)( рублей)', string=full).group(2)
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = re.search(pattern=r'(Купить )(.+)( по цене)', string=full).group(2)
    return {'price_element': price_element, 'name': name, 'shop': 're-store', 'category': shop_to_category['re-store']}



def get_product_bestmebelshop(product_url):
    '''Функция для парсинга товара из bestmebelshop'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    full = soup_engine.find('title').text.strip()
    price_element = int(re.search(pattern=r'\- (\d+) р', string=full).group(1))
    name = re.search(pattern=r'(.+) \- \d', string=full).group(1)
    return {'price_element': price_element, 'name': name, 'shop': 'bestmebelshop', 'category': shop_to_category['bestmebelshop']}



def get_product_garlyn(product_url):
    '''Функция для парсинга товара из garlyn'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', 'price current-price').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    try:
        price_element_marketplace = soup_engine.find('span', 'price-marketplace').text.strip()
        price_element_marketplace = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element_marketplace))))
        if price_element_marketplace < price_element:
            price_element = price_element_marketplace
    except: pass
    finally:
        name = soup_engine.find('h1', class_ = 'title').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'garlyn', 'category': shop_to_category['garlyn']}



def get_product_kuppersberg(product_url):
    '''Функция для парсинга товара из kuppersberg'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='prodMain__price--new').text.strip()
    name = soup_engine.find('h1').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    return {'price_element': price_element, 'name': name, 'shop': 'kuppersberg', 'category': shop_to_category['kuppersberg']}



def get_product_bosssleep(product_url):
    '''Функция для парсинга товара из bosssleep'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find_all('p', class_='item-header__price')
    price_element = list(map(lambda x: x.text, price_element))
    if '%' in price_element[1]:
        price_element = price_element[2]
    else:
        price_element = price_element[0]
    name = soup_engine.find('h1').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    return {'price_element': price_element, 'name': name, 'shop': 'bosssleep', 'category': shop_to_category['bosssleep']}



def get_product_muztorg(product_url):
    '''Функция для парсинга товара из muztorg'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    try:
        price_element = soup_engine.find('div', class_='mt-product-price__default-value').text.strip()
    except:
        price_element = soup_engine.find('div', class_='mt-product-price__discounted-value').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'muztorg', 'category': shop_to_category['muztorg']}



def get_product_finn_flare(product_url):
    '''Функция для парсинга товара из finn-flare'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    full = soup_engine.find('title').text.strip()
    price_element = re.search(pattern=r'(цене от )(.+)( в)', string=full).group(2)
    name = re.search(pattern=r'(.+) \(', string=full).group(1)
    price_element = int(int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element)))) * 0.95) #пока у них стоит скидка при оплате онлайн
    return {'price_element': price_element, 'name': name, 'shop': 'finn-flare', 'category': shop_to_category['finn-flare']}



def get_product_litres(product_url):
    '''Функция для парсинга товара из litres'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = str(soup_engine.find('meta', itemprop="price"))
    price_element = int(float(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element)))))
    name = soup_engine.find('title').text.strip()
    name = re.search(pattern=r'(.+)( \– )', string=name).group(1)
    return {'price_element': price_element, 'name': name, 'shop': 'litres', 'category': shop_to_category['litres']}



def get_product_orteka(product_url):
    '''Функция для парсинга товара из orteka'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    full = str(soup_engine.find('meta', attrs={'name':"description"}))
    price_element = re.search(pattern=r'(по цене )(.+)( руб.)', string=full).group(2)
    name = re.search(pattern=r'(купить )(.+)( по цене)', string=full).group(2)
    price_element = int(float(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element)))))
    return {'price_element': price_element, 'name': name, 'shop': 'orteka', 'category': shop_to_category['orteka']}



def get_product_quke(product_url):
    '''Функция для парсинга товара из quke'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('span', class_='price__value').text
    price_element = int(float(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element)))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'quke', 'category': shop_to_category['quke']}



def get_product_leonardo(product_url):
    '''Функция для парсинга товара из leonardo'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    full = soup_engine.find('title').text
    price_element = re.search(pattern=r'(за )(.+)( ₽)', string=full).group(2)
    price_element = ''.join(list(filter(lambda x: True if x.isdigit() or x==',' else False, price_element)))
    price_element = int(price_element.split(',')[0])
    name = re.search(pattern=r'(.+)( купить)', string=full).group(1)
    return {'price_element': price_element, 'name': name, 'shop': 'leonardo', 'category': shop_to_category['leonardo']}



def get_product_beeline(product_url):
    '''Функция для парсинга товара из beeline'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    response.encoding = response.apparent_encoding
    soup_engine = BeautifulSoup(response.text, 'lxml')
    full = str(soup_engine.find('meta', attrs={'name':'description'}))
    price_element = re.search(pattern=r'(цена )(.+)( руб.)', string=full).group(2)
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() or x==',' else False, price_element))))
    name = re.search(pattern=r'(купить )(.+)(\: цена)', string=full).group(2)
    return {'price_element': price_element, 'name': name, 'shop': 'beeline', 'category': shop_to_category['beeline']}



def get_product_tvoydom(product_url):
    '''Функция для парсинга товара из tvoydom'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    response.encoding = response.apparent_encoding
    soup_engine = BeautifulSoup(response.text, 'lxml')
    full = soup_engine.find('title').text.strip()
    price_element = re.search(pattern=r'(цене )(.+)( руб.)', string=full).group(2)
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = re.search(pattern=r'(.+)( купить)', string=full).group(1)
    return {'price_element': price_element, 'name': name, 'shop': 'tvoydom', 'category': shop_to_category['tvoydom']}



def get_product_sela(product_url):
    '''Функция для парсинга товара из sela'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    full = str(soup_engine.find('meta', attrs={'name': 'Description'}))
    price_element = re.search(pattern=r'(цене )(.+?)( руб\.)', string=full).group(2)
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = re.search(pattern=r'\"(.+)(, артикул)', string=full).group(1)
    return {'price_element': price_element, 'name': name, 'shop': 'sela', 'category': shop_to_category['sela']}



def get_product_aquaphor(product_url):
    '''Функция для парсинга товара из aquaphor'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='price-block').text.strip()
    price_element=price_element.split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('title').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'aquaphor', 'category': shop_to_category['aquaphor']}



def get_product_mnogomebeli(product_url):
    '''Функция для парсинга товара из mnogomebeli'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    full = soup_engine.find('title').text.strip()
    price_element = re.search(pattern=r'(ли )(\- )?(.+)( руб\.)', string=full).group(3)
    price_element = int(''.join(price_element.split('.')))
    name = re.search(pattern=r'(.+?)(\: )', string=full).group(1)
    return {'price_element': price_element, 'name': name, 'shop': 'mnogomebeli', 'category': shop_to_category['mnogomebeli']}



def get_product_davines(product_url):
    '''Функция для парсинга товара из davines'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    full = str(soup_engine.find('meta', attrs={'name': 'description'}))
    price_element = re.search(pattern=r'(за\s)(.+)(\sруб)', string=full).group(2)
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = re.search(pattern=r'\"(.+)( за )', string=full).group(1)
    return {'price_element': price_element, 'name': name, 'shop': 'davines', 'category': shop_to_category['davines']}



def get_product_vsesmart(product_url):
    '''Функция для парсинга товара из vsesmart'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='detail__price-cost').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'vsesmart', 'category': shop_to_category['vsesmart']}



def get_product_boobl_goom(product_url):
    '''Функция для парсинга товара из boobl-goom'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    full = str(soup_engine.find('meta', attrs={'name': 'description'}))
    price_element = re.search(pattern=r'(Цена )(.+)( рублей)', string=full).group(2)
    price_element = int(float(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element)))))
    name = re.search(pattern=r'(Купить )(.+)( в интернет)', string=full).group(2)
    return {'price_element': price_element, 'name': name, 'shop': 'boobl-goom', 'category': shop_to_category['boobl-goom']}



def get_product_ipiter(product_url):
    '''Функция для парсинга товара из ipiter'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    full = soup_engine.find('title')
    price_element = soup_engine.find('div', class_='saleprice price').text.strip()
    price_element = price_element.split('₽')[0]
    price_element = int(float(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element)))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'ipiter', 'category': shop_to_category['ipiter']}



def get_product_mie(product_url):
    '''Функция для парсинга товара из mie'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='current-price').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'mie', 'category': shop_to_category['mie']}



def get_product_evitastore(product_url):
    '''Функция для парсинга товара из evitastore'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='cd-price').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'evitastore', 'category': shop_to_category['evitastore']}



def get_product_chitai_gorod(product_url):
    '''Функция для парсинга товара из chitai-gorod'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='product-offer-price').text.strip()
    price_element = price_element.split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    try:
        author = soup_engine.find('a', class_='product-info-authors__author').text.strip()
        name = soup_engine.find('h1').text.strip()
        name = f'{name} ({author})'
    except:
        name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'chitai-gorod', 'category': shop_to_category['chitai-gorod']}



def get_product_bestwatch(product_url):
    '''Функция для парсинга товара из bestwatch'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('span', itemprop='price').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name1 = soup_engine.find('p', class_='card-model').text.strip()
    name2 = soup_engine.find('p', class_='card-name').text.strip()
    name = name2 + ' ' + name1
    return {'price_element': price_element, 'name': name, 'shop': 'bestwatch', 'category': shop_to_category['bestwatch']}



def get_product_koleso(product_url):
    '''Функция для парсинга товара из koleso'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_=re.compile(r'(PriceBlock_Price__).+')).text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'koleso', 'category': shop_to_category['koleso']}



def get_product_mann_ivanov_ferber(product_url):
    '''Функция для парсинга товара из mann-ivanov-ferber'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', attrs={'data-start-price-animation': 'priceElement'}).text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('title').text.strip()
    name = re.search(pattern=r'(.+)( — купить)', string=name).group(1)
    return {'price_element': price_element, 'name': name, 'shop': 'mann-ivanov-ferber', 'category': shop_to_category['mann-ivanov-ferber']}



def get_product_cozyhome(product_url):
    '''Функция для парсинга товара из cozyhome'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', attrs={'data-role': 'price'}).text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'cozyhome', 'category': shop_to_category['cozyhome']}



def get_product_christinacosmetics(product_url):
    '''Функция для парсинга товара из christinacosmetics'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='price-detale').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'christinacosmetics', 'category': shop_to_category['christinacosmetics']}



def get_product_velosklad(product_url):
    '''Функция для парсинга товара из velosklad'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    name = soup_engine.find('h1').text.strip()
    price_element = str(soup_engine.find('meta', itemprop='price'))
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    return {'price_element': price_element, 'name': name, 'shop': 'velosklad', 'category': shop_to_category['velosklad']}



def get_product_multivarka(product_url):
    '''Функция для парсинга товара из multivarka'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    try:
        price_element = soup_engine.find('div', class_='product-item-price-new').text.strip()
    except:
        price_element = soup_engine.find('div', class_='product-item-price').text.strip()
    price_element = price_element.split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'multivarka', 'category': shop_to_category['multivarka']}



def get_product_iboxstore(product_url):
    '''Функция для парсинга товара из iboxstore'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='product-card__price-current').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'iboxstore', 'category': shop_to_category['iboxstore']}



def get_product_market_sveta(product_url):
    '''Функция для парсинга товара из market-sveta'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='productfull-block-price').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'market-sveta', 'category': shop_to_category['market-sveta']}



def get_product_aravia(product_url):
    '''Функция для парсинга товара из aravia'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='product-detail-price-block').text.strip()
    price_element = price_element.split('₽')
    if price_element[1]:
        price_element = price_element[1]
    else:
        price_element = price_element[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'aravia', 'category': shop_to_category['aravia']}



def get_product_krona(product_url):
    '''Функция для парсинга товара из krona'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='card__price').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'krona', 'category': shop_to_category['krona']}



def get_product_tddomovoy(product_url):
    '''Функция для парсинга товара из tddomovoy'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('span', class_='base-product-price__main').text.strip()
    price_element = int(float(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element)))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'tddomovoy', 'category': shop_to_category['tddomovoy']}



def get_product_ansaligy(product_url):
    '''Функция для парсинга товара из ansaligy'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='product__price-current').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'ansaligy', 'category': shop_to_category['ansaligy']}



def get_product_hyperauto(product_url):
    '''Функция для парсинга товара из hyperauto'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('span', itemprop='price').text.strip()
    price_element = price_element.split(',')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'hyperauto', 'category': shop_to_category['hyperauto']}



def get_product_kubaninstrument(product_url):
    '''Функция для парсинга товара из kubaninstrument'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='product-price__std').text.strip()
    price_element = price_element.split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'kubaninstrument', 'category': shop_to_category['kubaninstrument']}



def get_product_nespresso(product_url):
    '''Функция для парсинга товара из nespresso'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    try:
        price_element = soup_engine.find('div', class_='product_prices -hasComparePrice').text.strip()
    except:
        price_element = soup_engine.find('div', class_='product_prices').text.strip()
    price_element = price_element.split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'nespresso', 'category': shop_to_category['nespresso']}



def get_product_aofb(product_url):
    '''Функция для парсинга товара из aofb'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = str(soup_engine.find('meta', itemprop='price'))
    price_element = re.search(pattern=r'\"(.+)₽', string=price_element).group(1).strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'aofb', 'category': shop_to_category['aofb']}



def get_product_yamanshop(product_url):
    '''Функция для парсинга товара из yamanshop'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='price-wrapper').text.strip()
    price_element = price_element.split('₽')
    if price_element[1]:
        price_element = price_element[2]
    else:
        price_element = price_element[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'yamanshop', 'category': shop_to_category['yamanshop']}



def get_product_dvamyacha(product_url):
    '''Функция для парсинга товара из dvamyacha'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='elem-description-price').text.strip()
    price_element = price_element.split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('title').text.strip()
    name = re.search(pattern=r'(.+)\sв\sИ', string=name).group(1)
    return {'price_element': price_element, 'name': name, 'shop': 'dvamyacha', 'category': shop_to_category['dvamyacha']}



def get_product_ochkarik(product_url):
    '''Функция для парсинга товара из ochkarik'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = re.search(r'(price":")(.+?)\"', response.text).group(2)
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = ' '.join(list(map(lambda x: x.strip(), soup_engine.find('h1').text.strip().split('\n'))))
    return {'price_element': price_element, 'name': name, 'shop': 'ochkarik', 'category': shop_to_category['ochkarik']}



def get_product_hi_stores(product_url):
    '''Функция для парсинга товара из hi-stores'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='cost prices detail').text.strip()
    price_element = re.search(pattern=r'(наличными\:)(.+)\n', string=price_element).group(2)
    price_element = int(float(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element)))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'hi-stores', 'category': shop_to_category['hi-stores']}



def get_product_fkniga(product_url):
    '''Функция для парсинга товара из fkniga'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='price price--ruble price--md').text.strip()
    price_element = int(float(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element)))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'fkniga', 'category': shop_to_category['fkniga']}



def get_product_santehnika_tut(product_url):
    '''Функция для парсинга товара из santehnika-tut'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    try:
        price_element = soup_engine.find('div', class_='price clubprice').text.strip()
    except:
        price_element = soup_engine.find('div', class_='price').text.strip()
    price_element = int(float(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element)))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'santehnika-tut', 'category': shop_to_category['santehnika-tut']}



def get_product_wau(product_url):
    '''Функция для парсинга товара из wau'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find('div', class_='product__price-wrapper').text.strip()
    price_element = price_element.split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'wau', 'category': shop_to_category['wau']}



def get_product_skinjestique(product_url):
    '''Функция для парсинга товара из skinjestique'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find_all('div', class_='product-item-price price-actual')[1].text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'skinjestique', 'category': shop_to_category['skinjestique']}



def get_product_igroray(product_url):
    '''Функция для парсинга товара из igroray'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('span', class_='product-info-main__price').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element))))
    name = ' '.join(list(map(lambda x: x.strip(), soup_engine.find('h1').text.strip().split('\n'))))
    return {'price_element': price_element, 'name': name, 'shop': 'igroray', 'category': shop_to_category['igroray']}



def get_product_hansa(product_url):
    '''Функция для парсинга товара из hansa'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    full = soup_engine.find('script', attrs={'type':'application/ld+json'}).text
    price_element = re.search(pattern=r'\"price\"\: \"(.+)\.', string=full).group(1)
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'hansa', 'category': shop_to_category['hansa']}



def get_product_zvet(product_url):
    '''Функция для парсинга товара из zvet'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('span', class_='detail-price__item current').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'zvet', 'category': shop_to_category['zvet']}



def get_product_x_moda(product_url):
    '''Функция для парсинга товара из x-moda'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='product-b__price-new').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'x-moda', 'category': shop_to_category['x-moda']}



def get_product_playtoday(product_url):
    '''Функция для парсинга товара из playtoday'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('span', class_='item-price__club-value').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'playtoday', 'category': shop_to_category['playtoday']}



def get_product_santehmoll(product_url):
    '''Функция для парсинга товара из santehmoll'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='pcard-info__price').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'santehmoll', 'category': shop_to_category['santehmoll']}



def get_product_golden_line(product_url):
    '''Функция для парсинга товара из golden-line'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('span', itemprop='price').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = ' '.join(list(map(lambda x: x.strip(), soup_engine.find('h1').text.strip().split('\n'))))
    return {'price_element': price_element, 'name': name, 'shop': 'golden-line', 'category': shop_to_category['golden-line']}



def get_product_tmktools(product_url):
    '''Функция для парсинга товара из tmktools'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = re.search(pattern=r'(\<meta itemprop\=\"price\")\s(content\=\"(.+))\"\>', string=response.text).group(3)
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = ' '.join(list(map(lambda x: x.strip(), soup_engine.find('h1').text.strip().split('\n'))))
    return {'price_element': price_element, 'name': name, 'shop': 'tmktools', 'category': shop_to_category['tmktools']}



def get_product_ochkov(product_url):
    '''Функция для парсинга товара из ochkov'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='nfe_single-product__price').text.strip()
    price_element = price_element.split('руб.')
    if price_element[1]:
        price_element = price_element[1]
    else:
        price_element = price_element[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = ' '.join(list(map(lambda x: x.strip(), soup_engine.find('h1').text.strip().split('\n'))))
    return {'price_element': price_element, 'name': name, 'shop': 'ochkov', 'category': shop_to_category['ochkov']}



def get_product_svetlux(product_url):
    '''Функция для парсинга товара из svetlux'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='catalog-item-price-cur').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = ' '.join(list(map(lambda x: x.strip(), soup_engine.find('h1').text.strip().split('\n'))))
    return {'price_element': price_element, 'name': name, 'shop': 'svetlux', 'category': shop_to_category['svetlux']}



def get_product_divanboss(product_url):
    '''Функция для парсинга товара из divanboss'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find_all('p', class_='item-header__price')
    price_element = list(map(lambda x: x.text, price_element))
    if '%' in price_element[1]:
        price_element = price_element[2]
    else:
        price_element = price_element[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = ' '.join(list(map(lambda x: x.strip(), soup_engine.find('h1').text.strip().split('\n'))))
    return {'price_element': price_element, 'name': name, 'shop': 'divanboss', 'category': shop_to_category['divanboss']}



def get_product_postel_deluxe(product_url):
    '''Функция для парсинга товара из postel-deluxe'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = str(soup_engine.find('meta', itemprop='price'))
    if price_element == 'None':
        price_element = soup_engine.find('p', class_='special-price').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = ' '.join(list(map(lambda x: x.strip(), soup_engine.find('h1').text.strip().split('\n'))))
    return {'price_element': price_element, 'name': name, 'shop': 'postel-deluxe', 'category': shop_to_category['postel-deluxe']}



def get_product_dushevoi(product_url):
    '''Функция для парсинга товара из dushevoi'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = str(soup_engine.find('meta', itemprop='price'))
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = ' '.join(list(map(lambda x: x.strip(), soup_engine.find('h1').text.strip().split('\n'))))
    return {'price_element': price_element, 'name': name, 'shop': 'dushevoi', 'category': shop_to_category['dushevoi']}



def get_product_tastycoffee(product_url):
    '''Функция для парсинга товара из tastycoffee'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = str(soup_engine.find('meta', itemprop='price'))
    price_element = re.search(pattern=r'(content)(.+?)\s', string=price_element).group(2)
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = ' '.join(list(map(lambda x: x.strip(), soup_engine.find('h1').text.strip().split('\n'))))
    return {'price_element': price_element, 'name': name, 'shop': 'tastycoffee', 'category': shop_to_category['tastycoffee']}



def get_product_eurodom(product_url):
    '''Функция для парсинга товара из eurodom'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find('div', class_='product-detail__main-info-prices-actual font-weight-bold').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'eurodom', 'category': shop_to_category['eurodom']}



def get_product_happylook(product_url):
    '''Функция для парсинга товара из happylook'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    try:
        price_element = soup_engine.find('div', class_='product-detail__price js-product-detail__price').text.strip()
    except:
        price_element = soup_engine.find('div', class_='actual-price product-detail__price js-price-id').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'happylook', 'category': shop_to_category['happylook']}




def get_product_consul_coton(product_url):
    '''Функция для парсинга товара из consul-coton'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = httpx.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    try:
        price_element = soup_engine.find('div', class_='detail-price__new detail-price__new_red').text
    except:
        try:
            price_element = soup_engine.find('div', class_='detail-price__new ').text
        except:
            price_element = soup_engine.find('div', class_='detail-price detail-price_type_compact detail-price_bottom_close').text
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = ' '.join(list(map(lambda x: x.strip(), soup_engine.find('h1').text.strip().split('\n'))))
    return {'price_element': price_element, 'name': name, 'shop': 'consul-coton', 'category': shop_to_category['consul-coton']}





def get_product_audiomania(product_url):
    '''Функция для парсинга товара из audiomania'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = httpx.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    try:
        price_element = soup_engine.find('span', class_='price-v3 price-sale').text
    except:
        price_element = soup_engine.find('span', class_='price-v3').text
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = ' '.join(list(map(lambda x: x.strip(), soup_engine.find('h1').text.strip().split('\n'))))
    return {'price_element': price_element, 'name': name, 'shop': 'audiomania', 'category': shop_to_category['audiomania']}




def get_product_planeta_sport(product_url):
    '''Функция для парсинга товара из planeta-sport'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find('span', class_='price_value').text.split()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text
    return {'price_element': price_element, 'name': name, 'shop': 'planeta-sport', 'category': shop_to_category['planeta-sport']}




def get_product_krups(product_url):
    '''Функция для парсинга товара из krups'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = re.search(pattern=r'items: \[\{(.+?)\}', string=response.text).group(1)
    price_element = re.search(pattern=r'\"price\"(.+)', string=response.text).group(1)
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'krups', 'category': shop_to_category['krups']}




def get_product_rocky_shop(product_url):
    '''Функция для парсинга товара из rocky-shop'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = re.search(pattern=r'\<meta\sitemprop\=\"price\" content\=\"(\d+)', string=response.text).group(1)
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'rocky-shop', 'category': shop_to_category['rocky-shop']}




def get_product_aromacode(product_url):
    '''Функция для парсинга товара из aromacode'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find_all('span', class_='price prices-price prices-price-regular active')
    price_element = list(map(lambda x: int(x.text), price_element))
    name = soup_engine.find_all('span', class_='sku-name')
    name = list(map(lambda x: x.text.strip(), name))
    dict_prices = dict(zip(name, price_element))
    name = tuple(dict_prices.keys())[-1]
    price_element = tuple(dict_prices.values())[-1]
    return {'price_element': price_element, 'name': name, 'shop': 'aromacode', 'category': shop_to_category['aromacode']}




def get_product_kosmetika_proff(product_url):
    '''Функция для парсинга товара из kosmetika-proff'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('span', class_='svg-currency').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'kosmetika-proff', 'category': shop_to_category['kosmetika-proff']}




def get_product_clever_media(product_url):
    '''Функция для парсинга товара из clever-media'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find('span', class_='product__price-cur').text
    price_element = re.findall(pattern=r'(\"price\"\:)(.+)', string=response.text)[0][1]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'clever-media', 'category': shop_to_category['clever-media']}




def get_product_elemis(product_url):
    '''Функция для парсинга товара из elemis'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find('span', class_='new').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'elemis', 'category': shop_to_category['elemis']}




def get_product_mdm_complect(product_url):
    '''Функция для парсинга товара из mdm-complect'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find('div', class_='price-main').text.strip()
    price_element = price_element.split('.')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'mdm-complect', 'category': shop_to_category['mdm-complect']}




def get_product_lu(product_url):
    '''Функция для парсинга товара из lu'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find('div', class_='card2-price__current').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'lu', 'category': shop_to_category['lu']}




def get_product_litnet(product_url):
    '''Функция для парсинга товара из litnet'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find('span', class_='ln_btn-get-text').text.strip()
    price_element = re.search(pattern=r'\s([\d\.]+)\s(RUB)', string=price_element).group(1)
    price_element = int(float(''.join(list(filter(lambda x: True if x.isdigit() or x == '.' else False, price_element)))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'litnet', 'category': shop_to_category['litnet']}




def get_product_mi_shop(product_url):
    '''Функция для парсинга товара из mi-shop'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find('div', class_='b-product-info__price-new').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'mi-shop', 'category': shop_to_category['mi-shop']}



def get_product_parfums(product_url):
    '''Функция для парсинга товара из parfums'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find_all('label', class_='pd-product__variants-item')
    price_element = list(map(lambda x: x.text.strip(' \n'), price_element))
    for i in range(len(price_element)):
        price_element[i] = ' '.join(list(filter(lambda x: True if x not in '\n ' else False, price_element[i].split()))) #уверен, что проще можно сделать
        if '%' in price_element[i]:
            price_element[i] = (re.search(pattern=r'(.+)\-\d', string=price_element[i]).group(1).strip(), int(re.search(pattern=r'\%\s(\d+?)\s(руб)', string=price_element[i]).group(1).strip()))
        elif 'Нет в наличии' in price_element[i]:
            price_element[i] = (re.search(pattern=r'(.+)\s(\d+?)\s(руб)', string=price_element[i]).group(1).strip(), 
                                re.search(pattern=r'(.+)\s(\d+?)\s(руб)', string=price_element[i]).group(2).strip())
        else:
            price_element[i] = (re.search(pattern=r'(.+)\s(\d+?)\s(руб)', string=price_element[i]).group(1).strip(), 
                                int(re.search(pattern=r'(.+)\s(\d+?)\s(руб)', string=price_element[i]).group(2).strip()))
    price_element = list(filter(lambda x: True if isinstance(x[1], int) else False, price_element))
    price_element = price_element[-1][1]
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'parfums', 'category': shop_to_category['parfums']}



def get_product_lex1(product_url):
    '''Функция для парсинга товара из lex1'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find('div', class_='item-single-product-price mb-3 price').text.strip()
    if '%' in price_element:
        price_element = re.search(pattern=r'(Текущая цена\:)\s([\d\s]+)₽', string = price_element).group(2)
    else:
        price_element = price_element.split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'lex1', 'category': shop_to_category['lex1']}



def get_product_r_ulybka(product_url):
    '''Функция для парсинга товара из r-ulybka'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find('script', attrs={'type':"application/ld+json"}).text.strip()
    price_element = re.search(pattern=r'(\"price\"\:)([\d ]+)\,', string=price_element).group(2)
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'r-ulybka', 'category': shop_to_category['r-ulybka']}



def get_product_top_santehnika(product_url):
    '''Функция для парсинга товара из top-santehnika'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    try:
        price_element = soup_engine.find('div', class_='coupon-price').text.strip()
    except:
        price_element = soup_engine.find('div', class_='product-cart__price measure-price').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'top-santehnika', 'category': shop_to_category['top-santehnika']}



def get_product_rossko(product_url):
    '''Функция для парсинга товара из rossko'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find('div', class_='price').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'rossko', 'category': shop_to_category['rossko']}



def get_product_z51(product_url):
    '''Функция для парсинга товара из z51'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find('div', class_='zone__product__price__value').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'z51', 'category': shop_to_category['z51']}



def get_product_moulinex(product_url):
    '''Функция для парсинга товара из moulinex'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find('title').text.strip()
    price_element = re.search(pattern=r'(цене\s)(.+)₽', string=price_element).group(2)
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'moulinex', 'category': shop_to_category['moulinex']}



def get_product_krutizmi(product_url):
    '''Функция для парсинга товара из krutizmi'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find('div', class_='sidebar-card__price').text.strip()
    price_element = price_element.split('руб.')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'krutizmi', 'category': shop_to_category['krutizmi']}



def get_product_pharmacosmetica(product_url):
    '''Функция для парсинга товара из pharmacosmetica'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    try:
        price_element = soup_engine.find('h2', class_='tprice').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
    except:
        price_element = soup_engine.find_all('tr', class_='colors-table__row')
        price_element = price_element[2:]
        final_price_element = []
        for elem in price_element:
            if 'уценка' in str(elem):
                final_price_element.append(int(re.search(pattern=r'(\<span\sclass\=\"tprice\"\>)(.+)\s₽\<', string=str(elem)).group(2)))
            else:
                final_price_element.append(int(re.search(pattern=r'(\<span class\=\"tprice\" data-action\-id\=\"0\"\>)(.+)\s₽\<', string=str(elem)).group(2)))
        name = soup_engine.find_all('td', class_='colors-table__name-cell')
        name = list(map(lambda x: re.search(pattern=r'(\<span\>)(.+?)\<', string=str(x)).group(2), name))
        name = list(map(lambda x: f'{soup_engine.find('h1').text.strip()} {x}', name))
        full = list(zip(final_price_element, name))
        actions = soup_engine.find_all('td', class_='colors-table__buy-cell')
        actions = list(map(lambda x: x.text, actions))
        list_to_delete = []
        for i in range(len(actions)):
            if 'Купить' not in actions[i]:
                list_to_delete.append(i)
        final_full = []
        for i in range(len(full)):
            if i not in list_to_delete:
                final_full.append(full[i])
        price_element, name = final_full[0]
    return {'price_element': price_element, 'name': name, 'shop': 'pharmacosmetica', 'category': shop_to_category['pharmacosmetica']}



def get_product_gamepark(product_url):
    '''Функция для парсинга товара из gamepark'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    if 'used' in product_url:
        price_element = soup_engine.find_all('div', class_='price')[1].text.strip()
    else:
        price_element = soup_engine.find('div', class_='price').text.strip()
    try:
        price_element = price_element.split('е')[0]
    except: pass
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    if 'used' in product_url:
        name = f'{soup_engine.find('h1').text.strip()} (Б/У)'
    else:
        name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'gamepark', 'category': shop_to_category['gamepark']}



def get_product_domsporta(product_url):
    '''Функция для парсинга товара из domsporta'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find('div', class_='b-detail__price').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'domsporta', 'category': shop_to_category['domsporta']}



def get_product_lustrof(product_url):
    '''Функция для парсинга товара из lustrof'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find('div', class_='price product__price').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'lustrof', 'category': shop_to_category['lustrof']}



def get_product_lakestone(product_url):
    '''Функция для парсинга товара из lakestone'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='price').text.strip()
    price_element = price_element.split('руб.')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'lakestone', 'category': shop_to_category['lakestone']}



def get_product_bookvoed(product_url):
    '''Функция для парсинга товара из bookvoed'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='price-block-price-info__price').text.strip()
    price_element = price_element.split(' ₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('title').text.strip()
    name = re.search(pattern=r'(.+)\s\-\s(купить)', string=name).group(1)
    return {'price_element': price_element, 'name': name, 'shop': 'bookvoed', 'category': shop_to_category['bookvoed']}



def get_product_proficosmetics(product_url):
    '''Функция для парсинга товара из proficosmetics'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('p', class_='new_price').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'proficosmetics', 'category': shop_to_category['proficosmetics']}



def get_product_vamvelosiped(product_url):
    '''Функция для парсинга товара из vamvelosiped'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    try:
        price_element = soup_engine.find_all('span', class_='price price-new')
        price_element = price_element[-1].text.strip()
    except:
        price_element = soup_engine.find('span', class_='price').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'vamvelosiped', 'category': shop_to_category['vamvelosiped']}



def get_product_book24(product_url):
    '''Функция для парсинга товара из book24'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('span', class_='app-price product-sidebar-price__price').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'book24', 'category': shop_to_category['book24']}



def get_product_birota(product_url):
    '''Функция для парсинга товара из birota'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('strong', class_='price').text.strip()
    price_element = price_element.split('руб.')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'birota', 'category': shop_to_category['birota']}



def get_product_bebakids(product_url):
    '''Функция для парсинга товара из bebakids'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='wr_item_3_1').text.strip()
    price_element = price_element.split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'bebakids', 'category': shop_to_category['bebakids']}



def get_product_med_magazin(product_url):
    '''Функция для парсинга товара из med-magazin'''
    headers = {"User-Agent": "Mozilla/5.0"}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find('div', class_='price-block').text.strip()
    price_element = price_element.split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find('h1').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'med-magazin', 'category': shop_to_category['med-magazin']}
























#магазины, которые блокируют обычные requests, поэтому их нужно делать по-другому
def get_product_goldapple(product_url): #точно бан
    ...

def get_product_lamoda(product_url): #есть имя, но нет цены в тайтле
    ...

def get_product_lgcity(product_url): #точно бан
    ...

def get_product_ozon(product_url): #точно бан
    ...

def get_product_sportmaster(product_url): #точно бан
    ...

def get_product_2moodstore(product_url):
    ...

def get_product_ostin(product_url):
    ...

def get_product_demix(product_url):
    ...

def get_product_thomas_muenz(product_url):
    ...

def get_product_ekonika(product_url):
    ...

def get_product_studio_29(product_url):
    ...

def get_product_baon(product_url):
    ...

def get_product_presentandsimple(product_url):
    ...

def get_product_henderson(product_url):
    ...

def get_product_sokolov(product_url):
    ...

def get_product_vseinstrumenti(product_url): #точно бан
    ...

def get_product_holodilnik(product_url):
    ...

def get_product_letu(product_url): #точно бан
    ...

def get_product_petrovich(product_url): #точно бан
    ...

def get_product_shoppinglive(product_url): #точно бан
    ...

def get_product_ormatek(product_url): #точно бан
    ...

def get_product_oldi(product_url): #точно бан
    ...

def get_product_gulliver(product_url): #точно бан
    ...

def get_product_imperiatechno(product_url): #точно бан
    ...

def get_product_kikocosmetics(product_url): #посмотреть - вроде cloudscraper должен обходить
    ...

def get_product_huawei(product_url):
    ...

def get_product_santehnika_room(product_url):
    ...

def get_product_maxidom(product_url):
    ...

def get_product_velodrive(product_url):
    ...

def get_product_stolplit(product_url):
    ...

def get_product_euro_diski(product_url):
    ...

def get_product_dvizhcom(product_url):
    ...

def get_product_bbcream(product_url):
    ...

def get_product_postmeridiem_brand(product_url): #цена не парсится из-за js-кода
    '''Функция для парсинга товара из postmeridiem-brand'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    price_element = soup_engine.find("div", class_='product-card__content-wrapper').text.strip()
    print(price_element)
    return
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("title").text.strip()
    name = re.search(pattern=r'(.+?)( купить)', string=name).group(1)
    return {'price_element': price_element, 'name': name, 'shop': 'postmeridiem-brand', 'category': shop_to_category['postmeridiem-brand']}

def get_product_askona(product_url): #блокает ip после 5-10 запросов
    '''Функция для парсинга товара из askona'''
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referrer": "https://www.askona.ru/",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}
    scraper = cloudscraper.create_scraper()
    response = scraper.get(product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'lxml')
    full = soup_engine.find('title').text.strip()
    try:
        price_element = re.search(pattern=r'(по цене от )(.+)( руб.)', string=full).group(2)
        name = re.search(pattern=r'(.+)( купить)', string=full).group(1)
    except:
        price_element = re.search(pattern=r'(цена от )(.+)', string=full).group(2)
        name = re.search(pattern=r'(Купить )(.+)( цена)', string=full).group(2)
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    return {'price_element': price_element, 'name': name, 'shop': 'askona', 'category': shop_to_category['askona']}


shop_to_func = {'brandshop': get_product_brandshop, 
                'rendez-vous': get_product_rendez_vous, 
                'tsum': get_product_tsum,  
                'street-beat': get_product_street_beat,
                'superstep': get_product_superstep,
                'lacoste': get_product_lacoste,
                'sv77': get_product_sv77,
                'elyts': get_product_elyts,
                'vipavenue': get_product_vipavenue,
                'aimclo': get_product_aimclo,
                'befree': get_product_befree,
                'loverepublic': get_product_loverepublic,
                'youstore': get_product_youstore,
                'gate31': get_product_gate31,
                'incanto': get_product_incanto,
                'sportcourt': get_product_sportcourt,
                '1811stores': get_product_1811stores,
                'bask': get_product_bask,
                'noone': get_product_noone,
                'elis': get_product_elis,
                'afinabags': get_product_afinabags,
                'crockid': get_product_crockid,
                'bungly': get_product_bungly,
                'aupontrouge': get_product_aupontrouge,
                'sohoshop': get_product_sohoshop,
                'lichi': get_product_lichi,
                'askent': get_product_askent,
                'darsi': get_product_darsi,
                'cocos-moscow': get_product_cocos_moscow,
                'inspireshop': get_product_inspireshop,
                'respect-shoes': get_product_respect_shoes,
                'pompa': get_product_pompa,
                'bunnyhill': get_product_bunnyhill,
                'annapekun': get_product_annapekun,
                'amazingred': get_product_amazingred,
                'm-reason': get_product_m_reason,
                'choux': get_product_choux,
                'fablestore': get_product_fablestore,
                'selfmade': get_product_selfmade,
                'kanzler-style': get_product_kanzler_style,
                'belleyou': get_product_belleyou,
                'zolla': get_product_zolla,
                'danielonline': get_product_danielonline,
                'zarina': get_product_zarina,
                'alexanderbogdanov': get_product_alexanderbogdanov,
                'werfstore': get_product_werfstore,
                'koffer': get_product_koffer,
                'age-of-innocence': get_product_age_of_innocence,
                'nice-one': get_product_nice_one,
                'alpindustria': get_product_alpindustria,
                'indiwd': get_product_indiwd,
                'yves-rocher': get_product_yves_rocher,
                'galaxystore': get_product_galaxystore,
                'megafon': get_product_megafon,
                'ecco': get_product_ecco,
                'xcom-shop': get_product_xcom_shop,
                'epldiamond': get_product_epldiamond,
                'doctorslon': get_product_doctorslon,
                'randewoo': get_product_randewoo,
                'babor': get_product_babor,
                'mir-kubikov': get_product_mir_kubikov,
                'bombbar': get_product_bombbar,
                'iledebeaute': get_product_iledebeaute,
                'shop-polaris': get_product_shop_polaris,
                'patchandgo': get_product_patchandgo,
                'madwave': get_product_madwave,
                'apple-avenue': get_product_apple_avenue,
                're-store': get_product_re_store,
                'bestmebelshop': get_product_bestmebelshop,
                'garlyn': get_product_garlyn,
                'kuppersberg': get_product_kuppersberg,
                'bosssleep': get_product_bosssleep,
                'muztorg': get_product_muztorg,
                'voishe': get_product_voishe,
                'finn-flare': get_product_finn_flare,
                'biggeek': get_product_biggeek,
                'tefal': get_product_tefal,
                'litres': get_product_litres,
                'orteka': get_product_orteka,
                'quke': get_product_quke,
                'leonardo': get_product_leonardo,
                'beeline': get_product_beeline,
                'tvoydom': get_product_tvoydom,
                'sela': get_product_sela,
                'aquaphor': get_product_aquaphor,
                'mnogomebeli': get_product_mnogomebeli,
                'davines': get_product_davines,
                'vsesmart': get_product_vsesmart,
                'boobl-goom': get_product_boobl_goom,
                'ipiter': get_product_ipiter,
                'mie': get_product_mie,
                'evitastore': get_product_evitastore,
                'chitai-gorod': get_product_chitai_gorod,
                'bestwatch': get_product_bestwatch,
                'koleso': get_product_koleso,
                'mann-ivanov-ferber': get_product_mann_ivanov_ferber,
                'cozyhome': get_product_cozyhome,
                'christinacosmetics': get_product_christinacosmetics,
                'velosklad': get_product_velosklad,
                'multivarka': get_product_multivarka,
                'iboxstore': get_product_iboxstore,
                'market-sveta': get_product_market_sveta,
                'aravia': get_product_aravia,
                'krona': get_product_krona,
                'tddomovoy': get_product_tddomovoy,
                'hyperauto': get_product_hyperauto,
                'kubaninstrument': get_product_kubaninstrument,
                'nespresso': get_product_nespresso,
                'aofb': get_product_aofb,
                'yamanshop': get_product_yamanshop,
                'dvamyacha': get_product_dvamyacha,
                'ochkarik': get_product_ochkarik,
                'hi-stores': get_product_hi_stores,
                'fkniga': get_product_fkniga,
                'santehnika-tut': get_product_santehnika_tut,
                'wau': get_product_wau,
                'skinjestique': get_product_skinjestique,
                'igroray': get_product_igroray,
                'hansa': get_product_hansa,
                'zvet': get_product_zvet,
                'x-moda': get_product_x_moda,
                'playtoday': get_product_playtoday,
                'santehmoll': get_product_santehmoll,
                'golden-line': get_product_golden_line,
                'tmktools': get_product_tmktools,
                'ochkov': get_product_ochkov,
                'svetlux': get_product_svetlux,
                'divanboss': get_product_divanboss,
                'postel-deluxe': get_product_postel_deluxe,
                'dushevoi': get_product_dushevoi,
                'tastycoffee': get_product_tastycoffee,
                'eurodom': get_product_eurodom,
                'happylook': get_product_happylook,
                'consul-coton': get_product_consul_coton,
                'planeta-sport': get_product_planeta_sport,
                'krups': get_product_krups,
                'rocky-shop': get_product_rocky_shop,
                'aromacode': get_product_aromacode,
                'kosmetika-proff': get_product_kosmetika_proff,
                'clever-media': get_product_clever_media,
                'elemis': get_product_elemis,
                'audiomania': get_product_audiomania,
                'mdm-complect': get_product_mdm_complect,
                'lu': get_product_lu,
                'litnet': get_product_litnet,
                'mi-shop': get_product_mi_shop,
                'parfums': get_product_parfums,
                'lex1': get_product_lex1,
                'r-ulybka': get_product_r_ulybka,
                'top-santehnika': get_product_top_santehnika,
                'rossko': get_product_rossko,
                'z51': get_product_z51,
                'moulinex': get_product_moulinex,
                'krutizmi': get_product_krutizmi,
                'pharmacosmetica': get_product_pharmacosmetica,
                'gamepark': get_product_gamepark,
                'domsporta': get_product_domsporta,
                'lustrof': get_product_lustrof,
                'lakestone': get_product_lakestone,
                'bookvoed': get_product_bookvoed,
                'proficosmetics': get_product_proficosmetics,
                'vamvelosiped': get_product_vamvelosiped,
                'book24': get_product_book24,
                'birota': get_product_birota,
                'bebakids': get_product_bebakids,
                'med-magazin': get_product_med_magazin,
                # 'iherbgroup': get_product_iherbgroup,

                #не работают с requests
                'goldapple': get_product_goldapple,
                'lamoda': get_product_lamoda,
                'sportmaster': get_product_sportmaster,
                'lgcity': get_product_lgcity,
                'ozon': get_product_ozon,
                '2moodstore': get_product_2moodstore,
                'ostin': get_product_ostin,
                'demix': get_product_demix,
                'thomas-muenz': get_product_thomas_muenz,
                'postmeridiem-brand': get_product_postmeridiem_brand,
                'ekonika':get_product_ekonika,
                'studio-29': get_product_studio_29,
                'baon': get_product_baon,
                'presentandsimple': get_product_presentandsimple,
                'henderson': get_product_henderson,
                'sokolov': get_product_sokolov,
                'vseinstrumenti': get_product_vseinstrumenti,
                'holodilnik': get_product_holodilnik,
                'letu': get_product_letu,
                'askona': get_product_askona,
                'petrovich': get_product_petrovich,
                'shoppinglive': get_product_shoppinglive,
                'ormatek': get_product_ormatek,
                'oldi': get_product_oldi,
                'gulliver': get_product_gulliver,
                'imperiatechno': get_product_imperiatechno,
                'kikocosmetics': get_product_kikocosmetics,
                'huawei': get_product_huawei,
                'ansaligy': get_product_ansaligy,
                'santehnika-room': get_product_santehnika_room,
                'maxidom': get_product_maxidom,
                'velodrive': get_product_velodrive,
                'stolplit': get_product_stolplit,
                'euro-diski': get_product_euro_diski,
                'dvizhcom': get_product_dvizhcom,
                'bbcream': get_product_bbcream,
                }


shop_to_category = {'brandshop': 'Одежда/обувь/аксессуары', 
                'rendez-vous': 'Одежда/обувь/аксессуары', 
                'tsum': 'Одежда/обувь/аксессуары',  
                'street-beat': 'Одежда/обувь/аксессуары',
                'superstep': 'Одежда/обувь/аксессуары',
                'lacoste': 'Одежда/обувь/аксессуары',
                'sv77': 'Одежда/обувь/аксессуары',
                'elyts': 'Одежда/обувь/аксессуары',
                'vipavenue': 'Одежда/обувь/аксессуары',
                'aimclo': 'Одежда/обувь/аксессуары',
                'befree': 'Одежда/обувь/аксессуары',
                'loverepublic': 'Одежда/обувь/аксессуары',
                'youstore': 'Одежда/обувь/аксессуары',
                'gate31': 'Одежда/обувь/аксессуары',
                'incanto': 'Одежда/обувь/аксессуары',
                'sportcourt': 'Одежда/обувь/аксессуары',
                '1811stores': 'Одежда/обувь/аксессуары',
                'bask': 'Одежда/обувь/аксессуары',
                'noone': 'Одежда/обувь/аксессуары',
                'elis': 'Одежда/обувь/аксессуары',
                'afinabags': 'Одежда/обувь/аксессуары',
                'crockid': 'Детская одежда/Одежда для мам',
                'tsum-outlet': 'Одежда/обувь/аксессуары',
                'bungly': 'Детская одежда/Одежда для мам',
                'aupontrouge': 'Одежда/обувь/аксессуары',
                'sohoshop': 'Одежда/обувь/аксессуары',
                'lichi': 'Одежда/обувь/аксессуары',
                'askent': 'Одежда/обувь/аксессуары',
                'darsi': 'Одежда/обувь/аксессуары',
                'cocos-moscow': 'Одежда/обувь/аксессуары',
                'inspireshop': 'Одежда/обувь/аксессуары',
                'respect-shoes': 'Одежда/обувь/аксессуары',
                'pompa': 'Одежда/обувь/аксессуары',
                'bunnyhill': 'Детская одежда/Одежда для мам', 
                'annapekun': 'Одежда/обувь/аксессуары',
                'amazingred': 'Одежда/обувь/аксессуары',
                'm-reason': 'Одежда/обувь/аксессуары',
                'voishe': 'Одежда/обувь/аксессуары',
                'choux': 'Одежда/обувь/аксессуары',
                'fablestore': 'Одежда/обувь/аксессуары',
                'selfmade': 'Одежда/обувь/аксессуары',
                'kanzler-style': 'Одежда/обувь/аксессуары',
                'belleyou': 'Одежда/обувь/аксессуары',
                'zolla': 'Одежда/обувь/аксессуары',
                'danielonline': 'Одежда/обувь/аксессуары',
                'zarina': 'Одежда/обувь/аксессуары',
                'alexanderbogdanov': 'Одежда/обувь/аксессуары',
                'werfstore': 'Одежда/обувь/аксессуары',
                'koffer': 'Одежда/обувь/аксессуары',
                'age-of-innocence': 'Детская одежда/Одежда для мам',
                'nice-one': 'Одежда/обувь/аксессуары',
                'alpindustria': 'Экипировка',
                'indiwd': 'Одежда/обувь/аксессуары',
                'biggeek': 'Электроника',
                'tefal': 'Бытовая техника',
                'yves-rocher': 'Косметика и парфюмерия',
                'galaxystore': 'Электроника',
                'megafon': 'Электроника',
                'ecco': 'Одежда/обувь/аксессуары',
                'xcom-shop': 'Электроника',
                'epldiamond': 'Ювелирные украшения',
                'doctorslon': 'Стоматологические товары',
                'randewoo': 'Косметика и парфюмерия',
                'babor': 'Косметика и парфюмерия',
                'mir-kubikov': 'Конструкторы',
                'bombbar': 'Спортивное питание',
                'iledebeaute': 'Косметика и парфюмерия',
                'shop-polaris': 'Бытовая техника',
                'patchandgo': 'Косметика и парфюмерия',
                'madwave': 'Экипировка',
                'apple-avenue': 'Электроника',
                're-store': 'Электроника',
                'bestmebelshop': 'Товары для дома',
                'garlyn': 'Бытовая техника',
                'kuppersberg': 'Бытовая техника',
                'bosssleep': 'Товары для дома',
                'muztorg': 'Музыкальная аппаратура',
                'finn-flare': 'Одежда/обувь/аксессуары',
                'litres': 'Книги и аудиокниги',
                'orteka': 'Ортопедический салон',
                'quke': 'Электроника',
                'leonardo': 'Товары для хобби',
                'beeline': 'Электроника',
                'tvoydom': 'Товары для дома',
                'sela': 'Одежда/обувь/аксессуары',
                'aquaphor': 'Фильтры для воды',
                'mnogomebeli': 'Товары для дома',
                'davines': 'Косметика и парфюмерия',
                'vsesmart': 'Электроника',
                'boobl-goom': 'Детская одежда/Одежда для мам',
                'ipiter': 'Электроника',
                'mie': 'Ювелирные украшения',
                'evitastore': 'Косметика и парфюмерия',
                'chitai-gorod': 'Книги и канцтовары',
                'bestwatch': 'Часы',
                'koleso': 'Автотовары',
                'mann-ivanov-ferber': 'Книги и аудиокниги',
                'cozyhome': 'Товары для дома',
                'christinacosmetics': 'Косметика и парфюмерия',
                'velosklad': 'Велосипеды',
                'multivarka': 'Бытовая техника',
                'iboxstore': 'Автоэлектроника',
                'market-sveta': 'Товары для дома',
                'aravia': 'Косметика и парфюмерия',
                'krona': 'Бытовая техника',
                'tddomovoy': 'Товары для дома',
                'hyperauto': 'Товары для авто',
                'kubaninstrument': 'Товары для дома',
                'nespresso': 'Кофе и кофемашины',
                'aofb': 'Товары для дома',
                'yamanshop': 'Косметика и парфюмерия',
                'dvamyacha': 'Одежда/обувь/аксессуары',
                'ochkarik': 'Оптика',
                'ansaligy': 'Косметика и парфюмерия',
                'hi-stores': 'Электроника',
                'fkniga': 'Книги и аудиокниги',
                'santehnika-tut': 'Сантехника',
                'wau': 'Косметика и парфюмерия',
                'skinjestique': 'Косметика и парфюмерия',
                'igroray': 'Игровые товары',
                'hansa': 'Бытовая техника',
                'zvet': 'Товары для дома',
                'x-moda': 'Одежда/обувь/аксессуары',
                'playtoday': 'Детская одежда/Одежда для мам',
                'santehmoll': 'Сантехника',
                'golden-line': 'Одежда/обувь/аксессуары',
                'tmktools': 'Инструменты',
                'ochkov': 'Оптика',
                'svetlux': 'Светильники',
                'divanboss': 'Товары для дома',
                'postel-deluxe': 'Товары для дома',
                'dushevoi': 'Сантехника',
                'tastycoffee': 'Кофе',
                'eurodom': 'Товары для дома',
                'happylook': 'Оптика',
                'consul-coton': 'Товары для дома',
                'planeta-sport': 'Одежда/обувь/аксессуары',
                'krups': 'Кофе',
                'rocky-shop': 'Боксерская экипировка',
                'aromacode': 'Косметика и парфюмерия',
                'kosmetika-proff': 'Косметика и парфюмерия',
                'clever-media': 'Книги',
                'elemis': 'Косметика и парфюмерия',
                'audiomania': 'Акустическая аппаратура',
                'mdm-complect': 'Товары для дома',
                'lu': 'Светильники',
                'litnet': 'Книги и аудиокниги',
                'mi-shop': 'Электроника',
                'parfums': 'Косметика и парфюмерия',
                'lex1': 'Бытовая техника',
                'r-ulybka': 'Косметика и парфюмерия',
                'top-santehnika': 'Сантехника',
                'rossko': 'Товары для авто',
                'z51': 'Компьютерная периферия',
                'moulinex': 'Бытовая техника',
                'krutizmi': 'Спорт-товары',
                'pharmacosmetica': 'Косметика и парфюмерия',
                'gamepark': 'Компьютерные игры и консоли',
                'domsporta': 'Спорт-товары',
                'lustrof': 'Товары для дома',
                'lakestone': 'Сумки и рюкзаки',
                'bookvoed': 'Книги и канцтовары',
                'proficosmetics': 'Косметика и парфюмерия',
                'vamvelosiped': 'Велосипеды и аксессуары',
                'book24': 'Книги и аудиокниги',
                'birota': 'Велосипеды и аксессуары',
                'bebakids': 'Детская одежда',
                'med-magazin': 'Мед инвентарь',
                'iherbgroup': 'Товары для здоровья',

                #не работают с requests
                'goldapple': 'Парфюмерия',
                'lamoda': 'Одежда/обувь/аксессуары',
                'sportmaster': 'Одежда/обувь/аксессуары',
                'lgcity': 'Одежда/обувь/аксессуары',
                'ozon': 'Маркетплейс',
                '2moodstore': 'Одежда/обувь/аксессуары',
                'ostin': 'Одежда/обувь/аксессуары',
                'demix': 'Одежда/обувь/аксессуары',
                'thomas-muenz': 'Одежда/обувь/аксессуары',
                'postmeridiem-brand': 'Одежда/обувь/аксессуары',
                'ekonika': 'Одежда/обувь/аксессуары',
                'studio-29': 'Одежда/обувь/аксессуары',
                'baon': 'Одежда/обувь/аксессуары',
                'presentandsimple': 'Одежда/обувь/аксессуары',
                'henderson': 'Одежда/обувь/аксессуары',
                'sokolov': 'Ювелирные украшения',
                'vseinstrumenti': 'Товары для дома',
                'holodilnik': 'Бытовая техника',
                'letu': 'Косметика и парфюмерия',
                'askona': 'Товары для дома',
                'petrovich': 'Товары для дома',
                'shoppinglive': 'Маркетплейс',
                'ormatek': 'Товары для дома',
                'oldi': 'Электроника',
                'gulliver': 'Детская одежда/Одежда для мам',
                'imperiatechno': 'Электроника',
                'kikocosmetics': 'Косметика и парфюмерия',
                'huawei': 'Электроника',
                'santehnika-room': 'Сантехника',
                'maxidom': 'Товары для дома',
                'velodrive': 'Велосипеды',
                'stolplit': 'Товары для дома',
                'euro-diski': 'Шины и диски',
                'dvizhcom': 'Товары для авто',
                'bbcream': 'Косметика и парфюмерия',
}


# ненужная регулярка для вычленения цены, тк bs4 сам это делает при переводе .text
# price_digger = re.search(pattern=r'[\d ]+ ₽', string='''<div class="product-order__price_new">
#     3 450 ₽
#   </div>''')
# print(price_digger.group(0).strip())

