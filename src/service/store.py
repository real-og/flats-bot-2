"""Single-host durable inbox/outbox. One parser process owns dispatch (file lock)."""

from contextlib import contextmanager
import json
import sqlite3
import time
from src.shared.config import DATA_DIR


class Store:
    def __init__(self, path=None):
        self.path = path or DATA_DIR / "delivery.sqlite3"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS sources (name TEXT PRIMARY KEY, success REAL NOT NULL, scan TEXT);
                CREATE TABLE IF NOT EXISTS inbox (
                    source TEXT, id TEXT, payload TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
                    attempts INTEGER NOT NULL DEFAULT 0, due REAL NOT NULL DEFAULT 0,
                    error TEXT, created REAL NOT NULL, PRIMARY KEY(source,id));
                CREATE INDEX IF NOT EXISTS inbox_due ON inbox(status,due);
                CREATE TABLE IF NOT EXISTS outbox (
                    source TEXT, ad_id TEXT, chat_id INTEGER, payload TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending', attempts INTEGER NOT NULL DEFAULT 0,
                    due REAL NOT NULL DEFAULT 0, error TEXT, created REAL NOT NULL,
                    PRIMARY KEY(source,ad_id,chat_id));
                CREATE INDEX IF NOT EXISTS outbox_due ON outbox(status,due);
                CREATE INDEX IF NOT EXISTS outbox_chat ON outbox(chat_id,status);
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def known(self, source, ids):
        with self.connect() as db:
            return {
                str(i)
                for i in ids
                if db.execute(
                    "SELECT 1 FROM inbox WHERE source=? AND id=?", (source, str(i))
                ).fetchone()
            }

    def initialized(self, source):
        with self.connect() as db:
            return bool(
                db.execute("SELECT 1 FROM sources WHERE name=?", (source,)).fetchone()
            )

    def ingest(self, source, ads, id_key, baseline=False, scan=None):
        now = time.time()
        with self.connect() as db:
            for ad in ads:
                db.execute(
                    "INSERT OR IGNORE INTO inbox(source,id,payload,status,created) VALUES(?,?,?,?,?)",
                    (
                        source,
                        str(ad[id_key]),
                        json.dumps(ad, ensure_ascii=False),
                        "baseline" if baseline else "pending",
                        now,
                    ),
                )
            db.execute(
                "INSERT INTO sources(name,success,scan) VALUES(?,?,?) ON CONFLICT(name) DO UPDATE SET success=excluded.success,scan=excluded.scan",
                (source, now, json.dumps(scan) if scan else None),
            )

    def next_item(self, table):
        assert table in ("inbox", "outbox")
        with self.connect() as db:
            row = db.execute(
                f"SELECT rowid,* FROM {table} WHERE status='pending' AND due<=? ORDER BY due,created LIMIT 1",
                (time.time(),),
            ).fetchone()
            return dict(row) if row else None

    def enqueue(self, item, ad, recipients):
        with self.connect() as db:
            for chat_id in recipients:
                db.execute(
                    "INSERT OR IGNORE INTO outbox(source,ad_id,chat_id,payload,created) VALUES(?,?,?,?,?)",
                    (
                        item["source"],
                        item["id"],
                        chat_id,
                        json.dumps(ad, ensure_ascii=False),
                        time.time(),
                    ),
                )
            db.execute(
                "UPDATE inbox SET status='done',error=NULL WHERE rowid=?",
                (item["rowid"],),
            )

    def finish(self, table, rowid, status="done"):
        assert table in ("inbox", "outbox")
        with self.connect() as db:
            db.execute(
                f"UPDATE {table} SET status=?,error=NULL WHERE rowid=?", (status, rowid)
            )

    def retry(self, table, item, error, delay=None, permanent=False):
        assert table in ("inbox", "outbox")
        attempts = item["attempts"] + 1
        delay = delay if delay is not None else min(1800, 2 ** min(attempts, 11))
        with self.connect() as db:
            db.execute(
                f"UPDATE {table} SET attempts=?,due=?,error=?,status=? WHERE rowid=?",
                (
                    attempts,
                    time.time() + delay,
                    str(error)[:500],
                    "failed" if permanent else "pending",
                    item["rowid"],
                ),
            )

    def status(self):
        with self.connect() as db:
            return {
                table: [
                    dict(r)
                    for r in db.execute(
                        f"SELECT status,count(*) AS count,min(created) AS oldest FROM {table} GROUP BY status"
                    )
                ]
                for table in ("inbox", "outbox")
            }

    def maintain(self):
        """Keep dedup keys, compact old successful payloads. Never prune pending/failed."""
        cutoff = time.time() - 30 * 86400
        with self.connect() as db:
            db.execute(
                "DELETE FROM outbox WHERE created<? AND status IN ('done','cancelled','blocked')",
                (cutoff,),
            )
            db.execute(
                "UPDATE inbox SET payload='{}' WHERE created<? AND status IN ('done','baseline') AND payload!='{}'",
                (cutoff,),
            )
        with self.connect() as db:
            db.execute("PRAGMA wal_checkpoint(PASSIVE)")

    def cooldown(self, chat_id, seconds):
        with self.connect() as db:
            db.execute(
                "UPDATE outbox SET due=max(due,?) WHERE chat_id=? AND status='pending'",
                (time.time() + seconds, chat_id),
            )

    def scan(self, source):
        with self.connect() as db:
            row = db.execute(
                "SELECT scan FROM sources WHERE name=?", (source,)
            ).fetchone()
            return json.loads(row[0]) if row and row[0] else None
