from __future__ import annotations
"""
Database abstraction layer.
PostgreSQL (Supabase/Neon) in production, SQLite for local development only.

Design rules (do not violate):
1. The backend is decided ONCE by configuration: if a PostgreSQL URL is set
   in secrets/env, this app is PostgreSQL-only. SQLite is used ONLY when no
   URL is configured (local dev).
2. is_postgres() depends only on configuration — never on per-thread
   connection state. SQL dialect decisions (SERIAL vs AUTOINCREMENT,
   ON CONFLICT vs OR IGNORE) must be deterministic.
3. There is NO silent fallback from PostgreSQL to SQLite. A transient PG
   failure triggers one reconnect + retry; if that fails, the error is
   raised and shown to the user. Silently writing to an ephemeral SQLite
   file loses data — that is worse than an error message.
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


def is_postgres() -> bool:
    """True when a PostgreSQL URL is configured. Configuration-based only —
    NEVER per-thread connection state, so SQL dialect is always consistent."""
    _detect_backend()
    return bool(_DB_URL)


def _open_sqlite():
    import sqlite3
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'commission_web.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    # isolation_level=None enables autocommit — matches PG's autocommit=True
    conn = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _pg_connect():
    import psycopg2
    conn = psycopg2.connect(_DB_URL, connect_timeout=10)
    conn.autocommit = True
    return conn


def _close_quietly():
    conn = getattr(_local, 'conn', None)
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass
    _local.conn = None


def get_conn():
    """Return a live connection for the configured backend."""
    _detect_backend()

    if _DB_URL:
        conn = getattr(_local, 'conn', None)
        if conn is not None and getattr(conn, 'closed', 1) == 0:
            return conn
        try:
            conn = _pg_connect()
        except Exception as e:
            raise RuntimeError(
                "Database connection failed — PostgreSQL is unreachable. "
                "Check the connection URL in Streamlit Cloud secrets "
                f"(special characters in the password must be URL-encoded). Detail: {e}"
            ) from e
        _local.conn = conn
        return conn

    # No URL configured — local development on SQLite
    conn = getattr(_local, 'conn', None)
    if conn is not None:
        return conn
    _local.conn = _open_sqlite()
    return _local.conn


def _adapt_sql(sql: str) -> str:
    """PostgreSQL uses %s placeholders; SQLite uses ?."""
    return sql if is_postgres() else sql.replace('%s', '?')


def execute(sql: str, params: tuple = ()) -> Any:
    conn    = get_conn()
    adapted = _adapt_sql(sql)
    try:
        cur = conn.cursor()
        cur.execute(adapted, params)
        return cur
    except Exception:
        if not is_postgres():
            raise
        # The connection may have been dropped by the pooler — reconnect
        # once and retry on PostgreSQL. Real SQL errors fail again and
        # propagate to the caller (shown to the user). NEVER fall back to
        # SQLite: a visible error beats silent data loss.
        _close_quietly()
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute(adapted, params)
        return cur


def execute_many(sql: str, seq_params) -> None:
    """Run one statement for many parameter tuples in a single round-trip.
    Far faster than calling execute() in a loop against a remote database."""
    seq_params = list(seq_params)
    if not seq_params:
        return
    conn    = get_conn()
    adapted = _adapt_sql(sql)
    try:
        cur = conn.cursor()
        cur.executemany(adapted, seq_params)
    except Exception:
        if not is_postgres():
            raise
        _close_quietly()
        conn = get_conn()
        cur  = conn.cursor()
        cur.executemany(adapted, seq_params)


def fetchall(sql: str, params: tuple = ()) -> list:
    cur = execute(sql, params)
    rows = cur.fetchall()
    if is_postgres():
        cols = [d[0] for d in cur.description]
        result = [dict(zip(cols, row)) for row in rows]
    else:
        result = [dict(row) for row in rows]
    cur.close()
    return result


def fetchone(sql: str, params: tuple = ()) -> dict | None:
    rows = fetchall(sql, params)
    return rows[0] if rows else None


def execute_insert(sql: str, params: tuple = ()) -> int:
    """Execute an INSERT and return the new row's id on both backends."""
    if is_postgres():
        cur = execute(sql + " RETURNING id", params)
        return cur.fetchone()[0]
    cur = execute(sql, params)
    return cur.lastrowid


def lastrowid(cur) -> int:
    if is_postgres():
        return cur.fetchone()[0] if cur.rowcount else None
    return cur.lastrowid


def db_status() -> dict:
    """Current backend and reachability — used for the sidebar health badge."""
    _detect_backend()
    if not _DB_URL:
        return {'backend': 'sqlite', 'ok': True,
                'label': 'Local database (dev only)'}
    try:
        cur = execute("SELECT 1", ())
        cur.fetchone()
        return {'backend': 'postgresql', 'ok': True, 'label': 'Cloud database'}
    except Exception as e:
        return {'backend': 'postgresql', 'ok': False,
                'label': 'Database unreachable', 'error': str(e)}
