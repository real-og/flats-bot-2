from aiogram import F
from aiogram.fsm.context import FSMContext
import asyncio
from src.bot.loader import dp, bot
from aiogram import types
from src.bot.texts import buttons
from src.bot.texts import answers
from src.bot.states import State
from src.bot import keyboards as kb
from src.shared import db


@dp.message(State.is_subway_needed, F.text)
async def is_subway_needed(message: types.Message, state: FSMContext):
    input = message.text.strip().title()
    if input == buttons.no_btn or input == buttons.no_btn_2:
        await message.answer(answers.enter_location_need, reply_markup=kb.yn_kb)
        await state.set_state(State.is_point_needed)
        await asyncio.to_thread(db.set_subway_need, message.from_user.id, False)
    elif input == buttons.yes_btn or input == buttons.yes_btn_2:
        await message.answer(
            answers.enter_subways,
            reply_markup=await asyncio.to_thread(
                kb.generate_sub_kb, message.from_user.id
            ),
        )
        await state.set_state(State.select_branch)
        await asyncio.to_thread(db.set_subway_need, message.from_user.id, True)
    else:
        await message.answer(answers.bad_input)


@dp.callback_query(State.select_branch, F.data)
async def select_branch(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "go":
        if not (await asyncio.to_thread(db.get_user_params, callback.from_user.id))[
            "subways"
        ]:
            await callback.answer("Выберите хотя бы одну станцию", show_alert=True)
            return
        await callback.message.answer(
            answers.enter_distance_subway, reply_markup=kb.dist_kb
        )
        await state.set_state(State.distance)
    elif callback.data.isdigit() and 0 <= int(callback.data) < len(kb.subways):
        await asyncio.to_thread(db.flag_subway, callback.from_user.id, callback.data)
        await callback.message.edit_reply_markup(
            reply_markup=await asyncio.to_thread(
                kb.generate_sub_kb, callback.from_user.id
            )
        )
    await bot.answer_callback_query(callback.id)


@dp.message(State.distance, F.text)
async def subway_distance(message: types.Message, state: FSMContext):
    input = message.text.strip()
    if input == buttons.no_matter_btn or (
        input.isdigit() and len(input) < 7 and (int(input) > 0)
    ):
        await message.answer(answers.enter_location_need, reply_markup=kb.yn_kb)
        await asyncio.to_thread(db.set_sub_distance, message.from_user.id, input)
        await state.set_state(State.is_point_needed)
    else:
        await message.answer(answers.bad_distance, reply_markup=kb.dist_kb)
