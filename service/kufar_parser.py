import requests
import logging
import time
from ad import Ad
from collections import deque


def init_used_ids_kufar():
    init_ids = []
    response = requests.get(kufar_url, kufar_params)
    kufar_ads = response.json().get('ads')
    for kufar_ad in kufar_ads:
        init_ids.append(kufar_ad.get('ad_id'))
    init_ids.reverse()
    return init_ids


def generate_ad_from_kufar(kufar_ad: dict):
    source = 'kufar'
    link = kufar_ad.get('ad_link')
    cost = kufar_ad.get('price_usd')

    ad_params = kufar_ad.get('ad_parameters')
    town = None
    for param in ad_params:
        if param.get('pl') == 'Город / Район':
            town = param.get('vl')
    return Ad(town, cost, link, source)
    

logging.basicConfig(level=logging.WARNING, filename="service/errors.log", filemode='w',
                    format="%(asctime)s %(levelname)s %(message)s")

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

kufar_used_ids = deque(init_used_ids_kufar())

while True:
    response = requests.get(kufar_url, kufar_params)

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

    except:
        logging.exception('КУФАР попытка взять JSON ответа')

    finally:
        time.sleep(regular_timeout)
