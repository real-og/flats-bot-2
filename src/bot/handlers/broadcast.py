from aiogram import F
from aiogram.fsm.context import FSMContext
import asyncio
from src.bot.loader import dp, ADMIN_ID
from aiogram import types
from aiogram.filters import Command
from src.bot.states import State
from src.bot.texts import answers
from src.bot import keyboards as kb
import logging
from src.shared import db
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError


@dp.message(F.from_user.id == ADMIN_ID, Command(*["broadcast"]), F.text)
async def ask_for_message(message: types.Message, state: FSMContext):
    await message.answer(answers.enter_message_to_broadcast)
    await state.set_state(State.broadcast)


@dp.message(F.from_user.id == ADMIN_ID, Command(*["quit"]), State.broadcast, F.text)
async def confirm(message: types.Message, state: FSMContext):
    await state.set_state(State.sending)
    await message.answer(answers.quited_broadcast, reply_markup=kb.main_menu_kb)


@dp.message(F.from_user.id == ADMIN_ID, State.broadcast)
async def broadcast(message: types.Message, state: FSMContext):
    id_rows = await asyncio.to_thread(db.get_all_users_ids)
    sent = failed = 0
    for id_row in id_rows:
        chat_id = id_row["id_tg"]
        for attempt in range(3):
            try:
                await message.copy_to(chat_id)
                sent += 1
                break
            except TelegramRetryAfter as exc:
                if attempt == 2:
                    failed += 1
                    logging.warning(
                        "Admin broadcast rate limit exhausted for %s", chat_id
                    )
                    break
                await asyncio.sleep(exc.retry_after)
            except TelegramForbiddenError:
                await asyncio.to_thread(db.set_user_status, chat_id, False)
                failed += 1
                break
            except Exception:
                logging.warning("Admin broadcast failed for %s", chat_id, exc_info=True)
                failed += 1
                break
        await asyncio.sleep(1.1)
    await state.set_state(State.sending)
    await message.answer(
        f"Рассылка завершена: {sent} отправлено, {failed} ошибок. Ошибки — в журнале.",
        reply_markup=kb.main_menu_kb,
    )
