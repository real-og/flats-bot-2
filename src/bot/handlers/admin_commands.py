from loader import dp, ADMIN_ID
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher import filters
from src.analytics.user_analyzer import write_users_csv
from src.analytics.flats_analyzer import analyze_minsk_advertisements


@dp.message_handler(filters.IDFilter(chat_id=[ADMIN_ID]), commands=["get_ads"], state="*", )
async def send_ads(message: types.Message, state: FSMContext):
    with open('src/service/ads.csv', 'rb') as file:
        await message.answer_document(file, caption='Отчет квартир')


@dp.message_handler(filters.IDFilter(chat_id=[ADMIN_ID]), commands=["get_errors"], state="*", )
async def send_errors(message: types.Message, state: FSMContext):
    with open('src/service/errors.log', 'rb') as file:
        await message.answer_document(file, caption='Отчет ошибок')


@dp.message_handler(filters.IDFilter(chat_id=[ADMIN_ID]), commands=["get_users"], state="*", )
async def send_users(message: types.Message, state: FSMContext):

    with open('src/analytics/users.csv', 'rb') as file:
        write_users_csv()
        await message.answer_document(file, caption='Отчет пользователей')


@dp.message_handler(filters.IDFilter(chat_id=[ADMIN_ID]), commands=["get_stats"], state="*", )
async def send_stats(message: types.Message, state: FSMContext):
    csv_file = 'src/service/ads.csv'
    await message.answer(analyze_minsk_advertisements(csv_file))
