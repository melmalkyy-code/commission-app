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
        from src.period_selection import current_period, previous_period, selected_period
        from datetime import date
        assert current_period(date(2026, 9, 7)) == (2026, 3)
        assert current_period(date(2027, 1, 1)) == (2027, 1)
        assert previous_period(2027, 1) == (2026, 4)
        state = {}
        assert selected_period(state, date(2026, 9, 7)) == (2026, 3)
        state['selected_period'] = (2025, 4)
        assert selected_period(state, date(2026, 9, 8)) == (2025, 4)
        assert selected_period(state, date(2026, 10, 1)) == (2026, 4)
        app.switch_page('pages/2_Sales.py').run()
        assert app.selectbox(key='_period_quarter_sales').value == current_period()[1]
        app.selectbox(key='_period_quarter_sales').set_value(1).run()
        app.switch_page('Home.py').run()
        assert app.selectbox(key='_period_quarter_home').value == 1
        app.switch_page('pages/5_Reports.py').run()
        assert app.selectbox(key='_period_quarter_reports').value == 1
        app.switch_page('pages/2_Sales.py').run()
        assert app.selectbox(key='_period_quarter_sales').value == 1
        assert not app.exception
        print('Calendar rollover, historical selection, and cross-page persistence PASS')
        if failures:
            raise SystemExit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
