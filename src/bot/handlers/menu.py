from loader import dp
from aiogram import types
from texts import buttons
from texts import answers
from states import State
import keyboards as kb
from src.shared import db


@dp.message_handler(state=State.sending)
async def handle_menu(message: types.Message):
    input = message.text.strip().title()
    if input == buttons.pause_btn:
        await message.answer(answers.paused, reply_markup=kb.restart_kb)
        db.set_user_status(message.from_id, False)
        await State.pause.set()
    elif input == buttons.change_btn:
        await message.answer(answers.reset_filters, reply_markup=kb.towns_kb)
        await State.choose_town.set()
    elif input == buttons.params_btn:
        await message.answer(answers.compose_params(message.from_user.id), reply_markup=kb.main_menu_kb)
        params = db.get_user_params(message.from_id)
        if params['isPointNeed']:
            await message.answer_location(params['lat'], params['lon'])
    else:
        await message.answer(answers.bad_input)


@dp.message_handler(state=State.pause)
async def subway_distance(message: types.Message):
    if message.text.title() == buttons.resume_btn:
        await message.answer(answers.resumed, reply_markup=kb.main_menu_kb)
        db.set_user_status(message.from_id, True)
        await State.sending.set()
    else:
        await message.answer(answers.bad_input_menu, reply_markup=kb.restart_kb)


@dp.message_handler()
async def default_handler(message: types.Message):
    await message.answer(answers.bad_input_universal)
