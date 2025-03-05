from requests import request
from bs4 import BeautifulSoup
import re
import json


def get_shop_of_product(product_url):
    '''Функция, определяющая, какому магазину принадлежит ссылка'''
    regex = r'://(www.)?([\w-]+).(\w+)/'
    return shop_to_func.get(re.search(pattern=regex, string=product_url).group(2))(product_url)

    
def get_product_brandshop(product_url):
    '''Функция для парсинга товара из brandshop'a'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url ,headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    try:
        price_element = soup_engine.find("div", class_="product-order__price_new").text.strip()
    except:
        price_element = soup_engine.find("div", class_="product-order__price-wrapper").text.strip()
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element.split()))))
    brand = soup_engine.find("div", class_="product-page__header font font_title-l").text.strip()
    category, model = map(lambda x: x.text.strip(), soup_engine.find_all("div", class_="product-page__subheader font font_m font_grey")) #модель не добавляю
    print(model)
    return {'price_element': price_element, 'name': brand + ' ' + category}


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
    return {'price_element': price_element, 'name': brand + ' ' + category}

def get_product_tsum(product_url):
    '''Функция для парсинга товара из tsum'a'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find("p", class_=re.compile(r'Price__price___\w+')).text.strip()
    brand = soup_engine.find("div", class_=re.compile(r'ColumnView__infoBlocksRow___\w+')).text.strip()
    brand = re.search(pattern=r'Бренд: (.+?)С', string=brand).group(1)
    category = soup_engine.find("h1", class_=re.compile(r'description__productName___\w+')).text.strip()
    category = re.search(pattern=r'[А-Я].+', string=category).group(0)
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element.split()))))
    return {'price_element': int(str(price_element)), 'name': brand + ' ' + category}


def get_product_lamoda(product_url):
    '''Функция для парсинга товара из lamoda'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url ,headers=headers)
    print(response.text)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
#     print(soup_engine)
#     price_element = soup_engine.find("div", class_=re.compile(r'_title_.+')).text.strip()
#     print(price_element)
#     # brand = soup_engine.find("div", class_=re.compile(r'ColumnView__infoBlocksRow___\w+')).text.strip()
#     # brand = re.search(pattern=r'Бренд: (.+?)С', string=brand).group(1)
#     # category = soup_engine.find("h1", class_=re.compile(r'description__productName___\w+')).text.strip()
#     # category = re.search(pattern=r'[А-Я].+', string=category).group(0)
#     # return {'price_element': price_element, 'brand': brand, 'model': 'model', 'category': category}



def get_product_street_beat(product_url):
    '''Функция для парсинга товара из street beat'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    digital_data_dict = re.search(r'window\.digitalData\s*=\s*(\{.*?\});', response.text)
    json_data = json.loads(digital_data_dict.group(1))
    name = json_data['product']['name']
    price_element = json_data['product']['unitPrice']
    return {'price_element': price_element, 'name': name}

shop_to_func = {'brandshop': get_product_brandshop, 
                'rendez-vous': get_product_rendez_vous, 
                'tsum': get_product_tsum, 
                'lamoda': get_product_lamoda, 
                'street-beat': get_product_street_beat}





# ненужная регулярка для вычленения цены, тк bs4 сам это делает при переводе .text
# price_digger = re.search(pattern=r'[\d ]+ ₽', string='''<div class="product-order__price_new">
#     3 450 ₽
#   </div>''')
# print(price_digger.group(0).strip())

