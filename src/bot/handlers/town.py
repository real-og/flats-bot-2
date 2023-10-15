from loader import dp
from aiogram import types
from texts import buttons
from texts import answers
from states import State
import keyboards as kb
from src.shared import db
from src.shared.towns import supported_towns


@dp.message_handler(state=State.choose_town)
async def choose_town(message: types.Message):
    input = message.text.strip().title()
    db.edit_town(message.from_id, input)
    if input in supported_towns:
        await message.answer(answers.town_chosen(input))
        await State.choose_cost.set()
    else:
        await message.answer(answers.no_town_supported, reply_markup=kb.continue_kb)
        await State.confirm_town.set()

@dp.message_handler(state=State.confirm_town)
async def confirm_town(message: types.Message):
    input = message.text.strip().title()
    if input != buttons.continue_btn:
        db.edit_town(message.from_id, input)
    await State.choose_cost.set()
    await message.answer(answers.enter_cost)
