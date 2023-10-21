from loader import dp
from aiogram import types
from aiogram.dispatcher import FSMContext
from texts import answers
from states import State
from src.shared import db


@dp.message_handler(commands=['start'], state="*")
async def send_welcome(message: types.Message):
    db.add_user(message.from_id, message.from_user.username)
    await message.answer(answers.welcome)
    await message.answer(answers.enter_town)
    await State.choose_town.set()
