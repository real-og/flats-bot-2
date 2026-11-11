"""Run with python -m src.service.main_flats_parser."""

from dataclasses import asdict
import fcntl
import json
import logging
import os
import random
import shutil
import signal
import threading
import time
from urllib.parse import urlencode
from src.shared.config import DATA_DIR, required, proxy
from src.shared.http import request_json
from src.shared.observability import configure_logging, redact
from src.shared import db
from src.shared.logic import is_comparable
from src.service.store import Store
from src.service.ad import Ad
from src.service.telegram import send_ad, TelegramFailure
from src.service.kufar_parser import kufar_url, kufar_params, generate_ad_from_kufar
from src.service.onliner_parser import (
    onliner_url,
    onliner_params,
    generate_ad_from_onliner,
)

log = logging.getLogger(__name__)
SOURCES = ("kufar", "kufar_rooms", "onliner")


def fetch_cycle(store, source):
    baseline = not store.initialized(source)
    key = "id" if source == "onliner" else "ad_id"
    params = dict(onliner_params if source == "onliner" else kufar_params)
    if source == "kufar_rooms":
        params["cat"] = "1040"
    url = onliner_url if source == "onliner" else kufar_url
    max_pages = int(os.environ.get("MAX_PAGES", "10"))
    if not 2 <= max_pages <= 100:
        raise ValueError("MAX_PAGES must be between 2 and 100")
    continuation = store.scan(source)
    collected = []

    def commit(scan=None):
        store.ingest(
            source, list(reversed(collected)), key, baseline=baseline, scan=scan
        )

    for page in range(1, max_pages + 1):
        result = request_json(
            url + "?" + urlencode(params), proxy=proxy("SOURCE_PROXY")
        )
        ads = result.get("apartments" if source == "onliner" else "ads")
        if not isinstance(ads, list) or not ads:
            raise ValueError(f"{source}: empty or invalid feed")
        valid = [ad for ad in ads if isinstance(ad, dict) and ad.get(key) is not None]
        if len(valid) != len(ads):
            log.error("%s: %s items without IDs skipped", source, len(ads) - len(valid))
        if not valid:
            raise ValueError(f"{source}: no valid IDs")
        known = store.known(source, [ad[key] for ad in valid])
        collected.extend(valid)
        if page == 1 and continuation:
            params = continuation
            continue
        if baseline or len(known) == len(valid):
            commit()
            return
        if source == "onliner":
            last = result.get("page", {}).get("last")
            if last is None:
                raise ValueError("Onliner pagination missing")
            current = int(params["page"])
            if current >= int(last):
                commit()
                return
            params["page"] = current + 1
        else:
            pagination = result.get("pagination")
            if not isinstance(pagination, dict) or "pages" not in pagination:
                raise ValueError("Kufar pagination missing")
            nxt = next(
                (p for p in pagination["pages"] if p.get("label") == "next"), None
            )
            if not nxt:
                commit()
                return
            if not nxt.get("token"):
                raise ValueError("Kufar next-page token missing")
            params["cursor"] = nxt["token"]
    commit(scan=params)
    log.critical(
        "%s: catch-up reached MAX_PAGES; saved cursor will continue next cycle", source
    )


def process_item(store, item):
    raw = json.loads(item["payload"])
    try:
        ad = (
            generate_ad_from_onliner(raw)
            if item["source"] == "onliner"
            else generate_ad_from_kufar(raw, room=item["source"] == "kufar_rooms")
        )
    except (ValueError, TypeError, KeyError, IndexError, ArithmeticError) as exc:
        # Preserve malformed payload for inspection/replay, don't poison the batch.
        store.retry("inbox", item, redact(str(exc)), permanent=True)
        log.critical(
            "Invalid listing preserved in inbox: source=%s id=%s error=%s",
            item["source"],
            item["id"],
            type(exc).__name__,
        )
        return
    recipients = []
    for user in db.get_active_users():
        try:
            if is_comparable(user["params"], ad):
                recipients.append(user["id_tg"])
        except (ValueError, TypeError, KeyError, IndexError):
            log.error("Invalid filters for user=%s", user["id_tg"])
            recipients.append(
                user["id_tg"]
            )  # Preserve a retryable failed delivery instead of losing it.
    store.enqueue(item, asdict(ad), recipients)


def deliver_item(store, item):
    # Respect unsubscribe/filter changes even for an old queued message.
    user = db.get_delivery_user(item["chat_id"])
    ad = Ad(**json.loads(item["payload"]))
    try:
        eligible = bool(user and user["isactive"] and is_comparable(user["params"], ad))
    except (ValueError, TypeError, KeyError, IndexError):
        store.retry("outbox", item, "Invalid user filters", permanent=True)
        log.critical(
            "Invalid user filters; delivery preserved for review: chat=%s",
            item["chat_id"],
        )
        return 0
    if not eligible:
        store.finish("outbox", item["rowid"], "cancelled")
        return 0
    try:
        send_ad(item["chat_id"], ad)
    except TelegramFailure as exc:
        if exc.code == 403 or (
            exc.code == 400 and "chat not found" in str(exc).lower()
        ):
            db.set_user_status(item["chat_id"], False)
            store.finish("outbox", item["rowid"], "blocked")
            log.warning("Unavailable Telegram recipient disabled: %s", item["chat_id"])
        elif exc.code == 429:
            delay = max(1, int(exc.retry_after or 30))
            store.retry("outbox", item, str(exc), delay=delay)
            log.warning("Telegram rate limit: retry in %s seconds", delay)
            return delay
        elif exc.code in (400, 404):
            store.retry("outbox", item, str(exc), permanent=True)
            log.critical(
                "Permanent delivery failure: source=%s id=%s chat=%s %s",
                item["source"],
                item["ad_id"],
                item["chat_id"],
                exc,
            )
        else:
            raise
    else:
        store.finish("outbox", item["rowid"])
        store.cooldown(item["chat_id"], 1.1)
    return max(
        0.1, len(ad.photos) * 0.1
    )  # At most 10 media/messages per second, with per-chat cooldown.


def main():
    configure_logging("parser")
    required("BOT_TOKEN")
    required("ADMIN_ID")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    lock = open(DATA_DIR / "parser.lock", "w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    store = Store()
    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())
    heartbeats = {}
    healthy = {}
    started = time.monotonic()

    def worker(name, action, interval):
        failures = 0
        while not stop.is_set():
            heartbeats[name] = time.monotonic()
            try:
                delay = action()
                if failures:
                    log.info("%s recovered after %s failures", name, failures)
                failures = 0
                healthy[name] = time.monotonic()
            except Exception as exc:
                failures += 1
                log.warning("%s failed: %s", name, redact(str(exc)), exc_info=True)
                if failures == 5 or failures % 30 == 0:
                    log.critical("%s repeatedly failing (%s attempts)", name, failures)
                delay = min(300, 2 ** min(failures, 8)) + random.random()
            heartbeats[name] = time.monotonic()
            stop.wait(interval if delay is None else delay)

    def queue_action(table):
        item = store.next_item(table)
        if item is None:
            return 1
        try:
            if table == "inbox":
                process_item(store, item)
                return 0
            return deliver_item(store, item)
        except Exception as exc:
            store.retry(table, item, redact(str(exc)))
            if (
                item["attempts"] in (4, 29)
                or isinstance(exc, TelegramFailure)
                and exc.code == 401
            ):
                log.critical(
                    "%s delivery pipeline unavailable: %s", table, redact(str(exc))
                )
            raise

    threads = []
    for name in SOURCES + ("inbox", "outbox"):
        action = (
            (lambda n=name: fetch_cycle(store, n))
            if name in SOURCES
            else (lambda n=name: queue_action(n))
        )
        thread = threading.Thread(
            target=worker,
            args=(name, action, 30 if name in SOURCES else 1),
            name=name,
            daemon=True,
        )
        threads.append(thread)
        thread.start()
    last_maintenance = time.monotonic()
    log.info("Parser started; durable queue=%s", store.path)
    while not stop.wait(30):
        now = time.monotonic()
        for thread in threads:
            if (
                not thread.is_alive()
                or now - heartbeats.get(thread.name, started) > 600
            ):
                log.critical(
                    "Worker dead or stalled: %s; exiting for systemd restart",
                    thread.name,
                )
                time.sleep(1)
                os._exit(1)
            if now - healthy.get(thread.name, started) > 600:
                log.critical(
                    "Worker has no successful cycle for 10 minutes: %s", thread.name
                )
        if now - last_maintenance > 3600:
            store.maintain()
            last_maintenance = now
        if shutil.disk_usage(DATA_DIR).free < 100 * 1024 * 1024:
            log.critical("Less than 100 MiB disk space remains for the queue")
        status = store.status()
        log.info("Queue status: %s", status)
        for table, rows in status.items():
            for row in rows:
                if row["status"] == "pending" and time.time() - row["oldest"] > 1800:
                    log.critical("Queue backlog older than 30 minutes: %s", table)
    for thread in threads:
        thread.join(timeout=25)
    log.info("Parser stopped; unfinished items remain in queue")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.critical("Parser stopped unexpectedly", exc_info=True)
        raise
