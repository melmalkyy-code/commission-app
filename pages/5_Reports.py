import sys, os, io, base64; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import streamlit as st
import pandas as pd
from src.startup import init_db
from src.auth import require_login
init_db()
require_login()
from src.models import get_setting, get_or_create_period, get_period, get_branches, get_salespersons
from src.calculations import calc_all_commissions, get_totals

from src.ui import inject_css, page_header, sidebar_logo
from src.i18n import t, tl, q_label, is_rtl
from src.pdf_arabic import cell as _ar_cell, pdf_font, pdf_font_bold, ar as _ar

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
def make_excel_company(lang: str = 'en') -> bytes:
    from openpyxl import Workbook
    wb = Workbook()
    ph = PRIMARY.lstrip('#')
    def _t(s): return tl(s, lang)
    _rtl = lang == 'ar'

    # Sheet 1: Summary
    ws = wb.active
    ws.title = _t("Company Summary")
    if _rtl: ws.sheet_view.rightToLeft = True
    ws.append([COMPANY, "", f"{_t('Commission Report')} - {period_label}"])
    _fill_row(ws, 1, PRIMARY)
    _insert_logo_xl(ws)
    ws.append([])
    ws.append([_t("Metric"), _t("Value")])
    _fill_row(ws, 3, PRIMARY)
    for row in [
        (_t("Total Sales (SAR)"),      round(totals['total_sales'], 0)),
        (_t("Total Target (SAR)"),     round(totals['total_target'], 0)),
        (_t("Achievement %"),          round(totals['achievement'], 1)),
        (_t("Base Commission (SAR)"),  round(totals['total_base'], 0)),
        (_t("Final Commission (SAR)"), round(totals['total_final'], 0)),
        (_t("Total Salespersons"),     totals['total_count']),
        (_t("Achieved Target"),        totals['achieved_count']),
    ]:
        ws.append(list(row))
    _auto_width(ws)

    # Sheet 2: All Salespersons
    ws2 = wb.create_sheet(_t("All Salespersons"))
    if _rtl: ws2.sheet_view.rightToLeft = True
    ws2.append([_t("Salesperson"), _t("Branch"), _t("Tier"), _t("Total Sales"), _t("Target"),
                _t("Achievement %"), _t("Base Comm."), _t("KPI Score"),
                _t("KPI Multiplier"), _t("Final Comm.")])
    _fill_row(ws2, 1, PRIMARY)
    for c in commissions:
        ws2.append([c['salesperson_name'], c['branch_name'], c['tier_name'],
                    round(c['total_actual'], 0), round(c['total_target'], 0),
                    round(c['achievement'], 1), round(c['base_commission'], 0),
                    round(c['kpi_score'], 2), c['kpi_multiplier'],
                    round(c['final_commission'], 0)])
    _auto_width(ws2)

    # Sheet 3: By Branch
    ws3 = wb.create_sheet(_t("By Branch"))
    if _rtl: ws3.sheet_view.rightToLeft = True
    ws3.append([_t("Branch"), _t("Salespersons"), _t("Total Sales"), _t("Target"),
                _t("Achievement %"), _t("Base Comm."), _t("Final Comm.")])
    _fill_row(ws3, 1, PRIMARY)
    branch_map: dict = {}
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

    # Sheet 4: By Category
    ws4 = wb.create_sheet(_t("By Category"))
    if _rtl: ws4.sheet_view.rightToLeft = True
    ws4.append([_t("Branch"), _t("Salesperson"), _t("Category"), _t("Actual Sales"),
                _t("Target"), _t("Achievement %"), _t("Rate %"), _t("Commission")])
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
        ws5 = wb.create_sheet(f"{_t('QoQ vs')} {_prev_label}")
        if _rtl: ws5.sheet_view.rightToLeft = True
        ws5.append([
            _t("Salesperson"), _t("Branch"),
            f"{_t('Sales')} {_prev_label}", f"{_t('Sales')} {period_label}", _t("Sales Growth"),
            f"{_t('Final Comm.')} {_prev_label}", f"{_t('Final Comm.')} {period_label}", _t("Comm. Growth"),
            f"{_t('Ach.')} {_prev_label}", f"{_t('Ach.')} {period_label}", _t("Ach. Δ pp"),
        ])
        _fill_row(ws5, 1, PRIMARY)
        for c in commissions:
            p  = _prev_sp_map.get(c['salesperson_name'], {})
            ps = p.get('total_actual', 0)
            pc = p.get('final_commission', 0)
            pa = p.get('achievement', 0)
            ws5.append([
                c['salesperson_name'], c['branch_name'],
                round(ps, 0), round(c['total_actual'], 0), _qoq_g(c['total_actual'], ps),
                round(pc, 0), round(c['final_commission'], 0), _qoq_g(c['final_commission'], pc),
                round(pa, 1), round(c['achievement'], 1),
                round(c['achievement'] - pa, 1),
            ])
        ws5.append([])
        ws5.append([
            _t("COMPANY TOTAL"), "",
            round(_prev_totals['total_sales'], 0), round(totals['total_sales'], 0),
            _qoq_g(totals['total_sales'], _prev_totals['total_sales']),
            round(_prev_totals['total_final'], 0), round(totals['total_final'], 0),
            _qoq_g(totals['total_final'], _prev_totals['total_final']),
            round(_prev_totals['achievement'], 1), round(totals['achievement'], 1),
            round(totals['achievement'] - _prev_totals['achievement'], 1),
        ])
        _fill_row(ws5, ws5.max_row, ACCENT, font_hex=ph, bold=True)
        _auto_width(ws5)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ─── Branch Excel ─────────────────────────────────────────────────────────────
def make_excel_branch(branch_name: str, persons: list, lang: str = 'en') -> bytes:
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    def _t(s): return tl(s, lang)
    ws.title = _t("Branch Report")
    if lang == 'ar': ws.sheet_view.rightToLeft = True
    ws.append([COMPANY, branch_name, period_label])
    _fill_row(ws, 1, PRIMARY)
    _insert_logo_xl(ws)
    ws.append([])
    ws.append([_t("Salesperson"), _t("Tier"), _t("Sales"), _t("Target"), _t("Achievement %"),
               _t("Base Comm."), _t("KPI Score"), _t("KPI x"), _t("Final Comm."),
               f"{_t('Sales')} {_prev_label}", _t("Sales Growth"),
               f"{_t('Final Comm.')} {_prev_label}", _t("Comm. Growth")])
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
    ws.append([_t("TOTAL"), "", round(b_sales, 0), round(b_target, 0), "", "", "", "",
               round(b_final, 0),
               round(pb_sales, 0), _qoq_g(b_sales, pb_sales),
               round(pb_final, 0), _qoq_g(b_final, pb_final)])
    _fill_row(ws, ws.max_row, ACCENT, font_hex=PRIMARY.lstrip('#'), bold=True)
    _auto_width(ws)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ─── Salesperson Excel ────────────────────────────────────────────────────────
def make_excel_salesperson(c: dict, lang: str = 'en') -> bytes:
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    def _t(s): return tl(s, lang)
    ws.title = _t("Commission Report")
    if lang == 'ar': ws.sheet_view.rightToLeft = True
    ws.append([COMPANY, period_label, c['salesperson_name'], c['branch_name'], c['tier_name']])
    _fill_row(ws, 1, PRIMARY)
    _insert_logo_xl(ws)
    ws.append([])
    ws.append([_t("Category"), _t("Actual Sales"), _t("Target"), _t("Achievement %"),
               _t("Bracket"), _t("Rate %"), _t("Commission")])
    _fill_row(ws, 3, PRIMARY)
    for cr in c['categories']:
        ach = (cr['actual_sales'] / cr['target'] * 100) if cr['target'] else 0
        ws.append([cr['category_name'], round(cr['actual_sales'], 0),
                   round(cr['target'], 0), round(ach, 1),
                   cr['bracket'], round(cr['rate'], 2), round(cr['commission'], 0)])
    ws.append([])
    for label, val in [(_t("Base Commission"), round(c['base_commission'], 0)),
                       (_t("KPI Score"),        round(c['kpi_score'], 2)),
                       (_t("KPI Multiplier"),   c['kpi_multiplier']),
                       (_t("FINAL COMMISSION"), round(c['final_commission'], 0))]:
        ws.append([label, val])
    _fill_row(ws, ws.max_row, ACCENT, font_hex=PRIMARY.lstrip('#'), bold=True)

    # QoQ comparison sheet
    p  = _prev_sp_map.get(c['salesperson_name'], {})
    if p:
        ws2 = wb.create_sheet(f"{_t('QoQ vs')} {_prev_label}")
        if lang == 'ar': ws2.sheet_view.rightToLeft = True
        ws2.append([f"{_t('QoQ Comparison')}: {c['salesperson_name']}",
                    _prev_label, period_label, _t("Growth QoQ")])
        _fill_row(ws2, 1, PRIMARY)
        ps = p.get('total_actual', 0)
        pc = p.get('final_commission', 0)
        pa = p.get('achievement', 0)
        for lbl, pv, cv in [
            (_t("Total Sales"),      ps,                   c['total_actual']),
            (_t("Achievement %"),    pa,                   c['achievement']),
            (_t("Base Commission"),  p.get('base_commission', 0), c['base_commission']),
            (_t("Final Commission"), pc,                   c['final_commission']),
        ]:
            ws2.append([lbl, round(pv, 1), round(cv, 1), _qoq_g(cv, pv)])
        ws2.append([])
        ws2.append([_t("FINAL COMMISSION GROWTH"), "", "", _qoq_g(c['final_commission'], pc)])
        _fill_row(ws2, ws2.max_row, ACCENT, font_hex=PRIMARY.lstrip('#'), bold=True)
        _auto_width(ws2)

    _auto_width(ws)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ─── Company PDF ─────────────────────────────────────────────────────────────
def make_pdf_company(lang: str = 'en') -> bytes:
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import A4
    def _t(s): return tl(s, lang)
    _c = lambda s: _ar_cell(s, lang)
    _fn  = pdf_font(lang)
    _fnb = pdf_font_bold(lang)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=40, rightMargin=40,
                            topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    pc = HexColor(PRIMARY)
    story = []

    title_st = ParagraphStyle('T', parent=styles['Title'], fontSize=16,
                               textColor=pc, fontName=_fn)
    sub_st   = ParagraphStyle('S', parent=styles['Normal'], fontSize=10,
                               textColor=HexColor('#5a7080'), fontName=_fn)
    sec_st   = ParagraphStyle('Sec', parent=styles['Normal'], fontSize=11,
                               fontName=_fnb, textColor=pc,
                               spaceBefore=12, spaceAfter=6)

    story.append(Paragraph(_c(COMPANY), title_st))
    story.append(Paragraph(_c(f"{_t('Commission Summary')} | {period_label}"), sub_st))
    story.append(HRFlowable(width="100%", thickness=2, color=pc))
    story.append(Spacer(1, 10))

    story.append(Paragraph(_c(_t("Company Summary")), sec_st))
    summary_data = [
        [_c(_t("Metric")), _c(_t("Value"))],
        [_c(_t("Total Sales (SAR)")),      f"SAR {totals['total_sales']:,.0f}"],
        [_c(_t("Total Target (SAR)")),     f"SAR {totals['total_target']:,.0f}"],
        [_c(_t("Achievement %")),          f"{totals['achievement']:.1f}%"],
        [_c(_t("Base Commission (SAR)")),  f"SAR {totals['total_base']:,.0f}"],
        [_c(_t("Final Commission (SAR)")), f"SAR {totals['total_final']:,.0f}"],
        [_c(_t("Total Salespersons")),     str(totals['total_count'])],
        [_c(_t("Achieved Target")),        str(totals['achieved_count'])],
    ]
    stbl = Table(summary_data, colWidths=[250, 180], hAlign='LEFT')
    stbl.setStyle(TableStyle([
        ('BACKGROUND',     (0, 0), (-1, 0),  pc),
        ('TEXTCOLOR',      (0, 0), (-1, 0),  HexColor('#ffffff')),
        ('FONTNAME',       (0, 0), (-1, -1), _fn),
        ('FONTNAME',       (0, 0), (-1, 0),  _fnb),
        ('FONTSIZE',       (0, 0), (-1, -1), 9),
        ('GRID',           (0, 0), (-1, -1), 0.3, HexColor('#dde5ea')),
        ('PADDING',        (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [HexColor('#ffffff'), HexColor('#f7f9fb')]),
    ]))
    story.append(stbl)
    story.append(Spacer(1, 14))

    story.append(Paragraph(_c(_t("All Salespersons")), sec_st))
    sp_data = [[_c(_t("Salesperson")), _c(_t("Branch")), _c(_t("Tier")),
                _c(_t("Total Sales (SAR)")), _c(_t("Achievement %")),
                _c(_t("KPI x")), _c(_t("Final Commission (SAR)"))]]
    for c in commissions:
        sp_data.append([
            _c(c['salesperson_name']), _c(c['branch_name'] or ''),
            _c(c['tier_name'] or ''),
            f"{c['total_actual']:,.0f}", f"{c['achievement']:.1f}%",
            f"x{c['kpi_multiplier']}", f"{c['final_commission']:,.0f}",
        ])
    sp_tbl = Table(sp_data, hAlign='LEFT', repeatRows=1)
    sp_tbl.setStyle(TableStyle([
        ('BACKGROUND',     (0, 0), (-1, 0),  pc),
        ('TEXTCOLOR',      (0, 0), (-1, 0),  HexColor('#ffffff')),
        ('FONTNAME',       (0, 0), (-1, -1), _fn),
        ('FONTNAME',       (0, 0), (-1, 0),  _fnb),
        ('FONTSIZE',       (0, 0), (-1, -1), 7),
        ('GRID',           (0, 0), (-1, -1), 0.3, HexColor('#dde5ea')),
        ('PADDING',        (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [HexColor('#ffffff'), HexColor('#f7f9fb')]),
    ]))
    story.append(sp_tbl)

    doc.build(story)
    return buf.getvalue()


# ─── Branch PDF ───────────────────────────────────────────────────────────────
def make_pdf_branch(branch_name: str, persons: list, lang: str = 'en') -> bytes:
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import A4
    def _t(s): return tl(s, lang)
    _c = lambda s: _ar_cell(s, lang)
    _fn  = pdf_font(lang)
    _fnb = pdf_font_bold(lang)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=40, rightMargin=40,
                            topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    pc = HexColor(PRIMARY)
    ac = HexColor(ACCENT)
    story = []

    title_st = ParagraphStyle('T', parent=styles['Title'], fontSize=16,
                               textColor=pc, fontName=_fn)
    sub_st   = ParagraphStyle('S', parent=styles['Normal'], fontSize=10,
                               textColor=HexColor('#5a7080'), fontName=_fn)
    sec_st   = ParagraphStyle('Sec', parent=styles['Normal'], fontSize=11,
                               fontName=_fnb, textColor=pc,
                               spaceBefore=12, spaceAfter=6)

    story.append(Paragraph(_c(COMPANY), title_st))
    story.append(Paragraph(
        _c(f"{_t('Branch Report')} | {branch_name} | {period_label}"), sub_st))
    story.append(HRFlowable(width="100%", thickness=2, color=pc))
    story.append(Spacer(1, 10))

    story.append(Paragraph(_c(_t("All Salespersons")), sec_st))
    tbl_data = [[_c(_t("Salesperson")), _c(_t("Tier")),
                 _c(_t("Total Sales (SAR)")), _c(_t("Total Target (SAR)")),
                 _c(_t("Achievement %")), _c(_t("KPI x")),
                 _c(_t("Final Commission (SAR)"))]]
    b_sales = b_target = b_final = 0.0
    for c in persons:
        ach = (c['total_actual'] / c['total_target'] * 100) if c['total_target'] else 0
        tbl_data.append([
            _c(c['salesperson_name']), _c(c['tier_name'] or ''),
            f"{c['total_actual']:,.0f}", f"{c['total_target']:,.0f}",
            f"{ach:.1f}%", f"x{c['kpi_multiplier']}",
            f"{c['final_commission']:,.0f}",
        ])
        b_sales  += c['total_actual']
        b_target += c['total_target']
        b_final  += c['final_commission']
    tbl_data.append([
        _c(_t("TOTAL")), "",
        f"{b_sales:,.0f}", f"{b_target:,.0f}",
        f"{(b_sales/b_target*100) if b_target else 0:.1f}%", "",
        f"{b_final:,.0f}",
    ])

    tbl = Table(tbl_data, hAlign='LEFT', repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND',     (0, 0),  (-1, 0),  pc),
        ('TEXTCOLOR',      (0, 0),  (-1, 0),  HexColor('#ffffff')),
        ('FONTNAME',       (0, 0),  (-1, -1), _fn),
        ('FONTNAME',       (0, 0),  (-1, 0),  _fnb),
        ('BACKGROUND',     (0, -1), (-1, -1), ac),
        ('FONTNAME',       (0, -1), (-1, -1), _fnb),
        ('FONTSIZE',       (0, 0),  (-1, -1), 8),
        ('GRID',           (0, 0),  (-1, -1), 0.3, HexColor('#dde5ea')),
        ('PADDING',        (0, 0),  (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1),  (-1, -2),
         [HexColor('#ffffff'), HexColor('#f7f9fb')]),
    ]))
    story.append(tbl)

    doc.build(story)
    return buf.getvalue()


# ─── Salesperson PDF ──────────────────────────────────────────────────────────
def make_pdf_salesperson(c: dict, lang: str = 'en') -> bytes:
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable,
                                    Image as _RLImage)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import A4
    def _t(s): return tl(s, lang)
    _c = lambda s: _ar_cell(s, lang)
    _fn  = pdf_font(lang)
    _fnb = pdf_font_bold(lang)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=40, rightMargin=40,
                            topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    pc = HexColor(PRIMARY)
    ac = HexColor(ACCENT)
    story = []

    title_st = ParagraphStyle('T', parent=styles['Title'],
                               fontSize=16, textColor=pc, fontName=_fn)
    sub_st   = ParagraphStyle('S', parent=styles['Normal'],
                               fontSize=10, textColor=HexColor('#5a7080'), fontName=_fn)
    sec_st   = ParagraphStyle('Sec', parent=styles['Normal'],
                               fontSize=11, fontName=_fnb,
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
        Paragraph(_c(COMPANY), title_st),
        Paragraph(
            _c(f"{_t('Commission Summary')} | {period_label} | "
               f"{c['salesperson_name']} | {c['branch_name']}"),
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

    story.append(Paragraph(_c(_t("Category Breakdown")), sec_st))
    tbl_data = [[_c(_t("Category")), _c(_t("Actual Sales")), _c(_t("Target")),
                 _c(_t("Achievement %")), _c(_t("Rate %")), _c(_t("Commission"))]]
    for cr in c['categories']:
        ach = (cr['actual_sales'] / cr['target'] * 100) if cr['target'] else 0
        tbl_data.append([
            _c(cr['category_name']),
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
        ('FONTNAME',     (0, 0), (-1, -1), _fn),
        ('FONTNAME',     (0, 0), (-1, 0),  _fnb),
        ('FONTSIZE',     (0, 0), (-1, -1), 8),
        ('GRID',         (0, 0), (-1, -1), 0.3, HexColor('#dde5ea')),
        ('PADDING',      (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [HexColor('#ffffff'), HexColor('#f7f9fb')]),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 12))

    story.append(Paragraph(_c(_t("Commission Summary")), sec_st))
    summary = [
        [_c(_t("Base Commission")), f"SAR {c['base_commission']:,.0f}"],
        [_c(_t("KPI Score")),       f"{c['kpi_score']:.2f}"],
        [_c(_t("KPI Multiplier")),  f"x {c['kpi_multiplier']}"],
        [_c(_t("FINAL COMMISSION")), f"SAR {c['final_commission']:,.0f}"],
    ]
    stbl = Table(summary, colWidths=[200, 200], hAlign='LEFT')
    stbl.setStyle(TableStyle([
        ('FONTNAME',    (0, 0), (-1, -1), _fn),
        ('FONTSIZE',    (0, 0), (-1, -1), 9),
        ('FONTNAME',    (0, -1), (-1, -1), _fnb),
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
        story.append(Paragraph(
            _c(f"{_t('QoQ Comparison')} vs {_prev_label}"), sec_st))
        ps_v = p_c.get('total_actual', 0)
        pc_v = p_c.get('final_commission', 0)
        pa_v = p_c.get('achievement', 0)
        qoq_data = [
            [_c(_t("Metric")), _prev_label, period_label, _c(_t("Growth QoQ"))],
            [_c(_t("Total Sales")),
             f"SAR {ps_v:,.0f}", f"SAR {c['total_actual']:,.0f}",
             _qoq_g(c['total_actual'], ps_v)],
            [_c(_t("Achievement %")),
             f"{pa_v:.1f}%", f"{c['achievement']:.1f}%",
             f"{c['achievement'] - pa_v:+.1f} pp"],
            [_c(_t("Final Commission")),
             f"SAR {pc_v:,.0f}", f"SAR {c['final_commission']:,.0f}",
             _qoq_g(c['final_commission'], pc_v)],
        ]
        qtbl = Table(qoq_data, hAlign='LEFT', repeatRows=1)
        qtbl.setStyle(TableStyle([
            ('BACKGROUND',   (0, 0), (-1, 0),  pc),
            ('TEXTCOLOR',    (0, 0), (-1, 0),  HexColor('#ffffff')),
            ('FONTNAME',     (0, 0), (-1, -1), _fn),
            ('FONTNAME',     (0, 0), (-1, 0),  _fnb),
            ('FONTSIZE',     (0, 0), (-1, -1), 8),
            ('GRID',         (0, 0), (-1, -1), 0.3, HexColor('#dde5ea')),
            ('PADDING',      (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [HexColor('#ffffff'), HexColor('#f7f9fb')]),
            ('FONTNAME',     (-1, 1), (-1, -1), _fnb),
        ]))
        story.append(qtbl)

    doc.build(story)
    return buf.getvalue()


# ── Reusable download options widget ─────────────────────────────────────────
def _download_options(key_prefix: str) -> tuple:
    """Render language + format selectors. Returns (lang_code, is_pdf)."""
    st.markdown(
        f"<div style='font-size:12px;font-weight:600;color:#354f61;"
        f"text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px'>"
        f"{t('Report Options')}</div>",
        unsafe_allow_html=True,
    )
    oc1, oc2 = st.columns(2)
    with oc1:
        lang_sel = st.radio(
            t("Report Language"),
            ["English", "العربية"],
            index=1 if is_rtl() else 0,
            horizontal=False,
            key=f"{key_prefix}_lang",
        )
    with oc2:
        fmt_sel = st.radio(
            t("Format"),
            ["Excel", "PDF"],
            horizontal=False,
            key=f"{key_prefix}_fmt",
        )
    _lang = 'ar' if 'العربية' in lang_sel else 'en'
    _pdf  = fmt_sel == "PDF"
    return _lang, _pdf


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
    _dl_lang_co, _dl_pdf_co = _download_options("co")
    if _dl_pdf_co:
        st.download_button(
            label=t('Download PDF'),
            data=make_pdf_company(lang=_dl_lang_co),
            file_name=f"{COMPANY}_{period_label.replace(' ','_')}_Report.pdf",
            mime="application/pdf",
            type="primary", use_container_width=True,
        )
    else:
        st.download_button(
            label=t('Download Excel'),
            data=make_excel_company(lang=_dl_lang_co),
            file_name=f"{COMPANY}_{period_label.replace(' ','_')}_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary", use_container_width=True,
        )
    st.caption(t("Includes: Company Summary, All Salespersons, By Branch, Category Breakdown"))


# ────────────────────────────────────────────────────────────────────────────
# BRANCH REPORT
# ────────────────────────────────────────────────────────────────────────────
with tab_branch:
    st.markdown(f"### {t('Branch Reports')} — {period_label}")

    branch_groups: dict = {}
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
            st.markdown(f"**{t('Branch Report')}: {sel_br}**")
            _dl_lang_br, _dl_pdf_br = _download_options("br")
            if _dl_pdf_br:
                st.download_button(
                    label=t('Download PDF'),
                    data=make_pdf_branch(sel_br, br_persons, lang=_dl_lang_br),
                    file_name=f"{sel_br}_{period_label.replace(' ','_')}_Branch.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            else:
                st.download_button(
                    label=t('Download {branch} — Excel').format(branch=sel_br),
                    data=make_excel_branch(sel_br, br_persons, lang=_dl_lang_br),
                    file_name=f"{sel_br}_{period_label.replace(' ','_')}_Branch.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

        st.markdown("---")
        st.markdown(f"**{t('Download All Branches (one file)')}**")
        _dl_lang_all, _dl_pdf_all = _download_options("br_all")
        if _dl_pdf_all:
            st.download_button(
                label=t('Download PDF'),
                data=make_pdf_company(lang=_dl_lang_all),
                file_name=f"AllBranches_{period_label.replace(' ','_')}_Report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.download_button(
                label=t('Download All Branches (one file)'),
                data=make_excel_company(lang=_dl_lang_all),
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
            m1.metric(t("Total Sales"),  f"SAR {sel_c['total_actual']:,.0f}")
            m2.metric(t("Achievement"),  f"{sel_c['achievement']:.1f}%")
            m3.metric(t("Base Comm."),   f"SAR {sel_c['base_commission']:,.0f}")
            m4.metric(t("Final Comm."),  f"SAR {sel_c['final_commission']:,.0f}")

            st.markdown("---")
            _dl_lang_sp, _dl_pdf_sp = _download_options("sp")
            if _dl_pdf_sp:
                st.download_button(
                    label=t('Download PDF'),
                    data=make_pdf_salesperson(sel_c, lang=_dl_lang_sp),
                    file_name=f"{selected_sp.replace(' ','_')}_{period_label.replace(' ','_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            else:
                st.download_button(
                    label=t('Download Excel'),
                    data=make_excel_salesperson(sel_c, lang=_dl_lang_sp),
                    file_name=f"{selected_sp.replace(' ','_')}_{period_label.replace(' ','_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
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


