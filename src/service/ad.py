import datetime
import csv
import asyncio
import json
import logging
from aiogram import types
from typing import List
from dataclasses import dataclass
from src.shared.db import get_active_users
from src.shared.logic import is_comparable
from src.bot.loader import bot

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
                         self.subway_dist
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
\n<a href="{self.link}">Ссылка</a>"""
        return text


    def broadcast(self):
        """sends current ad to all users with suitable filters from postgres"""

        active_users = get_active_users()
        async def send_telegram_message(user_id, message):
            """try-except for cases where users blocked the bot"""
            try:
                if len(self.photos) == 0:
                    await bot.send_message(chat_id=user_id, text=self.create_telegram_caption(), parse_mode='HTML')
                elif len(self.photos) == 1:
                    await bot.send_photo(user_id, photo=self.photos[0], caption=self.create_telegram_caption(), parse_mode='HTML')
                else:
                    await bot.send_media_group(user_id, media=self.create_telegram_mediagroup(self.create_telegram_caption()))
            except Exception as e:
                logging.error(e)

        async def send_messages():
            tasks = []
            for user in active_users:
                if is_comparable(user['params'], self):
                    task = asyncio.create_task(send_telegram_message(user['id_tg'], self))
                    tasks.append(task)
            await asyncio.gather(*tasks)
            s = await bot.get_session()
            await s.close()
        
        asyncio.run(send_messages())

