import psycopg2
import psycopg2.extras
from typing import List, Literal
import os
import json
import threading
from functools import wraps

_local = threading.local()


class Database(object):
    def __init__(self):
        self.conn = psycopg2.connect(
            database=str(os.environ.get("database")),
            user=str(os.environ.get("user")),
            password=str(os.environ.get("password")),
            host=str(os.environ.get("host")),
            port=str(os.environ.get("port", "5432")),
            connect_timeout=5,
            options="-c statement_timeout=5000 -c lock_timeout=3000",
        )
        self.curs = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def __enter__(self):
        return self.curs

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
        finally:
            self.curs.close()
            self.conn.close()


def check_user(id_tg: int) -> bool:
    with Database() as curs:
        curs.execute("SELECT 1 FROM users WHERE id_tg=%s", (id_tg,))
        return curs.fetchone() is not None


def add_user(id_tg: int, username: str = None):
    with Database() as curs:
        curs.execute(
            "INSERT INTO users(id_tg,username) VALUES(%s,%s) ON CONFLICT(id_tg) DO UPDATE SET username=EXCLUDED.username",
            (id_tg, username),
        )


def get_user_params(id_tg: int) -> dict:
    cursor = getattr(_local, "cursor", None)
    if cursor:
        cursor.execute("SELECT params FROM users WHERE id_tg=%s FOR UPDATE", (id_tg,))
        row = cursor.fetchone()
    else:
        with Database() as curs:
            curs.execute("SELECT params FROM users WHERE id_tg=%s", (id_tg,))
            row = curs.fetchone()
    if row is None:
        raise ValueError("User not registered; use /start")
    return row["params"]


def set_user_params(id_tg: int, data: dict):
    cursor = getattr(_local, "cursor", None)
    if cursor:
        cursor.execute(
            "UPDATE users SET params=%s WHERE id_tg=%s", (json.dumps(data), id_tg)
        )
    else:
        with Database() as curs:
            curs.execute(
                "UPDATE users SET params=%s WHERE id_tg=%s", (json.dumps(data), id_tg)
            )


def atomic_edit(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        with Database() as cursor:
            _local.cursor = cursor
            try:
                return fn(*args, **kwargs)
            finally:
                _local.cursor = None

    return wrapped


@atomic_edit
def edit_town(id_tg: int, town: str):
    params = get_user_params(id_tg)
    params["town"] = town
    set_user_params(id_tg, params)


@atomic_edit
def edit_cost(id_tg: int, minCost: int, maxCost: int):
    params = get_user_params(id_tg)
    params["minCost"] = minCost
    params["maxCost"] = maxCost
    set_user_params(id_tg, params)


@atomic_edit
def flag_room(id_tg: int, room: Literal["01", "02", "03", "04", "10"]):
    if room[0] == "1":
        room = "Комната"
    else:
        room = room[1]
    params = get_user_params(id_tg)
    if room in params["rooms"]:
        params["rooms"].remove(room)
    else:
        params["rooms"].append(room)
    set_user_params(id_tg, params)


@atomic_edit
def edit_landlord(id_tg: int, lord: str):
    params = get_user_params(id_tg)
    params["landlord"] = lord
    set_user_params(id_tg, params)


@atomic_edit
def flag_subway(id_tg: int, sub: str):
    """sub is a number from 0 to 32 included as a string"""

    params = get_user_params(id_tg)
    if sub in params["subways"]:
        params["subways"].remove(sub)
    else:
        params["subways"].append(sub)
    set_user_params(id_tg, params)


@atomic_edit
def set_subway_need(id_tg: int, is_need: bool):
    params = get_user_params(id_tg)
    params["isSubwayNeed"] = is_need
    set_user_params(id_tg, params)


@atomic_edit
def set_point_need(id_tg: int, is_need: bool):
    params = get_user_params(id_tg)
    params["isPointNeed"] = is_need
    set_user_params(id_tg, params)


@atomic_edit
def set_point(id_tg: int, lat: float, lon: float):
    params = get_user_params(id_tg)
    params["lat"] = lat
    params["lon"] = lon
    set_user_params(id_tg, params)


@atomic_edit
def set_point_radius(id_tg: int, radius: int):
    params = get_user_params(id_tg)
    params["point_dist"] = radius
    set_user_params(id_tg, params)


@atomic_edit
def set_sub_distance(id_tg: int, dist: int):
    if dist == "Не важно":
        dist = 9999999
    else:
        dist = int(dist)
    params = get_user_params(id_tg)
    params["subway_dist"] = dist
    set_user_params(id_tg, params)


def get_active_users() -> List[psycopg2.extras.RealDictRow]:
    with Database() as curs:
        _SQL = "SELECT id_tg, params FROM users WHERE isActive;"
        curs.execute(_SQL)
        return curs.fetchall()


def get_all_users_ids() -> List[psycopg2.extras.RealDictRow]:
    with Database() as curs:
        _SQL = "SELECT id_tg FROM users;"
        curs.execute(_SQL)
        return curs.fetchall()


def get_all_users() -> List[psycopg2.extras.RealDictRow]:
    with Database() as curs:
        _SQL = "SELECT * FROM users order by jointime;"
        curs.execute(_SQL)
        return curs.fetchall()


def set_user_status(id_tg: int, is_active: bool):
    with Database() as curs:
        curs.execute("UPDATE users SET isactive=%s WHERE id_tg=%s", (is_active, id_tg))


def get_delivery_user(id_tg):
    with Database() as curs:
        curs.execute("SELECT isactive,params FROM users WHERE id_tg=%s", (id_tg,))
        return curs.fetchone()


def ping():
    with Database() as cursor:
        cursor.execute("SELECT 1")
        return cursor.fetchone()[0]


@atomic_edit
def flag_source(id_tg, name):
    if name not in ("onliner", "kufar"):
        raise ValueError("Unknown source")
    params = get_user_params(id_tg)
    values = params.setdefault("source", [])
    if name in values:
        values.remove(name)
    else:
        values.append(name)
    set_user_params(id_tg, params)
