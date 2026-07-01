from __future__ import annotations
"""
Database abstraction layer.
PostgreSQL (Supabase) in production, SQLite fallback for local dev.
"""
import os
import threading
from typing import Any

_local = threading.local()
_IS_POSTGRES = False
_DB_URL = None
_backend_detected = False


def _detect_backend():
    global _IS_POSTGRES, _DB_URL, _backend_detected
    if _backend_detected:
        return
    _backend_detected = True

    # Try Streamlit secrets — multiple access patterns for robustness
    try:
        import streamlit as st
        url = ""
        try:
            url = st.secrets["database"]["url"]          # direct key access
        except Exception:
            try:
                url = st.secrets.get("database", {}).get("url", "")
            except Exception:
                pass
        url = str(url).strip()
        if url and ("postgresql" in url or "postgres" in url):
            if "sslmode" not in url:
                url += ("&" if "?" in url else "?") + "sslmode=require"
            _IS_POSTGRES = True
            _DB_URL = url
            return
    except Exception:
        pass

    # Try DATABASE_URL environment variable
    env_url = os.environ.get("DATABASE_URL", "").strip()
    if env_url and ("postgresql" in env_url or "postgres" in env_url):
        if "sslmode" not in env_url:
            env_url += ("&" if "?" in env_url else "?") + "sslmode=require"
        _IS_POSTGRES = True
        _DB_URL = env_url


def _open_sqlite():
    import sqlite3
    if os.path.exists('/home/adminuser'):
        db_path = '/tmp/commission_web.db'
    else:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'commission_web.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Note: foreign_keys OFF (default) to avoid FK errors during seed on SQLite
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def get_conn():
    global _IS_POSTGRES
    _detect_backend()

    conn = getattr(_local, 'conn', None)
    is_pg = getattr(_local, 'is_pg', False)

    if conn is None or (is_pg and getattr(conn, 'closed', 0) != 0):
        if _IS_POSTGRES:
            # Try psycopg2 first (C extension, best performance)
            try:
                import psycopg2
                conn = psycopg2.connect(_DB_URL)
                conn.autocommit = True
                _local.conn = conn
                _local.is_pg = True
                return conn
            except ImportError:
                pass
            except Exception:
                _IS_POSTGRES = False
                _local.is_pg = False

        # Try pg8000 (pure Python — works on any Python version)
        if _IS_POSTGRES:
            try:
                import pg8000.dbapi as _pg
                import urllib.parse as _up
                _p = _up.urlparse(_DB_URL)
                _db = (_p.path or '/postgres').lstrip('/').split('?')[0] or 'postgres'
                conn = _pg.connect(
                    host=_p.hostname,
                    port=_p.port or 5432,
                    database=_db,
                    user=_p.username,
                    password=_p.password,
                    ssl_context=True,
                )
                conn.autocommit = True
                _local.conn = conn
                _local.is_pg = True
                return conn
            except Exception:
                _IS_POSTGRES = False
                _local.is_pg = False

        _local.conn = _open_sqlite()
        _local.is_pg = False

    return _local.conn


def _adapt_sql(sql: str) -> str:
    return sql if getattr(_local, 'is_pg', False) else sql.replace('%s', '?')


def execute(sql: str, params: tuple = ()) -> Any:
    conn = get_conn()
    sql = _adapt_sql(sql)
    cur = conn.cursor()
    if getattr(_local, 'is_pg', False):
        cur.execute(sql, params)
    else:
        try:
            cur.execute(sql, params)
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            raise
    return cur


def fetchall(sql: str, params: tuple = ()) -> list:
    conn = get_conn()
    sql = _adapt_sql(sql)
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    if getattr(_local, 'is_pg', False):
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in rows]
    try:
        return [dict(row) for row in rows]
    except Exception:
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in rows]


def fetchone(sql: str, params: tuple = ()) -> dict | None:
    rows = fetchall(sql, params)
    return rows[0] if rows else None


def lastrowid(cur) -> int:
    if getattr(_local, 'is_pg', False):
        return cur.fetchone()[0] if cur.rowcount else None
    return cur.lastrowid


def is_postgres() -> bool:
    _detect_backend()
    return _IS_POSTGRES
