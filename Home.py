"""
Surveying Experts - Commission Calculator (Web Version)
Entry point - handles DB init and shows home dashboard.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from src.startup import init_db
from src.models import get_setting, get_or_create_period, get_sales
from src.calculations import calc_all_commissions, get_totals
from src.auth import require_login, logout_button

# Page config
st.set_page_config(
    page_title="Surveying Experts - Commission Calculator",
    page_icon="chart_with_upwards_trend",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()
require_login()

PRIMARY = get_setting('primary_color', '#354f61')
ACCENT  = get_setting('accent_color', '#f6ba3b')
company = get_setting('company_name', 'Surveying Experts')

# Sidebar branding
st.sidebar.markdown(
    f"<div style='background:{PRIMARY};padding:20px 16px 14px;margin:-1rem -1rem 0;"
    f"text-align:center;'>"
    f"<p style='color:white;font-size:18px;font-weight:bold;margin:0;'>{company}</p>"
    f"<p style='color:rgba(255,255,255,0.6);font-size:11px;margin:4px 0 0;'>"
    f"Commission Manager</p>"
    f"</div>",
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")
st.sidebar.markdown("**Navigation**")
st.sidebar.page_link("Home.py",               label="Dashboard")
st.sidebar.page_link("pages/2_Sales.py",      label="Sales Input")
st.sidebar.page_link("pages/3_KPI.py",        label="KPI Calculation")
st.sidebar.page_link("pages/4_Commission.py", label="Final Commission")
st.sidebar.page_link("pages/5_Reports.py",    label="Reports Center")
st.sidebar.page_link("pages/6_Settings.py",   label="Settings")
st.sidebar.page_link("pages/7_Audit.py",      label="Audit Log")

# Period selector
st.sidebar.markdown("---")
st.sidebar.markdown("**Active Period**")
col_y, col_q = st.sidebar.columns(2)
year    = col_y.selectbox("Year",    [2024, 2025, 2026, 2027], index=2, key="home_year")
quarter = col_q.selectbox("Quarter", [1, 2, 3, 4],             index=1, key="home_q",
                           format_func=lambda q: f"Q{q}")
period  = get_or_create_period(year, quarter)
period_label = f"Q{quarter} {year}"

# Page header
st.markdown(
    f"<h1 style='color:{PRIMARY};margin-bottom:2px;'>Real-Time Commission Dashboard</h1>"
    f"<p style='color:#5a7080;margin-top:0;'>Live overview for {period_label} "
    f"&mdash; three reporting levels below</p>",
    unsafe_allow_html=True,
)
st.divider()


@st.cache_data(ttl=60, show_spinner=False)
def _load(pid):
    c = calc_all_commissions(pid)
    return c, get_totals(c)


@st.cache_data(ttl=60, show_spinner=False)
def _load_sales(pid):
    return get_sales(pid)


with st.spinner("Calculating commissions..."):
    commissions, totals = _load(period['id'])

def sar(v): return f"SAR {v:,.0f}"
def pct(v): return f"{v:.1f}%"

# ── Top KPI metrics ──────────────────────────────────────────────────────────
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Total Sales",      sar(totals['total_sales']),
          f"Target: {sar(totals['total_target'])}")
m2.metric("Overall Achievement", pct(totals['achievement']))
m3.metric("Base Commission",  sar(totals['total_base']))
m4.metric("Final Commission", sar(totals['total_final']), "KPI adjusted")
m5.metric("Target Achieved",  f"{totals['achieved_count']} / {totals['total_count']}")

st.divider()

# ── Three-level tabs ─────────────────────────────────────────────────────────
tab_company, tab_branch, tab_person = st.tabs(
    ["Company Level", "Branch Level", "Salesperson Level"]
)

# ════════════════════════════════════════════════════════════════════════════
# COMPANY LEVEL
# ════════════════════════════════════════════════════════════════════════════
with tab_company:
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("#### Target vs Actual — All Salespersons")
        if commissions:
            names   = [c['salesperson_name'].split()[0] for c in commissions]
            targets = [c['total_target'] / 1000 for c in commissions]
            actuals = [c['total_actual'] / 1000 for c in commissions]
            fig = go.Figure()
            fig.add_bar(name='Target', x=names, y=targets,
                        marker_color=PRIMARY, opacity=0.75)
            fig.add_bar(name='Actual', x=names, y=actuals,
                        marker_color=ACCENT, opacity=0.9)
            fig.update_layout(
                barmode='group', height=320,
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation='h', y=1.1),
                yaxis_title="SAR (thousands)",
                plot_bgcolor='white', paper_bgcolor='white',
            )
            fig.update_yaxes(gridcolor='#f0f3f5')
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown("#### Achievement % Ranking")
        if commissions:
            sorted_c = sorted(commissions, key=lambda c: c['achievement'], reverse=True)
            names = [c['salesperson_name'].split()[0] for c in sorted_c]
            achs  = [c['achievement'] for c in sorted_c]
            colors = ['#27ae60' if a >= 100 else '#f39c12' if a >= 80 else '#e74c3c'
                      for a in achs]
            fig2 = go.Figure(go.Bar(
                x=achs, y=names, orientation='h',
                marker_color=colors, opacity=0.85,
            ))
            fig2.add_vline(x=100, line_dash="dash",
                           line_color=PRIMARY, line_width=1.5)
            fig2.update_layout(
                height=320, margin=dict(l=10, r=30, t=10, b=10),
                xaxis_title="Achievement %",
                plot_bgcolor='white', paper_bgcolor='white',
            )
            fig2.update_xaxes(gridcolor='#f0f3f5')
            st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    col_top5, col_pie = st.columns([2, 3])

    with col_top5:
        st.markdown("#### Top 5 Performers")
        top5 = totals.get('top5', [])
        if top5:
            medals = ["1st", "2nd", "3rd", "4th", "5th"]
            df_top = pd.DataFrame([{
                "Rank":        medals[i],
                "Salesperson": c['salesperson_name'],
                "Sales":       sar(c['total_actual']),
                "Ach %":       pct(c['achievement']),
            } for i, c in enumerate(top5)])
            st.dataframe(df_top, use_container_width=True, hide_index=True,
                         column_config={"Rank": st.column_config.TextColumn(width="small")})

    with col_pie:
        st.markdown("#### Sales Mix by Category")
        all_sales = _load_sales(period['id'])
        if all_sales:
            cat_totals = {}
            for r in all_sales:
                cat_totals[r['cat_name']] = cat_totals.get(r['cat_name'], 0) + r['actual_sales']
            fig3 = px.pie(
                values=list(cat_totals.values()),
                names=list(cat_totals.keys()),
                color_discrete_sequence=[PRIMARY, ACCENT, '#27ae60', '#e74c3c', '#8e44ad'],
                hole=0.35,
            )
            fig3.update_traces(textposition='inside', textinfo='percent+label')
            fig3.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10),
                               showlegend=True)
            st.plotly_chart(fig3, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# BRANCH LEVEL
# ════════════════════════════════════════════════════════════════════════════
with tab_branch:
    st.markdown("#### Branch Performance Summary")

    if not commissions:
        st.info("No data available.")
    else:
        branch_map = {}
        for c in commissions:
            b = c['branch_name'] or 'Unknown'
            if b not in branch_map:
                branch_map[b] = {'sales': 0, 'target': 0, 'base': 0,
                                 'final': 0, 'count': 0, 'persons': []}
            branch_map[b]['sales']   += c['total_actual']
            branch_map[b]['target']  += c['total_target']
            branch_map[b]['base']    += c['base_commission']
            branch_map[b]['final']   += c['final_commission']
            branch_map[b]['count']   += 1
            branch_map[b]['persons'].append(c)

        # Branch cards
        br_cols = st.columns(max(len(branch_map), 1))
        for col, (br_name, bv) in zip(br_cols, branch_map.items()):
            ach = (bv['sales'] / bv['target'] * 100) if bv['target'] else 0
            color = '#27ae60' if ach >= 100 else '#f39c12' if ach >= 80 else '#e74c3c'
            col.markdown(
                f"<div style='background:{PRIMARY};border-radius:10px;padding:16px;"
                f"text-align:center;color:white;'>"
                f"<p style='font-size:15px;font-weight:bold;margin:0 0 8px;'>{br_name}</p>"
                f"<p style='font-size:10px;opacity:.65;margin:0;'>SALES</p>"
                f"<p style='font-size:14px;font-weight:bold;color:{ACCENT};margin:2px 0 6px;'>"
                f"{sar(bv['sales'])}</p>"
                f"<p style='font-size:10px;opacity:.65;margin:0;'>ACHIEVEMENT</p>"
                f"<p style='font-size:16px;font-weight:bold;color:{color};margin:2px 0 6px;'>"
                f"{ach:.1f}%</p>"
                f"<p style='font-size:10px;opacity:.65;margin:0;'>FINAL COMMISSION</p>"
                f"<p style='font-size:14px;font-weight:bold;color:{ACCENT};margin:2px 0 0;'>"
                f"{sar(bv['final'])}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.divider()

        # Branch comparison bar
        br_names  = list(branch_map.keys())
        br_sales  = [branch_map[b]['sales']  / 1_000 for b in br_names]
        br_target = [branch_map[b]['target'] / 1_000 for b in br_names]
        br_final  = [branch_map[b]['final']  / 1_000 for b in br_names]
        fig_br = go.Figure()
        fig_br.add_bar(name='Target (k)',      x=br_names, y=br_target,
                       marker_color=PRIMARY, opacity=0.6)
        fig_br.add_bar(name='Actual Sales (k)',x=br_names, y=br_sales,
                       marker_color=ACCENT, opacity=0.85)
        fig_br.add_bar(name='Final Comm. (k)', x=br_names, y=br_final,
                       marker_color='#27ae60', opacity=0.85)
        fig_br.update_layout(
            barmode='group', height=280,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation='h', y=1.1),
            yaxis_title="SAR (thousands)",
            plot_bgcolor='white', paper_bgcolor='white',
        )
        fig_br.update_yaxes(gridcolor='#f0f3f5')
        st.plotly_chart(fig_br, use_container_width=True)

        # Branch detail table
        br_table = []
        for br_name, bv in branch_map.items():
            ach = (bv['sales'] / bv['target'] * 100) if bv['target'] else 0
            br_table.append({
                "Branch":          br_name,
                "Salespersons":    bv['count'],
                "Total Sales":     sar(bv['sales']),
                "Target":          sar(bv['target']),
                "Achievement":     pct(ach),
                "Base Comm.":      sar(bv['base']),
                "Final Comm.":     sar(bv['final']),
            })
        st.dataframe(pd.DataFrame(br_table), use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════════════════
# SALESPERSON LEVEL
# ════════════════════════════════════════════════════════════════════════════
with tab_person:
    st.markdown("#### Salesperson Performance")

    if not commissions:
        st.info("No data available.")
    else:
        # Full salesperson table with KPI info
        sp_rows = []
        for c in sorted(commissions, key=lambda x: x['final_commission'], reverse=True):
            sp_rows.append({
                "Salesperson":     c['salesperson_name'],
                "Branch":          c['branch_name'],
                "Tier":            c['tier_name'],
                "Total Sales":     sar(c['total_actual']),
                "Target":          sar(c['total_target']),
                "Achievement":     pct(c['achievement']),
                "Base Comm.":      sar(c['base_commission']),
                "KPI Score":       round(c['kpi_score'], 2),
                "KPI x":           c['kpi_multiplier'],
                "Final Comm.":     sar(c['final_commission']),
            })
        st.dataframe(
            pd.DataFrame(sp_rows), use_container_width=True, hide_index=True,
            column_config={
                "KPI Score": st.column_config.ProgressColumn(
                    "KPI Score", min_value=0, max_value=120, format="%.2f")
            },
        )

        st.divider()
        st.markdown("#### Salesperson Drilldown")
        sel_sp = st.selectbox(
            "Select Salesperson",
            [c['salesperson_name'] for c in commissions],
            key="home_sp_sel",
        )
        sel_c = next((c for c in commissions if c['salesperson_name'] == sel_sp), None)

        if sel_c:
            d1, d2, d3, d4 = st.columns(4)
            d1.metric("Sales",         sar(sel_c['total_actual']))
            d2.metric("Achievement",   pct(sel_c['achievement']))
            d3.metric("KPI Score",     f"{sel_c['kpi_score']:.2f}")
            d4.metric("Final Comm.",   sar(sel_c['final_commission']))

            cat_rows = [{
                "Category":    cr['category_name'],
                "Actual":      sar(cr['actual_sales']),
                "Target":      sar(cr['target']),
                "Achievement": pct(cr['achievement']),
                "Commission":  sar(cr['commission']),
            } for cr in sel_c['categories']]
            st.dataframe(pd.DataFrame(cat_rows),
                         use_container_width=True, hide_index=True)

st.sidebar.markdown("---")
logout_button()
st.sidebar.caption(f"v1.1.0 | {company}")
