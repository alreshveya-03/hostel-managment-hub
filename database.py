"""
database.py  –  thin wrapper around mysql-connector-python
"""
import mysql.connector
from flask import current_app, g


def get_db():
    if 'db' not in g:
        cfg = current_app.config
        g.db = mysql.connector.connect(
            host=cfg['MYSQL_HOST'],
            port=cfg['MYSQL_PORT'],
            user=cfg['MYSQL_USER'],
            password=cfg['MYSQL_PASSWORD'],
            database=cfg['MYSQL_DB'],
            autocommit=False,
        )
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
        except Exception:
            pass


# ── helpers ──────────────────────────────────────────────────

def fetch_one(query, params=None):
    db  = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute(query, params or ())
        return cur.fetchone()
    finally:
        cur.close()


def fetch_all(query, params=None):
    db  = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute(query, params or ())
        return cur.fetchall()
    finally:
        cur.close()


def execute_query(query, params=None):
    db  = get_db()
    cur = db.cursor()
    try:
        cur.execute(query, params or ())
        db.commit()
        return cur.rowcount
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()


def insert_and_get_id(query, params=None):
    db  = get_db()
    cur = db.cursor()
    try:
        cur.execute(query, params or ())
        db.commit()
        return cur.lastrowid
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()
