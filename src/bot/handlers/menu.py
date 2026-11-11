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


@dp.message(State.sending, F.text)
async def handle_menu(message: types.Message, state: FSMContext):
    input = message.text.strip().title()
    if input == buttons.pause_btn:
        await message.answer(answers.paused, reply_markup=kb.restart_kb)
        await asyncio.to_thread(db.set_user_status, message.from_user.id, False)
        await state.set_state(State.pause)
    elif input == buttons.change_btn:
        await asyncio.to_thread(db.set_user_status, message.from_user.id, False)
        await message.answer(answers.reset_filters, reply_markup=kb.towns_kb)
        await state.set_state(State.choose_town)
    elif input == buttons.params_btn:
        await message.answer(
            await asyncio.to_thread(answers.compose_params, message.from_user.id),
            reply_markup=kb.main_menu_kb,
        )
        params = await asyncio.to_thread(db.get_user_params, message.from_user.id)
        if params["isPointNeed"]:
            await message.answer_location(params["lat"], params["lon"])
    else:
        await message.answer(answers.bad_input)


@dp.message(State.pause, F.text)
async def subway_distance(message: types.Message, state: FSMContext):
    if message.text.title() == buttons.resume_btn:
        await message.answer(answers.resumed, reply_markup=kb.main_menu_kb)
        await asyncio.to_thread(db.set_user_status, message.from_user.id, True)
        await state.set_state(State.sending)
    else:
        await message.answer(answers.bad_input_menu, reply_markup=kb.restart_kb)
