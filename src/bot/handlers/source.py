import asyncio
from aiogram import F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from src.bot.loader import dp
from src.bot.states import State
from src.shared import db


def keyboard(selected):
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=("✅ " if name in selected else "❌ ") + name,
                    callback_data="source:" + name,
                )
                for name in ("onliner", "kufar")
            ],
            [
                types.InlineKeyboardButton(
                    text="Готово (пустой выбор = все)", callback_data="source:done"
                )
            ],
        ]
    )


@dp.message(Command("sources"))
async def choose_sources(message: types.Message, state: FSMContext):
    params = await asyncio.to_thread(db.get_user_params, message.from_user.id)
    previous = await state.get_state()
    if previous != State.choose_sources.state:
        await state.update_data(source_previous=previous)
    await state.set_state(State.choose_sources)
    await message.answer(
        "Выберите источники. Изменения применяются сразу; пустой выбор — оба источника.",
        reply_markup=keyboard(params.get("source", [])),
    )


@dp.callback_query(State.choose_sources, F.data.startswith("source:"))
async def source_callback(callback: types.CallbackQuery, state: FSMContext):
    name = callback.data.split(":", 1)[1]
    if name == "done":
        data = await state.get_data()
        await state.set_state(data.get("source_previous"))
        await callback.answer("Сохранено")
        return
    if name in ("onliner", "kufar"):
        await asyncio.to_thread(db.flag_source, callback.from_user.id, name)
        params = await asyncio.to_thread(db.get_user_params, callback.from_user.id)
        await callback.message.edit_reply_markup(
            reply_markup=keyboard(params.get("source", []))
        )
    await callback.answer()
