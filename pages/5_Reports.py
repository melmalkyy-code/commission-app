import sys, os, io, base64; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import streamlit as st
import pandas as pd
from src.startup import init_db
from src.auth import require_login, logout_button
init_db()
require_login()
from src.models import get_setting, get_or_create_period, get_period, get_branches, get_salespersons
from src.calculations import calc_all_commissions, get_totals

from src.ui import inject_css, page_header, sidebar_logo
from src.i18n import t, q_label

PRIMARY = get_setting('primary_color', '#354f61')
ACCENT  = get_setting('accent_color', '#f6ba3b')
COMPANY = get_setting('company_name', 'Surveying Experts')
_LOGO_B64   = get_setting('company_logo_b64', '')
_LOGO_BYTES = base64.b64decode(_LOGO_B64) if _LOGO_B64 else None
st.set_page_config(page_title="Reports Center — Surveying Experts", layout="wide")
inject_css(PRIMARY)
sidebar_logo(COMPANY, PRIMARY)
page_header(t("Reports Center"), t("Download commission reports at company, branch, and salesperson level"), PRIMARY)

col1, col2, _ = st.columns([1, 1, 4])
year    = col1.selectbox(t("Year"),    [2024, 2025, 2026, 2027], index=2, key="rep_year")
quarter = col2.selectbox(t("Quarter"), [1, 2, 3, 4],             index=1, key="rep_q",
                          format_func=q_label)
period  = get_or_create_period(year, quarter)
period_label = f"Q{quarter} {year}"

# ── Previous quarter for QoQ ─────────────────────────────────────────────────
_pq_y = year - 1 if quarter == 1 else year
_pq_q = 4        if quarter == 1 else quarter - 1
_prev_period = get_period(_pq_y, _pq_q)   # SELECT only — never inserts
_prev_label  = f"Q{_pq_q} {_pq_y}"

st.divider()

_EMPTY_T = {'total_sales': 0, 'total_target': 0, 'achievement': 0,
            'total_base': 0, 'total_final': 0, 'achieved_count': 0, 'total_count': 0}

with st.spinner(t("Loading data...")):
    commissions = calc_all_commissions(period['id'])
    totals      = get_totals(commissions)
    if _prev_period:
        _prev_commissions = calc_all_commissions(_prev_period['id'])
        _prev_totals      = get_totals(_prev_commissions)
    else:
        _prev_commissions = []
        _prev_totals      = _EMPTY_T
    _prev_sp_map = {c['salesperson_name']: c for c in _prev_commissions}


def _qoq_g(curr: float, prev: float) -> str:
    if prev == 0:
        return "—"
    d = (curr - prev) / prev * 100
    return f"{'▲' if d >= 0 else '▼'} {abs(d):.1f}%"


# ─── Excel helpers ────────────────────────────────────────────────────────────
def _fill_row(ws, row_idx, fill_hex, font_hex="FFFFFF", bold=True):
    from openpyxl.styles import PatternFill, Font, Alignment
    fill = PatternFill(start_color=fill_hex.lstrip('#'), end_color=fill_hex.lstrip('#'), fill_type="solid")
    font = Font(color=font_hex, bold=bold)
    for cell in ws[row_idx]:
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(horizontal='center', vertical='center')


def _auto_width(ws):
    for col in ws.columns:
        max_len = max((len(str(c.value or '')) for c in col), default=8)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 50)


def _insert_logo_xl(ws):
    if not _LOGO_BYTES:
        return
    try:
        from openpyxl.drawing.image import Image as XLImage
        img = XLImage(io.BytesIO(_LOGO_BYTES))
        img.width, img.height = 90, 45
        ws.add_image(img, 'A1')
        ws.row_dimensions[1].height = 40
    except Exception:
        pass


# ─── Company Excel ────────────────────────────────────────────────────────────
def make_excel_company() -> bytes:
    from openpyxl import Workbook
    wb = Workbook()
    ph = PRIMARY.lstrip('#')
    ah = ACCENT.lstrip('#')

    # Sheet 1: Summary
    ws = wb.active
    ws.title = "Company Summary"
    ws.append([COMPANY, "", f"Commission Report - {period_label}"])
    _fill_row(ws, 1, PRIMARY)
    _insert_logo_xl(ws)
    ws.append([])
    ws.append(["Metric", "Value"])
    _fill_row(ws, 3, PRIMARY)
    for row in [
        ("Total Sales (SAR)",        round(totals['total_sales'], 0)),
        ("Total Target (SAR)",       round(totals['total_target'], 0)),
        ("Achievement %",            round(totals['achievement'], 1)),
        ("Base Commission (SAR)",    round(totals['total_base'], 0)),
        ("Final Commission (SAR)",   round(totals['total_final'], 0)),
        ("Total Salespersons",       totals['total_count']),
        ("Achieved Target",          totals['achieved_count']),
    ]:
        ws.append(list(row))
    _auto_width(ws)

    # Sheet 2: All Salespersons
    ws2 = wb.create_sheet("All Salespersons")
    h2 = ["Salesperson", "Branch", "Tier", "Total Sales", "Target",
          "Achievement %", "Base Comm.", "KPI Score", "KPI Multiplier", "Final Comm."]
    ws2.append(h2)
    _fill_row(ws2, 1, PRIMARY)
    for c in commissions:
        ws2.append([c['salesperson_name'], c['branch_name'], c['tier_name'],
                    round(c['total_actual'], 0), round(c['total_target'], 0),
                    round(c['achievement'], 1), round(c['base_commission'], 0),
                    round(c['kpi_score'], 2), c['kpi_multiplier'],
                    round(c['final_commission'], 0)])
    _auto_width(ws2)

    # Sheet 3: By Branch
    ws3 = wb.create_sheet("By Branch")
    ws3.append(["Branch", "Salespersons", "Total Sales", "Target",
                "Achievement %", "Base Comm.", "Final Comm."])
    _fill_row(ws3, 1, PRIMARY)
    branch_map = {}
    for c in commissions:
        b = c['branch_name'] or 'Unknown'
        if b not in branch_map:
            branch_map[b] = {'count': 0, 'sales': 0, 'target': 0, 'base': 0, 'final': 0}
        branch_map[b]['count'] += 1
        branch_map[b]['sales']  += c['total_actual']
        branch_map[b]['target'] += c['total_target']
        branch_map[b]['base']   += c['base_commission']
        branch_map[b]['final']  += c['final_commission']
    for br, bv in branch_map.items():
        ach = (bv['sales'] / bv['target'] * 100) if bv['target'] else 0
        ws3.append([br, bv['count'], round(bv['sales'], 0), round(bv['target'], 0),
                    round(ach, 1), round(bv['base'], 0), round(bv['final'], 0)])
    _auto_width(ws3)

    # Sheet 4: Category Breakdown
    ws4 = wb.create_sheet("By Category")
    ws4.append(["Branch", "Salesperson", "Category", "Actual Sales",
                "Target", "Achievement %", "Rate %", "Commission"])
    _fill_row(ws4, 1, PRIMARY)
    for c in commissions:
        for cr in c['categories']:
            ach = (cr['actual_sales'] / cr['target'] * 100) if cr['target'] else 0
            ws4.append([c['branch_name'], c['salesperson_name'], cr['category_name'],
                        round(cr['actual_sales'], 0), round(cr['target'], 0),
                        round(ach, 1), round(cr['rate'], 2), round(cr['commission'], 0)])
    _auto_width(ws4)

    # Sheet 5: QoQ Analysis
    if _prev_commissions:
        ws5 = wb.create_sheet(f"QoQ vs {_prev_label}")
        ws5.append([
            "Salesperson", "Branch",
            f"Sales {_prev_label}", f"Sales {period_label}", "Sales Growth",
            f"Comm. {_prev_label}", f"Comm. {period_label}", "Comm. Growth",
            f"Ach. {_prev_label}", f"Ach. {period_label}", "Ach. Δ pp",
        ])
        _fill_row(ws5, 1, PRIMARY)
        for c in commissions:
            p  = _prev_sp_map.get(c['salesperson_name'], {})
            ps = p.get('total_actual', 0)
            pc = p.get('final_commission', 0)
            pa = p.get('achievement', 0)
            ws5.append([
                c['salesperson_name'], c['branch_name'],
                round(ps, 0), round(c['total_actual'], 0),
                _qoq_g(c['total_actual'], ps),
                round(pc, 0), round(c['final_commission'], 0),
                _qoq_g(c['final_commission'], pc),
                round(pa, 1), round(c['achievement'], 1),
                round(c['achievement'] - pa, 1),
            ])
        # Company totals row
        ws5.append([])
        ws5.append([
            "COMPANY TOTAL", "",
            round(_prev_totals['total_sales'], 0), round(totals['total_sales'], 0),
            _qoq_g(totals['total_sales'], _prev_totals['total_sales']),
            round(_prev_totals['total_final'], 0), round(totals['total_final'], 0),
            _qoq_g(totals['total_final'], _prev_totals['total_final']),
            round(_prev_totals['achievement'], 1), round(totals['achievement'], 1),
            round(totals['achievement'] - _prev_totals['achievement'], 1),
        ])
        _fill_row(ws5, ws5.max_row, ACCENT,
                  font_hex=ph, bold=True)
        _auto_width(ws5)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ─── Branch Excel ─────────────────────────────────────────────────────────────
def make_excel_branch(branch_name: str, persons: list) -> bytes:
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Branch Report"
    ws.append([COMPANY, branch_name, period_label])
    _fill_row(ws, 1, PRIMARY)
    _insert_logo_xl(ws)
    ws.append([])
    ws.append(["Salesperson", "Tier", "Sales", "Target", "Ach %",
               "Base Comm.", "KPI Score", "KPI x", "Final Comm.",
               f"Sales {_prev_label}", "Sales Growth",
               f"Comm. {_prev_label}", "Comm. Growth"])
    _fill_row(ws, 3, PRIMARY)
    for c in persons:
        p  = _prev_sp_map.get(c['salesperson_name'], {})
        ps = p.get('total_actual', 0)
        pc = p.get('final_commission', 0)
        ws.append([
            c['salesperson_name'], c['tier_name'],
            round(c['total_actual'], 0), round(c['total_target'], 0),
            round(c['achievement'], 1), round(c['base_commission'], 0),
            round(c['kpi_score'], 2), c['kpi_multiplier'],
            round(c['final_commission'], 0),
            round(ps, 0), _qoq_g(c['total_actual'], ps),
            round(pc, 0), _qoq_g(c['final_commission'], pc),
        ])
    # Totals row
    ws.append([])
    b_sales  = sum(c['total_actual'] for c in persons)
    b_target = sum(c['total_target'] for c in persons)
    b_final  = sum(c['final_commission'] for c in persons)
    pb_sales = sum(_prev_sp_map.get(c['salesperson_name'], {}).get('total_actual', 0) for c in persons)
    pb_final = sum(_prev_sp_map.get(c['salesperson_name'], {}).get('final_commission', 0) for c in persons)
    ws.append(["TOTAL", "", round(b_sales, 0), round(b_target, 0), "", "", "", "",
               round(b_final, 0),
               round(pb_sales, 0), _qoq_g(b_sales, pb_sales),
               round(pb_final, 0), _qoq_g(b_final, pb_final)])
    _fill_row(ws, ws.max_row, ACCENT, font_hex=PRIMARY.lstrip('#'), bold=True)
    _auto_width(ws)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ─── Salesperson Excel ────────────────────────────────────────────────────────
def make_excel_salesperson(c: dict) -> bytes:
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Commission Report"
    ws.append([COMPANY, period_label, c['salesperson_name'], c['branch_name'], c['tier_name']])
    _fill_row(ws, 1, PRIMARY)
    _insert_logo_xl(ws)
    ws.append([])
    ws.append(["Category", "Actual Sales", "Target", "Achievement %",
               "Bracket", "Rate %", "Commission"])
    _fill_row(ws, 3, PRIMARY)
    for cr in c['categories']:
        ach = (cr['actual_sales'] / cr['target'] * 100) if cr['target'] else 0
        ws.append([cr['category_name'], round(cr['actual_sales'], 0),
                   round(cr['target'], 0), round(ach, 1),
                   cr['bracket'], round(cr['rate'], 2), round(cr['commission'], 0)])
    ws.append([])
    for label, val in [("Base Commission", round(c['base_commission'], 0)),
                       ("KPI Score",        round(c['kpi_score'], 2)),
                       ("KPI Multiplier",   c['kpi_multiplier']),
                       ("FINAL COMMISSION", round(c['final_commission'], 0))]:
        ws.append([label, val])
    _fill_row(ws, ws.max_row, ACCENT, font_hex=PRIMARY.lstrip('#'), bold=True)

    # QoQ comparison sheet
    p  = _prev_sp_map.get(c['salesperson_name'], {})
    if p:
        ws2 = wb.create_sheet(f"QoQ vs {_prev_label}")
        ws2.append([f"QoQ Comparison: {c['salesperson_name']}",
                    _prev_label, period_label, "Growth"])
        _fill_row(ws2, 1, PRIMARY)
        ps = p.get('total_actual', 0)
        pc = p.get('final_commission', 0)
        pa = p.get('achievement', 0)
        for lbl, pv, cv in [
            ("Total Sales",      ps,                   c['total_actual']),
            ("Achievement %",    pa,                   c['achievement']),
            ("Base Commission",  p.get('base_commission', 0), c['base_commission']),
            ("Final Commission", pc,                   c['final_commission']),
        ]:
            ws2.append([lbl, round(pv, 1), round(cv, 1), _qoq_g(cv, pv)])
        ws2.append([])
        ws2.append(["FINAL COMMISSION GROWTH", "", "", _qoq_g(c['final_commission'], pc)])
        _fill_row(ws2, ws2.max_row, ACCENT, font_hex=PRIMARY.lstrip('#'), bold=True)
        _auto_width(ws2)

    _auto_width(ws)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ─── Salesperson PDF ──────────────────────────────────────────────────────────
def make_pdf_salesperson(c: dict) -> bytes:
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable,
                                    Image as _RLImage)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import A4
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=40, rightMargin=40,
                            topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    pc = HexColor(PRIMARY)
    ac = HexColor(ACCENT)
    story = []

    title_st = ParagraphStyle('T', parent=styles['Title'],
                               fontSize=16, textColor=pc)
    sub_st   = ParagraphStyle('S', parent=styles['Normal'],
                               fontSize=10, textColor=HexColor('#5a7080'))
    sec_st   = ParagraphStyle('Sec', parent=styles['Normal'],
                               fontSize=11, fontName='Helvetica-Bold',
                               textColor=pc, spaceBefore=12, spaceAfter=6)

    # Header — logo left, title right
    from reportlab.platypus import Table as RLTable, TableStyle as RLTS
    from reportlab.lib.units import cm
    header_logo = None
    if _LOGO_BYTES:
        try:
            from reportlab.lib.utils import ImageReader
            header_logo = _RLImage(ImageReader(io.BytesIO(_LOGO_BYTES)),
                                   width=2.4 * cm, height=1.2 * cm)
        except Exception:
            header_logo = None
    title_block = [
        Paragraph(COMPANY, title_st),
        Paragraph(
            f"Commission Report | {period_label} | "
            f"{c['salesperson_name']} | {c['branch_name']}",
            sub_st,
        ),
    ]
    if header_logo:
        hdr_tbl = RLTable([[header_logo, title_block]], colWidths=[2.8 * cm, None])
        hdr_tbl.setStyle(RLTS([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (0, 0), 0),
        ]))
        story.append(hdr_tbl)
    else:
        story.extend(title_block)
    story.append(HRFlowable(width="100%", thickness=2, color=pc))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Category Breakdown", sec_st))
    tbl_data = [["Category", "Actual Sales", "Target", "Ach %", "Rate", "Commission"]]
    for cr in c['categories']:
        ach = (cr['actual_sales'] / cr['target'] * 100) if cr['target'] else 0
        tbl_data.append([
            cr['category_name'],
            f"SAR {cr['actual_sales']:,.0f}",
            f"SAR {cr['target']:,.0f}",
            f"{ach:.1f}%",
            f"{cr['rate']:.2f}%",
            f"SAR {cr['commission']:,.0f}",
        ])
    tbl = Table(tbl_data, hAlign='LEFT', repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, 0),  pc),
        ('TEXTCOLOR',    (0, 0), (-1, 0),  HexColor('#ffffff')),
        ('FONTNAME',     (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',     (0, 0), (-1, -1), 8),
        ('GRID',         (0, 0), (-1, -1), 0.3, HexColor('#dde5ea')),
        ('PADDING',      (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [HexColor('#ffffff'), HexColor('#f7f9fb')]),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Commission Summary", sec_st))
    summary = [
        ["Base Commission", f"SAR {c['base_commission']:,.0f}"],
        ["KPI Score",       f"{c['kpi_score']:.2f}"],
        ["KPI Multiplier",  f"x {c['kpi_multiplier']}"],
        ["FINAL COMMISSION", f"SAR {c['final_commission']:,.0f}"],
    ]
    stbl = Table(summary, colWidths=[200, 200], hAlign='LEFT')
    stbl.setStyle(TableStyle([
        ('FONTNAME',    (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE',    (0, 0), (-1, -1), 9),
        ('FONTNAME',    (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',    (0, -1), (-1, -1), 11),
        ('BACKGROUND',  (0, -1), (-1, -1), ac),
        ('TEXTCOLOR',   (0, -1), (-1, -1), pc),
        ('GRID',        (0, 0), (-1, -1), 0.3, HexColor('#dde5ea')),
        ('PADDING',     (0, 0), (-1, -1), 6),
    ]))
    story.append(stbl)

    # ── QoQ Comparison section ────────────────────────────────────────────────
    p_c = _prev_sp_map.get(c['salesperson_name'], {})
    if p_c:
        story.append(Spacer(1, 14))
        story.append(Paragraph(f"Quarter-over-Quarter vs {_prev_label}", sec_st))
        ps_v = p_c.get('total_actual', 0)
        pc_v = p_c.get('final_commission', 0)
        pa_v = p_c.get('achievement', 0)
        qoq_data = [
            ["Metric", _prev_label, period_label, "Growth QoQ"],
            ["Total Sales",
             f"SAR {ps_v:,.0f}", f"SAR {c['total_actual']:,.0f}",
             _qoq_g(c['total_actual'], ps_v)],
            ["Achievement %",
             f"{pa_v:.1f}%", f"{c['achievement']:.1f}%",
             f"{c['achievement'] - pa_v:+.1f} pp"],
            ["Final Commission",
             f"SAR {pc_v:,.0f}", f"SAR {c['final_commission']:,.0f}",
             _qoq_g(c['final_commission'], pc_v)],
        ]
        qtbl = Table(qoq_data, hAlign='LEFT', repeatRows=1)
        qtbl.setStyle(TableStyle([
            ('BACKGROUND',   (0, 0), (-1, 0),  pc),
            ('TEXTCOLOR',    (0, 0), (-1, 0),  HexColor('#ffffff')),
            ('FONTNAME',     (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',     (0, 0), (-1, -1), 8),
            ('GRID',         (0, 0), (-1, -1), 0.3, HexColor('#dde5ea')),
            ('PADDING',      (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [HexColor('#ffffff'), HexColor('#f7f9fb')]),
            ('FONTNAME',     (-1, 1), (-1, -1), 'Helvetica-Bold'),
        ]))
        story.append(qtbl)

    doc.build(story)
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# THREE-LEVEL REPORT TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_company, tab_branch, tab_person = st.tabs([
    t("Company Report"), t("Branch Report"), t("Salesperson Report"),
])

# ────────────────────────────────────────────────────────────────────────────
# COMPANY REPORT
# ────────────────────────────────────────────────────────────────────────────
with tab_company:
    st.markdown(f"### {t('Company-Wide Report')} — {period_label}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("Total Sales"),      f"SAR {totals['total_sales']:,.0f}")
    c2.metric(t("Achievement"),      f"{totals['achievement']:.1f}%")
    c3.metric(t("Base Commission"),  f"SAR {totals['total_base']:,.0f}")
    c4.metric(t("Final Commission"), f"SAR {totals['total_final']:,.0f}")

    st.markdown("---")
    st.download_button(
        label=t("Download Company Excel (4 sheets)"),
        data=make_excel_company(),
        file_name=f"{COMPANY}_{period_label.replace(' ','_')}_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True,
    )
    st.caption(t("Includes: Company Summary, All Salespersons, By Branch, Category Breakdown"))


# ────────────────────────────────────────────────────────────────────────────
# BRANCH REPORT
# ────────────────────────────────────────────────────────────────────────────
with tab_branch:
    st.markdown(f"### {t('Branch Reports')} — {period_label}")

    # Build branch groups
    branch_groups = {}
    for c in commissions:
        b = c['branch_name'] or 'Unknown'
        branch_groups.setdefault(b, []).append(c)

    if not branch_groups:
        st.info(t("No commission data for this period."))
    else:
        # Summary table
        br_rows = []
        for br_name, persons in branch_groups.items():
            b_sales  = sum(c['total_actual'] for c in persons)
            b_target = sum(c['total_target'] for c in persons)
            b_final  = sum(c['final_commission'] for c in persons)
            ach = (b_sales / b_target * 100) if b_target else 0
            br_rows.append({
                t("Branch"):           br_name,
                t("Salespersons"):     len(persons),
                t("Total Sales"):      f"SAR {b_sales:,.0f}",
                t("Target"):           f"SAR {b_target:,.0f}",
                t("Achievement"):      f"{ach:.1f}%",
                t("Final Commission"): f"SAR {b_final:,.0f}",
            })
        st.dataframe(pd.DataFrame(br_rows), use_container_width=True, hide_index=True)
        st.markdown("---")

        # Per-branch download
        sel_br = st.selectbox(t("Select branch to download"), list(branch_groups.keys()),
                              key="rep_br_sel")
        if sel_br:
            br_persons = branch_groups[sel_br]
            col_a, col_b = st.columns(2)
            with col_a:
                st.download_button(
                    label=t("Download {branch} — Excel").format(branch=sel_br),
                    data=make_excel_branch(sel_br, br_persons),
                    file_name=f"{sel_br}_{period_label.replace(' ','_')}_Branch.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

        # All-branches download button
        st.download_button(
            label=t("Download All Branches (one file)"),
            data=make_excel_company(),
            file_name=f"AllBranches_{period_label.replace(' ','_')}_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


# ────────────────────────────────────────────────────────────────────────────
# SALESPERSON REPORT
# ────────────────────────────────────────────────────────────────────────────
with tab_person:
    st.markdown(f"### {t('Salesperson Reports')} — {period_label}")

    if not commissions:
        st.info(t("No commission data for this period."))
    else:
        sp_names    = [c['salesperson_name'] for c in commissions]
        selected_sp = st.selectbox(t("Select Salesperson"), sp_names, key="rep_sp_sel")
        sel_c       = next((c for c in commissions if c['salesperson_name'] == selected_sp), None)

        if sel_c:
            st.markdown(
                f"**{sel_c['salesperson_name']}** | "
                f"{sel_c['branch_name']} | {sel_c['tier_name']}"
            )
            m1, m2, m3, m4 = st.columns(4)
            m1.metric(t("Total Sales"),     f"SAR {sel_c['total_actual']:,.0f}")
            m2.metric(t("Achievement"),     f"{sel_c['achievement']:.1f}%")
            m3.metric(t("Base Comm."),      f"SAR {sel_c['base_commission']:,.0f}")
            m4.metric(t("Final Comm."),     f"SAR {sel_c['final_commission']:,.0f}")

            st.markdown("---")
            col_xl, col_pdf = st.columns(2)
            with col_xl:
                st.download_button(
                    label=t("Download Excel"),
                    data=make_excel_salesperson(sel_c),
                    file_name=f"{selected_sp.replace(' ','_')}_{period_label.replace(' ','_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            with col_pdf:
                st.download_button(
                    label=t("Download PDF"),
                    data=make_pdf_salesperson(sel_c),
                    file_name=f"{selected_sp.replace(' ','_')}_{period_label.replace(' ','_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

        st.divider()
        st.markdown(f"#### {t('All Salespersons Quick View')}")
        quick_rows = [{
            t("Name"):        c['salesperson_name'],
            t("Branch"):      c['branch_name'],
            t("Sales"):       f"SAR {c['total_actual']:,.0f}",
            t("Achievement"): f"{c['achievement']:.1f}%",
            t("Final Comm."): f"SAR {c['final_commission']:,.0f}",
        } for c in sorted(commissions, key=lambda x: x['final_commission'], reverse=True)]
        st.dataframe(pd.DataFrame(quick_rows), use_container_width=True, hide_index=True)

logout_button()
