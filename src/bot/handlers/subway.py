from loader import dp, bot
from aiogram import types
from texts import buttons
from texts import answers
from states import State
import keyboards as kb
from src.shared import db


@dp.message_handler(state=State.is_subway_needed)
async def is_subway_needed(message: types.Message):
    input = message.text.strip().title()
    if input == buttons.no_btn or input == buttons.no_btn_2:
        await message.answer(answers.enter_location_need, reply_markup=kb.yn_kb)
        await State.is_point_needed.set()
        db.set_subway_need(message.from_id, False)
    elif input == buttons.yes_btn or input == buttons.yes_btn_2:
        await message.answer(answers.enter_subways, reply_markup=kb.generate_sub_kb(message.from_id))
        await State.select_branch.set()
        db.set_subway_need(message.from_id, True)
    else:
        await message.answer(answers.bad_input)


@dp.callback_query_handler(state=State.select_branch)
async def select_branch(callback: types.CallbackQuery):
    if callback.data == 'go':
        await callback.message.answer(answers.enter_distance_subway, reply_markup=kb.dist_kb)
        await State.distance.set()   
    else: 
        db.flag_subway(callback.from_user.id, callback.data)
        await callback.message.edit_reply_markup(kb.generate_sub_kb(callback.from_user.id))
    await bot.answer_callback_query(callback.id)


@dp.message_handler(state=State.distance)
async def subway_distance(message: types.Message):
    input = message.text.strip()
    if input == buttons.no_matter_btn or (input.isdigit() and len(input) < 7 and int(input) > 0):
        await message.answer(answers.enter_location_need, reply_markup=kb.yn_kb)
        db.set_sub_distance(message.from_id, input)
        await State.is_point_needed.set()
    else:
        await message.answer(answers.bad_distance, reply_markup=kb.dist_kb)
        