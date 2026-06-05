"""
Surveying Experts — Commission Calculator (Web Version)
Entry point — handles DB init and shows home dashboard.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from src.schema import create_schema
from src.seed   import seed
from src.models import get_setting, get_periods, get_or_create_period
from src.calculations import calc_all_commissions, get_totals

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Surveying Experts — Commission Calculator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── DB init (runs once per session) ──────────────────────────────────────────
@st.cache_resource
def init_db():
    create_schema()
    seed()
    return True

init_db()

# ── Sidebar branding ──────────────────────────────────────────────────────────
PRIMARY = get_setting('primary_color', '#354f61')
ACCENT  = get_setting('accent_color', '#f6ba3b')
company = get_setting('company_name', 'Surveying Experts')

st.sidebar.markdown(f"""
<div style="background:{PRIMARY}; padding:20px 16px 14px; margin:-1rem -1rem 0; text-align:center;">
    <p style="color:white; font-size:18px; font-weight:bold; margin:0;">{company}</p>
    <p style="color:rgba(255,255,255,0.6); font-size:11px; margin:4px 0 0;">Commission Manager</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("**Navigation**")
st.sidebar.page_link("Home.py",              label="📊 Dashboard")
st.sidebar.page_link("pages/2_Sales.py",     label="📝 Sales Input")
st.sidebar.page_link("pages/3_KPI.py",       label="🎯 KPI Calculation")
st.sidebar.page_link("pages/4_Commission.py",label="💰 Final Commission")
st.sidebar.page_link("pages/5_Reports.py",   label="📄 Reports Center")
st.sidebar.page_link("pages/6_Settings.py",  label="⚙️ Settings")
st.sidebar.page_link("pages/7_Audit.py",     label="📋 Audit Log")

# ── Period selector ──────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown("**Active Period**")
col1, col2 = st.sidebar.columns(2)
year    = col1.selectbox("Year",    [2024, 2025, 2026, 2027], index=2, key="home_year")
quarter = col2.selectbox("Quarter", [1, 2, 3, 4],             index=1, key="home_q",
                          format_func=lambda q: f"Q{q}")
period  = get_or_create_period(year, quarter)

# ── Main content ──────────────────────────────────────────────────────────────
st.markdown(f"""
<h1 style="color:{PRIMARY}; margin-bottom:4px;">📊 Real-Time Dashboard</h1>
<p style="color:#5a7080;">Live commission overview · Q{quarter} {year}</p>
""", unsafe_allow_html=True)
st.divider()

with st.spinner("Calculating commissions..."):
    commissions = calc_all_commissions(period['id'])
    totals      = get_totals(commissions)

# ── KPI metric cards ──────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
def sar(v): return f"SAR {v:,.0f}"
def pct(v): return f"{v:.1f}%"

c1.metric("Total Actual Sales",  sar(totals['total_sales']),  f"vs target {sar(totals['total_target'])}")
c2.metric("Overall Achievement", pct(totals['achievement']))
c3.metric("Base Commission",     sar(totals['total_base']))
c4.metric("Final Commission",    sar(totals['total_final']),  f"KPI adjusted")
c5.metric("Achieved Target",     f"{totals['achieved_count']} / {totals['total_count']}")

st.divider()

# ── Charts row ────────────────────────────────────────────────────────────────
import plotly.graph_objects as go
import plotly.express as px

col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown(f"#### Target vs. Actual Sales by Salesperson")
    if commissions:
        names   = [c['salesperson_name'].split()[0] for c in commissions]
        targets = [c['total_target'] / 1000 for c in commissions]
        actuals = [c['total_actual'] / 1000 for c in commissions]
        fig = go.Figure()
        fig.add_bar(name='Target', x=names, y=targets, marker_color=PRIMARY, opacity=0.75)
        fig.add_bar(name='Actual', x=names, y=actuals, marker_color=ACCENT,  opacity=0.9)
        fig.update_layout(barmode='group', height=320, margin=dict(l=10,r=10,t=10,b=10),
                          legend=dict(orientation='h', y=1.1), yaxis_title="SAR (thousands)",
                          plot_bgcolor='white', paper_bgcolor='white')
        fig.update_yaxes(gridcolor='#f0f3f5')
        st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.markdown("#### Achievement % by Salesperson")
    if commissions:
        sorted_c = sorted(commissions, key=lambda c: c['achievement'], reverse=True)
        names = [c['salesperson_name'].split()[0] for c in sorted_c]
        achs  = [c['achievement'] for c in sorted_c]
        colors = ['#27ae60' if a >= 100 else '#f39c12' if a >= 80 else '#e74c3c' for a in achs]
        fig2 = go.Figure(go.Bar(x=achs, y=names, orientation='h', marker_color=colors, opacity=0.85))
        fig2.add_vline(x=100, line_dash="dash", line_color=PRIMARY, line_width=1.5)
        fig2.update_layout(height=320, margin=dict(l=10,r=30,t=10,b=10),
                            xaxis_title="Achievement %", plot_bgcolor='white', paper_bgcolor='white')
        fig2.update_xaxes(gridcolor='#f0f3f5')
        st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── Top 5 + Category pie ──────────────────────────────────────────────────────
col_top5, col_pie = st.columns([2, 3])

with col_top5:
    st.markdown(f"#### 🏆 Top 5 — Sales Overall")
    import pandas as pd
    medals = ["🥇", "🥈", "🥉", "4th", "5th"]
    top5   = totals.get('top5', [])
    if top5:
        df = pd.DataFrame([{
            "Rank": medals[i],
            "Salesperson": c['salesperson_name'],
            "Sales": sar(c['total_actual']),
            "Ach %": pct(c['achievement']),
        } for i, c in enumerate(top5)])
        st.dataframe(df, use_container_width=True, hide_index=True,
                     column_config={"Rank": st.column_config.TextColumn(width="small")})

with col_pie:
    st.markdown("#### Sales by Category")
    from src.models import get_sales
    all_sales = get_sales(period['id'])
    if all_sales:
        cat_totals = {}
        for r in all_sales:
            cat_totals[r['cat_name']] = cat_totals.get(r['cat_name'], 0) + r['actual_sales']
        fig3 = px.pie(values=list(cat_totals.values()), names=list(cat_totals.keys()),
                      color_discrete_sequence=[PRIMARY, ACCENT, '#27ae60', '#e74c3c', '#8e44ad'],
                      hole=0.35)
        fig3.update_traces(textposition='inside', textinfo='percent+label')
        fig3.update_layout(height=300, margin=dict(l=10,r=10,t=10,b=10),
                            showlegend=True, legend=dict(orientation='v'))
        st.plotly_chart(fig3, use_container_width=True)

# ── Branch summary table ──────────────────────────────────────────────────────
st.divider()
st.markdown("#### Branch Summary")
if commissions:
    branch_data = {}
    for c in commissions:
        b = c['branch_name']
        if b not in branch_data:
            branch_data[b] = {'sales': 0, 'target': 0, 'final': 0, 'count': 0}
        branch_data[b]['sales']  += c['total_actual']
        branch_data[b]['target'] += c['total_target']
        branch_data[b]['final']  += c['final_commission']
        branch_data[b]['count']  += 1

    df_br = pd.DataFrame([{
        "Branch":          b,
        "Total Sales":     sar(v['sales']),
        "Target":          sar(v['target']),
        "Achievement %":   pct((v['sales']/v['target']*100) if v['target'] else 0),
        "Final Commission":sar(v['final']),
        "Salespersons":    v['count'],
    } for b, v in branch_data.items()])
    st.dataframe(df_br, use_container_width=True, hide_index=True)

st.sidebar.markdown("---")
st.sidebar.caption(f"v1.0.0 · {company}")
