from aiogram import Bot
import os
import requests


BOT_TOKEN = str(os.environ.get("BOT_TOKEN"))
ADMIN_ID = str(os.environ.get("ADMIN_ID"))

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")

def send_document(filename, chat_id):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendDocument'
    data = {'chat_id': chat_id, 'caption': 'Результат куфара'}
    with open(filename, 'rb') as f:
        files = {'document': f}
        response = requests.post(url, data=data, files=files)
        print(response.text)

send_document('service/ads.csv', ADMIN_ID)
         