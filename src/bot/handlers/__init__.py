from . import source  # noqa: F401 - registers handlers
from . import commands  # noqa: F401 - registers handlers
from . import admin_commands  # noqa: F401 - registers handlers
from . import broadcast  # noqa: F401 - registers handlers
from . import cost  # noqa: F401 - registers handlers
from . import landlord  # noqa: F401 - registers handlers
from . import location  # noqa: F401 - registers handlers
from . import menu  # noqa: F401 - registers handlers
from . import rooms  # noqa: F401 - registers handlers
from . import subway  # noqa: F401 - registers handlers
from . import town  # noqa: F401 - registers handlers

from src.bot.loader import dp
from aiogram import types


@dp.message()
async def fallback(message: types.Message):
    await message.answer(
        "Используйте /start для настройки, /pause для паузы, /resume для возобновления."
    )
