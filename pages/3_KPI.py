import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import streamlit as st
from src.startup import init_db
from src.auth import require_login, logout_button
init_db()
require_login()
import pandas as pd
from src.models import (get_setting, get_salespersons, get_kpi_items,
                         get_or_create_period, get_kpi_score, save_kpi_score,
                         get_kpi_adjustment, save_kpi_adjustment, log_action,
                         get_category_achievement)
from src.calculations import calc_kpi
from src.ui import inject_css, page_header, sidebar_logo

PRIMARY = get_setting('primary_color', '#354f61')
ACCENT  = get_setting('accent_color', '#f6ba3b')
COMPANY = get_setting('company_name', 'Surveying Experts')

st.set_page_config(page_title="KPI Calculation — Surveying Experts", layout="wide")
inject_css(PRIMARY)
sidebar_logo(COMPANY, PRIMARY)
page_header("KPI Calculation", "Enter manual KPI scores (0–100) and review results", PRIMARY)

col1, col2 = st.columns([1, 1])
year    = col1.selectbox("Year",    [2024, 2025, 2026, 2027], index=2)
quarter = col2.selectbox("Quarter", [1, 2, 3, 4],             index=1,
                          format_func=lambda q: f"Q{q}")
period  = get_or_create_period(year, quarter)
st.divider()

kpi_items   = get_kpi_items(active_only=True)
salespeople = get_salespersons(active_only=True)

# Separate auto-calculated vs manual items
auto_items   = [i for i in kpi_items if i.get('linked_category_id')]
manual_items = [i for i in kpi_items if not i.get('linked_category_id')]

total_weight = sum(i['weight'] for i in kpi_items)
if abs(total_weight - 100.0) > 0.01:
    st.warning(
        f"KPI weights total {total_weight:.1f}% (should be 100%). "
        "Fix in Settings > KPI Settings."
    )

# ── Load all current DB state (auto + manual) ─────────────────────────────────
db_scores = {}
db_adjs   = {}
for sp in salespeople:
    for item in kpi_items:
        db_scores[(sp['id'], item['id'])] = float(
            get_kpi_score(period['id'], sp['id'], item['id']) or 0
        )
    adj = get_kpi_adjustment(period['id'], sp['id'])
    db_adjs[sp['id']] = {
        'bonus':   float(adj.get('bonus_points', 0) or 0),
        'penalty': float(adj.get('penalty_points', 0) or 0),
    }

# ── Unified KPI table — auto items shown (locked), manual items editable ──────
st.markdown("**KPI Scores** — auto-calculated items are locked (grey); manual items are editable.")
st.caption(
    "Scores are entered as raw values and calculated against each item's Max Score. "
    "Example: score 42 with Max 50 → 84 % of that item's weight."
)

rows = []
for sp in salespeople:
    row = {
        'Salesperson': sp['name'],
        'Branch':      sp.get('branch_name') or '',
        '_sp_id':      sp['id'],
    }
    for item in auto_items:
        ach = get_category_achievement(period['id'], sp['id'], item['linked_category_id'])
        col = f"{item['name']} ({item['weight']:.0f}%) [Auto]"
        row[col] = round(ach, 1)
    for item in manual_items:
        col = f"{item['name']} ({item['weight']:.0f}%)"
        row[col] = db_scores[(sp['id'], item['id'])]
    row['Bonus pts']   = db_adjs[sp['id']]['bonus']
    row['Penalty pts'] = db_adjs[sp['id']]['penalty']
    rows.append(row)

auto_col_names   = [f"{i['name']} ({i['weight']:.0f}%) [Auto]" for i in auto_items]
manual_col_names = [f"{i['name']} ({i['weight']:.0f}%)"        for i in manual_items]
display_cols     = (['Salesperson', 'Branch']
                    + auto_col_names + manual_col_names
                    + ['Bonus pts', 'Penalty pts'])
editable_df = pd.DataFrame(rows)[display_cols].copy()

col_configs: dict = {}
for col in auto_col_names:
    col_configs[col] = st.column_config.NumberColumn(
        col, disabled=True, format="%.1f",
        help="Auto-calculated from category achievement %. Read-only.",
    )
for item, col in zip(manual_items, manual_col_names):
    col_configs[col] = st.column_config.NumberColumn(
        col, min_value=0, step=0.5, format="%.1f",
        help=f"Max score for this item: {item['max_score']:.0f}. "
             f"Contribution = (score / {item['max_score']:.0f}) × {item['weight']:.0f}% weight.",
    )
col_configs['Bonus pts']   = st.column_config.NumberColumn("Bonus pts",   min_value=0, step=0.5)
col_configs['Penalty pts'] = st.column_config.NumberColumn("Penalty pts", min_value=0, step=0.5)

edited = st.data_editor(
    editable_df,
    use_container_width=True,
    disabled=['Salesperson', 'Branch'] + auto_col_names,
    column_config=col_configs,
    num_rows="fixed",
    hide_index=True,
    key="kpi_editor",
)


def _safe_float(series_row, col: str, default=0.0) -> float:
    raw = series_row.get(col)
    try:
        return default if (raw is None or pd.isna(raw)) else float(raw)
    except Exception:
        return default


def _auto_save_kpi():
    if not manual_items:
        return
    changed = False
    for idx, (_, row) in enumerate(edited.iterrows()):
        if idx >= len(salespeople):
            break
        sp = salespeople[idx]
        for item in manual_items:
            col = f"{item['name']} ({item['weight']:.0f}%)"
            val = _safe_float(row, col)               # no cap — open score
            if abs(val - db_scores[(sp['id'], item['id'])]) > 0.001:
                save_kpi_score(period['id'], sp['id'], item['id'], val)
                changed = True
        bonus   = _safe_float(row, 'Bonus pts')
        penalty = _safe_float(row, 'Penalty pts')
        prev    = db_adjs[sp['id']]
        if abs(bonus - prev['bonus']) > 0.001 or abs(penalty - prev['penalty']) > 0.001:
            save_kpi_adjustment(period['id'], sp['id'], bonus, penalty)
            changed = True
    if changed:
        st.cache_data.clear()
        st.toast("KPI changes saved", icon="✅")


_auto_save_kpi()

if st.button("Save KPI Scores", type="primary", key="save_kpi_scores"):
    for idx, (_, row) in enumerate(edited.iterrows()):
        if idx >= len(salespeople):
            break
        sp = salespeople[idx]
        for item in manual_items:
            col = f"{item['name']} ({item['weight']:.0f}%)"
            save_kpi_score(period['id'], sp['id'], item['id'], _safe_float(row, col))
        save_kpi_adjustment(
            period['id'], sp['id'],
            _safe_float(row, 'Bonus pts'),
            _safe_float(row, 'Penalty pts'),
        )
    log_action("KPI_SAVE_ALL", "kpi_records", notes=f"Q{quarter} {year}")
    st.cache_data.clear()
    st.success("KPI scores saved.")
    st.rerun()

# ── KPI Results Preview ───────────────────────────────────────────────────────
st.divider()
st.markdown("#### KPI Results Preview")

result_rows = []
for sp in salespeople:
    kpi = calc_kpi(period['id'], sp['id'])
    result_rows.append({
        "Salesperson":     sp['name'],
        "Branch":          sp.get('branch_name') or '',
        "Weighted Score":  f"{kpi['weighted_score']:.2f}",
        "Bonus":           f"+{kpi['bonus']:.1f}",
        "Penalty":         f"-{kpi['penalty']:.1f}",
        "Final KPI Score": kpi['final_score'],
        "KPI Multiplier":  f"x {kpi['multiplier']}",
    })

st.dataframe(
    pd.DataFrame(result_rows),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Final KPI Score": st.column_config.ProgressColumn(
            "Final KPI Score", min_value=0, max_value=120, format="%.2f",
        )
    },
)

# ── Per-item breakdown ────────────────────────────────────────────────────────
with st.expander("Detailed Item Breakdown (per salesperson)"):
    sp_names = [sp['name'] for sp in salespeople]
    sel = st.selectbox("Salesperson", sp_names, key="kpi_detail_sp")
    sel_sp = next((sp for sp in salespeople if sp['name'] == sel), None)
    if sel_sp:
        kpi = calc_kpi(period['id'], sel_sp['id'])
        detail_rows = []
        for d in kpi['items']:
            detail_rows.append({
                "KPI Item":     d['name'],
                "Weight %":     f"{d['weight']:.0f}%",
                "Source":       f"Auto ({d.get('linked_category_name', '?')})" if d.get('is_auto') else "Manual",
                "Raw Score":    f"{d['raw_score']:.1f}",
                "Normalized":   f"{d['normalized']:.1f}%",
                "Contribution": f"{d['contribution']:.2f}",
            })
        st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)
        c1, c2 = st.columns(2)
        c1.metric("Weighted Score", f"{kpi['weighted_score']:.2f}")
        c1.metric("Bonus",          f"+{kpi['bonus']:.1f}")
        c1.metric("Penalty",        f"-{kpi['penalty']:.1f}")
        c2.metric("Final KPI Score", f"{kpi['final_score']:.2f}")
        c2.metric("KPI Multiplier",  f"x {kpi['multiplier']}")

logout_button()
