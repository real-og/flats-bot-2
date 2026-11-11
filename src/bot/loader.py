import time
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import SimpleEventIsolation
from src.bot.storage import SQLiteStorage
from src.shared.config import required, proxy
from src.shared.observability import configure_logging

configure_logging("bot")
ADMIN_ID = int(required("ADMIN_ID"))
BOT_TOKEN = required("BOT_TOKEN")


class ObservedSession(AiohttpSession):
    last_poll_success = time.monotonic()

    async def make_request(self, bot, method, timeout=None):
        result = await super().make_request(bot, method, timeout=timeout)
        if method.__api_method__ == "getUpdates":
            self.last_poll_success = time.monotonic()
        return result


session = ObservedSession(proxy=proxy(), timeout=30)
bot = Bot(
    token=BOT_TOKEN, session=session, default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher(storage=SQLiteStorage(), events_isolation=SimpleEventIsolation())

dp.message.filter(F.chat.type == "private")
