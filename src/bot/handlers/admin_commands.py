from loader import dp, ADMIN_ID
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher import filters



@dp.message_handler(filters.IDFilter(chat_id=[ADMIN_ID]),commands=["get_ads"], state="*", )
async def send_welcome(message: types.Message, state: FSMContext):
    with open('src/service/ads.csv', 'rb') as file:
        await message.answer_document(file, caption='Отчет квартир')


@dp.message_handler(filters.IDFilter(chat_id=[ADMIN_ID]),commands=["get_errors"], state="*", )
async def send_welcome(message: types.Message, state: FSMContext):
    with open('src/service/errors.log', 'rb') as file:
        await message.answer_document(file, caption='Отчет ошибок')