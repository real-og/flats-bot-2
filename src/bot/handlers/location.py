from loader import dp
from aiogram import types
from texts import buttons
from texts import answers
from states import State
import keyboards as kb
from src.shared import db
from src.shared.logic import is_coordinates


@dp.message_handler(state=State.is_point_needed)
async def is_point_needed(message: types.Message):
    input = message.text
    if input == buttons.no_btn or input == buttons.no_btn_2:
        await message.answer(answers.finished, reply_markup=kb.main_menu_kb)
        await State.sending.set()
        db.set_user_status(message.from_id, True)
        db.set_point_need(message.from_id, False)
    elif input == buttons.yes_btn or input == buttons.yes_btn_2:
        await message.answer(answers.enter_location)
        await State.select_point.set()
        db.set_point_need(message.from_id, True)
    else:
        await message.answer(answers.bad_input)


@dp.message_handler(state=State.select_point, content_types=['location', 'text'])
async def select_needed(message: types.Message):
    if message.location:
        db.set_point(message.from_user.id, message.location.latitude, message.location.longitude)
    elif is_coordinates(message.text):
        db.set_point(message.from_user.id,
                     float(message.text.split(',')[0].strip()),
                     float(message.text.split(',')[1].strip()))
    else:
        await message.answer(answers.bad_input)
        return
    await message.answer(answers.enter_radius)
    await State.select_radius.set()


@dp.message_handler(state=State.select_radius)
async def select_radius(message: types.Message):
    if message.text.strip().isdigit():
        db.set_user_status(message.from_id, True)
        await message.answer(answers.finished, reply_markup=kb.main_menu_kb)
        await State.sending.set()
        db.set_point_radius(message.from_id, int(message.text))
    else:
        await message.answer(answers.bad_distance)
