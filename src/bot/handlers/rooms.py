from aiogram import F
from aiogram.fsm.context import FSMContext
import asyncio
from src.bot.loader import dp, bot
from aiogram import types
from src.bot.texts import answers
from src.bot.states import State
from src.bot import keyboards as kb
from src.shared import db


@dp.callback_query(State.choose_rooms, F.data)
async def select_room(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "go":
        if not (await asyncio.to_thread(db.get_user_params, callback.from_user.id))[
            "rooms"
        ]:
            await callback.answer("Выберите хотя бы один вариант", show_alert=True)
            return
        await callback.message.answer(
            answers.enter_landlord, reply_markup=kb.landlord_kb
        )
        await state.set_state(State.choose_landlord)
    elif callback.data in ("01", "02", "03", "04", "10"):
        await asyncio.to_thread(db.flag_room, callback.from_user.id, callback.data)
        await callback.message.edit_reply_markup(
            reply_markup=await asyncio.to_thread(
                kb.generate_rooms_kb, callback.from_user.id
            )
        )
    await bot.answer_callback_query(callback.id)
