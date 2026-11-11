import logging
from logging.handlers import RotatingFileHandler
import os
import re
import sqlite3
import hashlib
import threading
import time
from src.shared.config import DATA_DIR, LOG_DIR, proxy
from src.shared.http import request_json, HTTPFailure


def redact(text):
    text = re.sub(r"(?<!\d)\d{6,}:[A-Za-z0-9_-]{20,}", "[BOT_TOKEN]", text)
    text = re.sub(r"(https?://)[^\s/@]+:[^\s/@]+@", r"\1[REDACTED]@", text)
    for name in (
        "BOT_TOKEN",
        "ALERT_BOT_TOKEN",
        "password",
        "PGPASSWORD",
        "PROXY",
        "TELEGRAM_PROXY",
        "SOURCE_PROXY",
    ):
        secret = os.environ.get(name)
        if secret and len(secret) >= 4:
            text = text.replace(secret, "[REDACTED]")
    return text


class SafeFormatter(logging.Formatter):
    def format(self, record):
        return redact(super().format(record))


class AlertHandler(logging.Handler):
    """Persistent, deduplicated alerts, one owner per service process."""

    def __init__(self, service):
        super().__init__(logging.CRITICAL)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.path = DATA_DIR / f"alerts-{service}.sqlite3"
        db = sqlite3.connect(self.path)
        try:
            with db:
                db.execute(
                    'CREATE TABLE IF NOT EXISTS alerts(key TEXT PRIMARY KEY,text TEXT,created REAL,due REAL,attempts INTEGER DEFAULT 0,status TEXT DEFAULT "pending")'
                )
        finally:
            db.close()
        threading.Thread(target=self.run, name="critical-alerts", daemon=True).start()

    def emit(self, record):
        key = hashlib.sha256(f"{record.name}:{record.msg}".encode()).hexdigest()
        now = time.time()
        db = None
        try:
            db = sqlite3.connect(self.path, timeout=0.1)
            with db:
                row = db.execute(
                    "SELECT created,status FROM alerts WHERE key=?", (key,)
                ).fetchone()
                if row and (row[1] == "pending" or now - row[0] < 900):
                    return
                db.execute(
                    'INSERT INTO alerts(key,text,created,due) VALUES(?,?,?,?) ON CONFLICT(key) DO UPDATE SET text=excluded.text,created=excluded.created,due=excluded.due,attempts=0,status="pending"',
                    (key, self.format(record)[:3500], now, now),
                )
        except Exception:
            # Disk full/locked: the independent file/stderr log is still attempted.
            pass
        finally:
            if db:
                db.close()

    def run(self):
        token = os.environ.get("ALERT_BOT_TOKEN") or os.environ.get("BOT_TOKEN")
        admin = os.environ.get("ADMIN_ID")
        if not token or not admin:
            return
        while True:
            db = None
            try:
                db = sqlite3.connect(self.path, timeout=1)
                row = db.execute(
                    'SELECT key,text,attempts FROM alerts WHERE status="pending" AND due<=? ORDER BY due LIMIT 1',
                    (time.time(),),
                ).fetchone()
                if not row:
                    time.sleep(1)
                    continue
                success = False
                delay = min(3600, 5 * 2 ** min(row[2], 10))
                try:
                    result = request_json(
                        f"https://api.telegram.org/bot{token}/sendMessage",
                        {"chat_id": admin, "text": row[1]},
                        proxy=proxy("ALERT_PROXY"),
                        timeout=10,
                    )
                    success = bool(result.get("ok"))
                except HTTPFailure as exc:
                    try:
                        delay = max(
                            delay,
                            float(exc.body.get("parameters", {}).get("retry_after", 0)),
                        )
                    except (TypeError, ValueError, AttributeError):
                        pass
                except Exception:
                    pass
                with db:
                    db.execute(
                        "UPDATE alerts SET status=?,due=?,attempts=attempts+1 WHERE key=?",
                        ("done" if success else "pending", time.time() + delay, row[0]),
                    )
                    db.execute(
                        'DELETE FROM alerts WHERE status="done" AND created<?',
                        (time.time() - 30 * 86400,),
                    )
            except Exception:
                time.sleep(5)
            finally:
                if db:
                    db.close()


def configure_logging(service):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    formatter = SafeFormatter(
        "%(asctime)s %(levelname)s %(name)s %(threadName)s %(message)s"
    )
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    for old in root.handlers[:]:
        root.removeHandler(old)
        old.close()
    for handler in (
        logging.StreamHandler(),
        RotatingFileHandler(
            LOG_DIR / f"{service}.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        ),
        logging.NullHandler()
        if os.environ.get("DISABLE_ALERTS") == "1"
        else AlertHandler(service),
    ):
        handler.setFormatter(formatter)
        root.addHandler(handler)
