from requests import request
from bs4 import BeautifulSoup
import re
import json


def get_shop_of_product(product_url):
    '''Функция, определяющая, какому магазину принадлежит ссылка'''
    regex = r'://(www.)?([\w-]+).(\w+)/'
    return shop_to_func.get(re.search(pattern=regex, string=product_url).group(2).strip())(product_url)

    

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
    '''Функция для парсинга товара из superstep'a'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    price_element = soup_engine.find("div", class_="nl-product-price nl-product-configuration__price").text.strip().split('₽')[0]
    price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element.split()))))
    name = soup_engine.find("h4", class_="nl-product-configuration__title").text.strip()
    return {'price_element': price_element, 'name': name, 'shop': 'lacoste'}



def get_product_lamoda(product_url): #блокает
    '''Функция для парсинга товара из lamoda'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url ,headers=headers)
    return {'price_element': 6000, 'name': 'Кофта'}



def get_product_lgcity(product_url): #блокает
    '''Функция для парсинга товара из lady & gentleman city'''
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://google.com",
    "Accept-Encoding": "gzip, deflate, br"
}
    response = request('GET', url=product_url, headers=headers)
    soup_engine = BeautifulSoup(response.text, 'html.parser')
    print(soup_engine.text)
    try:
        price_element = soup_engine.find("div", class_="card__info-price-text").text.strip()
    except:
        price_element = soup_engine.find("div", class_="card__info-price-text card__info-price-text--new").text.strip()
    # price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element.split()))))
    print('зашел')
    print(price_element)
    return
    name = soup_engine.find("div", class_="detail__info-wrapper") #.split('\n')[0].strip()
    name = ' '.join(list(name.stripped_strings)) #переделанный в строку генератор отредактированных строк
    name = re.search(pattern=r'(.+?) Цвет', string=name).group(1)
    return {'price_element': price_element, 'name': name, 'shop': 'lady & gentleman city'}



def get_product_ozon(product_url): #блокает
    ...



def get_product_sportmaster(product_url): #блокает
    headers = {"User-Agent": "Mozilla/5.0"}
    response = request('GET', url=product_url, headers=headers)
    print(response.text)



shop_to_func = {'brandshop': get_product_brandshop, 
                'rendez-vous': get_product_rendez_vous, 
                'tsum': get_product_tsum, 
                'lamoda': get_product_lamoda, 
                'street-beat': get_product_street_beat,
                'ozon': get_product_ozon,
                'sportmaster': get_product_sportmaster,
                'superstep': get_product_superstep,
                'lgcity': get_product_lgcity,
                'lacoste': get_product_lacoste}





# ненужная регулярка для вычленения цены, тк bs4 сам это делает при переводе .text
# price_digger = re.search(pattern=r'[\d ]+ ₽', string='''<div class="product-order__price_new">
#     3 450 ₽
#   </div>''')
# print(price_digger.group(0).strip())

