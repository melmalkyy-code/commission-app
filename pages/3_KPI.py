import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import streamlit as st
from src.startup import init_db
from src.auth import require_login
init_db()
require_login()
import pandas as pd
from src.models import (get_setting, get_salespersons, get_kpi_items,
                         get_or_create_period, get_kpi_score, save_kpi_score,
                         get_kpi_adjustment, save_kpi_adjustment, log_action,
                         get_category_achievement)
from src.calculations import calc_kpi
from src.ui import inject_css, page_header, sidebar_logo
from src.i18n import t, q_label
from src.branding import page_icon

PRIMARY = get_setting('primary_color', '#354f61')
ACCENT  = get_setting('accent_color', '#f6ba3b')
COMPANY = get_setting('company_name', 'Surveying Experts')

st.set_page_config(page_title="KPI Calculation — Surveying Experts", page_icon=page_icon(), layout="wide")
inject_css(PRIMARY)
sidebar_logo(COMPANY, PRIMARY)
page_header(t("KPI Calculation"), t("Enter manual KPI scores (0–100) and review results"), PRIMARY)

col1, col2 = st.columns([1, 1])
year    = col1.selectbox(t("Year"),    [2024, 2025, 2026, 2027], index=2)
quarter = col2.selectbox(t("Quarter"), [1, 2, 3, 4],             index=1,
                          format_func=q_label)
period  = get_or_create_period(year, quarter)
st.divider()

kpi_items   = get_kpi_items(active_only=True)
salespeople = get_salespersons(active_only=True)

# Separate auto-calculated vs manual items
auto_items   = [i for i in kpi_items if i.get('linked_category_id')]
manual_items = [i for i in kpi_items if not i.get('linked_category_id')]

total_weight = sum(i['weight'] for i in kpi_items)
if abs(total_weight - 100.0) > 0.01:
    st.warning(t("KPI weights total {total_weight:.1f}% (should be 100%). Fix in Settings > KPI Settings.").format(total_weight=total_weight))

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
st.markdown(f"**{t('KPI Scores — auto-calculated items are locked (grey); manual items are editable.')}**")
st.caption(t("Scores are entered as raw values and calculated against each item's Max Score. Example: score 42 with Max 50 → 84 % of that item's weight."))

rows = []
for sp in salespeople:
    row = {
        t('Salesperson'): sp['name'],
        t('Branch'):      sp.get('branch_name') or '',
        '_sp_id':         sp['id'],
    }
    for item in auto_items:
        ach = get_category_achievement(period['id'], sp['id'], item['linked_category_id'])
        col = f"{item['name']} ({item['weight']:.0f}%) [Auto]"
        row[col] = round(ach, 1)
    for item in manual_items:
        col = f"{item['name']} ({item['weight']:.0f}%)"
        row[col] = db_scores[(sp['id'], item['id'])]
    row[t('Bonus pts')]   = db_adjs[sp['id']]['bonus']
    row[t('Penalty pts')] = db_adjs[sp['id']]['penalty']
    rows.append(row)

_auto_sfx = " [Auto]" if not t("Auto") == "Auto" else f" [{t('Auto')}]"
auto_col_names   = [f"{i['name']} ({i['weight']:.0f}%){_auto_sfx}" for i in auto_items]
manual_col_names = [f"{i['name']} ({i['weight']:.0f}%)"             for i in manual_items]
display_cols     = ([t('Salesperson'), t('Branch')]
                    + auto_col_names + manual_col_names
                    + [t('Bonus pts'), t('Penalty pts')])
editable_df = pd.DataFrame(rows)[display_cols].copy()

col_configs: dict = {}
for col in auto_col_names:
    col_configs[col] = st.column_config.NumberColumn(
        col, disabled=True, format="%.1f",
        help=t("Auto-calculated from category achievement %. Read-only."),
    )
for item, col in zip(manual_items, manual_col_names):
    col_configs[col] = st.column_config.NumberColumn(
        col, min_value=0, step=0.5, format="%.1f",
        help=f"Max score for this item: {item['max_score']:.0f}. "
             f"Contribution = (score / {item['max_score']:.0f}) × {item['weight']:.0f}% weight.",
    )
col_configs[t('Bonus pts')]   = st.column_config.NumberColumn(t("Bonus pts"),   min_value=0, step=0.5)
col_configs[t('Penalty pts')] = st.column_config.NumberColumn(t("Penalty pts"), min_value=0, step=0.5)

edited = st.data_editor(
    editable_df,
    use_container_width=True,
    disabled=[t('Salesperson'), t('Branch')] + auto_col_names,
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
        bonus   = _safe_float(row, t('Bonus pts'))
        penalty = _safe_float(row, t('Penalty pts'))
        prev    = db_adjs[sp['id']]
        if abs(bonus - prev['bonus']) > 0.001 or abs(penalty - prev['penalty']) > 0.001:
            save_kpi_adjustment(period['id'], sp['id'], bonus, penalty)
            changed = True
    if changed:
        st.cache_data.clear()
        st.toast(t("KPI changes saved"))


_auto_save_kpi()

if st.button(t("Save KPI Scores"), type="primary", key="save_kpi_scores"):
    for idx, (_, row) in enumerate(edited.iterrows()):
        if idx >= len(salespeople):
            break
        sp = salespeople[idx]
        for item in manual_items:
            col = f"{item['name']} ({item['weight']:.0f}%)"
            save_kpi_score(period['id'], sp['id'], item['id'], _safe_float(row, col))
        save_kpi_adjustment(
            period['id'], sp['id'],
            _safe_float(row, t('Bonus pts')),
            _safe_float(row, t('Penalty pts')),
        )
    log_action("KPI_SAVE_ALL", "kpi_records", notes=f"Q{quarter} {year}")
    st.cache_data.clear()
    st.success(t("KPI scores saved."))
    st.rerun()

# ── KPI Results Preview ───────────────────────────────────────────────────────
st.divider()
st.markdown(f"#### {t('KPI Results Preview')}")

result_rows = []
for sp in salespeople:
    kpi = calc_kpi(period['id'], sp['id'])
    result_rows.append({
        t("Salesperson"):     sp['name'],
        t("Branch"):          sp.get('branch_name') or '',
        t("Weighted Score"):  f"{kpi['weighted_score']:.2f}",
        t("Bonus"):           f"+{kpi['bonus']:.1f}",
        t("Penalty"):         f"-{kpi['penalty']:.1f}",
        t("Final KPI Score"): kpi['final_score'],
        t("KPI Multiplier"):  f"x {kpi['multiplier']}",
    })

_fks = t("Final KPI Score")
st.dataframe(
    pd.DataFrame(result_rows),
    use_container_width=True,
    hide_index=True,
    column_config={
        _fks: st.column_config.ProgressColumn(_fks, min_value=0, max_value=120, format="%.2f")
    },
)

# ── Per-item breakdown ────────────────────────────────────────────────────────
with st.expander(t("Detailed Item Breakdown (per salesperson)")):
    sp_names = [sp['name'] for sp in salespeople]
    sel = st.selectbox(t("Salesperson"), sp_names, key="kpi_detail_sp")
    sel_sp = next((sp for sp in salespeople if sp['name'] == sel), None)
    if sel_sp:
        kpi = calc_kpi(period['id'], sel_sp['id'])
        detail_rows = []
        for d in kpi['items']:
            detail_rows.append({
                t("KPI Item"):     d['name'],
                t("Weight %"):     f"{d['weight']:.0f}%",
                t("Source"):       f"Auto ({d.get('linked_category_name', '?')})" if d.get('is_auto') else t("Manual - Enter Score"),
                t("Raw Score"):    f"{d['raw_score']:.1f}",
                t("Normalized"):   f"{d['normalized']:.1f}%",
                t("Contribution"): f"{d['contribution']:.2f}",
            })
        st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)
        c1, c2 = st.columns(2)
        c1.metric(t("Weighted Score"), f"{kpi['weighted_score']:.2f}")
        c1.metric(t("Bonus"),          f"+{kpi['bonus']:.1f}")
        c1.metric(t("Penalty"),        f"-{kpi['penalty']:.1f}")
        c2.metric(t("Final KPI Score"), f"{kpi['final_score']:.2f}")
        c2.metric(t("KPI Multiplier"),  f"x {kpi['multiplier']}")


