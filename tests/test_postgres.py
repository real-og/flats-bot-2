import os
import uuid
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
import psycopg2
from src.shared import db


@unittest.skipUnless(
    os.environ.get("TEST_POSTGRES_DSN"),
    "Dedicated PostgreSQL test server not configured",
)
class PostgreSQLTests(unittest.TestCase):
    def setUp(self):
        self.dsn = os.environ["TEST_POSTGRES_DSN"]
        self.schema = "test_" + uuid.uuid4().hex
        self.real_connect = psycopg2.connect
        with self.real_connect(self.dsn) as conn:
            with conn.cursor() as c:
                c.execute(f"CREATE SCHEMA {self.schema}")
                c.execute(
                    f"""CREATE TABLE {self.schema}.users(id serial primary key,id_tg bigint unique not null,username varchar(51),isactive boolean default false,jointime timestamp default now(),params json default '{{"town":"","rooms":[],"source":[]}}')"""
                )

        def connect(**kwargs):
            return self.real_connect(
                self.dsn,
                options=f"-c search_path={self.schema} -c statement_timeout=5000 -c lock_timeout=3000",
            )

        self.patch = patch("src.shared.db.psycopg2.connect", side_effect=connect)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        with self.real_connect(self.dsn) as conn:
            with conn.cursor() as c:
                c.execute(f"DROP SCHEMA {self.schema} CASCADE")

    def test_concurrent_registration_and_filter_updates(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda _: db.add_user(123, "O'Reilly"), range(8)))
        self.assertEqual(len(db.get_all_users()), 1)
        with ThreadPoolExecutor(max_workers=2) as pool:
            a = pool.submit(db.edit_town, 123, "O'Reilly")
            b = pool.submit(db.edit_cost, 123, 100, 500)
            a.result()
            b.result()
        p = db.get_user_params(123)
        self.assertEqual(p["town"], "O'Reilly")
        self.assertEqual(p["maxCost"], 500)
        db.set_user_status(123, True)
        self.assertEqual(len(db.get_active_users()), 1)

    def test_transaction_rolls_back(self):
        db.add_user(1)
        with self.assertRaises(RuntimeError):
            with db.Database() as c:
                c.execute("UPDATE users SET isactive=true WHERE id_tg=1")
                raise RuntimeError("interrupted transaction")
        self.assertFalse(db.get_delivery_user(1)["isactive"])
