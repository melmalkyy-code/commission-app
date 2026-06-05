import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import streamlit as st
import pandas as pd
from src.models import get_setting, get_or_create_period
from src.calculations import calc_all_commissions, get_totals

PRIMARY = get_setting('primary_color', '#354f61')
ACCENT  = get_setting('accent_color', '#f6ba3b')
st.set_page_config(page_title="Final Commission", layout="wide")
st.markdown(f"<h1 style='color:{PRIMARY}'>💰 Final Commission</h1>", unsafe_allow_html=True)
st.caption("Formula: **Final Commission = Base Commission × KPI Multiplier**")

col1, col2 = st.columns([1, 1])
year    = col1.selectbox("Year",    [2024, 2025, 2026, 2027], index=2)
quarter = col2.selectbox("Quarter", [1, 2, 3, 4],             index=1, format_func=lambda q: f"Q{q}")
period  = get_or_create_period(year, quarter)
st.divider()

with st.spinner("Computing commissions..."):
    commissions = calc_all_commissions(period['id'])
    totals      = get_totals(commissions)

# ── Summary cards ─────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total Sales",       f"SAR {totals['total_sales']:,.0f}")
c2.metric("Total Target",      f"SAR {totals['total_target']:,.0f}")
c3.metric("Achievement",       f"{totals['achievement']:.1f}%")
c4.metric("Base Commission",   f"SAR {totals['total_base']:,.0f}")
c5.metric("Final Commission",  f"SAR {totals['total_final']:,.0f}")
c6.metric("Achieved Target",   f"{totals['achieved_count']} / {totals['total_count']}")

st.divider()

# ── Main commission table ─────────────────────────────────────────────────────
summary_rows = [{
    "Salesperson":    c['salesperson_name'],
    "Branch":         c['branch_name'],
    "Tier":           c['tier_name'],
    "Total Sales":    f"SAR {c['total_actual']:,.0f}",
    "Total Target":   f"SAR {c['total_target']:,.0f}",
    "Achievement %":  f"{c['achievement']:.1f}%",
    "Base Commission":f"SAR {c['base_commission']:,.0f}",
    "KPI Score":      c['kpi_score'],
    "KPI Multiplier": f"× {c['kpi_multiplier']}",
    "Final Commission":f"SAR {c['final_commission']:,.0f}",
} for c in commissions]

st.markdown("#### Commission Summary")
st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True,
             column_config={
                 "KPI Score": st.column_config.ProgressColumn("KPI Score", min_value=0, max_value=120, format="%.2f")
             })

# ── Salesperson drilldown ─────────────────────────────────────────────────────
st.divider()
st.markdown("#### Salesperson Breakdown")
sp_names = [c['salesperson_name'] for c in commissions]
selected = st.selectbox("Select Salesperson", sp_names)
selected_c = next((c for c in commissions if c['salesperson_name'] == selected), None)

if selected_c:
    col_info, col_final = st.columns([2, 1])
    with col_info:
        st.markdown(f"**{selected_c['salesperson_name']}** · {selected_c['branch_name']} · {selected_c['tier_name']}")
        cat_rows = [{
            "Category":    cr['category_name'],
            "Actual Sales":f"SAR {cr['actual_sales']:,.0f}",
            "Target":      f"SAR {cr['target']:,.0f}",
            "Achievement": f"{cr['achievement']:.1f}%",
            "Bracket":     cr['bracket'],
            "Rate":        f"{cr['rate']:.2f}%",
            "Commission":  f"SAR {cr['commission']:,.0f}",
        } for cr in selected_c['categories']]
        st.dataframe(pd.DataFrame(cat_rows), use_container_width=True, hide_index=True)

    with col_final:
        st.markdown(f"""
<div style="background:{PRIMARY}; border-radius:10px; padding:20px; text-align:center; color:white;">
    <p style="margin:0; font-size:11px; opacity:0.7;">BASE COMMISSION</p>
    <p style="margin:4px 0; font-size:20px; font-weight:bold;">SAR {selected_c['base_commission']:,.0f}</p>
    <p style="margin:8px 0 0; font-size:11px; opacity:0.7;">× KPI MULTIPLIER</p>
    <p style="margin:4px 0; font-size:20px; font-weight:bold; color:{ACCENT};">× {selected_c['kpi_multiplier']}</p>
    <hr style="border-color:rgba(255,255,255,0.2); margin:12px 0;">
    <p style="margin:0; font-size:11px; opacity:0.7;">FINAL COMMISSION</p>
    <p style="margin:4px 0; font-size:28px; font-weight:bold; color:{ACCENT};">SAR {selected_c['final_commission']:,.0f}</p>
    <p style="margin:8px 0 0; font-size:10px; opacity:0.5;">KPI Score: {selected_c['kpi_score']:.2f}</p>
</div>
        """, unsafe_allow_html=True)
