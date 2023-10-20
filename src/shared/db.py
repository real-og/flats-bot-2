import psycopg2
import psycopg2.extras
from typing import List, Literal
import os
import json 

class Database(object):
    def __init__(self):
        self.conn = psycopg2.connect(
            database=str(os.environ.get('database')),
            user=str(os.environ.get('user')),
            password=str(os.environ.get('password')),
            host=str(os.environ.get('host')),
            port=str(os.environ.get('port'))
        )
        self.curs = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def __enter__(self):
        return self.curs

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.commit()
        self.conn.close()

def check_user(id_tg: int) -> bool:
    with Database() as curs:
        _SQL = f"SELECT id FROM users WHERE id_tg = {id_tg};"
        curs.execute(_SQL)
        if len(curs.fetchall()) == 0:
            return False
        return True

def add_user(id_tg: int, username: str=None):
    with Database() as curs:
        if not check_user(id_tg):
            if username:
                _SQL = f'INSERT INTO users (id_tg, username, isActive) VALUES ({id_tg}, $${username}$$, false);'
            else:
                _SQL = f'INSERT INTO users (id_tg, isActive) VALUES ({id_tg}, false);'
            curs.execute(_SQL)

def get_user_params(id_tg: int) -> dict:
    with Database() as curs:
        _SQL = f"SELECT params FROM users WHERE id_tg = {id_tg};"
        curs.execute(_SQL)
        res = curs.fetchall()
        if len(res) == 0:
            return None
        return res[0]['params']

def set_user_params(id_tg: int, data: dict):
    with Database() as curs:
        _SQL = f"UPDATE users SET params = '{json.dumps(data)}' WHERE id_tg = {id_tg};"
        curs.execute(_SQL)

def edit_town(id_tg: int, town: str):
    params = get_user_params(id_tg)
    params['town'] = town
    set_user_params(id_tg, params)

def edit_cost(id_tg: int, minCost: int, maxCost: int):
    params = get_user_params(id_tg)
    params['minCost'] = minCost
    params['maxCost'] = maxCost
    set_user_params(id_tg, params)

def flag_room(id_tg: int, room: Literal['01', '02', '03', '04', '10']):
    if room[0] == '1':
        room = 'Комната'
    else:
        room = room[1]
    params = get_user_params(id_tg)
    if room in params['rooms']:
        params['rooms'].remove(room)
    else:
        params['rooms'].append(room)
    set_user_params(id_tg, params)

def edit_landlord(id_tg: int, lord: str):
    params = get_user_params(id_tg)
    params['landlord'] = lord
    set_user_params(id_tg, params)


def flag_subway(id_tg: int, sub: str):
    """sub is a number from 0 to 32 included as a string"""

    params = get_user_params(id_tg)
    if sub in params['subways']:
        params['subways'].remove(sub)
    else:
        params['subways'].append(sub)
    set_user_params(id_tg, params)


def set_subway_need(id_tg: int, is_need: bool):
    params = get_user_params(id_tg)
    params['isSubwayNeed'] = is_need
    set_user_params(id_tg, params)

def set_point_need(id_tg: int, is_need: bool):
    params = get_user_params(id_tg)
    params['isPointNeed'] = is_need
    set_user_params(id_tg, params)

def set_point(id_tg: int, lat: float, lon: float):
    params = get_user_params(id_tg)
    params['lat'] = lat
    params['lon'] = lon
    set_user_params(id_tg, params)

def set_point_radius(id_tg: int, radius: int):
    params = get_user_params(id_tg)
    params['point_dist'] = radius
    set_user_params(id_tg, params)


def set_sub_distance(id_tg: int, dist: int):
    if dist == 'Не важно':
        dist = 9999999
    else:
        dist = int(dist)
    params = get_user_params(id_tg)
    params['subway_dist'] = dist
    set_user_params(id_tg, params)

def get_active_users() -> List[psycopg2.extras.RealDictRow]:
    with Database() as curs:
        _SQL = "SELECT id_tg, params FROM users WHERE isActive;"
        curs.execute(_SQL)
        return curs.fetchall()
    

def get_all_users() -> List[psycopg2.extras.RealDictRow]:
    with Database() as curs:
        _SQL = "SELECT id_tg FROM users;"
        curs.execute(_SQL)
        return curs.fetchall()
    


def set_user_status(id_tg: int, is_active: bool):
    with Database() as curs:
        _SQL = f"UPDATE users SET isActive = {is_active} WHERE id_tg = {id_tg};"
        curs.execute(_SQL)