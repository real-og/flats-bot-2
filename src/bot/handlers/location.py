from aiogram import F
from aiogram.fsm.context import FSMContext
import asyncio
from src.bot.loader import dp
from aiogram import types
from src.bot.texts import buttons
from src.bot.texts import answers
from src.bot.states import State
from src.bot import keyboards as kb
from src.shared import db
from src.shared.logic import is_coordinates


@dp.message(State.is_point_needed, F.text)
async def is_point_needed(message: types.Message, state: FSMContext):
    input = message.text
    if input == buttons.no_btn or input == buttons.no_btn_2:
        await asyncio.to_thread(db.set_point_need, message.from_user.id, False)
        await asyncio.to_thread(db.set_user_status, message.from_user.id, True)
        await state.set_state(State.sending)
        await message.answer(answers.finished, reply_markup=kb.main_menu_kb)
    elif input == buttons.yes_btn or input == buttons.yes_btn_2:
        await message.answer(answers.enter_location)
        await state.set_state(State.select_point)
        await asyncio.to_thread(db.set_point_need, message.from_user.id, True)
    else:
        await message.answer(answers.bad_input)


@dp.message(State.select_point, F.text | F.location)
async def select_needed(message: types.Message, state: FSMContext):
    if message.location:
        await asyncio.to_thread(
            db.set_point,
            message.from_user.id,
            message.location.latitude,
            message.location.longitude,
        )
    elif is_coordinates(message.text):
        await asyncio.to_thread(
            db.set_point,
            message.from_user.id,
            float(message.text.split(",")[0].strip()),
            float(message.text.split(",")[1].strip()),
        )
    else:
        await message.answer(answers.bad_input)
        return
    await message.answer(answers.enter_radius)
    await state.set_state(State.select_radius)


@dp.message(State.select_radius, F.text)
async def select_radius(message: types.Message, state: FSMContext):
    if message.text.strip().isdigit() and 0 < int(message.text) <= 1000000:
        await asyncio.to_thread(
            db.set_point_radius, message.from_user.id, int(message.text)
        )
        await asyncio.to_thread(db.set_user_status, message.from_user.id, True)
        await message.answer(answers.finished, reply_markup=kb.main_menu_kb)
        await state.set_state(State.sending)
    else:
        await message.answer(answers.bad_distance)
