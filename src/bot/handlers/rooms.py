from loader import dp, bot
from aiogram import types
from texts import buttons
from texts import answers
from states import State
import keyboards as kb
from src.shared import db


@dp.callback_query_handler(state=State.choose_rooms)
async def select_room(callback: types.CallbackQuery):
    if callback.data == 'go':
        await callback.message.answer(answers.enter_landlord, reply_markup=kb.landlord_kb)
        await State.choose_landlord.set()
    else:
        keyboard = callback.message.reply_markup.inline_keyboard
        await callback.message.edit_reply_markup(kb.generate_new_kb(keyboard, callback.data, 4))
        db.flag_room(callback.from_user.id, callback.data)
    await bot.answer_callback_query(callback.id)