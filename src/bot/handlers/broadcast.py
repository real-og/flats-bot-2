from loader import dp, ADMIN_ID
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher import filters
from states import State
from texts import answers
import keyboards as kb
import logging
from src.shared import db

@dp.message_handler(filters.IDFilter(chat_id=[ADMIN_ID]),
                    commands=['broadcast'],
                    state='*')
async def confirm(message: types.Message):
    await message.answer(answers.enter_message_to_broadcast)
    await State.broadcast.set()


@dp.message_handler(filters.IDFilter(chat_id=[ADMIN_ID]),
                    commands=['quit'],
                    state=State.broadcast
                    )
async def confirm(message: types.Message):
   await State.sending.set()
   await message.answer(answers.quited_broadcast, reply_markup=kb.main_menu_kb)

@dp.message_handler(filters.IDFilter(chat_id=[ADMIN_ID]),
                    state=State.broadcast,
                    content_types=['any'])
async def confirm(message: types.Message):
    id_rows = db.get_all_users_ids()
    for id_row in id_rows:
        id = id_row['id_tg']
        try:
            await message.send_copy(id)
        except Exception as e:
            logging.warning(f'Рассылка сообщения не сработала для {id}')