import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import streamlit as st
from src.startup import init_db
from src.auth import require_login, require_editor
init_db()
require_login()
require_editor()   # viewers are read-only — no KPI input
import pandas as pd
from src.models import (get_setting, get_salespersons, get_kpi_items,
                         get_or_create_period, get_kpi_score,
                         save_kpi_scores_bulk,
                         get_kpi_adjustment, save_kpi_adjustment,
                         get_category_achievement)
from src.calculations import calc_kpi, calc_all_commissions
from src.ui import inject_css, page_header, sidebar_logo, render_df
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

# ── Unified KPI table — auto items shown (locked), manual items editable ──────
st.markdown(f"**{t('KPI Scores — auto-calculated items are locked (grey); manual items are editable.')}**")
st.caption(t("Scores are entered as raw values and calculated against each item's Max Score. Example: score 42 with Max 50 → 84 % of that item's weight."))

period_id = period['id']
_auto_sfx = " [Auto]" if not t("Auto") == "Auto" else f" [{t('Auto')}]"
auto_col_names   = [f"{i['name']} ({i['weight']:.0f}%){_auto_sfx}" for i in auto_items]
manual_col_names = [f"{i['name']} ({i['weight']:.0f}%)"             for i in manual_items]
display_cols     = ([t('Salesperson'), t('Branch')]
                    + auto_col_names + manual_col_names
                    + [t('Bonus pts'), t('Penalty pts')])

# Build the editor + saved-value snapshot ONCE per signature; kept in
# session_state so it is not rebuilt from the DB (dozens of per-cell queries)
# on every keystroke — that rebuild is what dropped the value being typed.
_sig      = f"{period_id}-{'.'.join(str(s['id']) for s in salespeople)}-{'.'.join(str(i['id']) for i in kpi_items)}"
_base_key = f"_kpi_base_{_sig}"
_snap_key = f"_kpi_snap_{_sig}"

if _base_key not in st.session_state:
    _rows = []
    _snap = {'scores': {}, 'adjs': {}}
    for sp in salespeople:
        row = {t('Salesperson'): sp['name'], t('Branch'): sp.get('branch_name') or ''}
        for item, col in zip(auto_items, auto_col_names):
            row[col] = round(get_category_achievement(period_id, sp['id'], item['linked_category_id']), 1)
        for item, col in zip(manual_items, manual_col_names):
            v = float(get_kpi_score(period_id, sp['id'], item['id']) or 0)
            row[col] = v
            _snap['scores'][(sp['id'], item['id'])] = v
        adj = get_kpi_adjustment(period_id, sp['id'])
        b = float(adj.get('bonus_points', 0) or 0)
        p = float(adj.get('penalty_points', 0) or 0)
        row[t('Bonus pts')]   = b
        row[t('Penalty pts')] = p
        _snap['adjs'][sp['id']] = {'bonus': b, 'penalty': p}
        _rows.append(row)
    st.session_state[_base_key] = pd.DataFrame(_rows)[display_cols]
    st.session_state[_snap_key] = _snap

editable_df = st.session_state[_base_key]

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
    key=f"kpi_editor_{_sig}",
)


def _safe_float(series_row, col: str, default=0.0) -> float:
    raw = series_row.get(col)
    try:
        return default if (raw is None or pd.isna(raw)) else float(raw)
    except Exception:
        return default


# ── Fast autosave: only changed scores (one bulk round-trip) + adjustments ────
if manual_items:
    _snap = st.session_state[_snap_key]
    score_changes = []
    adj_changes   = []
    for idx, sp in enumerate(salespeople):
        if idx >= len(edited):
            break
        row = edited.iloc[idx]
        for item, col in zip(manual_items, manual_col_names):
            val = _safe_float(row, col)
            if abs(val - _snap['scores'].get((sp['id'], item['id']), 0.0)) > 0.001:
                score_changes.append((sp['id'], item['id'], val))
                _snap['scores'][(sp['id'], item['id'])] = val
        bonus   = _safe_float(row, t('Bonus pts'))
        penalty = _safe_float(row, t('Penalty pts'))
        prev    = _snap['adjs'][sp['id']]
        if abs(bonus - prev['bonus']) > 0.001 or abs(penalty - prev['penalty']) > 0.001:
            adj_changes.append((sp['id'], bonus, penalty))
            _snap['adjs'][sp['id']] = {'bonus': bonus, 'penalty': penalty}

    if score_changes:
        save_kpi_scores_bulk(period_id, score_changes)
    for sp_id, bonus, penalty in adj_changes:
        save_kpi_adjustment(period_id, sp_id, bonus, penalty)
    if score_changes or adj_changes:
        calc_all_commissions.clear()   # cheap cache-drop so dashboards refresh
        st.toast(f"{t('Saved')} · {len(score_changes) + len(adj_changes)}")

# ── KPI results — computed on demand so typing stays instant ──────────────────
st.divider()
if st.button(t("Calculate KPI Results"), type="primary", key="calc_kpi_results"):
    with st.spinner(t("Calculating...")):
        st.session_state['_kpi_results'] = [{
            t("Salesperson"):     sp['name'],
            t("Branch"):          sp.get('branch_name') or '',
            t("Weighted Score"):  f"{k['weighted_score']:.2f}",
            t("Bonus"):           f"+{k['bonus']:.1f}",
            t("Penalty"):         f"-{k['penalty']:.1f}",
            t("Final KPI Score"): k['final_score'],
            t("KPI Multiplier"):  f"x {k['multiplier']}",
        } for sp in salespeople for k in [calc_kpi(period_id, sp['id'])]]

if st.session_state.get('_kpi_results'):
    st.markdown(f"#### {t('KPI Results Preview')}")
    render_df(pd.DataFrame(st.session_state['_kpi_results']))

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
        render_df(pd.DataFrame(detail_rows))
        c1, c2 = st.columns(2)
        c1.metric(t("Weighted Score"), f"{kpi['weighted_score']:.2f}")
        c1.metric(t("Bonus"),          f"+{kpi['bonus']:.1f}")
        c1.metric(t("Penalty"),        f"-{kpi['penalty']:.1f}")
        c2.metric(t("Final KPI Score"), f"{kpi['final_score']:.2f}")
        c2.metric(t("KPI Multiplier"),  f"x {kpi['multiplier']}")


