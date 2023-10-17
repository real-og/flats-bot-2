from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage2
import logging
import os
import sys


logging.basicConfig(level=logging.WARNING, filename="src/service/errors.log", filemode='w',
                    format="%(asctime)s %(levelname)s %(message)s")
ADMIN_ID = str(os.environ.get("ADMIN_ID"))
BOT_TOKEN = str(os.environ.get("BOT_TOKEN"))
ROOT_PATH = str(os.environ.get("ROOT_PATH"))

sys.path.append(ROOT_PATH)

storage = RedisStorage2(db=2)
# storage = MemoryStorage()

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=storage)
