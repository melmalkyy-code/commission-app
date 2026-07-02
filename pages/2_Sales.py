import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import streamlit as st
from src.startup import init_db
from src.auth import require_login, logout_button
init_db()
require_login()
import pandas as pd
from src.models import (get_setting, get_salespersons, get_categories,
                         get_or_create_period, save_sale, get_sales,
                         get_tier_target, log_action)
from src.calculations import calc_all_commissions, get_totals
from src.ui import inject_css, page_header, sidebar_logo
from src.i18n import t, q_label

PRIMARY = get_setting('primary_color', '#354f61')
ACCENT  = get_setting('accent_color', '#f6ba3b')
COMPANY = get_setting('company_name', 'Surveying Experts')

st.set_page_config(page_title="Sales Input — Surveying Experts", layout="wide")
inject_css(PRIMARY)
sidebar_logo(COMPANY, PRIMARY)
page_header(t("Sales Input"), t("Enter actual sales amounts (SAR) for each salesperson"), PRIMARY)

col1, col2 = st.columns([1, 1])
year    = col1.selectbox(t("Year"),    [2024, 2025, 2026, 2027], index=2)
quarter = col2.selectbox(t("Quarter"), [1, 2, 3, 4],             index=1,
                          format_func=q_label)
period  = get_or_create_period(year, quarter)

if period.get('is_locked'):
    st.warning(t("This quarter is locked. Contact your manager to unlock it in Settings."))
    st.stop()

st.divider()

salespeople = get_salespersons(active_only=True)
categories  = [c for c in get_categories(active_only=True) if c['include_in_commission']]
all_sales   = get_sales(period['id'])
sales_map   = {(r['salesperson_id'], r['category_id']): float(r['actual_sales'] or 0)
               for r in all_sales}

if not salespeople:
    st.info(t("No active salespersons found. Please add salespersons in Settings first."))
    st.stop()
if not categories:
    st.info(t("No active categories found. Please configure categories in Settings first."))
    st.stop()

# Build editable dataframe — use `or ''` to convert SQL NULL to empty string
rows = []
for sp in salespeople:
    row = {
        t('Salesperson'): sp['name'],
        t('Branch'):      sp.get('branch_name') or '',
        t('Tier'):        sp.get('tier_name') or '',
        '_sp_id':      sp['id'],
        '_tier_id':    sp.get('tier_id'),
    }
    for cat in categories:
        actual = sales_map.get((sp['id'], cat['id']), 0.0)
        row[cat['name']] = actual
    rows.append(row)

df           = pd.DataFrame(rows)
display_cols = [t('Salesperson'), t('Branch'), t('Tier')] + [c['name'] for c in categories]
editable_df  = df[display_cols].copy()

st.markdown(f"**{t('Enter actual sales amounts (SAR) for each salesperson:')}**")
st.caption(t("Changes are saved automatically as you edit each cell."))

edited = st.data_editor(
    editable_df,
    use_container_width=True,
    disabled=[t('Salesperson'), t('Branch'), t('Tier')],
    num_rows="fixed",
    column_config={
        cat['name']: st.column_config.NumberColumn(
            cat['name'],
            min_value=0,
            format="SAR %d",
            step=1000,
        )
        for cat in categories
    },
    key="sales_editor",
    hide_index=True,
)

# ── Auto-save on cell change ──────────────────────────────────────────────────
def _read_row_val(row, col_name: str) -> float:
    """Read a value from an iterrows() Series by exact column name, returning 0.0 on null."""
    raw = row.get(col_name)
    try:
        return 0.0 if (raw is None or pd.isna(raw)) else float(raw)
    except Exception:
        return 0.0

def _auto_save_sales():
    current_map = {}
    for idx, (_, row) in enumerate(edited.iterrows()):
        if idx >= len(salespeople):
            break
        sp = salespeople[idx]
        for cat in categories:
            current_map[(sp['id'], cat['id'])] = _read_row_val(row, cat['name'])

    if current_map != sales_map:
        for (sp_id, cat_id), val in current_map.items():
            save_sale(period['id'], sp_id, cat_id, val)
        st.cache_data.clear()
        log_action("SALES_AUTO_SAVE", "sales_records", notes=f"Q{quarter} {year}")
        st.toast(t("Changes saved"))

_auto_save_sales()

# Manual save button as explicit confirmation / fallback
if st.button(t("Save All Changes"), type="primary"):
    for idx, (_, row) in enumerate(edited.iterrows()):
        if idx >= len(salespeople):
            break
        sp = salespeople[idx]
        for cat in categories:
            save_sale(period['id'], sp['id'], cat['id'], _read_row_val(row, cat['name']))
    log_action("SALES_SAVE_ALL", "sales_records", notes=f"Q{quarter} {year}")
    st.cache_data.clear()
    st.success(t("Saved all sales records for Q{quarter} {year}.").format(quarter=quarter, year=year))
    st.rerun()

# ── Live commission preview ───────────────────────────────────────────────────
st.divider()
st.markdown(f"#### {t('Live Commission Preview')}")
with st.spinner(t("Calculating...")):
    commissions = calc_all_commissions(period['id'])
    totals      = get_totals(commissions)

c1, c2, c3, c4 = st.columns(4)
c1.metric(t("Total Sales"),      f"SAR {totals['total_sales']:,.0f}")
c2.metric(t("Total Target"),     f"SAR {totals['total_target']:,.0f}")
c3.metric(t("Achievement"),      f"{totals['achievement']:.1f}%")
c4.metric(t("Final Commission"), f"SAR {totals['total_final']:,.0f}")

preview_rows = [{
    t("Salesperson"):  c['salesperson_name'],
    t("Branch"):       c['branch_name'] or '',
    t("Total Sales"):  f"SAR {c['total_actual']:,.0f}",
    t("Target"):       f"SAR {c['total_target']:,.0f}",
    t("Achievement"):  f"{c['achievement']:.1f}%",
    t("Base Comm."):   f"SAR {c['base_commission']:,.0f}",
    t("KPI Mult."):    f"x {c['kpi_multiplier']}",
    t("Final Comm."):  f"SAR {c['final_commission']:,.0f}",
} for c in commissions]

st.dataframe(pd.DataFrame(preview_rows), use_container_width=True, hide_index=True)

# ── Import / Export ────────────────────────────────────────────────────────────
st.divider()
with st.expander(t("Import from Excel / Download Template")):
    import io
    from openpyxl import Workbook
    from openpyxl.styles import PatternFill, Font

    wb = Workbook()
    ws = wb.active
    ws.title = "Sales Import"
    headers = ["Year", "Quarter", "Salesperson Name"] + [c['name'] for c in categories]
    fill = PatternFill(start_color="354f61", end_color="354f61", fill_type="solid")
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = fill
        cell.font = Font(color="FFFFFF", bold=True)
    for sp in salespeople:
        ws.append([year, quarter, sp['name']] + [0] * len(categories))

    buf = io.BytesIO()
    wb.save(buf)
    st.download_button(
        t("Download Import Template"), buf.getvalue(),
        file_name=f"Sales_Template_Q{quarter}_{year}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    uploaded = st.file_uploader(t("Upload filled template:"), type=['xlsx'])
    if uploaded:
        import openpyxl
        wb2 = openpyxl.load_workbook(uploaded)
        ws2 = wb2.active
        hdrs = [str(c.value).strip() if c.value else '' for c in ws2[1]]
        sp_map_by_name = {s['name']: s for s in salespeople}
        cat_map = {c['name']: c for c in categories}
        errors, count = [], 0
        for row in ws2.iter_rows(min_row=2, values_only=True):
            if not any(row):
                continue
            d = dict(zip(hdrs, row))
            sp_name = str(d.get('Salesperson Name', '') or '').strip()
            sp = sp_map_by_name.get(sp_name)
            if not sp:
                errors.append(f"Salesperson not found: {sp_name}")
                continue
            for cat_name, cat in cat_map.items():
                val = d.get(cat_name)
                if val is not None:
                    try:
                        save_sale(period['id'], sp['id'], cat['id'], float(val))
                        count += 1
                    except Exception as e:
                        errors.append(str(e))
        if errors:
            st.warning("\n".join(errors[:5]))
        st.cache_data.clear()
        st.success(t("Imported {count} records.").format(count=count))
        st.rerun()

logout_button()
