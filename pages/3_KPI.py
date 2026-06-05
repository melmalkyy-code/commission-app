import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import streamlit as st
import pandas as pd
from src.models import (get_setting, get_salespersons, get_kpi_items,
                         get_or_create_period, get_kpi_score, save_kpi_score,
                         get_kpi_adjustment, save_kpi_adjustment, log_action)
from src.calculations import calc_kpi

PRIMARY = get_setting('primary_color', '#354f61')
st.set_page_config(page_title="KPI Calculation", layout="wide")
st.markdown(f"<h1 style='color:{PRIMARY}'>🎯 KPI Calculation</h1>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])
year    = col1.selectbox("Year",    [2024, 2025, 2026, 2027], index=2)
quarter = col2.selectbox("Quarter", [1, 2, 3, 4],             index=1, format_func=lambda q: f"Q{q}")
period  = get_or_create_period(year, quarter)
st.divider()

kpi_items   = get_kpi_items(active_only=True)
salespeople = get_salespersons(active_only=True)

total_weight = sum(i['weight'] for i in kpi_items)
if abs(total_weight - 100.0) > 0.01:
    st.warning(f"⚠️ KPI item weights total {total_weight:.1f}% (should be 100%). Results may be inaccurate. Fix in Settings → KPI Settings.")

# Build KPI input dataframe
rows = []
for sp in salespeople:
    row = {
        'Salesperson': sp['name'],
        'Branch': sp.get('branch_name', ''),
        '_sp_id': sp['id'],
    }
    for item in kpi_items:
        row[f"{item['name']} ({item['weight']:.0f}%)"] = get_kpi_score(period['id'], sp['id'], item['id'])
    adj = get_kpi_adjustment(period['id'], sp['id'])
    row['Bonus pts']   = adj.get('bonus_points', 0) or 0
    row['Penalty pts'] = adj.get('penalty_points', 0) or 0
    rows.append(row)

df = pd.DataFrame(rows)
kpi_col_names = [f"{i['name']} ({i['weight']:.0f}%)" for i in kpi_items]
display_cols  = ['Salesperson', 'Branch'] + kpi_col_names + ['Bonus pts', 'Penalty pts']
editable_df   = df[display_cols].copy()

st.markdown("**Enter KPI scores (0–100 per item). Multiplier is assigned automatically.**")

col_configs = {
    col_name: st.column_config.NumberColumn(col_name, min_value=0, max_value=100, step=1, format="%.1f")
    for col_name in kpi_col_names
}
col_configs['Bonus pts']   = st.column_config.NumberColumn("Bonus pts",   min_value=0, max_value=20, step=0.5)
col_configs['Penalty pts'] = st.column_config.NumberColumn("Penalty pts", min_value=0, max_value=20, step=0.5)

edited = st.data_editor(
    editable_df,
    use_container_width=True,
    disabled=['Salesperson', 'Branch'],
    column_config=col_configs,
    num_rows="fixed",
    hide_index=True,
    key="kpi_editor",
)

if st.button("💾 Save KPI Scores", type="primary"):
    for i, row in edited.iterrows():
        sp = salespeople[i]
        for item in kpi_items:
            col = f"{item['name']} ({item['weight']:.0f}%)"
            score = float(row.get(col, 0) or 0)
            save_kpi_score(period['id'], sp['id'], item['id'], min(score, item['max_score']))
        bonus   = float(row.get('Bonus pts', 0) or 0)
        penalty = float(row.get('Penalty pts', 0) or 0)
        save_kpi_adjustment(period['id'], sp['id'], bonus, penalty)
    log_action("KPI_SAVE_ALL", "kpi_records", None, f"Q{quarter} {year}", username="manager")
    st.success("✅ KPI scores saved.")
    st.rerun()

# ── KPI results preview ───────────────────────────────────────────────────────
st.divider()
st.markdown("#### KPI Results Preview")

result_rows = []
for sp in salespeople:
    kpi = calc_kpi(period['id'], sp['id'])
    score = kpi['final_score']
    mult  = kpi['multiplier']
    result_rows.append({
        "Salesperson":    sp['name'],
        "Branch":         sp.get('branch_name', ''),
        "Weighted Score": f"{kpi['weighted_score']:.2f}",
        "Bonus":          f"+{kpi['bonus']:.1f}",
        "Penalty":        f"-{kpi['penalty']:.1f}",
        "Final KPI Score":score,
        "KPI Multiplier": f"× {mult}",
    })

df_res = pd.DataFrame(result_rows)
st.dataframe(
    df_res,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Final KPI Score": st.column_config.ProgressColumn(
            "Final KPI Score",
            min_value=0, max_value=120, format="%.2f",
        )
    }
)
