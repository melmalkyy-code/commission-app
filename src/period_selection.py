"""Calendar-based period selection shared across Streamlit pages."""
from datetime import datetime, timezone, timedelta


def current_period(today=None):
    today = today or datetime.now(timezone(timedelta(hours=3)))
    return today.year, (today.month - 1) // 3 + 1


def previous_period(year, quarter):
    return (year - 1, 4) if quarter == 1 else (year, quarter - 1)


def selected_period(state, today=None):
    current = current_period(today)
    if state.get('calendar_period') != current:
        state['calendar_period'] = current
        state['selected_period'] = current
    return state.setdefault('selected_period', current)


def period_inputs(c1, c2, page):
    import streamlit as st
    from src.i18n import t, q_label
    from src.models import get_periods
    year, quarter = selected_period(st.session_state)
    current_year, _ = current_period()
    years = sorted(set(range(min(2024, year), max(current_year + 1, year) + 1))
                   | {p['year'] for p in get_periods()})
    ykey, qkey = f'_period_year_{page}', f'_period_quarter_{page}'
    st.session_state[ykey] = year
    st.session_state[qkey] = quarter

    def remember():
        st.session_state['selected_period'] = (st.session_state[ykey], st.session_state[qkey])

    year = c1.selectbox(t('Year'), years, key=ykey, on_change=remember)
    quarter = c2.selectbox(t('Quarter'), [1, 2, 3, 4], key=qkey,
                           format_func=q_label, on_change=remember)
    return year, quarter
