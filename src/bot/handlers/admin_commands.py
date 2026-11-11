from aiogram import F
from aiogram.fsm.context import FSMContext
import asyncio
import io
import json
from aiogram import types
from aiogram.filters import Command
from src.bot.loader import dp, ADMIN_ID
from src.shared.config import LOG_DIR
from src.service.store import Store
from src.shared import db
from src.analytics.flats_analyzer import analyze_minsk_advertisements


@dp.message(F.from_user.id == ADMIN_ID, Command(*["get_errors"]), F.text)
async def send_errors(message: types.Message, state: FSMContext):
    for name in ("bot", "parser"):
        path = LOG_DIR / f"{name}.log"
        if path.exists():
            await message.answer_document(
                types.FSInputFile(path),
                caption=f"{name}: текущий журнал; архивы доступны на сервере",
            )


@dp.message(F.from_user.id == ADMIN_ID, Command(*["status"]), F.text)
async def status(message: types.Message, state: FSMContext):
    report = await asyncio.to_thread(
        lambda: json.dumps(Store().status(), ensure_ascii=False, indent=2)
    )
    await message.answer(report, parse_mode=None)


@dp.message(F.from_user.id == ADMIN_ID, Command(*["get_users"]), F.text)
async def send_users(message: types.Message, state: FSMContext):
    users = await asyncio.to_thread(db.get_all_users)
    output = io.BytesIO(
        json.dumps([dict(u) for u in users], ensure_ascii=False, default=str).encode()
    )
    await message.answer_document(
        types.BufferedInputFile(output.getvalue(), filename="users.json")
    )


@dp.message(F.from_user.id == ADMIN_ID, Command(*["get_stats"]), F.text)
async def send_stats(message: types.Message, state: FSMContext):
    await message.answer(
        await asyncio.to_thread(analyze_minsk_advertisements), parse_mode=None
    )


@dp.message(F.from_user.id == ADMIN_ID, Command(*["get_ads"]), F.text)
async def send_ads(message: types.Message, state: FSMContext):
    await message.answer(
        "Объявления хранятся в постоянной очереди. /status — состояние, /get_stats — статистика. Полный экспорт: python -m src.service.manage export на сервере."
    )
