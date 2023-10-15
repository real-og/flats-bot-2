from loader import dp
from aiogram import types
from texts import buttons
from texts import answers
from states import State
import keyboards as kb
from src.shared import db


@dp.message_handler(state=State.choose_landlord)
async def choose_landlord(message: types.Message):
    input = message.text.strip()
    if (buttons.owner_btn == input) or (buttons.agent_btn == input) or (buttons.no_matter_btn == input):
        await message.answer(answers.enter_subway_need, reply_markup=kb.yn_kb)
        db.edit_landlord(message.from_id, input)
        await State.is_subway_needed.set()
    else:
        await message.answer(answers.bad_input)