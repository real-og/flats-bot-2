import datetime
import csv
import asyncio
from typing import List
from dataclasses import dataclass
from src.shared.db import get_active_users
from src.bot.loader import bot

@dataclass
class Ad:
    town: str
    photos: List[str]
    cost: float
    landlord: str
    latitude: float
    longitude: float
    rooms_amount: float
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

    def broadcast(self):
        """sends current ad to all users with suitable filters from postgres"""

        active_users = get_active_users()

        async def send_telegram_message(user_id, message):
            """try-except for cases where users blocked the bot"""
            try:
                await bot.send_message(chat_id=user_id, text=message)
            except:
                pass

        async def send_messages():
            tasks = []
            for user in active_users:
                task = asyncio.create_task(send_telegram_message(user['id_tg'], self))
                tasks.append(task)
            await asyncio.gather(*tasks)
            s = await bot.get_session()
            await s.close()
        
        asyncio.run(send_messages())

