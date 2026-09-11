import os
import sqlite3
import json
from contextlib import contextmanager

DB_FILE = os.environ.get("SQLITE_DB_PATH", os.path.join(os.path.dirname(__file__), "pcware_production.db"))
SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "schema.sql")

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, timeout=30.0, check_same_thread=False)
    conn.row_factory = dict_factory
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn

@contextmanager
def get_db():
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db(force_reset=False):
    if force_reset and os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    
    with open(SCHEMA_FILE, "r") as f:
        schema_sql = f.read()
        
    with get_db() as conn:
        conn.executescript(schema_sql)
    print(f"Database initialized at {DB_FILE}")

def query_all(query, params=()):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

def query_one(query, params=()):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

def execute_commit(query, params=()):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.lastrowid
