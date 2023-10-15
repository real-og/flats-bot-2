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


def get_active_users() -> List[psycopg2.extras.RealDictRow]:
    """returns list of dicts with keys id_tg:int and params:dict"""
    
    with Database() as curs:
        _SQL = "SELECT id_tg, params FROM users WHERE isActive;"
        curs.execute(_SQL)
        return curs.fetchall()