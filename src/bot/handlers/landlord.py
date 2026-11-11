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


@dp.message(State.choose_landlord, F.text)
async def choose_landlord(message: types.Message, state: FSMContext):
    input = message.text.strip()
    if (
        buttons.owner_btn == input
        or buttons.agent_btn == input
        or buttons.no_matter_btn == input
    ):
        await message.answer(answers.enter_subway_need, reply_markup=kb.yn_kb)
        await asyncio.to_thread(db.edit_landlord, message.from_user.id, input)
        await state.set_state(State.is_subway_needed)
    else:
        await message.answer(answers.bad_input)
