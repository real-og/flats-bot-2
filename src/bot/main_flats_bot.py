"""Run with python -m src.bot.main_flats_bot."""

import asyncio
import logging
import fcntl
import os
import threading
import time
from contextlib import suppress
from aiogram.types import ErrorEvent
from src.shared.config import DATA_DIR
from src.shared import db
from src.bot.loader import dp, bot, session
from src.bot import handlers  # noqa: F401 - registers handlers


@dp.errors()
async def on_error(event: ErrorEvent):
    exc = event.exception
    logging.error(
        "Telegram handler failed: %s",
        type(exc).__name__,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    message = event.update.message or (
        event.update.callback_query.message if event.update.callback_query else None
    )
    if message:
        with suppress(Exception):
            await message.answer(
                "Не удалось выполнить действие. Попробуйте ещё раз; если настройка сбилась, используйте /start."
            )
    return True


async def main():
    lock = open(DATA_DIR / "bot.lock", "w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    heartbeat = [time.monotonic()]
    stopping = threading.Event()

    def watchdog():
        while not stopping.wait(30):
            if time.monotonic() - heartbeat[0] > 120:
                logging.critical("Bot event loop stalled; exiting for systemd restart")
                time.sleep(1)
                os._exit(1)

    async def health():
        database_failures = 0
        while True:
            heartbeat[0] = time.monotonic()
            if time.monotonic() - session.last_poll_success > 300:
                logging.critical("Telegram polling unavailable for more than 5 minutes")
            try:
                await asyncio.to_thread(db.ping)
                if database_failures:
                    logging.info("PostgreSQL connection recovered")
                database_failures = 0
            except Exception:
                database_failures += 1
                logging.error("PostgreSQL health check failed", exc_info=True)
                if database_failures >= 3:
                    logging.critical("PostgreSQL unavailable to the Telegram interface")
            await asyncio.sleep(30)

    threading.Thread(target=watchdog, name="bot-watchdog", daemon=True).start()
    monitor = asyncio.create_task(health())
    try:
        # No drop_pending_updates: preserve pending commands across restarts.
        await bot.delete_webhook(drop_pending_updates=False)
        await dp.start_polling(
            bot,
            handle_as_tasks=True,
            tasks_concurrency_limit=32,
            polling_timeout=20,
            allowed_updates=dp.resolve_used_update_types(),
        )
    finally:
        stopping.set()
        monitor.cancel()
        with suppress(asyncio.CancelledError):
            await monitor
        await bot.session.close()
        lock.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        logging.critical("Bot stopped unexpectedly", exc_info=True)
        raise
