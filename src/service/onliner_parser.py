import requests
import logging
import time
from ad import Ad
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
    init_ids = []
    response = requests.get(onliner_url, onliner_params)
    onliner_ads = response.json().get('apartments')
    for onliner_ad in onliner_ads:
        init_ids.append(onliner_ad.get('id'))
    init_ids.reverse()
    return init_ids


def generate_ad_from_onliner(onliner_ad: dict):
    source = 'onliner'
    cost = onliner_ad['price']['amount']
    town = onliner_ad['location']['address']
    link = onliner_ad['url']
    return Ad(town, cost, link, source)
    


def poll_onliner():
    onliner_used_ids = deque(init_used_ids_onliner())

    while True:
        response = requests.get(onliner_url, onliner_params)

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
