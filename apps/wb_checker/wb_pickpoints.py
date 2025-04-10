import os
import cloudscraper


def get_coordinates(address):
    '''Берет широту и долготу через api яндекс карт'''
    url = f"https://geocode-maps.yandex.ru/v1/?"
    params = {
        "apikey": os.getenv('YANDEX_MAPS_API_KEY'),
        "geocode": address,
        "format": 'json'
    }
    scraper = cloudscraper.create_scraper()
    response = scraper.get(url, params=params)
    json_data = response.json()
    coordinates = json_data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos'].split()
    latitude = coordinates[1]
    longitude = coordinates[0]
    return latitude, longitude


def get_dest(address):
    '''Получает id широты и долготы на wb'''
    latitude, longitude = get_coordinates(address)
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f'https://user-geo-data.wildberries.ru/get-geo-info?currency=RUB&latitude={latitude}&longitude={longitude}&locale=ru&dt=1743520473&currentLocale=ru&b2bMode=false&addressType=self'
    scraper = cloudscraper.create_scraper()
    response = scraper.get(url, headers=headers)
    json_data = response.json()
    return json_data['destinations'][-1], address
