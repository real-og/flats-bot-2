import requests
import logging
import time
from ad import Ad
from src.shared.subway_map import get_closest_subway
from collections import deque


error_timeout = 15
regular_timeout = 10

kufar_url = "https://api.kufar.by/search-api/v1/search/rendered-paginated"
kufar_params = {'cat': '1010',
                'cur': 'BYR',
                'gtsy': 'country-belarus',
                'lang': 'ru',
                'rnt': '1',
                'size': '30',
                'typ': 'let'}


def init_used_ids_kufar():
    init_ids = []
    response = requests.get(kufar_url, kufar_params)
    try:
        kufar_ads = response.json().get('ads', [])
    except:
        kufar_ads = []
        logging.error(f"Не удалось получить словарь при инициализации КУФАРА\n{response[:100]}")
    if len(kufar_ads) == 0:
        logging.warning('Куфар проблема с запросом инициализации')
    for kufar_ad in kufar_ads:
        init_ids.append(kufar_ad.get('ad_id'))
    init_ids.reverse()
    return init_ids


def generate_ad_from_kufar(kufar_ad: dict):

    ad_params = kufar_ad.get('ad_parameters', [])
    rooms_amount = None
    town = None
    lat = None
    lon = None
    for param in ad_params:
        if param.get('pl') == 'Область' and  param.get('vl') == 'Минск':
            town = 'Минск'
        if param.get('pl') == 'Город / Район' and (town != 'Минск'):
            town = param.get('vl')
        if param.get('p') == 'coordinates':
            lon = param.get('v')[0]
            lat = param.get('v')[1]
        if param.get('p') == 'rooms':
            rooms_amount = param.get('v')

    subway = get_closest_subway(lat, lon)
    subway_dist = None
    subway_name = None
    if subway:
        subway_dist = subway.distance_to(lat, lon)
        subway_name = subway.name

    source = 'kufar'
    link = kufar_ad.get('ad_link')
    cost = str(kufar_ad.get('price_usd'))
    if cost and '.' not in cost:
        cost = f"{cost[:-2]}.{cost[-2:]}"
    
    if kufar_ad.get('company_ad') == True:
        landlord = 'Агентство'
    elif kufar_ad.get('company_ad') == False:
        landlord = 'Собственник'
    else:
        landlord = None

    image_urls = []
    for img in kufar_ad['images'][:9]:
        image_urls.append(f"https://rms4.kufar.by/v1/gallery/{img['path']}")

    return Ad(town, image_urls, cost, landlord, lat, lon, rooms_amount, link, source, subway_name, subway_dist)
    

def poll_kufar():

    kufar_used_ids = deque(init_used_ids_kufar())

    while True:
        kufar_params['size'] = 15
        try:
            response = requests.get(kufar_url, kufar_params)
        except:
            logging.error("КУФАР ошибка во время запроса")
            time.sleep(error_timeout)
            continue

        if response.status_code != 200:
            logging.warning(f'Ответ КУФАРА не 200, первые 100 символов:\n{response.text[:100]}')
            time.sleep(error_timeout)
            continue
        try:
            kufar_ads = response.json().get('ads')

            if kufar_ads is None or len(kufar_ads) == 0:
                logging.warning(f'КУФАР не вернул объявления:\n{kufar_ads[:100]}')
                continue
            
            for kufar_ad in kufar_ads:
                ad_id = kufar_ad.get('ad_id')

                if ad_id is None:
                    logging.warning(f'КУФАР объявление не имеет id:\n{kufar_ad}')

                if ad_id not in kufar_used_ids:
                    kufar_used_ids.append(ad_id)
                    kufar_used_ids.popleft()
                    ad = generate_ad_from_kufar(kufar_ad)
                    ad.save()
                    ad.broadcast()

        except:
            logging.exception('КУФАР попытка взять JSON ответа')

        finally:
            time.sleep(regular_timeout)

