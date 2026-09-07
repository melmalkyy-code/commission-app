"""Render all pages with synthetic, in-memory data. No live secrets or writes."""
from pathlib import Path
import logging
import sqlite3
import streamlit as st
from streamlit.testing.v1 import AppTest
import src.db as db


def main():
    for name in ('streamlit.runtime.caching.cache_data_api',
                 'streamlit.runtime.scriptrunner_utils.script_run_context'):
        logging.getLogger(name).setLevel(logging.ERROR)
    conn = sqlite3.connect(':memory:', check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    db._detected, db._DB_URL = True, None
    db._open_sqlite = lambda: conn
    st.cache_resource.clear()
    st.cache_data.clear()
    root = Path(__file__).resolve().parent
    app = AppTest.from_file(str(root / 'Home.py'), default_timeout=45)
    for key, value in dict(authenticated=True, username='test_admin',
                           role='admin', full_name='Test Admin').items():
        app.session_state[key] = value
    failures = []
    try:
        app.run()
        errors = [e.message for e in app.exception]
        failures.extend(errors)
        print('PAGE Home.py', errors or 'PASS')
        for page in sorted((root / 'pages').glob('*.py')):
            app.switch_page('pages/' + page.name).run()
            errors = [e.message for e in app.exception]
            failures.extend(errors)
            print('PAGE', page.name, errors or 'PASS')
        if failures:
            raise SystemExit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
