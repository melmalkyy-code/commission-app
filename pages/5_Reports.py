import sys, os, io; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import streamlit as st
import pandas as pd
from src.models import get_setting, get_or_create_period, get_branches, get_salespersons
from src.calculations import calc_all_commissions, get_totals

PRIMARY = get_setting('primary_color', '#354f61')
ACCENT  = get_setting('accent_color', '#f6ba3b')
COMPANY = get_setting('company_name', 'Surveying Experts')
st.set_page_config(page_title="Reports Center", layout="wide")
st.markdown(f"<h1 style='color:{PRIMARY}'>📄 Reports Center</h1>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])
year    = col1.selectbox("Year",    [2024, 2025, 2026, 2027], index=2)
quarter = col2.selectbox("Quarter", [1, 2, 3, 4],             index=1, format_func=lambda q: f"Q{q}")
period  = get_or_create_period(year, quarter)
period_label = f"Q{quarter} {year}"

with st.spinner("Loading commission data..."):
    commissions = calc_all_commissions(period['id'])
    totals      = get_totals(commissions)
st.divider()


def make_excel_company() -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import PatternFill, Font, Alignment
    wb = Workbook()

    # Sheet 1: Summary
    ws = wb.active; ws.title = "Company Summary"
    fill = PatternFill(start_color="354f61", end_color="354f61", fill_type="solid")
    hdr_font = Font(color="FFFFFF", bold=True)
    ws.append([COMPANY, "", f"Company Commission Report — {period_label}"])
    for c in ws[1]: c.fill = fill; c.font = hdr_font
    ws.append([])
    ws.append(["Metric", "Value"])
    for c in ws[3]: c.fill = fill; c.font = hdr_font
    for row in [
        ("Total Sales", totals['total_sales']),
        ("Total Target", totals['total_target']),
        ("Achievement %", round(totals['achievement'], 1)),
        ("Base Commission", totals['total_base']),
        ("Final Commission", totals['total_final']),
        ("Salespersons", totals['total_count']),
        ("Achieved Target", totals['achieved_count']),
    ]:
        ws.append(list(row))

    # Sheet 2: All salespersons
    ws2 = wb.create_sheet("All Salespersons")
    headers = ["Salesperson","Branch","Tier","Total Sales","Target","Achievement %","Base Comm.","KPI Score","Multiplier","Final Comm."]
    ws2.append(headers)
    for c in ws2[1]: c.fill = fill; c.font = hdr_font
    for c in commissions:
        ws2.append([c['salesperson_name'], c['branch_name'], c['tier_name'],
                    c['total_actual'], c['total_target'], round(c['achievement'],1),
                    c['base_commission'], c['kpi_score'], c['kpi_multiplier'], c['final_commission']])

    # Sheet 3: By Branch
    ws3 = wb.create_sheet("By Branch")
    ws3.append(["Branch","Total Sales","Target","Achievement %","Base Comm.","Final Comm.","Salespersons"])
    for c in ws3[1]: c.fill = fill; c.font = hdr_font
    branch_data = {}
    for c in commissions:
        b = c['branch_name']
        if b not in branch_data:
            branch_data[b] = {'sales':0,'target':0,'base':0,'final':0,'count':0}
        branch_data[b]['sales']  += c['total_actual']
        branch_data[b]['target'] += c['total_target']
        branch_data[b]['base']   += c['base_commission']
        branch_data[b]['final']  += c['final_commission']
        branch_data[b]['count']  += 1
    for br_name, bv in branch_data.items():
        ach = (bv['sales']/bv['target']*100) if bv['target'] else 0
        ws3.append([br_name, bv['sales'], bv['target'], round(ach,1), bv['base'], bv['final'], bv['count']])

    # Sheet 4: Category breakdown
    ws4 = wb.create_sheet("By Category")
    ws4.append(["Branch","Salesperson","Category","Actual Sales","Target","Achievement %","Commission"])
    for c in ws4[1]: c.fill = fill; c.font = hdr_font
    for c in commissions:
        for cr in c['categories']:
            ach = (cr['actual_sales']/cr['target']*100) if cr['target'] else 0
            ws4.append([c['branch_name'], c['salesperson_name'], cr['category_name'],
                        cr['actual_sales'], cr['target'], round(ach,1), cr['commission']])

    for ws in [ws, ws2, ws3, ws4]:
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = max(len(str(c.value or '')) for c in col) + 4

    buf = io.BytesIO(); wb.save(buf); return buf.getvalue()


def make_excel_salesperson(c: dict) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import PatternFill, Font
    wb = Workbook(); ws = wb.active
    ws.title = "Commission Report"
    fill = PatternFill(start_color="354f61", end_color="354f61", fill_type="solid")
    hdr = Font(color="FFFFFF", bold=True)
    ws.append([COMPANY, period_label, c['salesperson_name'], c['branch_name'], c['tier_name']])
    for cell in ws[1]: cell.fill = fill; cell.font = hdr
    ws.append([])
    ws.append(["Category","Actual Sales","Target","Achievement %","Bracket","Rate %","Commission"])
    for cell in ws[3]: cell.fill = fill; cell.font = hdr
    for cr in c['categories']:
        ach = (cr['actual_sales']/cr['target']*100) if cr['target'] else 0
        ws.append([cr['category_name'], cr['actual_sales'], cr['target'], round(ach,1), cr['bracket'], cr['rate'], cr['commission']])
    ws.append([])
    ws.append(["Base Commission", c['base_commission']])
    ws.append(["KPI Score", c['kpi_score']])
    ws.append(["KPI Multiplier", c['kpi_multiplier']])
    ws.append(["FINAL COMMISSION", c['final_commission']])
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = 20
    buf = io.BytesIO(); wb.save(buf); return buf.getvalue()


def make_pdf_salesperson(c: dict) -> bytes:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import A4
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    primary = HexColor(PRIMARY)
    accent  = HexColor(ACCENT)
    story   = []

    title_st = ParagraphStyle('T', parent=styles['Title'], fontSize=16, textColor=primary)
    sub_st   = ParagraphStyle('S', parent=styles['Normal'], fontSize=10, textColor=HexColor('#5a7080'))
    sec_st   = ParagraphStyle('Sec', parent=styles['Normal'], fontSize=11, fontName='Helvetica-Bold', textColor=primary, spaceBefore=12, spaceAfter=6)

    story.append(Paragraph(f"{COMPANY}", title_st))
    story.append(Paragraph(f"Commission Report · {period_label} · {c['salesperson_name']} · {c['branch_name']}", sub_st))
    story.append(HRFlowable(width="100%", thickness=2, color=primary))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Category Breakdown", sec_st))
    data = [["Category","Actual Sales","Target","Ach %","Rate","Commission"]]
    for cr in c['categories']:
        ach = (cr['actual_sales']/cr['target']*100) if cr['target'] else 0
        data.append([cr['category_name'], f"SAR {cr['actual_sales']:,.0f}", f"SAR {cr['target']:,.0f}",
                     f"{ach:.1f}%", f"{cr['rate']:.2f}%", f"SAR {cr['commission']:,.0f}"])

    tbl = Table(data, hAlign='LEFT', repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,0), primary), ('TEXTCOLOR', (0,0),(-1,0), HexColor('#ffffff')),
        ('FONTNAME', (0,0),(-1,0), 'Helvetica-Bold'), ('FONTSIZE', (0,0),(-1,-1), 8),
        ('GRID', (0,0),(-1,-1), 0.3, HexColor('#dde5ea')), ('PADDING', (0,0),(-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1),(-1,-1), [HexColor('#ffffff'), HexColor('#f7f9fb')]),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Commission Summary", sec_st))
    summary = [
        ["Base Commission", f"SAR {c['base_commission']:,.0f}"],
        ["KPI Score",       f"{c['kpi_score']:.2f}"],
        ["KPI Multiplier",  f"× {c['kpi_multiplier']}"],
        ["FINAL COMMISSION",f"SAR {c['final_commission']:,.0f}"],
    ]
    stbl = Table(summary, colWidths=[200, 200], hAlign='LEFT')
    stbl.setStyle(TableStyle([
        ('FONTNAME', (0,0),(-1,-1), 'Helvetica'), ('FONTSIZE', (0,0),(-1,-1), 9),
        ('FONTNAME', (0,-1),(-1,-1), 'Helvetica-Bold'), ('FONTSIZE', (0,-1),(-1,-1), 11),
        ('BACKGROUND', (0,-1),(-1,-1), accent), ('TEXTCOLOR', (0,-1),(-1,-1), primary),
        ('GRID', (0,0),(-1,-1), 0.3, HexColor('#dde5ea')), ('PADDING', (0,0),(-1,-1), 6),
    ]))
    story.append(stbl)
    doc.build(story)
    return buf.getvalue()


# ── Report buttons ────────────────────────────────────────────────────────────
st.markdown("### Report 1 — Company-Wide Report")
col_a, col_b = st.columns(2)
with col_a:
    st.download_button("📥 Download Excel (Company)", make_excel_company(),
                       f"Company_{period_label.replace(' ','_')}_Report.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       type="primary", use_container_width=True)

st.divider()
st.markdown("### Report 2 — Single Salesperson Report")
sp_names   = [c['salesperson_name'] for c in commissions]
selected_sp = st.selectbox("Select Salesperson", sp_names, key="rep_sp")
selected_c  = next((c for c in commissions if c['salesperson_name'] == selected_sp), None)

if selected_c:
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📥 Download Excel",
            make_excel_salesperson(selected_c),
            f"{selected_sp.replace(' ','_')}_{period_label.replace(' ','_')}_Commission.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "📄 Download PDF",
            make_pdf_salesperson(selected_c),
            f"{selected_sp.replace(' ','_')}_{period_label.replace(' ','_')}_Commission.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
