from requests import request
from bs4 import BeautifulSoup
import re
import json
import httpx


def get_shop_of_product(product_url):
    '''Функция, определяющая, какому магазину принадлежит ссылка'''
    regex = r'://(www\.)?(ru\.)?(mytishchi\.)?(moscow\.)?(outlet\.)?([\w-]+)\.(\w+)/'
    return shop_to_func.get(re.search(pattern=regex, string=product_url).group(6).strip())(product_url)

    

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














#магазины, которые блокируют обычные requests, поэтому их нужно делать по-другому
def get_product_goldapple(product_url):
    ...

def get_product_lamoda(product_url):
    ...

def get_product_lgcity(product_url): #блокает
    ...

def get_product_ozon(product_url): #блокает
    ...

def get_product_sportmaster(product_url): #блокает
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

def get_product_finn_flare(product_url):
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
                'voishe': get_product_voishe,
                'presentandsimple': get_product_presentandsimple,
                'henderson': get_product_henderson,
                'finn-flare': get_product_finn_flare,
                'biggeek': get_product_biggeek,
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
                'finn-flare': 'Одежда/обувь/аксессуары',

}


# ненужная регулярка для вычленения цены, тк bs4 сам это делает при переводе .text
# price_digger = re.search(pattern=r'[\d ]+ ₽', string='''<div class="product-order__price_new">
#     3 450 ₽
#   </div>''')
# print(price_digger.group(0).strip())

