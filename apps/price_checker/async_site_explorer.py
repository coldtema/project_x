from functools import wraps
import time
from requests import request
from bs4 import BeautifulSoup
import re
import json
import httpx
import traceback
import asyncio

class Parser:

    def __init__(self):
        self.client = httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, limits=httpx.Limits(max_connections=200, max_keepalive_connections=200), timeout=httpx.Timeout(10.0, connect=9.0))

    def get_shop_of_product(self, product_url):
        '''Функция, определяющая, какому магазину принадлежит ссылка'''
        regex = r'://(www\.)?(ru\.)?(mytishchi\.)?(moscow\.)?(msk\.)?(moskva\.)?(outlet\.)?(shop\.)?([\w-]+)\.(\w+)/'
        return self.shop_to_func.get(re.search(pattern=regex, string=product_url).group(9).strip())
    

    def exc_returner(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                return args
        return wrapper

        
        
    @exc_returner
    async def get_product_brandshop(self, product_url):
        '''Функция для парсинга товара из brandshop'a'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        try:
            price_element = soup_engine.find("div", class_="product-order__price_new").text.strip()
        except:
            price_element = soup_engine.find("div", class_="product-order__price-wrapper").text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element.split())))) #добавление только цифр в поле price
        brand = soup_engine.find("div", class_="product-page__header font font_title-l").text.strip()
        category, model = map(lambda x: x.text.strip(), soup_engine.find_all("div", class_="product-page__subheader font font_m font_grey")) #модель не добавляю
        return {'price_element': price_element, 'name': brand + ' ' + category, 'shop': 'brandshop',}



    @exc_returner
    async def get_product_superstep(self, product_url):
        '''Функция для парсинга товара из superstep'a'''
        response = await self.client.get(product_url)
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
        return {'price_element': price_element, 'name': name, 'shop': 'superstep',}



    @exc_returner
    async def get_product_rendez_vous(self, product_url):
        '''Функция для парсинга товара из rendez-vous'''
        response = await self.client.get(product_url)
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
        return {'price_element': price_element, 'name': brand + ' ' + category, 'shop': 'rendez-vous'}



    @exc_returner
    async def get_product_tsum_outlet(self, product_url):
        '''Функция для парсинга товара из tsum_outlet'a'''
        response = await self.client.get(product_url)
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
        return {'price_element': int(str(price_element)), 'name': name, 'shop': 'tsum-outlet'}




    @exc_returner
    async def get_product_tsum(self, product_url):
        '''Функция для парсинга товара из tsum'a'''
        if 'outlet' in product_url:
            return await self.get_product_tsum_outlet(product_url)

        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find("p", class_=re.compile(r'Price__price___\w+')).text.strip()
        price_element = price_element.split('₽')
        if price_element[1]:
            price_element = price_element[1]
        else:
            price_element = price_element[0]
        brand = soup_engine.find("span", class_=re.compile(r'Properties__text___\w+')).text.strip()
        category = soup_engine.find("h1", class_=re.compile(r'Description__productName___\w+')).text.strip()
        category = re.search(pattern=r'[А-Я].+', string=category).group(0)
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element.split()))))
        return {'price_element': int(str(price_element)), 'name': brand + ' ' + category, 'shop': 'tsum'}



    @exc_returner
    async def get_product_street_beat(self, product_url):
        '''Функция для парсинга товара из street beat'''
        response = await self.client.get(product_url)
        digital_data_dict = re.search(r'window\.digitalData\s*=\s*(\{.*?\});', response.text)
        json_data = json.loads(digital_data_dict.group(1))
        name = json_data['product']['name']
        price_element = json_data['product']['unitPrice']
        return {'price_element': price_element, 'name': name, 'shop': 'street-beat'}


    @exc_returner
    async def get_product_lacoste(self, product_url):
        '''Функция для парсинга товара из lacoste'a'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find("div", class_="nl-product-price nl-product-configuration__price").text.strip().split('₽')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element.split()))))
        name = soup_engine.find("h4", class_="nl-product-configuration__title").text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'lacoste'}



    @exc_returner
    async def get_product_sv77(self, product_url):
        '''Функция для парсинга товара из sv77'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find("button", class_="button button-bordered items-center button-rect w-100 db fade button-hover-black").text.strip().split('руб.')
        if price_element[1] != '':
            price_element = price_element[1]
        else:
            price_element = price_element[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element.split()))))
        name = soup_engine.find("h1", class_="product-view-title uppercase").text.strip()
        name = ' '.join(name.split('\n'))
        return {'price_element': price_element, 'name': name, 'shop': 'sv77'}



    @exc_returner
    async def get_product_elyts(self, product_url):
        '''Функция для парсинга товара из elyts'a'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find("div", class_="final-price-block").text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element.split()))))
        name = soup_engine.find("h1").text
        return {'price_element': price_element, 'name': name, 'shop': 'elyts'}



    @exc_returner
    async def get_product_vipavenue(self, product_url):
        '''Функция для парсинга товара из vipavenue'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find("div", class_="product__card--price-actual").text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element.split()))))
        name = soup_engine.find("div", class_="product__card--title").text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'vipavenue'}



    @exc_returner
    async def get_product_aimclo(self, product_url):
        '''Функция для парсинга товара из aimclo'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        try:
            price_element = soup_engine.find("div", class_="product-information__price js-element-price").text.strip()
        except:
            price_element = soup_engine.find("div", class_="product-information__price product-information__sale js-element-price").text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find("h1", class_="product-information__title").text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'aimclo'}



    @exc_returner
    async def get_product_befree(self, product_url):
        '''Функция для парсинга товара из befree'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find("div", class_=re.compile(r'.+(digi-product-price)')).text.strip()
        price_element = price_element.split('₽')[0]
        name = soup_engine.find("span", class_=re.compile(r'.+( title)')).text.strip()
        return {'price_element': int(price_element), 'name': name, 'shop': 'befree'}


    @exc_returner
    async def get_product_loverepublic(self, product_url):
        '''Функция для парсинга товара из love republic'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find("div", class_='item-prices').text.strip()
        price_element = price_element.split('₽')
        if price_element[1]:
            price_element = price_element[1].split('%')[1]
        else:
            price_element = price_element[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find("h1", class_='catalog-element__title').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'love republic'}



    @exc_returner
    async def get_product_youstore(self, product_url):
        '''Функция для парсинга товара из youstore'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find("div", class_='product-view-price').text.strip()
        price_element = price_element.split('₽')[0].strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find("h1").text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'youstore'}



    @exc_returner
    async def get_product_gate31(self, product_url): #вообще не увидел раздел скидок
        '''Функция для парсинга товара из gate31'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find("div", class_='product-price__default').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find("div", class_='ProductPage__title').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'gate31'}



    @exc_returner
    async def get_product_incanto(self, product_url):
        '''Функция для парсинга товара из incanto'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        full = soup_engine.find("title").text.strip()
        price_element = re.search(pattern=r'(цене )(.+?)( ₽)', string=full).group(2)
        name = re.search(pattern=r'(.+)( Incanto)', string=full).group(1)
        return {'price_element': int(float(price_element)), 'name': name, 'shop': 'incanto'}



    @exc_returner
    async def get_product_sportcourt(self, product_url):
        '''Функция для парсинга товара из sportcourt'''
        response = await self.client.get(product_url)
        #response.encoding = response.apparent_encoding #свойство, которое угадывает кодировку на основе содержимого
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find("div", class_='p_price').text.strip()
        if price_element.split('₽')[1]:
            price_element = price_element.split('₽')[1]
        else:
            price_element = price_element.split('₽')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find("div", class_='model_name').text.strip()
        return {'price_element': int(float(price_element)), 'name': name, 'shop': 'sportcourt'}




    @exc_returner
    async def get_product_1811stores(self, product_url):
        '''Функция для парсинга товара из 1811stores'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        full = soup_engine.find("title").text.strip()
        price_element = re.search(pattern=r'(за )(.+?)( руб.)', string=full).group(2)
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = re.search(pattern=r'(.+?)( купить)', string=full).group(1)
        return {'price_element': int(float(price_element)), 'name': name, 'shop': '1811stores'}



    @exc_returner
    async def get_product_bask(self, product_url):
        '''Функция для парсинга товара из bask'''
        response = await self.client.get(product_url)
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
        return {'price_element': int(float(price_element)), 'name': name, 'shop': 'bask'}



    @exc_returner
    async def get_product_noone(self, product_url):
        '''Функция для парсинга товара из noone'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find("div", class_='item-price').text.strip()
        price_element = price_element.split('RUB')[0].strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find("title").text.strip()
        name = re.search(pattern=r'(.+?)( купить)', string=name).group(1)
        return {'price_element': price_element, 'name': name, 'shop': 'noone'}


    @exc_returner
    async def get_product_elis(self, product_url):
        '''Функция для парсинга товара из elis'''
        response = await self.client.get(product_url) #httpx.get(url=product_url, headers=self.headers, verify=False) #пока выключил проверку SSL-сертификатов - что-то с ними случилось
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find("span", class_='price').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find("h1", class_='item-detail__title').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'elis'}



    @exc_returner
    async def get_product_afinabags(self, product_url):
        '''Функция для парсинга товара из afinabags'''
        response = await self.client.get(product_url)
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
        return {'price_element': price_element, 'name': name, 'shop': 'afinabags'}



    @exc_returner
    async def get_product_crockid(self, product_url):
        '''Функция для парсинга товара из crockid'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find("div", class_=re.compile(r'(cost)(.+)?')).text.strip()
        price_element = price_element.split('р.')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find("h1", class_='name').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'crockid'}



    @exc_returner
    async def get_product_bungly(self, product_url):
        '''Функция для парсинга товара из bungly'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find("div", class_='price-first-load').text.strip().split('руб.')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find("div", class_='product-title').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'bungly'}



    @exc_returner
    async def get_product_aupontrouge(self, product_url):
        '''Функция для парсинга товара из aupontrouge'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find("div", class_='product-price').text.strip()
        price_element = price_element.split('₽')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find("title").text.strip()
        name = re.search(pattern=r'(.+?)( купить)', string=name).group(1)
        return {'price_element': price_element, 'name': name, 'shop': 'aupontrouge'}



    @exc_returner
    async def get_product_sohoshop(self, product_url):
        '''Функция для парсинга товара из sohoshop'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find("div", class_='prices_block').text.strip()
        price_element = price_element.split('руб')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find("div", class_='topic__inner').text.strip()
        name = name.split('\n')[-1]
        return {'price_element': price_element, 'name': name, 'shop': 'sohoshop'}



    @exc_returner
    async def get_product_lichi(self, product_url):
        '''Функция для парсинга товара из lichi'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find("div", class_=re.compile(r'(product-content_price_box__).+')).text.strip()
        price_element = price_element.split('₽')
        if price_element[2]:
            price_element = price_element[1]
        else:
            price_element=price_element[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find("h1").text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'lichi'}



    @exc_returner
    async def get_product_askent(self, product_url):
        '''Функция для парсинга товара из askent'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find("div", class_='product__currentPrice').text.strip()
        price_element = price_element.split('₽')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find("div", class_='productName').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'askent'}



    @exc_returner
    async def get_product_darsi(self, product_url):
        '''Функция для парсинга товара из darsi'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        full = soup_engine.find("title").text.strip()
        price_element = re.search(pattern=r'(цене )(.+?)( руб)', string=full).group(2)
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = re.search(pattern=r'(.+?)( купить)', string=full).group(1)
        return {'price_element': price_element, 'name': name, 'shop': 'darsi'}



    @exc_returner
    async def get_product_cocos_moscow(self, product_url):
        '''Функция для парсинга товара из cocos-moscow'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find("div", class_='product-item-detail-price').text.strip()
        price_element = price_element.split('₽')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find("div", class_='product_card__title').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'cocos-moscow'}



    @exc_returner
    async def get_product_inspireshop(self, product_url):
        '''Функция для парсинга товара из inspireshop'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find("div", class_='product-page__item-price-container').text.strip()
        price_element = price_element.split('₽')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find("h1", class_='product-page__item-name').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'inspireshop'}



    @exc_returner
    async def get_product_respect_shoes(self, product_url):
        '''Функция для парсинга товара из respect-shoes'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find("div", class_='price-div-flex').text.strip()
        price_element = price_element.split('₽')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find("h1", class_='h1-cart').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'respect-shoes'}



    @exc_returner
    async def get_product_pompa(self, product_url):
        '''Функция для парсинга товара из pompa'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find("span", class_='current_price').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find("h1", class_='detail-item-title d-sm-block d-none').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'pompa'}



    @exc_returner
    async def get_product_bunnyhill(self, product_url):
        '''Функция для парсинга товара из bunnyhill'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find("span", class_='price price_to_change').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find("h1", class_='name js-ga-name').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'bunnyhill'}



    @exc_returner
    async def get_product_annapekun(self, product_url):
        '''Функция для парсинга товара из annapekun'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find("div", class_='catalog-item__price').text.strip()
        price_element = price_element.split('₽')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('title').text.strip()
        name = re.search(pattern=r'(.+?)( - купить)', string=name).group(1)
        return {'price_element': price_element, 'name': name, 'shop': 'annapekun'}



    @exc_returner
    async def get_product_amazingred(self, product_url):
        '''Функция для парсинга товара из amazingred'''
        response = await self.client.get(product_url)
        digital_data_dict = re.search(r'window\.digitalData\s*=\s*(\{.*?\});', response.text)
        json_data = json.loads(digital_data_dict.group(1))
        price_element = json_data['product']['unitSalePrice']
        name = json_data['product']['name']
        return {'price_element': price_element, 'name': name, 'shop': 'amazingred'}



    @exc_returner
    async def get_product_m_reason(self, product_url):
        '''Функция для парсинга товара из m-reason'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find("div", class_='price').text.strip()
        price_element = price_element.split('i')
        if price_element[1]:
            price_element = price_element[1]
        else:
            price_element = price_element[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1', class_='product-detail__title').text.strip()
        name = ' '.join(name.split())
        return {'price_element': price_element, 'name': name, 'shop': 'm-reason'}



    @exc_returner
    async def get_product_voishe(self, product_url):
        '''Функция для парсинга товара из voishe'''
        headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://www.voishe.ru/",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find("div", class_='js-product-price js-store-prod-price-val t-store__prod-popup__price-value').text.strip()
        price_element = price_element.split(',')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('title').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'voishe'}



    @exc_returner
    async def get_product_choux(self, product_url):
        '''Функция для парсинга товара из choux'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        full = soup_engine.find('title').text.strip()
        price_element = re.search(pattern=r'(цене )(.+?)( ₽)', string=full).group(2)
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = re.search(pattern=r'(.+?)( купить)', string=full).group(1)
        return {'price_element': price_element, 'name': name, 'shop': 'choux'}



    @exc_returner
    async def get_product_fablestore(self, product_url):
        '''Функция для парсинга товара из fablestore'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='product-result__price body-text').text.strip()
        price_element = price_element.split('₽')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1', class_='product-info__title').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'fablestore'}



    @exc_returner
    async def get_product_selfmade(self, product_url):
        '''Функция для парсинга товара из selfmade'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='product-price').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1', class_='product-name').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'selfmade'}



    @exc_returner
    async def get_product_kanzler_style(self, product_url):
        '''Функция для парсинга товара из kanzler-style'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='product__price-wrapper').text.strip()
        price_element = price_element.split('₽')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1', class_='product__title').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'kanzler-style'}



    @exc_returner
    async def get_product_belleyou(self, product_url):
        '''Функция для парсинга товара из belleyou'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('span', class_='current-price').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1', class_='product-desc-title').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'belleyou'}



    @exc_returner
    async def get_product_zolla(self, product_url):
        '''Функция для парсинга товара из zolla'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='catalog-detail--redesign__aside-price-current').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1', class_='catalog-detail--redesign__aside-title').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'zolla'}



    @exc_returner
    async def get_product_danielonline(self, product_url):
        '''Функция для парсинга товара из danielonline'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='item-price__value').text.strip()
        price_element = price_element.split('руб.')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'danielonline'}



    @exc_returner
    async def get_product_zarina(self, product_url):
        '''Функция для парсинга товара из zarina'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='product__price-current').text.strip()
        price_element = price_element.split('руб.')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'zarina'}



    @exc_returner
    async def get_product_alexanderbogdanov(self, product_url):
        '''Функция для парсинга товара из alexanderbogdanov'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='product-card-info__prices').text.strip()
        price_element = price_element.split('₽')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('p', class_='product-card-info__title').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'alexanderbogdanov'}



    @exc_returner
    async def get_product_werfstore(self, product_url): #не нашел скидок
        '''Функция для парсинга товара из werfstore'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('p', class_='price').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1', class_='product_title entry-title').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'werfstore'}



    @exc_returner
    async def get_product_koffer(self, product_url):
        '''Функция для парсинга товара из koffer'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='product-info__buy-block').text.strip()
        price_element = price_element.split('₽')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'koffer'}



    @exc_returner
    async def get_product_age_of_innocence(self, product_url):
        '''Функция для парсинга товара из age-of-innocence'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find_all('div', class_='v-stack')
        price_element = ''.join(list(map(lambda x: x.text.strip(), price_element)))
        price_element = re.search(pattern=r'(₽)(.+?)\,', string=price_element).group(2)
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('title').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'age-of-innocence'}



    @exc_returner
    async def get_product_nice_one(self, product_url):
        '''Функция для парсинга товара из nice-one'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='price').text.strip()
        price_element = price_element.split('руб.')
        if price_element[1]:
            price_element = price_element[1]
        else:
            price_element = price_element[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'nice-one'}



    @exc_returner
    async def get_product_alpindustria(self, product_url):
        '''Функция для парсинга товара из alpindustria'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='product__price-wrap').text.strip()
        price_element = price_element.split('руб.')
        if price_element[1]:
            price_element = price_element[1]
        else:
            price_element = price_element[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'alpindustria'}



    @exc_returner
    async def get_product_indiwd(self, product_url):
        '''Функция для парсинга товара из indiwd'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='h3 product__page-price').text.strip()
        price_element = price_element.split('₽')
        price_element = price_element[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'indiwd'}



    @exc_returner
    async def get_product_biggeek(self, product_url):
        '''Функция для парсинга товара из biggeek'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('span', class_='total-prod-price').text.strip()
        price_element = price_element.split('₽')
        price_element = price_element[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'biggeek'}



    @exc_returner
    async def get_product_tefal(self, product_url):
        '''Функция для парсинга товара из tefal'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        full = soup_engine.find('title').text.strip()
        price_element = int(float(re.search(pattern=r'(цена )(.+)( руб)', string=full).group(2)))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'tefal'}



    @exc_returner
    async def get_product_yves_rocher(self, product_url):
        '''Функция для парсинга товара из yves-rocher'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('span', class_='bold text_size_20 tab_text_size_24').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'yves-rocher'}



    @exc_returner
    async def get_product_galaxystore(self, product_url):
        '''Функция для парсинга товара из galaxystore'''
        response = await self.client.get(product_url)
        digital_data_dict = re.search(r'window\.digitalData\s*=\s*(\{.*?\});', response.text)
        json_data = json.loads(digital_data_dict.group(1))
        price_element = int(json_data['product']['unitSalePrice'])
        name = json_data['product']['name']
        return {'price_element': price_element, 'name': name, 'shop': 'galaxystore'}



    @exc_returner
    async def get_product_megafon(self, product_url):
        '''Функция для парсинга товара из megafon'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_=re.compile(r'(Price_text__).+')).text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'megafon'}



    @exc_returner
    async def get_product_ecco(self, product_url):
        '''Функция для парсинга товара из ecco'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('span', class_='price').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'ecco'}



    @exc_returner
    async def get_product_xcom_shop(self, product_url):
        '''Функция для парсинга товара из xcom-shop'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='card-content-total-price__current').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'xcom-shop'}



    @exc_returner
    async def get_product_epldiamond(self, product_url):
        '''Функция для парсинга товара из epldiamond'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('title').text.strip()
        price_element = re.search(pattern=r'(цене )(.+)( руб)', string=price_element).group(2)
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'epldiamond'}



    @exc_returner
    async def get_product_doctorslon(self, product_url):
        '''Функция для парсинга товара из doctorslon'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='product-price').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'doctorslon'}



    @exc_returner
    async def get_product_randewoo(self, product_url): #пока добавляется последний элемент, если там список ароматов, подумать, как предложить выбор
        '''Функция для парсинга товара из randewoo'''
        response = await self.client.get(product_url)
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
        return {'price_element': int(price_element), 'name': name, 'shop': 'randewoo'}



    @exc_returner
    async def get_product_babor(self, product_url):
        '''Функция для парсинга товара из babor'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='productCard-price').text.strip()
        price_element = price_element.split('₽')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'babor'}



    @exc_returner
    async def get_product_mir_kubikov(self, product_url):
        '''Функция для парсинга товара из mir-kubikov'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        try:
            price_element = soup_engine.find('p', class_='product__info__price g-h2 m-old').text.strip()
            price_element = price_element.split('\n')[0]
        except:
            price_element = soup_engine.find('p', class_='product__info__price g-h2').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('title').text.strip()
        name = re.search(pattern=r'(.+)( \- купить)', string=name).group(1)
        return {'price_element': price_element, 'name': name, 'shop': 'mir-kubikov'}



    @exc_returner
    async def get_product_bombbar(self, product_url): #может отлетать - надо давать таймаут
        '''Функция для парсинга товара из bombbar'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='price').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'bombbar'}



    @exc_returner
    async def get_product_iledebeaute(self, product_url): 
        '''Функция для парсинга товара из iledebeaute'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', itemprop='price').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'iledebeaute'}



    @exc_returner
    async def get_product_shop_polaris(self, product_url): 
        '''Функция для парсинга товара из shop-polaris'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='price d-flex').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'shop-polaris'}



    @exc_returner
    async def get_product_patchandgo(self, product_url):
        '''Функция для парсинга товара из patchandgo'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='product-page__controls__price').text.strip()
        price_element = price_element.split('р.')
        if price_element[1]:
            price_element = price_element[1].strip()
        else:
            price_element = price_element[0].strip()
        price_element = int(float(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element)))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'patchandgo'}



    @exc_returner
    async def get_product_madwave(self, product_url):
        '''Функция для парсинга товара из madwave'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find_all('span', class_='target-price')
        price_element = list(map(lambda x: x.text, price_element))[-1].strip(' .')
        price_element = int(float(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element)))))
        name = soup_engine.find('title').text.strip()
        name = re.search(pattern=r'((.+)\s\|\s(.+))\|', string=name).group(1)
        return {'price_element': price_element, 'name': name, 'shop': 'madwave'}



    @exc_returner
    async def get_product_apple_avenue(self, product_url):
        '''Функция для парсинга товара из apple-avenue'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='price font-price-large bold').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'apple-avenue'}



    @exc_returner
    async def get_product_re_store(self, product_url):
        '''Функция для парсинга товара из re-store'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        full = str(soup_engine.find('meta', attrs={'name':'description'}))
        price_element = re.search(pattern=r'(по цене )(.+)( рублей)', string=full).group(2)
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = re.search(pattern=r'(Купить )(.+)( по цене)', string=full).group(2)
        return {'price_element': price_element, 'name': name, 'shop': 're-store'}



    @exc_returner
    async def get_product_bestmebelshop(self, product_url):
        '''Функция для парсинга товара из bestmebelshop'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        full = soup_engine.find('title').text.strip()
        price_element = int(re.search(pattern=r'\- (\d+) р', string=full).group(1))
        name = re.search(pattern=r'(.+) \- \d', string=full).group(1)
        return {'price_element': price_element, 'name': name, 'shop': 'bestmebelshop'}



    @exc_returner
    async def get_product_garlyn(self, product_url):
        '''Функция для парсинга товара из garlyn'''
        response = await self.client.get(product_url)
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
        return {'price_element': price_element, 'name': name, 'shop': 'garlyn'}



    @exc_returner
    async def get_product_kuppersberg(self, product_url):
        '''Функция для парсинга товара из kuppersberg'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='prodMain__price--new').text.strip()
        name = soup_engine.find('h1').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        return {'price_element': price_element, 'name': name, 'shop': 'kuppersberg'}



    @exc_returner
    async def get_product_bosssleep(self, product_url):
        '''Функция для парсинга товара из bosssleep'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find_all('p', class_='item-header__price')
        price_element = list(map(lambda x: x.text, price_element))
        if '%' in price_element[1]:
            price_element = price_element[2]
        else:
            price_element = price_element[0]
        name = soup_engine.find('h1').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        return {'price_element': price_element, 'name': name, 'shop': 'bosssleep'}



    @exc_returner
    async def get_product_muztorg(self, product_url):
        '''Функция для парсинга товара из muztorg'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        try:
            price_element = soup_engine.find('div', class_='mt-product-price__default-value').text.strip()
        except:
            price_element = soup_engine.find('div', class_='mt-product-price__discounted-value').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'muztorg'}



    @exc_returner
    async def get_product_finn_flare(self, product_url):
        '''Функция для парсинга товара из finn-flare'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        full = soup_engine.find('title').text.strip()
        price_element = re.search(pattern=r'(цене от )(.+)( в)', string=full).group(2)
        name = re.search(pattern=r'(.+) \(', string=full).group(1)
        price_element = int(int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element)))) * 0.95) #пока у них стоит скидка при оплате онлайн
        return {'price_element': price_element, 'name': name, 'shop': 'finn-flare'}



    @exc_returner
    async def get_product_litres(self, product_url):
        '''Функция для парсинга товара из litres'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = str(soup_engine.find('meta', itemprop="price"))
        price_element = int(float(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element)))))
        name = soup_engine.find('title').text.strip()
        name = re.search(pattern=r'(.+)( \– )', string=name).group(1)
        return {'price_element': price_element, 'name': name, 'shop': 'litres'}



    @exc_returner
    async def get_product_orteka(self, product_url):
        '''Функция для парсинга товара из orteka'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        full = str(soup_engine.find('meta', attrs={'name':"description"}))
        price_element = re.search(pattern=r'(по цене )(.+)( руб.)', string=full).group(2)
        name = re.search(pattern=r'(купить )(.+)( по цене)', string=full).group(2)
        price_element = int(float(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element)))))
        return {'price_element': price_element, 'name': name, 'shop': 'orteka'}



    @exc_returner
    async def get_product_quke(self, product_url):
        '''Функция для парсинга товара из quke'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('span', class_='price__value').text
        price_element = int(float(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element)))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'quke'}



    @exc_returner
    async def get_product_leonardo(self, product_url):
        '''Функция для парсинга товара из leonardo'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        full = soup_engine.find('title').text
        price_element = re.search(pattern=r'(за )(.+)( ₽)', string=full).group(2)
        price_element = ''.join(list(filter(lambda x: True if x.isdigit() or x==',' else False, price_element)))
        price_element = int(price_element.split(',')[0])
        name = re.search(pattern=r'(.+)( купить)', string=full).group(1)
        return {'price_element': price_element, 'name': name, 'shop': 'leonardo'}



    @exc_returner
    async def get_product_beeline(self, product_url):
        '''Функция для парсинга товара из beeline'''
        response = await self.client.get(product_url)
        # response.encoding = response.apparent_encoding
        soup_engine = BeautifulSoup(response.text, 'lxml')
        full = str(soup_engine.find('meta', attrs={'name':'description'}))
        price_element = re.search(pattern=r'(цена )(.+)( руб.)', string=full).group(2)
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() or x==',' else False, price_element))))
        name = re.search(pattern=r'(купить )(.+)(\: цена)', string=full).group(2)
        return {'price_element': price_element, 'name': name, 'shop': 'beeline'}



    @exc_returner
    async def get_product_tvoydom(self, product_url):
        '''Функция для парсинга товара из tvoydom'''
        response = await self.client.get(product_url)
        # response.encoding = response.apparent_encoding
        soup_engine = BeautifulSoup(response.text, 'lxml')
        full = soup_engine.find('title').text.strip()
        price_element = re.search(pattern=r'(цене )(.+)( руб.)', string=full).group(2)
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = re.search(pattern=r'(.+)( купить)', string=full).group(1)
        return {'price_element': price_element, 'name': name, 'shop': 'tvoydom'}



    @exc_returner
    async def get_product_sela(self, product_url):
        '''Функция для парсинга товара из sela'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        full = str(soup_engine.find('meta', attrs={'name': 'Description'}))
        price_element = re.search(pattern=r'(цене )(.+?)( руб\.)', string=full).group(2)
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = re.search(pattern=r'\"(.+)(, артикул)', string=full).group(1)
        return {'price_element': price_element, 'name': name, 'shop': 'sela'}



    @exc_returner
    async def get_product_aquaphor(self, product_url):
        '''Функция для парсинга товара из aquaphor'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='price-block').text.strip()
        price_element=price_element.split('₽')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('title').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'aquaphor'}



    @exc_returner
    async def get_product_mnogomebeli(self, product_url):
        '''Функция для парсинга товара из mnogomebeli'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        full = soup_engine.find('title').text.strip()
        price_element = re.search(pattern=r'(ли )(\- )?(.+)( руб\.)', string=full).group(3)
        price_element = int(''.join(price_element.split('.')))
        name = re.search(pattern=r'(.+?)(\: )', string=full).group(1)
        return {'price_element': price_element, 'name': name, 'shop': 'mnogomebeli'}



    @exc_returner
    async def get_product_davines(self, product_url):
        '''Функция для парсинга товара из davines'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        full = str(soup_engine.find('meta', attrs={'name': 'description'}))
        price_element = re.search(pattern=r'(за\s)(.+)(\sруб)', string=full).group(2)
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = re.search(pattern=r'\"(.+)( за )', string=full).group(1)
        return {'price_element': price_element, 'name': name, 'shop': 'davines'}



    @exc_returner
    async def get_product_vsesmart(self, product_url):
        '''Функция для парсинга товара из vsesmart'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='detail__price-cost').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'vsesmart'}



    @exc_returner
    async def get_product_boobl_goom(self, product_url):
        '''Функция для парсинга товара из boobl-goom'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        full = str(soup_engine.find('meta', attrs={'name': 'description'}))
        price_element = re.search(pattern=r'(Цена )(.+)( рублей)', string=full).group(2)
        price_element = int(float(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element)))))
        name = re.search(pattern=r'(Купить )(.+)( в интернет)', string=full).group(2)
        return {'price_element': price_element, 'name': name, 'shop': 'boobl-goom'}



    @exc_returner
    async def get_product_ipiter(self, product_url):
        '''Функция для парсинга товара из ipiter'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        full = soup_engine.find('title')
        price_element = soup_engine.find('div', class_='saleprice price').text.strip()
        price_element = price_element.split('₽')[0]
        price_element = int(float(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element)))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'ipiter'}



    @exc_returner
    async def get_product_mie(self, product_url):
        '''Функция для парсинга товара из mie'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='current-price').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'mie'}



    @exc_returner
    async def get_product_evitastore(self, product_url):
        '''Функция для парсинга товара из evitastore'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='cd-price').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'evitastore'}



    @exc_returner
    async def get_product_chitai_gorod(self, product_url):
        '''Функция для парсинга товара из chitai-gorod'''
        response = await self.client.get(product_url)
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
        return {'price_element': price_element, 'name': name, 'shop': 'chitai-gorod'}



    @exc_returner
    async def get_product_bestwatch(self, product_url):
        '''Функция для парсинга товара из bestwatch'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('span', itemprop='price').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name1 = soup_engine.find('p', class_='card-model').text.strip()
        name2 = soup_engine.find('p', class_='card-name').text.strip()
        name = name2 + ' ' + name1
        return {'price_element': price_element, 'name': name, 'shop': 'bestwatch'}



    @exc_returner
    async def get_product_koleso(self, product_url):
        '''Функция для парсинга товара из koleso'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_=re.compile(r'(PriceBlock_Price__).+')).text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'koleso'}



    @exc_returner
    async def get_product_mann_ivanov_ferber(self, product_url):
        '''Функция для парсинга товара из mann-ivanov-ferber'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', attrs={'data-start-price-animation': 'priceElement'}).text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('title').text.strip()
        name = re.search(pattern=r'(.+)( — купить)', string=name).group(1)
        return {'price_element': price_element, 'name': name, 'shop': 'mann-ivanov-ferber'}



    @exc_returner
    async def get_product_cozyhome(self, product_url):
        '''Функция для парсинга товара из cozyhome'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', attrs={'data-role': 'price'}).text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'cozyhome'}



    @exc_returner
    async def get_product_christinacosmetics(self, product_url):
        '''Функция для парсинга товара из christinacosmetics'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='price-detale').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'christinacosmetics'}



    @exc_returner
    async def get_product_velosklad(self, product_url):
        '''Функция для парсинга товара из velosklad'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        name = soup_engine.find('h1').text.strip()
        price_element = str(soup_engine.find('meta', itemprop='price'))
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        return {'price_element': price_element, 'name': name, 'shop': 'velosklad'}



    @exc_returner
    async def get_product_multivarka(self, product_url):
        '''Функция для парсинга товара из multivarka'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        try:
            price_element = soup_engine.find('div', class_='product-item-price-new').text.strip()
        except:
            price_element = soup_engine.find('div', class_='product-item-price').text.strip()
        price_element = price_element.split('₽')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'multivarka'}



    @exc_returner
    async def get_product_iboxstore(self, product_url):
        '''Функция для парсинга товара из iboxstore'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='product-card__price-current').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'iboxstore'}



    @exc_returner
    async def get_product_market_sveta(self, product_url):
        '''Функция для парсинга товара из market-sveta'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='productfull-block-price').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'market-sveta'}



    @exc_returner
    async def get_product_aravia(self, product_url):
        '''Функция для парсинга товара из aravia'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='product-detail-price-block').text.strip()
        price_element = price_element.split('₽')
        if price_element[1]:
            price_element = price_element[1]
        else:
            price_element = price_element[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'aravia'}



    @exc_returner
    async def get_product_krona(self, product_url):
        '''Функция для парсинга товара из krona'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='card__price').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'krona'}



    @exc_returner
    async def get_product_tddomovoy(self, product_url):
        '''Функция для парсинга товара из tddomovoy'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('span', class_='base-product-price__main').text.strip()
        price_element = int(float(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element)))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'tddomovoy'}



    @exc_returner
    async def get_product_ansaligy(self, product_url):
        '''Функция для парсинга товара из ansaligy'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='product__price-current').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'ansaligy'}



    @exc_returner
    async def get_product_hyperauto(self, product_url):
        '''Функция для парсинга товара из hyperauto'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('span', itemprop='price').text.strip()
        price_element = price_element.split(',')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'hyperauto'}



    @exc_returner
    async def get_product_kubaninstrument(self, product_url):
        '''Функция для парсинга товара из kubaninstrument'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='product-price__std').text.strip()
        price_element = price_element.split('₽')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'kubaninstrument'}



    @exc_returner
    async def get_product_nespresso(self, product_url):
        '''Функция для парсинга товара из nespresso'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        try:
            price_element = soup_engine.find('div', class_='product_prices -hasComparePrice').text.strip()
        except:
            price_element = soup_engine.find('div', class_='product_prices').text.strip()
        price_element = price_element.split('₽')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'nespresso'}



    @exc_returner
    async def get_product_aofb(self, product_url):
        '''Функция для парсинга товара из aofb'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = str(soup_engine.find('meta', itemprop='price'))
        price_element = re.search(pattern=r'\"(.+)₽', string=price_element).group(1).strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'aofb'}



    @exc_returner
    async def get_product_yamanshop(self, product_url):
        '''Функция для парсинга товара из yamanshop'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='price-wrapper').text.strip()
        price_element = price_element.split('₽')
        if price_element[1]:
            price_element = price_element[2]
        else:
            price_element = price_element[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'yamanshop'}



    @exc_returner
    async def get_product_dvamyacha(self, product_url):
        '''Функция для парсинга товара из dvamyacha'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='elem-description-price').text.strip()
        price_element = price_element.split('₽')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('title').text.strip()
        name = re.search(pattern=r'(.+)\sв\sИ', string=name).group(1)
        return {'price_element': price_element, 'name': name, 'shop': 'dvamyacha'}



    @exc_returner
    async def get_product_ochkarik(self, product_url):
        '''Функция для парсинга товара из ochkarik'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', 'basket-info__price').text.split('₽')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = ' '.join(list(map(lambda x: x.strip(), soup_engine.find('h1').text.strip().split('\n'))))
        return {'price_element': price_element, 'name': name, 'shop': 'ochkarik'}



    @exc_returner
    async def get_product_hi_stores(self, product_url):
        '''Функция для парсинга товара из hi-stores'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='cost prices detail').text.strip()
        price_element = re.search(pattern=r'(наличными\:)(.+)\n', string=price_element).group(2)
        price_element = int(float(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element)))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'hi-stores'}



    @exc_returner
    async def get_product_fkniga(self, product_url):
        '''Функция для парсинга товара из fkniga'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='price price--ruble price--md').text.strip()
        price_element = int(float(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element)))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'fkniga'}



    @exc_returner
    async def get_product_santehnika_tut(self, product_url):
        '''Функция для парсинга товара из santehnika-tut'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        try:
            price_element = soup_engine.find('div', class_='price clubprice').text.strip()
        except:
            price_element = soup_engine.find('div', class_='price').text.strip()
        price_element = int(float(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element)))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'santehnika-tut'}



    @exc_returner
    async def get_product_wau(self, product_url):
        '''Функция для парсинга товара из wau'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'html.parser')
        price_element = soup_engine.find('div', class_='product__price-wrapper').text.strip()
        price_element = price_element.split('₽')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'wau'}



    @exc_returner
    async def get_product_skinjestique(self, product_url):
        '''Функция для парсинга товара из skinjestique'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find_all('div', class_='product-item-price price-actual')[1].text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'skinjestique'}



    @exc_returner
    async def get_product_igroray(self, product_url):
        '''Функция для парсинга товара из igroray'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('span', class_='product-info-main__price').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element))))
        name = ' '.join(list(map(lambda x: x.strip(), soup_engine.find('h1').text.strip().split('\n'))))
        return {'price_element': price_element, 'name': name, 'shop': 'igroray'}



    @exc_returner
    async def get_product_hansa(self, product_url):
        '''Функция для парсинга товара из hansa'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        full = soup_engine.find('script', attrs={'type':'application/ld+json'}).text
        price_element = re.search(pattern=r'\"price\"\: \"(.+)\.', string=full).group(1)
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'hansa'}



    @exc_returner
    async def get_product_zvet(self, product_url):
        '''Функция для парсинга товара из zvet'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('span', class_='detail-price__item current').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'zvet'}



    @exc_returner
    async def get_product_x_moda(self, product_url):
        '''Функция для парсинга товара из x-moda'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='product-b__price-new').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() or x=='.' else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'x-moda'}



    @exc_returner
    async def get_product_playtoday(self, product_url):
        '''Функция для парсинга товара из playtoday'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('span', class_='item-price__club-value').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'playtoday'}



    @exc_returner
    async def get_product_santehmoll(self, product_url):
        '''Функция для парсинга товара из santehmoll'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='pcard-info__price').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'santehmoll'}



    @exc_returner
    async def get_product_golden_line(self, product_url):
        '''Функция для парсинга товара из golden-line'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('span', itemprop='price').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = ' '.join(list(map(lambda x: x.strip(), soup_engine.find('h1').text.strip().split('\n'))))
        return {'price_element': price_element, 'name': name, 'shop': 'golden-line'}



    @exc_returner
    async def get_product_tmktools(self, product_url):
        '''Функция для парсинга товара из tmktools'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = re.search(pattern=r'(\<meta itemprop\=\"price\")\s(content\=\"(.+))\"\>', string=response.text).group(3)
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = ' '.join(list(map(lambda x: x.strip(), soup_engine.find('h1').text.strip().split('\n'))))
        return {'price_element': price_element, 'name': name, 'shop': 'tmktools'}



    @exc_returner
    async def get_product_ochkov(self, product_url):
        '''Функция для парсинга товара из ochkov'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='nfe_single-product__price').text.strip()
        price_element = price_element.split('руб.')
        if price_element[1]:
            price_element = price_element[1]
        else:
            price_element = price_element[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = ' '.join(list(map(lambda x: x.strip(), soup_engine.find('h1').text.strip().split('\n'))))
        return {'price_element': price_element, 'name': name, 'shop': 'ochkov'}



    @exc_returner
    async def get_product_svetlux(self, product_url):
        '''Функция для парсинга товара из svetlux'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='catalog-item-price-cur').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = ' '.join(list(map(lambda x: x.strip(), soup_engine.find('h1').text.strip().split('\n'))))
        return {'price_element': price_element, 'name': name, 'shop': 'svetlux'}



    @exc_returner
    async def get_product_divanboss(self, product_url):
        '''Функция для парсинга товара из divanboss'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find_all('p', class_='item-header__price')
        price_element = list(map(lambda x: x.text, price_element))
        if '%' in price_element[1]:
            price_element = price_element[2]
        else:
            price_element = price_element[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = ' '.join(list(map(lambda x: x.strip(), soup_engine.find('h1').text.strip().split('\n'))))
        return {'price_element': price_element, 'name': name, 'shop': 'divanboss'}



    @exc_returner
    async def get_product_postel_deluxe(self, product_url):
        '''Функция для парсинга товара из postel-deluxe'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'html.parser')
        price_element = str(soup_engine.find('meta', itemprop='price'))
        if price_element == 'None':
            price_element = soup_engine.find('p', class_='special-price').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = ' '.join(list(map(lambda x: x.strip(), soup_engine.find('h1').text.strip().split('\n'))))
        return {'price_element': price_element, 'name': name, 'shop': 'postel-deluxe'}



    @exc_returner
    async def get_product_dushevoi(self, product_url):
        '''Функция для парсинга товара из dushevoi'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'html.parser')
        price_element = str(soup_engine.find('meta', itemprop='price'))
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = ' '.join(list(map(lambda x: x.strip(), soup_engine.find('h1').text.strip().split('\n'))))
        return {'price_element': price_element, 'name': name, 'shop': 'dushevoi'}



    @exc_returner
    async def get_product_tastycoffee(self, product_url):
        '''Функция для парсинга товара из tastycoffee'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'html.parser')
        price_element = str(soup_engine.find('meta', itemprop='price'))
        price_element = re.search(pattern=r'(content)(.+?)\s', string=price_element).group(2)
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = ' '.join(list(map(lambda x: x.strip(), soup_engine.find('h1').text.strip().split('\n'))))
        return {'price_element': price_element, 'name': name, 'shop': 'tastycoffee'}



    @exc_returner
    async def get_product_eurodom(self, product_url):
        '''Функция для парсинга товара из eurodom'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'html.parser')
        price_element = soup_engine.find('div', class_='product-detail__main-info-prices-actual font-weight-bold').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'eurodom'}



    @exc_returner
    async def get_product_happylook(self, product_url):
        '''Функция для парсинга товара из happylook'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'html.parser')
        try:
            price_element = soup_engine.find('div', class_='product-detail__price js-product-detail__price').text.strip()
        except:
            price_element = soup_engine.find('div', class_='actual-price product-detail__price js-price-id').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'happylook'}




    @exc_returner
    async def get_product_consul_coton(self, product_url):
        '''Функция для парсинга товара из consul-coton'''
        response = await self.client.get(product_url)
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
        return {'price_element': price_element, 'name': name, 'shop': 'consul-coton'}





    @exc_returner
    async def get_product_audiomania(self, product_url):
        '''Функция для парсинга товара из audiomania'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'html.parser')
        try:
            price_element = soup_engine.find('span', class_='price-v3 price-sale').text
        except:
            price_element = soup_engine.find('span', class_='price-v3').text
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = ' '.join(list(map(lambda x: x.strip(), soup_engine.find('h1').text.strip().split('\n'))))
        return {'price_element': price_element, 'name': name, 'shop': 'audiomania'}




    @exc_returner
    async def get_product_planeta_sport(self, product_url):
        '''Функция для парсинга товара из planeta-sport'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'html.parser')
        price_element = soup_engine.find('span', class_='price_value').text.split()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text
        return {'price_element': price_element, 'name': name, 'shop': 'planeta-sport'}




    @exc_returner
    async def get_product_krups(self, product_url):
        '''Функция для парсинга товара из krups'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'html.parser')
        full = soup_engine.find('title').text
        price_element = re.search(pattern=r'(выгодной цене )(.+?)( в магазине)', string=full).group(2)
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'krups'}




    @exc_returner
    async def get_product_rocky_shop(self, product_url):
        '''Функция для парсинга товара из rocky-shop'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'html.parser')
        price_element = re.search(pattern=r'\<meta\sitemprop\=\"price\" content\=\"(\d+)', string=response.text).group(1)
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'rocky-shop'}




    @exc_returner
    async def get_product_aromacode(self, product_url):
        '''Функция для парсинга товара из aromacode'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find_all('span', class_='price prices-price prices-price-regular active')
        price_element = list(map(lambda x: int(x.text), price_element))
        name = soup_engine.find_all('span', class_='sku-name')
        name = list(map(lambda x: x.text.strip(), name))
        dict_prices = dict(zip(name, price_element))
        name = tuple(dict_prices.keys())[-1]
        price_element = tuple(dict_prices.values())[-1]
        return {'price_element': price_element, 'name': name, 'shop': 'aromacode'}




    @exc_returner
    async def get_product_kosmetika_proff(self, product_url):
        '''Функция для парсинга товара из kosmetika-proff'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('span', class_='svg-currency').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'kosmetika-proff'}




    @exc_returner
    async def get_product_clever_media(self, product_url):
        '''Функция для парсинга товара из clever-media'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'html.parser')
        price_element = soup_engine.find('span', class_='product__price-cur').text
        price_element = re.findall(pattern=r'(\"price\"\:)(.+)', string=response.text)[0][1]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'clever-media'}




    @exc_returner
    async def get_product_elemis(self, product_url):
        '''Функция для парсинга товара из elemis'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'html.parser')
        price_element = soup_engine.find('span', class_='new').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'elemis'}




    @exc_returner
    async def get_product_mdm_complect(self, product_url):
        '''Функция для парсинга товара из mdm-complect'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'html.parser')
        price_element = soup_engine.find('div', class_='price-main').text.strip()
        price_element = price_element.split('.')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'mdm-complect'}




    @exc_returner
    async def get_product_lu(self, product_url):
        '''Функция для парсинга товара из lu'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'html.parser')
        price_element = soup_engine.find('div', class_='card2-price__current').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'lu'}




    @exc_returner
    async def get_product_litnet(self, product_url):
        '''Функция для парсинга товара из litnet'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'html.parser')
        price_element = soup_engine.find('span', class_='ln_btn-get-text').text.strip()
        price_element = re.search(pattern=r'\s([\d\.]+)\s(RUB)', string=price_element).group(1)
        price_element = int(float(''.join(list(filter(lambda x: True if x.isdigit() or x == '.' else False, price_element)))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'litnet'}




    @exc_returner
    async def get_product_mi_shop(self, product_url):
        '''Функция для парсинга товара из mi-shop'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'html.parser')
        price_element = soup_engine.find('div', class_='b-product-info__price-new').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'mi-shop'}



    @exc_returner
    async def get_product_parfums(self, product_url):
        '''Функция для парсинга товара из parfums'''
        response = await self.client.get(product_url)
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
        return {'price_element': price_element, 'name': name, 'shop': 'parfums'}



    @exc_returner
    async def get_product_lex1(self, product_url):
        '''Функция для парсинга товара из lex1'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'html.parser')
        price_element = soup_engine.find('div', class_='item-single-product-price mb-3 price').text.strip()
        if '%' in price_element:
            price_element = re.search(pattern=r'(Текущая цена\:)\s([\d\s]+)₽', string = price_element).group(2)
        else:
            price_element = price_element.split('₽')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'lex1'}



    @exc_returner
    async def get_product_r_ulybka(self, product_url):
        '''Функция для парсинга товара из r-ulybka'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'html.parser')
        price_element = soup_engine.find('script', attrs={'type':"application/ld+json"}).text.strip()
        price_element = re.search(pattern=r'(\"price\"\:)([\d ]+)\,', string=price_element).group(2)
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'r-ulybka'}



    @exc_returner
    async def get_product_top_santehnika(self, product_url):
        '''Функция для парсинга товара из top-santehnika'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'html.parser')
        try:
            price_element = soup_engine.find('div', class_='coupon-price').text.strip()
        except:
            price_element = soup_engine.find('div', class_='product-cart__price measure-price').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'top-santehnika'}



    @exc_returner
    async def get_product_rossko(self, product_url):
        '''Функция для парсинга товара из rossko'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'html.parser')
        price_element = soup_engine.find('div', class_='price').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'rossko'}



    @exc_returner
    async def get_product_z51(self, product_url):
        '''Функция для парсинга товара из z51'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'html.parser')
        price_element = soup_engine.find('div', class_='zone__product__price__value').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'z51'}



    @exc_returner
    async def get_product_moulinex(self, product_url):
        '''Функция для парсинга товара из moulinex'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'html.parser')
        price_element = soup_engine.find('title').text.strip()
        price_element = re.search(pattern=r'(цене\s)(.+)₽', string=price_element).group(2)
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'moulinex'}



    @exc_returner
    async def get_product_krutizmi(self, product_url):
        '''Функция для парсинга товара из krutizmi'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'html.parser')
        price_element = soup_engine.find('div', class_='sidebar-card__price').text.strip()
        price_element = price_element.split('руб.')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'krutizmi'}



    @exc_returner
    async def get_product_pharmacosmetica(self, product_url):
        '''Функция для парсинга товара из pharmacosmetica'''
        response = await self.client.get(product_url)
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
        return {'price_element': price_element, 'name': name, 'shop': 'pharmacosmetica'}



    @exc_returner
    async def get_product_gamepark(self, product_url):
        '''Функция для парсинга товара из gamepark'''
        response = await self.client.get(product_url)
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
        return {'price_element': price_element, 'name': name, 'shop': 'gamepark'}



    @exc_returner
    async def get_product_domsporta(self, product_url):
        '''Функция для парсинга товара из domsporta'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'html.parser')
        price_element = soup_engine.find('div', class_='b-detail__price').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'domsporta'}



    @exc_returner
    async def get_product_lustrof(self, product_url):
        '''Функция для парсинга товара из lustrof'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'html.parser')
        price_element = soup_engine.find('div', class_='price product__price').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'lustrof'}



    @exc_returner
    async def get_product_lakestone(self, product_url):
        '''Функция для парсинга товара из lakestone'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='price').text.strip()
        price_element = price_element.split('руб.')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'lakestone'}



    @exc_returner
    async def get_product_bookvoed(self, product_url):
        '''Функция для парсинга товара из bookvoed'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='price-block-price-info__price').text.strip()
        price_element = price_element.split('₽')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('title').text.strip()
        name = re.search(pattern=r'(.+)\s\-\s(купить)', string=name).group(1)
        return {'price_element': price_element, 'name': name, 'shop': 'bookvoed'}



    @exc_returner
    async def get_product_proficosmetics(self, product_url):
        '''Функция для парсинга товара из proficosmetics'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('p', class_='new_price').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'proficosmetics'}



    @exc_returner
    async def get_product_vamvelosiped(self, product_url):
        '''Функция для парсинга товара из vamvelosiped'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        try:
            price_element = soup_engine.find_all('span', class_='price price-new')
            price_element = price_element[-1].text.strip()
        except:
            price_element = soup_engine.find('span', class_='price').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'vamvelosiped'}



    @exc_returner
    async def get_product_book24(self, product_url):
        '''Функция для парсинга товара из book24'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('span', class_='app-price product-sidebar-price__price').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'book24'}



    @exc_returner
    async def get_product_birota(self, product_url):
        '''Функция для парсинга товара из birota'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('strong', class_='price').text.strip()
        price_element = price_element.split('руб.')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'birota'}



    @exc_returner
    async def get_product_bebakids(self, product_url):
        '''Функция для парсинга товара из bebakids'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='wr_item_3_1').text.strip()
        price_element = price_element.split('₽')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'bebakids'}



    @exc_returner
    async def get_product_med_magazin(self, product_url):
        '''Функция для парсинга товара из med-magazin'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('div', class_='price-block').text.strip()
        price_element = price_element.split('₽')[0]
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'med-magazin'}



    @exc_returner
    async def get_product_iherbgroup(self, product_url):
        '''Функция для парсинга товара из iherbgroup'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find('span', class_='product__price price nowrap').text.strip()
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find('h1').text.strip()
        return {'price_element': price_element, 'name': name, 'shop': 'iherbgroup'}
























    #магазины, которые блокируют обычные requests, поэтому их нужно делать по-другому
    @exc_returner
    async def get_product_goldapple(self, product_url): #точно бан
        ...

    @exc_returner
    async def get_product_lamoda(self, product_url): #есть имя, но нет цены в тайтле
        ...

    @exc_returner
    async def get_product_lgcity(self, product_url): #точно бан
        ...

    @exc_returner
    async def get_product_ozon(self, product_url): #точно бан
        ...

    @exc_returner
    async def get_product_sportmaster(self, product_url): #точно бан
        ...

    @exc_returner
    async def get_product_2moodstore(self, product_url):
        ...

    @exc_returner
    async def get_product_ostin(self, product_url):
        ...

    @exc_returner
    async def get_product_demix(self, product_url):
        ...

    @exc_returner
    async def get_product_thomas_muenz(self, product_url):
        ...

    @exc_returner
    async def get_product_ekonika(self, product_url):
        ...

    @exc_returner
    async def get_product_studio_29(self, product_url):
        ...

    @exc_returner
    async def get_product_baon(self, product_url):
        ...

    @exc_returner
    async def get_product_presentandsimple(self, product_url):
        ...

    @exc_returner
    async def get_product_henderson(self, product_url):
        ...

    @exc_returner
    async def get_product_sokolov(self, product_url):
        ...

    @exc_returner
    async def get_product_vseinstrumenti(self, product_url): #точно бан
        ...

    @exc_returner
    async def get_product_holodilnik(self, product_url):
        ...

    @exc_returner
    async def get_product_letu(self, product_url): #точно бан
        ...

    @exc_returner
    async def get_product_petrovich(self, product_url): #точно бан
        ...

    @exc_returner
    async def get_product_shoppinglive(self, product_url): #точно бан
        ...

    @exc_returner
    async def get_product_ormatek(self, product_url): #точно бан
        ...

    @exc_returner
    async def get_product_oldi(self, product_url): #точно бан
        ...

    @exc_returner
    async def get_product_gulliver(self, product_url): #точно бан
        ...

    @exc_returner
    async def get_product_imperiatechno(self, product_url): #точно бан
        ...

    @exc_returner
    async def get_product_kikocosmetics(self, product_url): #посмотреть - вроде cloudhttpx должен обходить
        ...

    @exc_returner
    async def get_product_huawei(self, product_url):
        ...

    @exc_returner
    async def get_product_santehnika_room(self, product_url):
        ...

    @exc_returner
    async def get_product_maxidom(self, product_url):
        ...

    @exc_returner
    async def get_product_velodrive(self, product_url):
        ...

    @exc_returner
    async def get_product_stolplit(self, product_url):
        ...

    @exc_returner
    async def get_product_euro_diski(self, product_url):
        ...

    @exc_returner
    async def get_product_dvizhcom(self, product_url):
        ...

    @exc_returner
    async def get_product_bbcream(self, product_url):
        ...

    @exc_returner
    async def get_product_postmeridiem_brand(self, product_url): #цена не парсится из-за js-кода
        '''Функция для парсинга товара из postmeridiem-brand'''
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        price_element = soup_engine.find("div", class_='product-card__content-wrapper').text.strip()
        print(price_element)
        return
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        name = soup_engine.find("title").text.strip()
        name = re.search(pattern=r'(.+?)( купить)', string=name).group(1)
        return {'price_element': price_element, 'name': name, 'shop': 'postmeridiem-brand', 'category': shop_to_category['postmeridiem-brand']}

    @exc_returner
    async def get_product_askona(self, product_url): #блокает ip после 5-10 запросов
        '''Функция для парсинга товара из askona'''
        headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referrer": "https://www.askona.ru/",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }
        
        response = await self.client.get(product_url)
        soup_engine = BeautifulSoup(response.text, 'lxml')
        full = soup_engine.find('title').text.strip()
        try:
            price_element = re.search(pattern=r'(по цене от )(.+)( руб.)', string=full).group(2)
            name = re.search(pattern=r'(.+)( купить)', string=full).group(1)
        except:
            price_element = re.search(pattern=r'(цена от )(.+)', string=full).group(2)
            name = re.search(pattern=r'(Купить )(.+)( цена)', string=full).group(2)
        price_element = int(''.join(list(filter(lambda x: True if x.isdigit() else False, price_element))))
        return {'price_element': price_element, 'name': name, 'shop': 'askona'}


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
                    'iherbgroup': get_product_iherbgroup,

                    #не работают с requests
                    'goldapple': get_product_goldapple, #вообще нет
                    'lamoda': get_product_lamoda, #нашел только рекомендации
                    'sportmaster': get_product_sportmaster, #нашел апи, но банит даже с куками
                    'lgcity': get_product_lgcity, #нашел только рекомендации
                    'ozon': get_product_ozon, #нашел только персональные рекомендации, но даже там банит
                    '2moodstore': get_product_2moodstore, #не дает пройти из за токена
                    'ostin': get_product_ostin, #qrator
                    'demix': get_product_demix,
                    'thomas-muenz': get_product_thomas_muenz,
                    'postmeridiem-brand': get_product_postmeridiem_brand,
                    'ekonika':get_product_ekonika, #qrator
                    'studio-29': get_product_studio_29,
                    'baon': get_product_baon,#работает
                    'presentandsimple': get_product_presentandsimple,
                    'henderson': get_product_henderson, #работает с куками
                    'sokolov': get_product_sokolov, #qrator
                    'vseinstrumenti': get_product_vseinstrumenti,#блокает прайсы даже на клиенте
                    'holodilnik': get_product_holodilnik,
                    'letu': get_product_letu, #вроде получилось
                    'askona': get_product_askona,#есть джсон прайса, но банит аксесс даже с клиента
                    'petrovich': get_product_petrovich,#не нашел прайс, нашел апи, но там прайс 0
                    'shoppinglive': get_product_shoppinglive,
                    'ormatek': get_product_ormatek,
                    'oldi': get_product_oldi,
                    'gulliver': get_product_gulliver, #работает с куками
                    'imperiatechno': get_product_imperiatechno, #работает с куками
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
    
    async def process_all_sites(self, prods_to_go):
        tasks = []
        for product in prods_to_go:
            parser_func = eval(f'self.{self.get_shop_of_product(product.url).__name__}')
            tasks.append(parser_func(product.url))
        print(len(tasks))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Печать результатов
        return results







