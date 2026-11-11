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
from src.shared.towns import supported_towns, normalize_town


@dp.message(State.choose_town, F.text)
async def choose_town(message: types.Message, state: FSMContext):
    input = normalize_town(message.text.strip().title())
    if len(input) > 120:
        await message.answer(answers.bad_input)
        return
    await asyncio.to_thread(db.edit_town, message.from_user.id, input)
    if input in supported_towns:
        await message.answer(answers.town_chosen(input))
        await state.set_state(State.choose_cost)
    else:
        await message.answer(answers.no_town_supported, reply_markup=kb.continue_kb)
        await state.set_state(State.confirm_town)


@dp.message(State.confirm_town, F.text)
async def confirm_town(message: types.Message, state: FSMContext):
    input = normalize_town(message.text.strip().title())
    if len(input) > 120:
        await message.answer(answers.bad_input)
        return
    if input != buttons.continue_btn:
        await asyncio.to_thread(db.edit_town, message.from_user.id, input)
    await state.set_state(State.choose_cost)
    await message.answer(answers.enter_cost)
