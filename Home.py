import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from src.startup import init_db
from src.auth import require_login, logout_button
from src.models import get_setting, get_or_create_period, get_sales

st.set_page_config(
    page_title="Commission Dashboard — Surveying Experts",
    page_icon="chart_with_upwards_trend",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()
require_login()

from src.ui import inject_css, page_header, sidebar_logo, sar, pct
from src.calculations import calc_all_commissions, get_totals

PRIMARY = get_setting('primary_color', '#354f61')
ACCENT  = get_setting('accent_color',  '#f6ba3b')
COMPANY = get_setting('company_name',  'Surveying Experts')

inject_css(PRIMARY)
sidebar_logo(COMPANY, PRIMARY)

# ── Sidebar nav + period ──────────────────────────────────────────────────────
st.sidebar.page_link("Home.py",               label="Dashboard")
st.sidebar.page_link("pages/2_Sales.py",      label="Sales Input")
st.sidebar.page_link("pages/3_KPI.py",        label="KPI Calculation")
st.sidebar.page_link("pages/4_Commission.py", label="Commission Report")
st.sidebar.page_link("pages/5_Reports.py",    label="Reports Center")
st.sidebar.page_link("pages/6_Settings.py",   label="Settings")
st.sidebar.page_link("pages/7_Audit.py",      label="Audit Log")
st.sidebar.markdown("---")
st.sidebar.markdown("<span style='font-size:11px;text-transform:uppercase;letter-spacing:.1em'>Active Period</span>", unsafe_allow_html=True)
c1, c2 = st.sidebar.columns(2)
year    = c1.selectbox("Year",    [2024, 2025, 2026, 2027], index=2, key="home_year")
quarter = c2.selectbox("Quarter", [1, 2, 3, 4],             index=1, key="home_q",
                        format_func=lambda q: f"Q{q}")
period  = get_or_create_period(year, quarter)
st.sidebar.markdown("---")
logout_button()

period_label = f"Q{quarter} {year}"
lock_badge   = "Locked" if period.get('is_locked') else "Open"
lock_color   = "#e0a520" if period.get('is_locked') else "#1f9d62"

page_header(
    "Commission Dashboard",
    f"{period_label} &nbsp;·&nbsp; <span style='color:{lock_color};font-weight:500'>{lock_badge}</span>",
    PRIMARY,
)


@st.cache_data(ttl=60, show_spinner=False)
def _load(pid):
    c = calc_all_commissions(pid)
    return c, get_totals(c)


@st.cache_data(ttl=60, show_spinner=False)
def _sales(pid):
    return get_sales(pid)


# ── Previous quarter for QoQ ─────────────────────────────────────────────────
_pq_y = year - 1 if quarter == 1 else year
_pq_q = 4        if quarter == 1 else quarter - 1
prev_period = get_or_create_period(_pq_y, _pq_q)
prev_label  = f"Q{_pq_q} {_pq_y}"

with st.spinner(""):
    commissions,  totals      = _load(period['id'])
    prev_comms,   prev_totals = _load(prev_period['id'])

prev_sp_map = {c['salesperson_name']: c for c in prev_comms}


def _qd(curr: float, prev: float):
    """QoQ delta string for st.metric — None if no prev data."""
    if not prev:
        return None
    return f"{(curr - prev) / prev * 100:+.1f}% vs {prev_label}"


def _qg(curr: float, prev: float) -> str:
    """QoQ growth label for tables."""
    if prev == 0:
        return "—"
    d = (curr - prev) / prev * 100
    return f"{'▲' if d >= 0 else '▼'} {abs(d):.1f}%"


# ── KPI metric strip ──────────────────────────────────────────────────────────
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Total Sales",      sar(totals['total_sales']),  _qd(totals['total_sales'],  prev_totals['total_sales']))
m2.metric("Achievement",      pct(totals['achievement']),  _qd(totals['achievement'],  prev_totals['achievement']))
m3.metric("Base Commission",  sar(totals['total_base']),   _qd(totals['total_base'],   prev_totals['total_base']))
m4.metric("Final Commission", sar(totals['total_final']),  _qd(totals['total_final'],  prev_totals['total_final']))
m5.metric("On Target",        f"{totals['achieved_count']} / {totals['total_count']}")

st.markdown("<div style='margin:1.5rem 0 0'></div>", unsafe_allow_html=True)

# ── Three-level tabs ──────────────────────────────────────────────────────────
tab_co, tab_br, tab_sp, tab_qoq = st.tabs(
    ["Company", "By Branch", "By Salesperson", f"QoQ vs {prev_label}"]
)


# ════════════════════ COMPANY ═════════════════════════════════════════════════
with tab_co:
    if not commissions:
        st.info("No data for this period.")
    else:
        col_l, col_r = st.columns([3, 2])

        with col_l:
            st.markdown("#### Target vs Actual Sales")
            names   = [c['salesperson_name'].split()[0] for c in commissions]
            targets = [c['total_target'] / 1_000 for c in commissions]
            actuals = [c['total_actual'] / 1_000 for c in commissions]
            fig = go.Figure()
            fig.add_bar(name='Target', x=names, y=targets, marker_color=PRIMARY, opacity=0.65)
            fig.add_bar(name='Actual', x=names, y=actuals, marker_color=ACCENT,  opacity=0.9)
            fig.update_layout(
                barmode='group', height=300,
                margin=dict(l=0, r=0, t=8, b=8),
                legend=dict(orientation='h', y=1.08, font=dict(size=12)),
                yaxis_title="SAR (thousands)",
                yaxis=dict(gridcolor='#f0f3f5', zeroline=False),
                plot_bgcolor='white', paper_bgcolor='white',
                font=dict(family='IBM Plex Sans, system-ui, sans-serif', size=12),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_r:
            st.markdown("#### Achievement Ranking")
            sorted_c = sorted(commissions, key=lambda c: c['achievement'], reverse=True)
            fig2 = go.Figure(go.Bar(
                x=[c['achievement'] for c in sorted_c],
                y=[c['salesperson_name'].split()[0] for c in sorted_c],
                orientation='h',
                marker_color=['#1f9d62' if c['achievement'] >= 100
                              else '#e0a520' if c['achievement'] >= 80
                              else '#d64545'
                              for c in sorted_c],
                opacity=0.85,
            ))
            fig2.add_vline(x=100, line_dash="dash", line_color=PRIMARY, line_width=1.5)
            fig2.update_layout(
                height=300, margin=dict(l=0, r=20, t=8, b=8),
                xaxis=dict(title="Achievement %", gridcolor='#f0f3f5', zeroline=False),
                plot_bgcolor='white', paper_bgcolor='white',
                font=dict(family='IBM Plex Sans, system-ui, sans-serif', size=12),
            )
            st.plotly_chart(fig2, use_container_width=True)

        col_top, col_pie = st.columns([2, 3])
        with col_top:
            st.markdown("#### Top Performers")
            medals = ["1st", "2nd", "3rd", "4th", "5th"]
            top5   = totals.get('top5', [])
            df_top = pd.DataFrame([{
                "#": medals[i], "Salesperson": c['salesperson_name'],
                "Sales": sar(c['total_actual']), "Ach.": pct(c['achievement']),
            } for i, c in enumerate(top5)])
            st.dataframe(df_top, use_container_width=True, hide_index=True,
                         column_config={"#": st.column_config.TextColumn(width="small")})

        with col_pie:
            st.markdown("#### Sales Mix by Category")
            all_sales = _sales(period['id'])
            if all_sales:
                cat_totals = {}
                for r in all_sales:
                    cat_totals[r['cat_name']] = cat_totals.get(r['cat_name'], 0) + r['actual_sales']
                fig3 = px.pie(
                    values=list(cat_totals.values()),
                    names=list(cat_totals.keys()),
                    color_discrete_sequence=[PRIMARY, ACCENT, '#1f9d62', '#22A7A8', '#d64545',
                                             '#4a6a7e', '#f6ba3b', '#6b757d'],
                    hole=0.38,
                )
                fig3.update_traces(textposition='inside', textinfo='percent+label',
                                   textfont_size=11)
                fig3.update_layout(height=280, margin=dict(l=0, r=0, t=0, b=0),
                                   showlegend=False,
                                   font=dict(family='IBM Plex Sans, system-ui, sans-serif'))
                st.plotly_chart(fig3, use_container_width=True)


# ════════════════════ BY BRANCH ══════════════════════════════════════════════
with tab_br:
    if not commissions:
        st.info("No data for this period.")
    else:
        branch_map = {}
        for c in commissions:
            b = c['branch_name'] or 'Unknown'
            if b not in branch_map:
                branch_map[b] = {'sales': 0, 'target': 0, 'base': 0,
                                 'final': 0, 'count': 0, 'persons': []}
            branch_map[b]['sales']  += c['total_actual']
            branch_map[b]['target'] += c['total_target']
            branch_map[b]['base']   += c['base_commission']
            branch_map[b]['final']  += c['final_commission']
            branch_map[b]['count']  += 1
            branch_map[b]['persons'].append(c)

        # Branch summary cards
        br_cols = st.columns(max(len(branch_map), 1))
        for col, (br_name, bv) in zip(br_cols, branch_map.items()):
            ach   = (bv['sales'] / bv['target'] * 100) if bv['target'] else 0
            a_col = '#1f9d62' if ach >= 100 else '#e0a520' if ach >= 80 else '#d64545'
            col.markdown(
                f"<div style='background:{PRIMARY};border-radius:10px;padding:16px 14px;"
                f"text-align:center;color:rgba(255,255,255,0.9)'>"
                f"<div style='font-size:14px;font-weight:700;color:#fff;margin-bottom:10px'>"
                f"{br_name}</div>"
                f"<div style='font-size:10px;text-transform:uppercase;letter-spacing:.08em;"
                f"color:rgba(255,255,255,.5);margin-bottom:2px'>Salespersons</div>"
                f"<div style='font-size:16px;font-weight:600;color:#fff'>{bv['count']}</div>"
                f"<div style='font-size:10px;text-transform:uppercase;letter-spacing:.08em;"
                f"color:rgba(255,255,255,.5);margin:8px 0 2px'>Sales</div>"
                f"<div style='font-size:13px;font-weight:600;color:{ACCENT}'>{sar(bv['sales'])}</div>"
                f"<div style='font-size:10px;text-transform:uppercase;letter-spacing:.08em;"
                f"color:rgba(255,255,255,.5);margin:8px 0 2px'>Achievement</div>"
                f"<div style='font-size:18px;font-weight:700;color:{a_col}'>{ach:.1f}%</div>"
                f"<div style='font-size:10px;text-transform:uppercase;letter-spacing:.08em;"
                f"color:rgba(255,255,255,.5);margin:8px 0 2px'>Final Comm.</div>"
                f"<div style='font-size:13px;font-weight:600;color:{ACCENT}'>{sar(bv['final'])}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<div style='margin:1rem 0'></div>", unsafe_allow_html=True)

        br_names = list(branch_map.keys())
        fig_br   = go.Figure()
        fig_br.add_bar(name='Target',     x=br_names,
                       y=[branch_map[b]['target'] / 1_000 for b in br_names],
                       marker_color=PRIMARY, opacity=0.55)
        fig_br.add_bar(name='Sales',      x=br_names,
                       y=[branch_map[b]['sales']  / 1_000 for b in br_names],
                       marker_color=ACCENT, opacity=0.9)
        fig_br.add_bar(name='Commission', x=br_names,
                       y=[branch_map[b]['final']  / 1_000 for b in br_names],
                       marker_color='#1f9d62', opacity=0.85)
        fig_br.update_layout(
            barmode='group', height=260,
            margin=dict(l=0, r=0, t=8, b=8),
            legend=dict(orientation='h', y=1.08, font=dict(size=12)),
            yaxis=dict(title="SAR (thousands)", gridcolor='#f0f3f5', zeroline=False),
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(family='IBM Plex Sans, system-ui, sans-serif', size=12),
        )
        st.plotly_chart(fig_br, use_container_width=True)

        br_table = []
        for bname, bv in branch_map.items():
            ach = (bv['sales'] / bv['target'] * 100) if bv['target'] else 0
            br_table.append({
                "Branch": bname, "Staff": bv['count'],
                "Sales": sar(bv['sales']), "Target": sar(bv['target']),
                "Achievement": pct(ach), "Base": sar(bv['base']),
                "Final Commission": sar(bv['final']),
            })
        st.dataframe(pd.DataFrame(br_table), use_container_width=True, hide_index=True)


# ════════════════════ BY SALESPERSON ═════════════════════════════════════════
with tab_sp:
    if not commissions:
        st.info("No data for this period.")
    else:
        rows = [{
            "Salesperson": c['salesperson_name'],
            "Branch":      c['branch_name'],
            "Tier":        c['tier_name'],
            "Sales":       sar(c['total_actual']),
            "Target":      sar(c['total_target']),
            "Achievement": pct(c['achievement']),
            "Base Comm.":  sar(c['base_commission']),
            "KPI Score":   round(c['kpi_score'], 2),
            "KPI Mult.":   f"x{c['kpi_multiplier']}",
            "Final Comm.": sar(c['final_commission']),
        } for c in sorted(commissions, key=lambda c: c['final_commission'], reverse=True)]

        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
                     column_config={
                         "KPI Score": st.column_config.ProgressColumn(
                             "KPI Score", min_value=0, max_value=120, format="%.1f")
                     })

        st.markdown("#### Salesperson Drilldown")
        sel = st.selectbox("Select salesperson",
                           [c['salesperson_name'] for c in commissions],
                           key="home_sp")
        sel_c = next((c for c in commissions if c['salesperson_name'] == sel), None)
        if sel_c:
            d1, d2, d3, d4 = st.columns(4)
            d1.metric("Sales",        sar(sel_c['total_actual']))
            d2.metric("Achievement",  pct(sel_c['achievement']))
            d3.metric("KPI Score",    f"{sel_c['kpi_score']:.2f}")
            d4.metric("Final Comm.",  sar(sel_c['final_commission']))

            cat_rows = [{
                "Category":    cr['category_name'],
                "Actual":      sar(cr['actual_sales']),
                "Target":      sar(cr['target']),
                "Achievement": pct(cr['achievement']),
                "Commission":  sar(cr['commission']),
            } for cr in sel_c['categories']]
            st.dataframe(pd.DataFrame(cat_rows), use_container_width=True, hide_index=True)


# ════════════════════ QOQ COMPARISON ═════════════════════════════════════════
with tab_qoq:
    st.markdown(
        f"<div style='font-size:13px;color:#6b757d;margin-bottom:1rem'>"
        f"Comparing <b>{period_label}</b> against <b>{prev_label}</b>. "
        f"Growth is calculated as (Current − Previous) / Previous × 100.</div>",
        unsafe_allow_html=True,
    )

    if not prev_comms:
        st.info(f"No data recorded for {prev_label} — enter sales for that quarter first.")
    else:
        # ── Company summary ───────────────────────────────────────────────────
        st.markdown("#### Company Summary")
        comp_rows = [
            {
                "Metric":        "Total Sales",
                prev_label:      sar(prev_totals['total_sales']),
                period_label:    sar(totals['total_sales']),
                "Growth QoQ":    _qg(totals['total_sales'],   prev_totals['total_sales']),
            },
            {
                "Metric":        "Total Target",
                prev_label:      sar(prev_totals['total_target']),
                period_label:    sar(totals['total_target']),
                "Growth QoQ":    _qg(totals['total_target'],  prev_totals['total_target']),
            },
            {
                "Metric":        "Achievement %",
                prev_label:      pct(prev_totals['achievement']),
                period_label:    pct(totals['achievement']),
                "Growth QoQ":    f"{totals['achievement'] - prev_totals['achievement']:+.1f} pp",
            },
            {
                "Metric":        "Base Commission",
                prev_label:      sar(prev_totals['total_base']),
                period_label:    sar(totals['total_base']),
                "Growth QoQ":    _qg(totals['total_base'],    prev_totals['total_base']),
            },
            {
                "Metric":        "Final Commission",
                prev_label:      sar(prev_totals['total_final']),
                period_label:    sar(totals['total_final']),
                "Growth QoQ":    _qg(totals['total_final'],   prev_totals['total_final']),
            },
        ]
        st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)

        # ── Sales comparison chart ────────────────────────────────────────────
        st.markdown("#### Sales Trend by Salesperson")
        names_q  = [c['salesperson_name'].split()[0] for c in commissions]
        prev_s_q = [prev_sp_map.get(c['salesperson_name'], {}).get('total_actual', 0) / 1_000
                    for c in commissions]
        curr_s_q = [c['total_actual'] / 1_000 for c in commissions]
        fig_qoq = go.Figure()
        fig_qoq.add_bar(name=prev_label,   x=names_q, y=prev_s_q,
                        marker_color='#9ab2c0', opacity=0.8)
        fig_qoq.add_bar(name=period_label, x=names_q, y=curr_s_q,
                        marker_color=PRIMARY,   opacity=0.9)
        fig_qoq.update_layout(
            barmode='group', height=280,
            margin=dict(l=0, r=0, t=8, b=8),
            legend=dict(orientation='h', y=1.1, font=dict(size=12)),
            yaxis=dict(title="SAR (thousands)", gridcolor='#f0f3f5', zeroline=False),
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(family='IBM Plex Sans, system-ui, sans-serif', size=12),
        )
        st.plotly_chart(fig_qoq, use_container_width=True)

        # ── By salesperson ────────────────────────────────────────────────────
        st.markdown("#### By Salesperson")
        sp_qoq = []
        for c in sorted(commissions, key=lambda x: x['total_actual'], reverse=True):
            p  = prev_sp_map.get(c['salesperson_name'], {})
            ps = p.get('total_actual', 0)
            pc = p.get('final_commission', 0)
            sp_qoq.append({
                "Salesperson":             c['salesperson_name'],
                "Branch":                  c['branch_name'],
                f"Sales {prev_label}":     sar(ps),
                f"Sales {period_label}":   sar(c['total_actual']),
                "Sales Growth":            _qg(c['total_actual'], ps),
                f"Comm. {prev_label}":     sar(pc),
                f"Comm. {period_label}":   sar(c['final_commission']),
                "Comm. Growth":            _qg(c['final_commission'], pc),
            })
        st.dataframe(pd.DataFrame(sp_qoq), use_container_width=True, hide_index=True)

        # ── By branch ─────────────────────────────────────────────────────────
        st.markdown("#### By Branch")
        curr_br_agg: dict = {}
        prev_br_agg: dict = {}
        for c in commissions:
            b = c['branch_name'] or 'Unknown'
            curr_br_agg.setdefault(b, {'sales': 0, 'final': 0})
            curr_br_agg[b]['sales'] += c['total_actual']
            curr_br_agg[b]['final'] += c['final_commission']
        for c in prev_comms:
            b = c['branch_name'] or 'Unknown'
            prev_br_agg.setdefault(b, {'sales': 0, 'final': 0})
            prev_br_agg[b]['sales'] += c['total_actual']
            prev_br_agg[b]['final'] += c['final_commission']

        br_qoq = []
        for b in sorted(set(list(curr_br_agg) + list(prev_br_agg))):
            cs = curr_br_agg.get(b, {}).get('sales', 0)
            ps = prev_br_agg.get(b, {}).get('sales', 0)
            cf = curr_br_agg.get(b, {}).get('final', 0)
            pf = prev_br_agg.get(b, {}).get('final', 0)
            br_qoq.append({
                "Branch":                  b,
                f"Sales {prev_label}":     sar(ps),
                f"Sales {period_label}":   sar(cs),
                "Sales Growth":            _qg(cs, ps),
                f"Comm. {prev_label}":     sar(pf),
                f"Comm. {period_label}":   sar(cf),
                "Comm. Growth":            _qg(cf, pf),
            })
        st.dataframe(pd.DataFrame(br_qoq), use_container_width=True, hide_index=True)
