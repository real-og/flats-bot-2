from dataclasses import asdict
import logging
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from src.service.store import Store
from src.service.telegram import TelegramFailure, send_ad, call
from src.service.main_flats_parser import fetch_cycle, process_item, deliver_item
from src.service.onliner_parser import generate_ad_from_onliner, address_town
from src.service.kufar_parser import generate_ad_from_kufar
from src.shared.observability import SafeFormatter
from src.shared.http import HTTPFailure
from src.shared.logic import is_comparable, is_coordinates
from src.shared import db
from src.bot.storage import SQLiteStorage


def raw_onliner(id=1):
    return {
        "id": id,
        "price": {"amount": "350", "currency": "USD"},
        "rent_type": "2_rooms",
        "location": {
            "address": "Беларусь, Минск, Улица, 1",
            "latitude": 53.9,
            "longitude": 27.5,
        },
        "url": f"https://r.onliner.by/ak/apartments/{id}",
        "contact": {"owner": True},
        "photo": "https://example.org/p.jpg",
    }


def ad():
    return generate_ad_from_onliner(raw_onliner())


def params():
    return dict(
        town="Минск",
        minCost=0,
        maxCost=1000,
        landlord="Не важно",
        rooms=["2"],
        isSubwayNeed=False,
        isPointNeed=False,
        source=[],
    )


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "queue.db"
        self.store = Store(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def pending(self):
        self.store.ingest("onliner", [raw_onliner()], "id")
        return self.store.next_item("inbox")

    def queued(self):
        item = self.pending()
        self.store.enqueue(item, asdict(ad()), [123])
        return self.store.next_item("outbox")

    def test_restart_dedup_and_per_recipient_ack(self):
        item = self.pending()
        self.store.enqueue(item, asdict(ad()), [123, 456, 123])
        item = self.store.next_item("outbox")
        self.store.finish("outbox", item["rowid"])
        reopened = Store(self.path)
        reopened.ingest("onliner", [raw_onliner()], "id")
        self.assertIsNone(reopened.next_item("inbox"))
        self.assertEqual(reopened.next_item("outbox")["chat_id"], 456)

    def test_enqueue_is_atomic(self):
        item = self.pending()
        with self.assertRaises(Exception):
            self.store.enqueue(item, asdict(ad()), [123, object()])
        self.assertIsNotNone(self.store.next_item("inbox"))
        self.assertIsNone(self.store.next_item("outbox"))

    def test_baseline_only_once(self):
        with patch(
            "src.service.main_flats_parser.request_json",
            return_value={"apartments": [raw_onliner()], "page": {"last": 1}},
        ):
            fetch_cycle(self.store, "onliner")
        self.assertIsNone(self.store.next_item("inbox"))
        with patch(
            "src.service.main_flats_parser.request_json",
            return_value={
                "apartments": [raw_onliner(2), raw_onliner()],
                "page": {"last": 1},
            },
        ):
            fetch_cycle(Store(self.path), "onliner")
        self.assertEqual(self.store.next_item("inbox")["id"], "2")

    def test_source_restart_retries_bad_initialization(self):
        with patch(
            "src.service.main_flats_parser.request_json", side_effect=TimeoutError
        ):
            with self.assertRaises(TimeoutError):
                fetch_cycle(self.store, "kufar")
        self.assertFalse(self.store.initialized("kufar"))

    def test_partial_pagination_does_not_commit(self):
        self.store.ingest("onliner", [raw_onliner()], "id", baseline=True)
        with patch(
            "src.service.main_flats_parser.request_json",
            side_effect=[
                {"apartments": [raw_onliner(2)], "page": {"last": 2}},
                TimeoutError,
            ],
        ):
            with self.assertRaises(TimeoutError):
                fetch_cycle(self.store, "onliner")
        self.assertEqual(self.store.known("onliner", [2]), set())

    def test_pages_until_known_page(self):
        self.store.ingest("onliner", [raw_onliner()], "id", baseline=True)
        with patch(
            "src.service.main_flats_parser.request_json",
            side_effect=[
                {"apartments": [raw_onliner(2)], "page": {"last": 2}},
                {"apartments": [raw_onliner()], "page": {"last": 2}},
            ],
        ) as fetch:
            fetch_cycle(self.store, "onliner")
        self.assertEqual(fetch.call_count, 2)
        self.assertEqual(self.store.next_item("inbox")["id"], "2")

    def test_bad_ad_is_preserved_without_poisoning_next(self):
        bad = raw_onliner()
        bad["price"]["amount"] = "NaN"
        self.store.ingest("onliner", [bad, raw_onliner(2)], "id")
        process_item(self.store, self.store.next_item("inbox"))
        self.assertEqual(self.store.next_item("inbox")["id"], "2")
        with self.store.connect() as c:
            self.assertEqual(
                c.execute("SELECT status FROM inbox WHERE id='1'").fetchone()[0],
                "failed",
            )

    def test_database_outage_does_not_ack(self):
        item = self.pending()
        with patch("src.shared.db.get_active_users", side_effect=ConnectionError):
            with self.assertRaises(ConnectionError):
                process_item(self.store, item)
        self.assertIsNotNone(self.store.next_item("inbox"))

    def test_invalid_user_isolated(self):
        with patch(
            "src.shared.db.get_active_users",
            return_value=[{"id_tg": 1, "params": {}}, {"id_tg": 2, "params": params()}],
        ):
            process_item(self.store, self.pending())
        self.assertEqual(self.store.next_item("outbox")["chat_id"], 1)
        with self.store.connect() as c:
            self.assertEqual(c.execute("SELECT count(*) FROM outbox").fetchone()[0], 2)

    def test_429_obeys_retry_after_and_keeps_payload(self):
        item = self.queued()
        with (
            patch(
                "src.shared.db.get_delivery_user",
                return_value={"isactive": True, "params": params()},
            ),
            patch(
                "src.service.main_flats_parser.send_ad",
                side_effect=TelegramFailure(429, "rate limit", 75),
            ),
        ):
            self.assertEqual(deliver_item(self.store, item), 75)
        with self.store.connect() as c:
            row = c.execute("SELECT * FROM outbox").fetchone()
            self.assertEqual(row["status"], "pending")
            self.assertEqual(row["payload"], item["payload"])
            self.assertEqual(row["attempts"], 1)
        self.assertIsNone(self.store.next_item("outbox"))

    def test_blocked_user_disabled(self):
        item = self.queued()
        with (
            patch(
                "src.shared.db.get_delivery_user",
                return_value={"isactive": True, "params": params()},
            ),
            patch(
                "src.service.main_flats_parser.send_ad",
                side_effect=TelegramFailure(403, "blocked"),
            ),
            patch("src.shared.db.set_user_status") as disable,
        ):
            deliver_item(self.store, item)
            disable.assert_called_once_with(123, False)
        self.assertIsNone(self.store.next_item("outbox"))

    def test_pause_cancels_queued_delivery(self):
        item = self.queued()
        with (
            patch(
                "src.shared.db.get_delivery_user",
                return_value={"isactive": False, "params": params()},
            ),
            patch("src.service.main_flats_parser.send_ad") as send,
        ):
            deliver_item(self.store, item)
            send.assert_not_called()

    def test_timeout_keeps_delivery_unacked(self):
        item = self.queued()
        with (
            patch(
                "src.shared.db.get_delivery_user",
                return_value={"isactive": True, "params": params()},
            ),
            patch("src.service.main_flats_parser.send_ad", side_effect=TimeoutError),
        ):
            with self.assertRaises(TimeoutError):
                deliver_item(self.store, item)
        self.assertIsNotNone(self.store.next_item("outbox"))

    def test_catchup_cursor_survives_restart(self):
        self.store.ingest("onliner", [raw_onliner()], "id", baseline=True)
        pages = [
            {"apartments": [raw_onliner(4)], "page": {"last": 4}},
            {"apartments": [raw_onliner(3)], "page": {"last": 4}},
        ]
        with (
            patch.dict("os.environ", MAX_PAGES="2"),
            patch("src.service.main_flats_parser.request_json", side_effect=pages),
        ):
            fetch_cycle(self.store, "onliner")
        self.assertEqual(Store(self.path).scan("onliner")["page"], 3)
        pages = [
            {"apartments": [raw_onliner(4)], "page": {"last": 4}},
            {"apartments": [raw_onliner(2)], "page": {"last": 4}},
            {"apartments": [raw_onliner()], "page": {"last": 4}},
        ]
        with (
            patch.dict("os.environ", MAX_PAGES="3"),
            patch(
                "src.service.main_flats_parser.request_json", side_effect=pages
            ) as request,
        ):
            fetch_cycle(Store(self.path), "onliner")
            self.assertIn("page=3", request.call_args_list[1].args[0])
        self.assertIsNone(self.store.scan("onliner"))
        self.assertEqual(
            self.store.known("onliner", [1, 2, 3, 4]), {"1", "2", "3", "4"}
        )

    def test_maintenance_never_deletes_pending_or_failed(self):
        self.queued()
        with self.store.connect() as c:
            c.execute("UPDATE inbox SET created=0")
            c.execute("UPDATE outbox SET created=0")
        self.store.maintain()
        self.assertIsNotNone(self.store.next_item("outbox"))
        self.assertEqual(self.store.known("onliner", [1]), {"1"})

    def test_cooldown_does_not_block_other_chats(self):
        item = self.pending()
        self.store.enqueue(item, asdict(ad()), [123, 456])
        self.store.cooldown(123, 10)
        self.assertEqual(self.store.next_item("outbox")["chat_id"], 456)


class ParsingTests(unittest.TestCase):
    def test_address_variants(self):
        for address, expected in [
            ("Minsk, Street", "Минск"),
            ("Гомель, Улица", "Гомель"),
            ("Беларусь, г. Минск, Улица", "Минск"),
            ("Ждановичский сельский Совет, Ратомка, Улица", "Ратомка"),
        ]:
            self.assertEqual(address_town(address), expected)

    def test_user_address_fallback(self):
        raw = raw_onliner()
        raw["location"]["address"] = ""
        raw["location"]["user_address"] = "Минск"
        self.assertEqual(generate_ad_from_onliner(raw).town, "Минск")

    def test_minor_units_zero_missing_images_and_coordinates(self):
        raw = {
            "ad_parameters": [{"p": "area", "vl": "Могилев"}, {"p": "rooms", "v": "2"}],
            "ad_link": "https://re.kufar.by/vi/1",
            "price_usd": "5",
        }
        result = generate_ad_from_kufar(raw)
        self.assertEqual(result.cost, 0.05)
        self.assertEqual(result.town, "Могилёв")
        self.assertEqual(result.photos, [])
        self.assertIsNone(result.latitude)
        raw["price_usd"] = "0"
        self.assertEqual(generate_ad_from_kufar(raw).cost, 0)

    def test_geo_missing_only_excludes_geo_filters(self):
        a = ad()
        a.latitude = a.longitude = None
        self.assertTrue(is_comparable(params(), a))
        p = params()
        p["isPointNeed"] = True
        self.assertFalse(is_comparable(p, a))

    def test_sources_filter(self):
        p = params()
        p["source"] = ["kufar"]
        self.assertFalse(is_comparable(p, ad()))

    def test_coordinates_reject_nan_allow_negative(self):
        self.assertTrue(is_coordinates("-33, -70"))
        self.assertFalse(is_coordinates("nan, 20"))
        self.assertFalse(is_coordinates("91, 20"))

    def test_html_escaped(self):
        a = ad()
        a.author_name = "<script>&"
        self.assertIn("&lt;script&gt;&amp;", a.create_telegram_caption())

    def test_room_full_number(self):
        raw = raw_onliner()
        raw["rent_type"] = "12_rooms"
        self.assertEqual(generate_ad_from_onliner(raw).rooms_amount, "12")


class TelegramTests(unittest.TestCase):
    def test_media_400_falls_back_to_text(self):
        a = ad()
        a.photos *= 3
        with patch(
            "src.service.telegram.call",
            side_effect=[TelegramFailure(400, "bad image"), {}],
        ) as send:
            send_ad(123, a)
            self.assertEqual(send.call_args_list[-1].args[0], "sendMessage")

    def test_timeout_does_not_fallback_and_duplicate(self):
        with patch("src.service.telegram.call", side_effect=TimeoutError) as send:
            with self.assertRaises(TimeoutError):
                send_ad(123, ad())
            self.assertEqual(send.call_count, 1)

    def test_album_limited_to_ten(self):
        a = ad()
        a.photos *= 20
        with patch("src.service.telegram.call") as send:
            send_ad(1, a)
            self.assertEqual(len(send.call_args.args[1]["media"]), 10)

    def test_http_429_description_and_parameters(self):
        with (
            patch.dict("os.environ", BOT_TOKEN="fake"),
            patch(
                "src.service.telegram.request_json",
                side_effect=HTTPFailure(
                    429, {"description": "wait", "parameters": {"retry_after": 42}}
                ),
            ),
        ):
            with self.assertRaises(TelegramFailure) as cm:
                call("sendMessage", {})
            self.assertEqual(cm.exception.retry_after, 42)

    def test_json_false_is_failure_even_http_success(self):
        with (
            patch.dict("os.environ", BOT_TOKEN="fake"),
            patch(
                "src.service.telegram.request_json",
                return_value={
                    "ok": False,
                    "error_code": 401,
                    "description": "unauthorized",
                },
            ),
        ):
            with self.assertRaises(TelegramFailure):
                call("sendMessage", {})


class LoggingTests(unittest.TestCase):
    def test_secret_removed_from_exception_and_message(self):
        token = "123456789:" + ("a" * 35)
        try:
            raise RuntimeError(
                f"https://api.telegram.org/bot{token}/sendMessage http://login:secret@proxy:8080"
            )
        except RuntimeError:
            import sys

            record = logging.LogRecord("x", 40, "", 1, token, (), sys.exc_info())
        result = SafeFormatter().format(record)
        self.assertNotIn(token, result)
        self.assertNotIn("login:secret", result)
        self.assertIn("RuntimeError", result)

    def test_critical_alert_persists_and_deduplicates(self):
        from src.shared.observability import AlertHandler

        with (
            tempfile.TemporaryDirectory() as d,
            patch("src.shared.observability.DATA_DIR", Path(d)),
            patch("threading.Thread.start"),
        ):
            handler = AlertHandler("test")
            handler.setFormatter(SafeFormatter())
            record = logging.LogRecord(
                "module", 50, "", 1, "Failure for id=%s", (1,), None
            )
            handler.emit(record)
            record.args = (2,)
            handler.emit(record)
            restarted = AlertHandler("test")
            import sqlite3

            with sqlite3.connect(restarted.path) as c:
                row = c.execute("SELECT count(*),status,text FROM alerts").fetchone()
            self.assertEqual(row[0], 1)
            self.assertEqual(row[1], "pending")
            self.assertIn("id=1", row[2])


class DBTests(unittest.TestCase):
    def test_rollback_and_close_on_error(self):
        with patch("src.shared.db.psycopg2.connect") as connect:
            with self.assertRaises(ValueError):
                with db.Database():
                    raise ValueError()
            connect.return_value.rollback.assert_called_once()
            connect.return_value.commit.assert_not_called()
            connect.return_value.close.assert_called_once()

    def test_parameterized_user_data(self):
        with patch("src.shared.db.psycopg2.connect") as connect:
            db.add_user(1, "x'); DROP TABLE users;--")
            sql, values = (
                connect.return_value.cursor.return_value.execute.call_args.args
            )
            self.assertNotIn("DROP", sql)
            self.assertEqual(values[1], "x'); DROP TABLE users;--")


class FSMTests(unittest.IsolatedAsyncioTestCase):
    async def test_restart_and_updates(self):
        from aiogram.fsm.storage.base import StorageKey
        from aiogram.fsm.context import FSMContext

        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "fsm.db"
            s = SQLiteStorage(path)
            key = StorageKey(bot_id=1, chat_id=1, user_id=1)
            await s.set_state(key, "State:sending")
            await s.set_data(key, {"a": 1})
            s = SQLiteStorage(path)
            self.assertEqual(await s.get_state(key), "State:sending")
            await s.update_data(key, {"b": 2})
            self.assertEqual(await s.get_data(key), {"a": 1, "b": 2})
            await FSMContext(s, key).clear()
            self.assertIsNone(await s.get_state(key))
            self.assertEqual(await s.get_data(key), {})


if __name__ == "__main__":
    unittest.main()
