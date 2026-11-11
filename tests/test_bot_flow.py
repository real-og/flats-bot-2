"""Offline routing/FSM regression: no real Telegram API calls or production DB."""

import os
import tempfile

_test_data = tempfile.TemporaryDirectory()
os.environ["DISABLE_ALERTS"] = "1"
os.environ.setdefault("BOT_TOKEN", "123456789:" + ("x" * 35))
os.environ.setdefault("ADMIN_ID", "999999")
os.environ.setdefault("DATA_DIR", _test_data.name)
os.environ.setdefault("LOG_DIR", _test_data.name)
import unittest
from unittest.mock import patch
from datetime import datetime, timezone
from aiogram.types import Update, Message, Chat, User, CallbackQuery
from aiogram.fsm.storage.base import StorageKey
from src.bot.loader import dp, bot
from src.bot import handlers  # noqa: F401 - registers handlers


class BotFlowTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.user = User(id=123, is_bot=False, first_name="Test")
        self.key = StorageKey(bot_id=bot.id, chat_id=123, user_id=123)
        await dp.storage.set_state(self.key, None)
        self.params = dict(
            town="",
            minCost=0,
            maxCost=1000,
            landlord="",
            rooms=[],
            isSubwayNeed=False,
            subways=[],
            isPointNeed=False,
            source=[],
        )
        self.sent = []
        self.active = False

        async def request(bot, method, timeout=None):
            self.sent.append(method)
            if method.__api_method__ == "answerCallbackQuery":
                return True
            return Message(
                message_id=100,
                date=datetime.now(timezone.utc),
                chat=Chat(id=123, type="private"),
                text=getattr(method, "text", None),
            )

        self.patches = [
            patch.object(bot.session, "make_request", side_effect=request),
            patch("src.shared.db.add_user"),
            patch(
                "src.bot.keyboards.get_user_params",
                side_effect=lambda _: dict(self.params),
            ),
            patch(
                "src.shared.db.get_user_params", side_effect=lambda _: dict(self.params)
            ),
            patch(
                "src.shared.db.set_user_status",
                side_effect=lambda _, value: setattr(self, "active", value),
            ),
            patch(
                "src.shared.db.edit_town",
                side_effect=lambda _, town: self.params.update(town=town),
            ),
            patch(
                "src.shared.db.edit_cost",
                side_effect=lambda _, a, b: self.params.update(minCost=a, maxCost=b),
            ),
            patch(
                "src.shared.db.edit_landlord",
                side_effect=lambda _, v: self.params.update(landlord=v),
            ),
            patch(
                "src.shared.db.flag_room",
                side_effect=lambda _, v: self.params["rooms"].append(v[1]),
            ),
            patch(
                "src.shared.db.set_subway_need",
                side_effect=lambda _, v: self.params.update(isSubwayNeed=v),
            ),
            patch(
                "src.shared.db.set_point_need",
                side_effect=lambda _, v: self.params.update(isPointNeed=v),
            ),
        ]
        for p in self.patches:
            p.start()
        self.update = 0

    async def asyncTearDown(self):
        for p in reversed(self.patches):
            p.stop()

    async def message(self, text):
        self.update += 1
        msg = Message(
            message_id=self.update,
            date=datetime.now(timezone.utc),
            chat=Chat(id=123, type="private"),
            from_user=self.user,
            text=text,
        )
        await dp.feed_update(bot, Update(update_id=self.update, message=msg))

    async def callback(self, value):
        self.update += 1
        msg = Message(
            message_id=99,
            date=datetime.now(timezone.utc),
            chat=Chat(id=123, type="private"),
            from_user=self.user,
            text="Choose",
        )
        query = CallbackQuery(
            id=str(self.update),
            from_user=self.user,
            chat_instance="test",
            data=value,
            message=msg,
        )
        await dp.feed_update(bot, Update(update_id=self.update, callback_query=query))

    async def test_full_setup_pause_resume_edit(self):
        await self.message("/start")
        self.assertEqual(await dp.storage.get_state(self.key), "State:choose_town")
        await self.message("Минск")
        self.assertEqual(await dp.storage.get_state(self.key), "State:choose_cost")
        await self.message("300 450")
        self.assertEqual(await dp.storage.get_state(self.key), "State:choose_rooms")
        await self.callback("go")
        self.assertEqual(await dp.storage.get_state(self.key), "State:choose_rooms")
        await self.callback("02")
        await self.callback("go")
        self.assertEqual(await dp.storage.get_state(self.key), "State:choose_landlord")
        await self.message("Не важно")
        await self.message("Нет")
        await self.message("Нет")
        self.assertTrue(self.active)
        self.assertEqual(await dp.storage.get_state(self.key), "State:sending")
        await self.message("Приостановить")
        self.assertFalse(self.active)
        await self.message("/resume")
        self.assertTrue(self.active)
        await self.message("Изменить")
        self.assertFalse(self.active)

    async def test_admin_command_not_available_to_user(self):
        await self.message("/get_users")
        self.assertFalse(any(m.__api_method__ == "sendDocument" for m in self.sent))

    async def test_start_recovers_any_state(self):
        await dp.storage.set_state(self.key, "State:select_radius")
        await self.message("/start")
        self.assertEqual(await dp.storage.get_state(self.key), "State:choose_town")

    async def test_source_selection_restores_state(self):
        await dp.storage.set_state(self.key, "State:choose_cost")
        await self.message("/sources")
        self.assertEqual(await dp.storage.get_state(self.key), "State:choose_sources")
        with patch(
            "src.shared.db.flag_source",
            side_effect=lambda _, name: self.params.update(source=[name]),
        ):
            await self.callback("source:kufar")
        await self.callback("source:done")
        self.assertEqual(self.params["source"], ["kufar"])
        self.assertEqual(await dp.storage.get_state(self.key), "State:choose_cost")
