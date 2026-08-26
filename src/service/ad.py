import datetime
import csv
import asyncio
import traceback
import logging
import requests
import time
from aiogram import types
from typing import List
from dataclasses import dataclass
from src.shared.db import get_active_users
from src.shared.logic import is_comparable
import os

BOT_TOKEN = str(os.environ.get("BOT_TOKEN"))


def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    params = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, params=params)
        response.raise_for_status() 

    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 429:
            retry_after = 1 
            time.sleep(retry_after)  
            send_telegram_message(token, chat_id, message)
        else:
            logging.error('ошибка тг бродкаст', exc_info=True)
    except Exception as err:
        logging.error('необычная ошибка тг бродкаст', exc_info=True)


def send_telegram_photo(token, chat_id, photo_url, caption=None):
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    params = {
        'chat_id': chat_id,
        'photo': photo_url,
        'parse_mode': 'HTML'
    }
    if caption:
        params['caption'] = caption  
    try:
        response = requests.post(url, params=params)
        response.raise_for_status()  
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 429:
            retry_after = 1 
            time.sleep(retry_after)  
            send_telegram_photo(token, chat_id, photo_url, caption=None)
        else:
            logging.error('ошибка тг бродкаст', exc_info=True)
    except Exception as err:
        logging.error('необычная ошибка тг бродкаст', exc_info=True)


def send_telegram_media_group(token, chat_id, media_files, caption=None):
    url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
    media = []
    for file_url in media_files:
        media_item = {'type': 'photo', 'media': file_url}
        if not media:
            media_item['caption'] = caption
            media_item['parse_mode'] = 'HTML'
        media.append(media_item)
    params = {
        'chat_id': chat_id,
        'media': media,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, json=params)
        response.raise_for_status() 
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 429:
            retry_after = 1 
            time.sleep(retry_after)  
            send_telegram_media_group(token, chat_id, media_files, caption=None)
        else:
            logging.error('ошибка тг бродкаст', exc_info=True)
    except Exception as err:
        logging.error('необычная ошибка тг бродкаст', exc_info=True)




@dataclass
class Ad:
    town: str
    photos: List[str]
    cost: float
    landlord: str
    latitude: float
    longitude: float
    rooms_amount: int
    link: str
    source: str
    subway_name: str
    subway_dist: int
    author_name: str

    def save(self):
        data_to_write = [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                         self.source,
                         self.town,
                         self.cost,
                         self.landlord,
                         self.latitude,
                         self.longitude,
                         self.rooms_amount,
                         self.link,
                         self.subway_name,
                         self.subway_dist,
                         self.author_name
                         ]
        with open('src/service/ads.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(data_to_write)

    def create_telegram_mediagroup(self, caption):
        media = types.MediaGroup()
        media.attach_photo(self.photos[0], caption, parse_mode='HTML')    
        for photo_url in self.photos[1:]:
            media.attach_photo(photo_url)
        return media

    def create_telegram_caption(self):
        text = f"""<b>Комнат: </b> {self.rooms_amount}
<b>Город: </b> {self.town}
<b>Цена: </b> {self.cost} USD
<b>Сдаёт: </b>{self.landlord}
🚇 {self.subway_name}, {self.subway_dist}м
<b>Источник: </b>{self.source}
\n<a href="{self.link}">Ссылка</a>
<b>Автор: </b> {self.author_name}"""
        return text

    def broadcast(self):
        """sends current ad to all users with suitable filters from postgres"""

        active_users = get_active_users()
        text = self.create_telegram_caption()
        photos = self.photos

        for user in active_users:
            if is_comparable(user['params'], self):
                user_id = user['id_tg']

                if len(photos) == 0:
                    send_telegram_message(BOT_TOKEN, user_id, text)
                elif len(photos) == 1:
                    send_telegram_photo(BOT_TOKEN, user_id, photos[0], text)
                elif len(photos) > 1:
                    send_telegram_media_group(BOT_TOKEN, user_id, photos, text)
                time.sleep(0.5) 


        
