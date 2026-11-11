"""Persistent aiogram 3 FSM without a Redis server."""

import asyncio
import json
import sqlite3
from aiogram.fsm.storage.base import BaseStorage, StorageKey
from aiogram.fsm.state import State
from src.shared.config import DATA_DIR


class SQLiteStorage(BaseStorage):
    def __init__(self, path=None):
        self.path = path or DATA_DIR / "fsm.sqlite3"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path)
        try:
            with db:
                db.execute("PRAGMA journal_mode=WAL")
                db.execute(
                    'CREATE TABLE IF NOT EXISTS fsm_v3(key TEXT PRIMARY KEY,state TEXT,data TEXT NOT NULL DEFAULT "{}")'
                )
        finally:
            db.close()

    def _run(self, key, field, value=None, write=False, merge=False):
        key = json.dumps(
            [
                key.bot_id,
                key.chat_id,
                key.user_id,
                key.thread_id,
                key.business_connection_id,
                key.destiny,
            ]
        )
        db = sqlite3.connect(self.path, timeout=5)
        try:
            with db:
                if write:
                    db.execute("INSERT OR IGNORE INTO fsm_v3(key) VALUES(?)", (key,))
                    if merge:
                        old = json.loads(
                            db.execute(
                                "SELECT data FROM fsm_v3 WHERE key=?", (key,)
                            ).fetchone()[0]
                        )
                        old.update(value)
                        value = old
                    db.execute(
                        f"UPDATE fsm_v3 SET {field}=? WHERE key=?",
                        (json.dumps(value) if field == "data" else value, key),
                    )
                    return value
                row = db.execute(
                    f"SELECT {field} FROM fsm_v3 WHERE key=?", (key,)
                ).fetchone()
                return (
                    (json.loads(row[0]) if field == "data" else row[0]) if row else None
                )
        finally:
            db.close()

    async def get_state(self, key: StorageKey):
        return await asyncio.to_thread(self._run, key, "state")

    async def set_state(self, key: StorageKey, state=None):
        await asyncio.to_thread(
            self._run,
            key,
            "state",
            state.state if isinstance(state, State) else state,
            True,
        )

    async def get_data(self, key: StorageKey):
        return await asyncio.to_thread(self._run, key, "data") or {}

    async def set_data(self, key: StorageKey, data):
        await asyncio.to_thread(self._run, key, "data", dict(data), True)

    async def update_data(self, key: StorageKey, data):
        return await asyncio.to_thread(self._run, key, "data", dict(data), True, True)

    async def close(self):
        pass
