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

PRIMARY = get_setting('primary_color', '#354f61')
ACCENT  = get_setting('accent_color', '#f6ba3b')
st.set_page_config(page_title="KPI Calculation", layout="wide")
st.markdown(f"<h1 style='color:{PRIMARY}'>🎯 KPI Calculation</h1>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])
year    = col1.selectbox("Year",    [2024, 2025, 2026, 2027], index=2)
quarter = col2.selectbox("Quarter", [1, 2, 3, 4],             index=1, format_func=lambda q: f"Q{q}")
period  = get_or_create_period(year, quarter)
st.divider()

kpi_items   = get_kpi_items(active_only=True)
salespeople = get_salespersons(active_only=True)

# Separate auto-calculated vs manual items
auto_items   = [i for i in kpi_items if i.get('linked_category_id')]
manual_items = [i for i in kpi_items if not i.get('linked_category_id')]

total_weight = sum(i['weight'] for i in kpi_items)
if abs(total_weight - 100.0) > 0.01:
    st.warning(f"⚠️ KPI weights total {total_weight:.1f}% (should be 100%). Fix in ⚙️ Settings → KPI Settings.")

# ── Auto-calculated items info ────────────────────────────────────────────────
if auto_items:
    with st.expander(f"📊 Auto-Calculated KPI Items ({len(auto_items)} items — from category achievement %)", expanded=False):
        st.caption("These scores are pulled automatically from actual sales vs target. No manual entry needed.")
        auto_rows = []
        for sp in salespeople:
            row = {"Salesperson": sp['name'], "Branch": sp.get('branch_name', '')}
            for item in auto_items:
                ach = get_category_achievement(period['id'], sp['id'], item['linked_category_id'])
                row[f"{item['name']} ({item['weight']:.0f}%) [Auto]"] = f"{ach:.1f}%"
            auto_rows.append(row)
        st.dataframe(pd.DataFrame(auto_rows), use_container_width=True, hide_index=True)

# ── Manual KPI entry ─────────────────────────────────────────────────────────
if manual_items:
    st.markdown("**Manual KPI Scores** — Enter scores (0–100) for each item:")
    st.caption("Auto-linked items (based on category achievement) are shown above — only manual items appear here.")

    rows = []
    for sp in salespeople:
        row = {
            'Salesperson': sp['name'],
            'Branch': sp.get('branch_name', ''),
            '_sp_id': sp['id'],
        }
        for item in manual_items:
            row[f"{item['name']} ({item['weight']:.0f}%)"] = get_kpi_score(period['id'], sp['id'], item['id'])
        adj = get_kpi_adjustment(period['id'], sp['id'])
        row['Bonus pts']   = adj.get('bonus_points', 0) or 0
        row['Penalty pts'] = adj.get('penalty_points', 0) or 0
        rows.append(row)

    df = pd.DataFrame(rows)
    manual_col_names = [f"{i['name']} ({i['weight']:.0f}%)" for i in manual_items]
    display_cols     = ['Salesperson', 'Branch'] + manual_col_names + ['Bonus pts', 'Penalty pts']
    editable_df      = df[display_cols].copy()

    col_configs = {
        col_name: st.column_config.NumberColumn(col_name, min_value=0, max_value=100, step=1, format="%.1f")
        for col_name in manual_col_names
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
            for item in manual_items:
                col = f"{item['name']} ({item['weight']:.0f}%)"
                score = float(row.get(col, 0) or 0)
                save_kpi_score(period['id'], sp['id'], item['id'], min(score, item['max_score']))
            bonus   = float(row.get('Bonus pts', 0) or 0)
            penalty = float(row.get('Penalty pts', 0) or 0)
            save_kpi_adjustment(period['id'], sp['id'], bonus, penalty)
        log_action("KPI_SAVE_ALL", "kpi_records", None, f"Q{quarter} {year}", username="manager")
        st.success("✅ KPI scores saved.")
        st.rerun()
else:
    st.info("ℹ️ All KPI items are linked to categories and auto-calculated. No manual entry needed.")
    # Still allow adjustments
    st.markdown("**Bonus / Penalty Adjustments:**")
    adj_rows = []
    for sp in salespeople:
        adj = get_kpi_adjustment(period['id'], sp['id'])
        adj_rows.append({
            'Salesperson': sp['name'], 'Branch': sp.get('branch_name', ''),
            '_sp_id': sp['id'],
            'Bonus pts': adj.get('bonus_points', 0) or 0,
            'Penalty pts': adj.get('penalty_points', 0) or 0,
        })
    adj_df = pd.DataFrame(adj_rows)[['Salesperson', 'Branch', 'Bonus pts', 'Penalty pts']]
    edited_adj = st.data_editor(adj_df, use_container_width=True, disabled=['Salesperson', 'Branch'],
                                 hide_index=True, key="adj_editor")
    if st.button("💾 Save Adjustments", type="primary"):
        for i, row in edited_adj.iterrows():
            sp = salespeople[i]
            save_kpi_adjustment(period['id'], sp['id'],
                                float(row.get('Bonus pts', 0) or 0),
                                float(row.get('Penalty pts', 0) or 0))
        st.success("✅ Adjustments saved.")
        st.rerun()

# ── KPI Results Preview ───────────────────────────────────────────────────────
st.divider()
st.markdown("#### 📊 KPI Results Preview")

result_rows = []
for sp in salespeople:
    kpi = calc_kpi(period['id'], sp['id'])
    result_rows.append({
        "Salesperson":     sp['name'],
        "Branch":          sp.get('branch_name', ''),
        "Weighted Score":  f"{kpi['weighted_score']:.2f}",
        "Bonus":           f"+{kpi['bonus']:.1f}",
        "Penalty":         f"-{kpi['penalty']:.1f}",
        "Final KPI Score": kpi['final_score'],
        "KPI Multiplier":  f"× {kpi['multiplier']}",
    })

st.dataframe(
    pd.DataFrame(result_rows),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Final KPI Score": st.column_config.ProgressColumn(
            "Final KPI Score", min_value=0, max_value=120, format="%.2f",
        )
    }
)

# ── Per-item breakdown expander ───────────────────────────────────────────────
with st.expander("🔍 Detailed Item Breakdown (per salesperson)"):
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
                "Source":       f"🤖 Auto ({d.get('linked_category_name','?')})" if d.get('is_auto') else "✏️ Manual",
                "Raw Score":    f"{d['raw_score']:.1f}",
                "Normalized":   f"{d['normalized']:.1f}%",
                "Contribution": f"{d['contribution']:.2f}",
            })
        st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)
        st.markdown(f"""
| | |
|---|---|
| Weighted Score | **{kpi['weighted_score']:.2f}** |
| Bonus | **+{kpi['bonus']:.1f}** |
| Penalty | **-{kpi['penalty']:.1f}** |
| **Final KPI Score** | **{kpi['final_score']:.2f}** |
| **Multiplier** | **× {kpi['multiplier']}** |
""")
