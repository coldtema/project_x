from requests import request
from bs4 import BeautifulSoup
import re
import json


def get_shop_of_product(product_url):
    '''Функция, определяющая, какому магазину принадлежит ссылка'''
    regex = r'://(www\.)?(ru\.)?([\w-]+).(\w+)/'
    return shop_to_func.get(re.search(pattern=regex, string=product_url).group(3).strip())(product_url)

    

def get_product_brandshop(product_url):
    '''Функция для парсинга товара из brandshop'a'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    try:
        price_element = soup_engine.find("div", class_="product-order__price_new").text.strip()
    except:
        price_element = soup_engine.find("div", class_="product-order__price-wrapper").text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element.split())))) #добавление только цифр в поле price
    brand = soup_engine.find("div", class_="product-page__header font font_title-l").text.strip()
    category, model = map(lambda x: x.text.strip(), soup_engine.find_all("div", class_="product-page__subheader font font_m font_grey")) #модель не добавляю
    return {'price_element': price_element, 'name': brand + ' ' + category, 'shop': 'brandshop'}



def get_product_superstep(product_url):
    '''Функция для парсинга товара из superstep'a'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    try:
        price_element = soup_engine.find("div", class_="product-detail__sale-price--black").text.strip()
    except:
        price_element = soup_engine.find("div", class_="price").text.strip()
        price_element = price_element.split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element.split()))))
    name = soup_engine.find("div", class_="detail__info-wrapper")
    name = ' '.join(list(name.stripped_strings)) #переделанный в строку генератор отредактированных строк
    name = re.search(pattern=r'(.+?) Цвет', string=name).group(1)
    return {'price_element': price_element, 'name': name, 'shop': 'superstep'}



def get_product_rendez_vous(product_url):
    '''Функция для парсинга товара из rendez-vous'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
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
    return {'price_element': price_element, 'name': brand + ' ' + category, 'shop': 'rendez-vous'}



def get_product_tsum(product_url):
    '''Функция для парсинга товара из tsum'a'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
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
    return {'price_element': int(str(price_element)), 'name': brand + ' ' + category, 'shop': 'tsum'}



def get_product_street_beat(product_url):
    '''Функция для парсинга товара из street beat'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    digital_data_dict = re.search(r'window\.digitalData\s*=\s*(\{.*?\});', response.text)
    json_data = json.loads(digital_data_dict.group(1))
    name = json_data['product']['name']
    price_element = json_data['product']['unitPrice']
    return {'price_element': price_element, 'name': name, 'shop': 'street-beat'}


def get_product_lacoste(product_url):
    '''Функция для парсинга товара из lacoste'a'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find("div", class_="nl-product-price nl-product-configuration__price").text.strip().split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element.split()))))
    name = soup_engine.find("h4", class_="nl-product-configuration__title").text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'lacoste'}



def get_product_sv77(product_url):
    '''Функция для парсинга товара из sv77'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find("button", class_="button button-bordered items-center button-rect w-100 db fade button-hover-black").text.strip().split('руб.')
    if price_element[1] != '':
        price_element = price_element[1]
    else:
        price_element = price_element[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element.split()))))
    name = soup_engine.find("h1", class_="product-view-title uppercase").text.strip()
    name = ' '.join(name.split('\n'))
    return {'price_element': price_element, 'name': name, 'shop': 'sv77'}



def get_product_elyts(product_url):
    '''Функция для парсинга товара из elyts'a'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find("div", class_="final-price-block").text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element.split()))))
    name = soup_engine.find("h1").text
    return {'price_element': price_element, 'name': name, 'shop': 'elyts'}



def get_product_vipavenue(product_url):
    '''Функция для парсинга товара из vipavenue'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find("div", class_="product__card--price-actual").text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element.split()))))
    name = soup_engine.find("div", class_="product__card--title").text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'vipavenue'}



def get_product_aimclo(product_url):
    '''Функция для парсинга товара из aimclo'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    try:
        price_element = soup_engine.find("div", class_="product-information__price js-element-price").text.strip()
    except:
        price_element = soup_engine.find("div", class_="product-information__price product-information__sale js-element-price").text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("h1", class_="product-information__title").text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'aimclo'}



def get_product_befree(product_url):
    '''Функция для парсинга товара из befree'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find("div", class_=re.compile(r'.+(digi-product-price)')).text.strip()
    price_element = price_element.split('₽')[0]
    name = soup_engine.find("span", class_=re.compile(r'.+( title)')).text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'befree'}


def get_product_loverepublic(product_url):
    '''Функция для парсинга товара из love republic'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find("div", class_='item-prices').text.strip()
    price_element = price_element.split('₽')
    if price_element[1]:
        price_element = price_element[1].split('%')[1]
    else:
        price_element = price_element[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("h1", class_='catalog-element__title').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'love republic'}



def get_product_youstore(product_url):
    '''Функция для парсинга товара из youstore'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find("div", class_='product-view-price').text.strip()
    price_element = price_element.split('₽')[0].strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("h1").text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'youstore'}



def get_product_gate31(product_url): #вообще не увидел раздел скидок
    '''Функция для парсинга товара из gate31'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find("div", class_='product-price__default').text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("div", class_='ProductPage__title').text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'gate31'}



def get_product_incanto(product_url):
    '''Функция для парсинга товара из incanto'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    full = soup_engine.find("title").text.strip()
    price_element = re.search(pattern=r'(цене )(.+?)( ₽)', string=full).group(2)
    name = re.search(pattern=r'(.+)( Incanto)', string=full).group(1)
    return {'price_element': int(float(price_element)), 'name': name, 'shop': 'incanto'}



def get_product_sportcourt(product_url):
    '''Функция для парсинга товара из sportcourt'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    response.encoding = response.apparent_encoding #свойство, которое угадывает кодировку на основе содержимого
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find("div", class_='p_price').text.strip()
    if price_element.split('₽')[1]:
        price_element = price_element.split('₽')[1]
    else:
        price_element = price_element.split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("div", class_='model_name').text.strip()
    return {'price_element': int(float(price_element)), 'name': name, 'shop': 'sportcourt'}




def get_product_1811stores(product_url):
    '''Функция для парсинга товара из 1811stores'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    full = soup_engine.find("title").text.strip()
    price_element = re.search(pattern=r'(за )(.+?)( руб.)', string=full).group(2)
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = re.search(pattern=r'(.+?)( купить)', string=full).group(1)
    return {'price_element': int(float(price_element)), 'name': name, 'shop': '1811stores'}



def get_product_bask(product_url):
    '''Функция для парсинга товара из bask'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find("span", class_='avail-b').text.strip()
    price_element = re.search(pattern=r'(.+?)(Доступно)', string=price_element).group(1)
    if price_element.split('₽')[1]:
        price_element = price_element.split('₽')[1]
    else:
        price_element = price_element.split('₽')[0]
    print(price_element)
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("title").text.strip()
    name = re.search(pattern=r'(.+?)( - )', string=name).group(1)
    print(name)
    return {'price_element': int(float(price_element)), 'name': name, 'shop': 'bask'}



def get_product_noone(product_url):
    '''Функция для парсинга товара из noone'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find("div", class_='item-price').text.strip()
    price_element = price_element.split('RUB')[0].strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
    name = soup_engine.find("title").text.strip()
    name = re.search(pattern=r'(.+?)( купить)', string=name).group(1)
    print(name)
    return {'price_element': price_element, 'name': name, 'shop': 'noone'}

















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


                #не работают с requests
                'goldapple': get_product_goldapple,
                'lamoda': get_product_lamoda,
                'sportmaster': get_product_sportmaster,
                'lgcity': get_product_lgcity,
                'ozon': get_product_ozon,
                '2moodstore': get_product_2moodstore
                }





# ненужная регулярка для вычленения цены, тк bs4 сам это делает при переводе .text
# price_digger = re.search(pattern=r'[\d ]+ ₽', string='''<div class="product-order__price_new">
#     3 450 ₽
#   </div>''')
# print(price_digger.group(0).strip())

