from loader import dp, ADMIN_ID
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher import filters
import texts


@dp.message_handler(filters.IDFilter(chat_id=[ADMIN_ID]),commands=["get_ads"], state="*", )
async def send_welcome(message: types.Message, state: FSMContext):
    await message.answer(f"{message.from_user.language_code} - {texts.your_lang}")