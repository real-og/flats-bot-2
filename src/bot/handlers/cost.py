from aiogram import F
from aiogram.fsm.context import FSMContext
import asyncio
from src.bot.loader import dp
from aiogram import types
from src.bot.texts import answers
from src.bot.states import State
from src.bot import keyboards as kb
from src.shared import db


@dp.message(State.choose_cost, F.text)
async def choose_cost(message: types.Message, state: FSMContext):
    costs = message.text.strip().split()
    if len(costs) != 2:
        await message.answer(answers.bad_input)
        return
    if costs[0].isdigit() and costs[1].isdigit():
        min_cost = int(costs[0])
        max_cost = int(costs[1])
        if min_cost <= max_cost <= 1000000:
            await asyncio.to_thread(
                db.edit_cost, message.from_user.id, min_cost, max_cost
            )
            await message.answer(answers.cost_chosen(min_cost, max_cost))
            await message.answer(
                answers.enter_rooms,
                reply_markup=await asyncio.to_thread(
                    kb.generate_rooms_kb, message.from_user.id
                ),
            )
            await state.set_state(State.choose_rooms)
        else:
            await message.answer(answers.min_max_error)
    else:
        await message.answer(answers.bad_input)
