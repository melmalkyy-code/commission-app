import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.startup import init_db
from src.auth import require_login
init_db()
require_login()
from src.models import get_setting, get_or_create_period
from src.calculations import calc_all_commissions, get_totals
from src.ui import inject_css, page_header, sidebar_logo, sar, pct
from src.i18n import t, q_label

PRIMARY = get_setting('primary_color', '#354f61')
ACCENT  = get_setting('accent_color', '#f6ba3b')
COMPANY = get_setting('company_name', 'Surveying Experts')

st.set_page_config(page_title="Commission Report — Surveying Experts", layout="wide")
inject_css(PRIMARY)
sidebar_logo(COMPANY, PRIMARY)
page_header(t("Commission Report"), t("Base Commission × KPI Multiplier = Final Commission"), PRIMARY)

# ── Period selector ──────────────────────────────────────────────────────────
col1, col2, _ = st.columns([1, 1, 4])
year    = col1.selectbox(t("Year"),    [2024, 2025, 2026, 2027], index=2, key="comm_year")
quarter = col2.selectbox(t("Quarter"), [1, 2, 3, 4],             index=1, key="comm_q",
                          format_func=q_label)
period  = get_or_create_period(year, quarter)
period_label = f"Q{quarter} {year}"
st.divider()

@st.cache_data(ttl=60, show_spinner=False)
def _load(pid):
    c = calc_all_commissions(pid)
    return c, get_totals(c)

with st.spinner(t("Computing commissions...")):
    commissions, totals = _load(period['id'])

# ── Three-level tabs ─────────────────────────────────────────────────────────
tab_company, tab_branch, tab_person = st.tabs([
    t("Company Level"), t("Branch Level"), t("Salesperson Level"),
])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — COMPANY LEVEL
# ════════════════════════════════════════════════════════════════════════════
with tab_company:
    st.markdown(f"### {t('Company')} — {period_label}")

    # KPI cards
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric(t("Total Sales"),      sar(totals['total_sales']))
    m2.metric(t("Total Target"),     sar(totals['total_target']))
    m3.metric(t("Achievement"),      pct(totals['achievement']))
    m4.metric(t("Base Commission"),  sar(totals['total_base']))
    m5.metric(t("Final Commission"), sar(totals['total_final']))
    m6.metric(t("Target Achieved"),  f"{totals['achieved_count']} / {totals['total_count']}")

    st.divider()

    # Bar chart — target vs actual per salesperson
    if commissions:
        names   = [c['salesperson_name'] for c in commissions]
        targets = [c['total_target'] / 1_000 for c in commissions]
        actuals = [c['total_actual'] / 1_000 for c in commissions]
        fig = go.Figure()
        fig.add_bar(name='Target (SAR k)', x=names, y=targets,
                    marker_color=PRIMARY, opacity=0.75)
        fig.add_bar(name='Actual (SAR k)', x=names, y=actuals,
                    marker_color=ACCENT, opacity=0.9)
        fig.update_layout(
            barmode='group', height=340,
            margin=dict(l=10, r=10, t=10, b=60),
            legend=dict(orientation='h', y=1.05),
            yaxis_title="SAR (thousands)",
            plot_bgcolor='white', paper_bgcolor='white',
            xaxis_tickangle=-25,
        )
        fig.update_yaxes(gridcolor='#f0f3f5')
        st.plotly_chart(fig, use_container_width=True)

    # Company-wide salesperson summary table
    st.markdown(f"#### {t('All Salespersons')}")
    rows = [{
        t("Salesperson"):    c['salesperson_name'],
        t("Branch"):         c['branch_name'],
        t("Tier"):           c['tier_name'],
        t("Total Sales"):    sar(c['total_actual']),
        t("Target"):         sar(c['total_target']),
        t("Achievement"):    pct(c['achievement']),
        t("Base Comm."):     sar(c['base_commission']),
        t("KPI Score"):      round(c['kpi_score'], 2),
        t("KPI Multiplier"): f"x {c['kpi_multiplier']}",
        t("Final Comm."):    sar(c['final_commission']),
    } for c in commissions]
    _ks = t("KPI Score")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
                 column_config={
                     _ks: st.column_config.ProgressColumn(_ks, min_value=0, max_value=120, format="%.2f")
                 })


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — BRANCH LEVEL
# ════════════════════════════════════════════════════════════════════════════
with tab_branch:
    st.markdown(f"### {t('By Branch')} — {period_label}")

    # Aggregate commissions by branch
    branch_map = {}
    for c in commissions:
        b = c['branch_name'] or 'Unknown'
        if b not in branch_map:
            branch_map[b] = {
                'sales': 0, 'target': 0, 'base': 0,
                'final': 0, 'count': 0, 'persons': [],
            }
        branch_map[b]['sales']   += c['total_actual']
        branch_map[b]['target']  += c['total_target']
        branch_map[b]['base']    += c['base_commission']
        branch_map[b]['final']   += c['final_commission']
        branch_map[b]['count']   += 1
        branch_map[b]['persons'].append(c)

    # Summary cards per branch
    if branch_map:
        br_cols = st.columns(len(branch_map))
        for col, (br_name, bv) in zip(br_cols, branch_map.items()):
            ach = (bv['sales'] / bv['target'] * 100) if bv['target'] else 0
            col.markdown(
                f"<div style='background:{PRIMARY};border-radius:8px;padding:14px;"
                f"text-align:center;color:white;'>"
                f"<b style='font-size:14px'>{br_name}</b><br>"
                f"<span style='font-size:11px;opacity:.7'>{t('Salespersons')}</span><br>"
                f"<b>{bv['count']}</b><br>"
                f"<span style='font-size:11px;opacity:.7'>{t('Sales')}</span><br>"
                f"<b style='color:{ACCENT}'>{sar(bv['sales'])}</b><br>"
                f"<span style='font-size:11px;opacity:.7'>{t('Achievement')}</span><br>"
                f"<b>{ach:.1f}%</b><br>"
                f"<span style='font-size:11px;opacity:.7'>{t('Final Comm.')}</span><br>"
                f"<b style='color:{ACCENT}'>{sar(bv['final'])}</b>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.divider()

        # Branch comparison chart
        br_names  = list(branch_map.keys())
        br_sales  = [branch_map[b]['sales'] / 1_000 for b in br_names]
        br_target = [branch_map[b]['target'] / 1_000 for b in br_names]
        br_final  = [branch_map[b]['final'] / 1_000 for b in br_names]

        fig_br = go.Figure()
        fig_br.add_bar(name='Target (SAR k)',       x=br_names, y=br_target,
                       marker_color=PRIMARY, opacity=0.6)
        fig_br.add_bar(name='Actual Sales (SAR k)', x=br_names, y=br_sales,
                       marker_color=ACCENT, opacity=0.85)
        fig_br.add_bar(name='Final Comm. (SAR k)',  x=br_names, y=br_final,
                       marker_color='#27ae60', opacity=0.85)
        fig_br.update_layout(
            barmode='group', height=300,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation='h', y=1.05),
            plot_bgcolor='white', paper_bgcolor='white',
        )
        fig_br.update_yaxes(gridcolor='#f0f3f5')
        st.plotly_chart(fig_br, use_container_width=True)

        # Per-branch drilldown
        st.markdown(f"#### {t('Branch Drilldown')}")
        sel_branch = st.selectbox(t("Select Branch"), br_names, key="comm_br_sel")
        if sel_branch and sel_branch in branch_map:
            bv = branch_map[sel_branch]
            ach = (bv['sales'] / bv['target'] * 100) if bv['target'] else 0

            b1, b2, b3, b4 = st.columns(4)
            b1.metric(t("Total Sales"),      sar(bv['sales']))
            b2.metric(t("Target"),           sar(bv['target']))
            b3.metric(t("Achievement"),      f"{ach:.1f}%")
            b4.metric(t("Final Commission"), sar(bv['final']))

            br_persons = [{
                t("Salesperson"):  c['salesperson_name'],
                t("Tier"):         c['tier_name'],
                t("Sales"):        sar(c['total_actual']),
                t("Target"):       sar(c['total_target']),
                t("Achievement"):  pct(c['achievement']),
                t("Base Comm."):   sar(c['base_commission']),
                t("KPI Mult."):    f"x {c['kpi_multiplier']}",
                t("Final Comm."):  sar(c['final_commission']),
            } for c in bv['persons']]
            st.dataframe(pd.DataFrame(br_persons),
                         use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — SALESPERSON LEVEL
# ════════════════════════════════════════════════════════════════════════════
with tab_person:
    st.markdown(f"### {t('By Salesperson')} — {period_label}")

    if not commissions:
        st.info(t("No commission data available for this period."))
    else:
        sp_names = [c['salesperson_name'] for c in commissions]
        selected = st.selectbox(t("Select Salesperson"), sp_names, key="comm_sp_sel")
        sel_c = next((c for c in commissions if c['salesperson_name'] == selected), None)

        if sel_c:
            col_info, col_card = st.columns([2, 1])

            with col_info:
                st.markdown(
                    f"**{sel_c['salesperson_name']}** | "
                    f"{sel_c['branch_name']} | {sel_c['tier_name']}"
                )
                cat_rows = [{
                    t("Category"):     cr['category_name'],
                    t("Actual Sales"): sar(cr['actual_sales']),
                    t("Target"):       sar(cr['target']),
                    t("Achievement"):  pct(cr['achievement']),
                    t("Bracket"):      cr['bracket'],
                    t("Rate"):         f"{cr['rate']:.2f}%",
                    t("Commission"):   sar(cr['commission']),
                } for cr in sel_c['categories']]
                st.dataframe(pd.DataFrame(cat_rows),
                             use_container_width=True, hide_index=True)

                # Achievement bar chart by category
                cat_names = [cr['category_name'] for cr in sel_c['categories']]
                cat_achs  = [cr['achievement'] for cr in sel_c['categories']]
                cat_cols  = ['#27ae60' if a >= 100 else '#f39c12' if a >= 80 else '#e74c3c'
                             for a in cat_achs]
                fig_cat = go.Figure(go.Bar(
                    x=cat_names, y=cat_achs,
                    marker_color=cat_cols, opacity=0.85,
                ))
                fig_cat.add_hline(y=100, line_dash="dash",
                                  line_color=PRIMARY, line_width=1.5)
                fig_cat.update_layout(
                    height=220, yaxis_title="Achievement %",
                    margin=dict(l=10, r=10, t=10, b=10),
                    plot_bgcolor='white', paper_bgcolor='white',
                )
                fig_cat.update_yaxes(gridcolor='#f0f3f5')
                st.plotly_chart(fig_cat, use_container_width=True)

            with col_card:
                st.markdown(
                    f"<div style='background:{PRIMARY};border-radius:12px;padding:24px;"
                    f"text-align:center;color:white;height:100%'>"
                    f"<p style='margin:0;font-size:11px;opacity:.65;'>{t('BASE COMMISSION')}</p>"
                    f"<p style='margin:4px 0;font-size:22px;font-weight:bold;'>"
                    f"{sar(sel_c['base_commission'])}</p>"
                    f"<p style='margin:12px 0 0;font-size:11px;opacity:.65;'>{t('KPI MULTIPLIER')}</p>"
                    f"<p style='margin:4px 0;font-size:22px;font-weight:bold;"
                    f"color:{ACCENT};'>x {sel_c['kpi_multiplier']}</p>"
                    f"<hr style='border-color:rgba(255,255,255,.2);margin:16px 0'>"
                    f"<p style='margin:0;font-size:11px;opacity:.65;'>{t('FINAL COMMISSION')}</p>"
                    f"<p style='margin:4px 0;font-size:30px;font-weight:bold;"
                    f"color:{ACCENT};'>{sar(sel_c['final_commission'])}</p>"
                    f"<p style='margin:10px 0 0;font-size:10px;opacity:.5;'>"
                    f"{t('KPI Score')}: {sel_c['kpi_score']:.2f}</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )


