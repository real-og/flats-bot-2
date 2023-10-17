import requests
import logging
import time
from ad import Ad
from src.shared.subway_map import get_closest_subway
from src.shared.logic import get_city_by_cords
from collections import deque


error_timeout = 15
regular_timeout = 10

onliner_url = "https://r.onliner.by/sdapi/ak.api/search/apartments"
onliner_params = {'bounds[lb][lat]': '45.41737821965764',
                'bounds[lb][long]': '19.53972860486743',
                'bounds[rt][lat]': '56.686967637946275',
                'bounds[rt][long]': '32.15970564951255',
                'order': 'created_at:desc',
                'page': '1',
                'v': '0.2754033164126508'}


def init_used_ids_onliner():
    init_ids = [0 for i in range(10)] #to keep used_ids in collection bigger then amount of received ads
    response = requests.get(onliner_url, onliner_params)
    try:
        onliner_ads = response.json().get('apartments', [])
    except:
        onliner_ads = []
        logging.error(f"Не удалось получить словарь при инициализации ОНЛАЙНЕР\n{response[:100]}")
    if len(onliner_ads) == 0:
        logging.warning('Онлайнер проблема с запросом инициализации')
    for onliner_ad in onliner_ads:
        init_ids.append(onliner_ad.get('id'))
    init_ids.reverse()
    return init_ids


def generate_ad_from_onliner(onliner_ad: dict):
    
    photos = []
    if onliner_ad.get('photo'):
        photos.append(onliner_ad.get('photo'))
    cost = onliner_ad.get('price', dict()).get('amount')
    landlord = onliner_ad.get('contact', dict()).get('owner')
    if landlord == True:
        landlord = 'Собственник'
    elif landlord == False:
        landlord = 'Агентство'
    lat = onliner_ad.get('location', dict()).get('latitude')
    lon = onliner_ad.get('location', dict()).get('longitude')
    town = get_city_by_cords(lat, lon)
    
    rooms_amount = onliner_ad.get('rent_type')
    if rooms_amount == 'room':
        rooms_amount = 'Комната'
    elif rooms_amount is not None:
        rooms_amount = rooms_amount[0]

    link = onliner_ad.get('url')
    source = 'onliner'
    subway = get_closest_subway(lat, lon)
    subway_dist = None
    subway_name = None
    if subway:
        subway_dist = subway.distance_to(lat, lon)
        subway_name = subway.name
        
    return Ad(town, photos, cost, landlord, lat, lon, rooms_amount, link, source, subway_name, subway_dist)
    


def poll_onliner():
    onliner_used_ids = deque(init_used_ids_onliner())

    while True:
        try:
            response = requests.get(onliner_url, onliner_params)
        except:
            logging.error("ОЛАЙНЕР ошибка во время запроса")
            time.sleep(error_timeout)
            continue

        if response.status_code != 200:
            logging.warning(f'Ответ ОНЛАЙНЕРА не 200, первые 100 символов:\n{response.text[:100]}')
            time.sleep(error_timeout)
            continue
        try:
            onliner_ads = response.json().get('apartments')

            if onliner_ads is None or len(onliner_ads) == 0:
                logging.warning(f'ОНЛАЙНЕР не вернул объявления:\n{onliner_ads[:100]}')
                continue
            
            for onliner_ad in onliner_ads:
                ad_id = onliner_ad.get('id')

                if ad_id is None:
                    logging.warning(f'ОНЛАЙНЕР объявление не имеет id:\n{onliner_ad}')

                if ad_id not in onliner_used_ids:
                    onliner_used_ids.append(ad_id)
                    onliner_used_ids.popleft()
                    ad = generate_ad_from_onliner(onliner_ad)
                    ad.save()
                    ad.broadcast()

        except:
            logging.exception('ОНЛАЙНЕР попытка взять JSON ответа не удалась')

        finally:
            time.sleep(regular_timeout)
