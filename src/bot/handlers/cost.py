from loader import dp
from aiogram import types
from texts import answers
from states import State
import keyboards as kb
from src.shared import db


@dp.message_handler(state=State.choose_cost)
async def choose_cost(message: types.Message):
    costs = message.text.strip().split()
    if len(costs) != 2:
        await message.answer(answers.bad_input)
        return 
    if (costs[0].isdigit() and costs[1].isdigit()):
        min_cost = int(costs[0])
        max_cost = int(costs[1])
        if min_cost <= max_cost:
            await message.answer(answers.cost_chosen(min_cost, max_cost))
            await message.answer(answers.enter_rooms, reply_markup=kb.generate_rooms_kb(message.from_id))
            await State.choose_rooms.set()
            db.edit_cost(message.from_id, min_cost, max_cost)
        else:
            await message.answer(answers.min_max_error)
    else:
        await message.answer(answers.bad_input)