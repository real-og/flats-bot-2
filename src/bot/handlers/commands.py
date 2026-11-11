from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import asyncio
from src.bot.loader import dp
from aiogram import types
from src.bot.texts import answers
from src.bot.states import State
from src.shared import db


@dp.message(Command(*["start"]), F.text)
async def send_welcome(message: types.Message, state: FSMContext):
    await asyncio.to_thread(
        db.add_user, message.from_user.id, message.from_user.username
    )
    await asyncio.to_thread(db.set_user_status, message.from_user.id, False)
    await message.answer(answers.welcome)
    await message.answer(answers.enter_town)
    await state.set_state(State.choose_town)


@dp.message(Command(*["pause"]), F.text)
async def pause(message: types.Message, state: FSMContext):
    await asyncio.to_thread(db.set_user_status, message.from_user.id, False)
    await state.set_state(State.pause)
    await message.answer("Рассылка приостановлена. /resume — возобновить.")


@dp.message(Command(*["resume"]), F.text)
async def resume(message: types.Message, state: FSMContext):
    params = await asyncio.to_thread(db.get_user_params, message.from_user.id)
    if not params.get("town") or not params.get("rooms") or not params.get("landlord"):
        await message.answer("Сначала настройте фильтры: /start")
        return
    await asyncio.to_thread(db.set_user_status, message.from_user.id, True)
    await state.set_state(State.sending)
    await message.answer("Рассылка возобновлена.")
