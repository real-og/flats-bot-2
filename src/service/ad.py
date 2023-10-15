import datetime
import csv
import asyncio
import sys
from db import get_active_users

sys.path.append('/Users/friend/Desktop/flats-bot-2')
from src.bot.loader import bot


class Ad:
    def __init__(self,
                town: str,
                cost: int,
                link: str,
                source: str):
        self.town = town
        self.cost = cost
        self.link = link
        self.source = source

    def save(self):
        data_to_write = [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                         self.source,
                         self.town,
                         self.cost,
                         self.link,
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
                task = asyncio.create_task(send_telegram_message(user['id_tg'], self.link))
                tasks.append(task)
            await asyncio.gather(*tasks)
            s = await bot.get_session()
            await s.close()
        
        asyncio.run(send_messages())

