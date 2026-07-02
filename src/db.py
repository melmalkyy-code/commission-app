from __future__ import annotations
"""
Database abstraction layer.
PostgreSQL (Supabase) in production, SQLite fallback for local dev.

Connection strategy:
- PostgreSQL: one psycopg2 connection per thread, re-opened if closed.
  If PG fails at CONNECT time, fall back to SQLite for that thread but
  keep _DB_URL so future threads can retry — never permanently disable PG.
- SQLite: local file, WAL mode, always available.
"""
import os
import threading
from typing import Any

_local    = threading.local()
_DB_URL   = None
_detected = False


def _detect_backend():
    global _DB_URL, _detected
    if _detected:
        return
    _detected = True

    try:
        import streamlit as st
        url = ""
        try:
            url = st.secrets["database"]["url"]
        except Exception:
            try:
                url = st.secrets.get("database", {}).get("url", "")
            except Exception:
                pass
        url = str(url).strip()
        if url and ("postgresql" in url or "postgres" in url):
            if "sslmode" not in url:
                url += ("&" if "?" in url else "?") + "sslmode=require"
            _DB_URL = url
            return
    except Exception:
        pass

    env_url = os.environ.get("DATABASE_URL", "").strip()
    if env_url and ("postgresql" in env_url or "postgres" in env_url):
        if "sslmode" not in env_url:
            env_url += ("&" if "?" in env_url else "?") + "sslmode=require"
        _DB_URL = env_url


def _open_sqlite():
    import sqlite3
    # On Streamlit Cloud, /home/adminuser exists; use /tmp for ephemeral writable storage.
    # For local dev, use the data/ directory next to this file.
    if os.path.exists('/home/adminuser'):
        db_path = '/tmp/commission_web.db'
    else:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'commission_web.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    # isolation_level=None enables autocommit — matches PG's autocommit=True
    # and avoids "cannot commit transaction - SQL statements in progress" errors
    # that occur when conn.commit() is called while a RETURNING cursor is open.
    conn = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _pg_connect():
    """Open a fresh psycopg2 connection. Returns None if unavailable."""
    if not _DB_URL:
        return None
    try:
        import psycopg2
        conn = psycopg2.connect(_DB_URL)
        conn.autocommit = True
        return conn
    except Exception:
        return None


def get_conn():
    """Return a live connection (PostgreSQL preferred, SQLite fallback)."""
    _detect_backend()

    conn  = getattr(_local, 'conn', None)
    is_pg = getattr(_local, 'is_pg', False)

    # Reuse existing PG connection if still open
    if conn is not None and is_pg:
        if getattr(conn, 'closed', 1) == 0:
            return conn
        # Connection was closed — try to reconnect
        conn = _pg_connect()
        if conn:
            _local.conn  = conn
            _local.is_pg = True
            return conn
        # PG unavailable right now — use SQLite for this request only
        _local.conn  = _open_sqlite()
        _local.is_pg = False
        return _local.conn

    # Reuse existing SQLite connection
    if conn is not None and not is_pg:
        return conn

    # First call in this thread — prefer PG if configured
    if _DB_URL:
        pg = _pg_connect()
        if pg:
            _local.conn  = pg
            _local.is_pg = True
            return pg

    # SQLite fallback
    _local.conn  = _open_sqlite()
    _local.is_pg = False
    return _local.conn


def _adapt_sql(sql: str) -> str:
    """Replace %s → ? for SQLite."""
    return sql if getattr(_local, 'is_pg', False) else sql.replace('%s', '?')


def _thread_fallback_to_sqlite():
    """Switch the CURRENT THREAD to SQLite. PG can still be retried next request."""
    _local.is_pg = False
    _local.conn  = _open_sqlite()


def execute(sql: str, params: tuple = ()) -> Any:
    conn    = get_conn()
    adapted = _adapt_sql(sql)
    is_pg   = getattr(_local, 'is_pg', False)
    cur     = conn.cursor()
    try:
        cur.execute(adapted, params)
        # No explicit commit: PG uses autocommit=True, SQLite uses isolation_level=None
        return cur
    except Exception:
        if not is_pg:
            raise
        # PostgreSQL failed mid-query — fall back to SQLite for this thread
        _thread_fallback_to_sqlite()
        adapted2 = sql.replace('%s', '?')
        cur2     = _local.conn.cursor()
        cur2.execute(adapted2, params)
        return cur2


def fetchall(sql: str, params: tuple = ()) -> list:
    conn    = get_conn()
    adapted = _adapt_sql(sql)
    is_pg   = getattr(_local, 'is_pg', False)
    try:
        cur = conn.cursor()
        cur.execute(adapted, params)
        rows = cur.fetchall()
        if is_pg:
            cols   = [d[0] for d in cur.description]
            result = [dict(zip(cols, row)) for row in rows]
        else:
            try:
                result = [dict(row) for row in rows]
            except Exception:
                cols   = [d[0] for d in cur.description]
                result = [dict(zip(cols, row)) for row in rows]
        cur.close()
        return result
    except Exception:
        if not is_pg:
            raise
        _thread_fallback_to_sqlite()
        adapted2 = sql.replace('%s', '?')
        cur2     = _local.conn.cursor()
        cur2.execute(adapted2, params)
        rows2    = cur2.fetchall()
        try:
            result = [dict(row) for row in rows2]
        except Exception:
            cols   = [d[0] for d in cur2.description]
            result = [dict(zip(cols, row)) for row in rows2]
        cur2.close()
        return result


def fetchone(sql: str, params: tuple = ()) -> dict | None:
    rows = fetchall(sql, params)
    return rows[0] if rows else None


def lastrowid(cur) -> int:
    if getattr(_local, 'is_pg', False):
        return cur.fetchone()[0] if cur.rowcount else None
    return cur.lastrowid


def execute_insert(sql: str, params: tuple = ()) -> int:
    """Execute an INSERT and return the new row's id. Works on PostgreSQL and SQLite."""
    is_pg = getattr(_local, 'is_pg', False)
    if is_pg:
        cur = execute(sql + " RETURNING id", params)
        return cur.fetchone()[0]
    cur = execute(sql, params)
    return cur.lastrowid


def is_postgres() -> bool:
    _detect_backend()
    return bool(_DB_URL) and getattr(_local, 'is_pg', False)
