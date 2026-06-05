"""
Database abstraction layer.
Uses Supabase PostgreSQL in production (via st.secrets or DATABASE_URL env var).
Falls back to SQLite for local development.
"""
import os
import threading
from typing import Any

_local = threading.local()
_IS_POSTGRES = False
_DB_URL = None


def _detect_backend():
    global _IS_POSTGRES, _DB_URL
    try:
        import streamlit as st
        url = st.secrets.get("database", {}).get("url", "")
        if url and url.startswith("postgresql"):
            _IS_POSTGRES = True
            _DB_URL = url
            return
    except Exception:
        pass
    env_url = os.environ.get("DATABASE_URL", "")
    if env_url and env_url.startswith("postgresql"):
        _IS_POSTGRES = True
        _DB_URL = env_url


_detect_backend()


def get_conn():
    if not hasattr(_local, 'conn') or _local.conn is None:
        if _IS_POSTGRES:
            import psycopg2
            import psycopg2.extras
            _local.conn = psycopg2.connect(_DB_URL)
            _local.conn.autocommit = False
        else:
            import sqlite3
            db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'commission_web.db')
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            _local.conn = sqlite3.connect(db_path, check_same_thread=False)
            _local.conn.row_factory = sqlite3.Row
            _local.conn.execute("PRAGMA foreign_keys = ON")
    return _local.conn


def _adapt_sql(sql: str) -> str:
    """Convert %s placeholders to ? for SQLite."""
    if not _IS_POSTGRES:
        return sql.replace('%s', '?')
    return sql


def execute(sql: str, params: tuple = ()) -> Any:
    conn = get_conn()
    sql = _adapt_sql(sql)
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    return cur


def fetchall(sql: str, params: tuple = ()) -> list:
    conn = get_conn()
    sql = _adapt_sql(sql)
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    if _IS_POSTGRES:
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in rows]
    return [dict(row) for row in rows]


def fetchone(sql: str, params: tuple = ()) -> dict | None:
    rows = fetchall(sql, params)
    return rows[0] if rows else None


def lastrowid(cur) -> int:
    if _IS_POSTGRES:
        return cur.fetchone()[0] if cur.rowcount else None
    return cur.lastrowid


def is_postgres() -> bool:
    return _IS_POSTGRES
