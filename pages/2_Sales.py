import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import streamlit as st
import pandas as pd
from src.models import (get_setting, get_salespersons, get_categories,
                         get_or_create_period, save_sale, get_sales,
                         get_tier_target, log_action)
from src.calculations import calc_all_commissions, get_totals

PRIMARY = get_setting('primary_color', '#354f61')
ACCENT  = get_setting('accent_color', '#f6ba3b')

st.set_page_config(page_title="Sales Input", layout="wide")
st.markdown(f"<h1 style='color:{PRIMARY}'>📝 Sales Input</h1>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])
year    = col1.selectbox("Year",    [2024, 2025, 2026, 2027], index=2)
quarter = col2.selectbox("Quarter", [1, 2, 3, 4],             index=1, format_func=lambda q: f"Q{q}")
period  = get_or_create_period(year, quarter)

if period.get('is_locked'):
    st.warning("🔒 This quarter is locked. Contact your manager to unlock.")
    st.stop()

st.divider()

salespeople = get_salespersons(active_only=True)
categories  = [c for c in get_categories(active_only=True) if c['include_in_commission']]
all_sales   = get_sales(period['id'])
sales_map   = {(r['salesperson_id'], r['category_id']): r['actual_sales'] for r in all_sales}

# Build editable dataframe
rows = []
for sp in salespeople:
    row = {
        'Salesperson': sp['name'],
        'Branch': sp.get('branch_name', ''),
        'Tier': sp.get('tier_name', ''),
        '_sp_id': sp['id'],
        '_tier_id': sp.get('tier_id'),
    }
    for cat in categories:
        actual  = sales_map.get((sp['id'], cat['id']), 0.0)
        target  = get_tier_target(sp.get('tier_id'), cat['id']) if sp.get('tier_id') else 0.0
        row[cat['name']] = actual
        row[f"_{cat['id']}_target"] = target
    rows.append(row)

df = pd.DataFrame(rows)

# Only show editable columns (category actuals)
display_cols = ['Salesperson', 'Branch', 'Tier'] + [c['name'] for c in categories]
editable_df  = df[display_cols].copy()

st.markdown("**Enter actual sales amounts (SAR) for each salesperson:**")
st.caption("✏️ Edit any cell directly — click Save Changes when done.")

edited = st.data_editor(
    editable_df,
    use_container_width=True,
    disabled=['Salesperson', 'Branch', 'Tier'],
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

if st.button("💾 Save All Changes", type="primary", use_container_width=False):
    saved = 0
    for i, row in edited.iterrows():
        sp = salespeople[i]
        for cat in categories:
            val = row.get(cat['name'], 0) or 0
            save_sale(period['id'], sp['id'], cat['id'], float(val))
            saved += 1
    log_action("SALES_SAVE_ALL", "sales_records", None, f"Q{quarter} {year}", username="manager")
    st.success(f"✅ Saved {saved} sales records for Q{quarter} {year}.")
    st.rerun()

# ── Live commission preview ───────────────────────────────────────────────────
st.divider()
st.markdown("#### 📊 Live Commission Preview")
with st.spinner("Calculating..."):
    commissions = calc_all_commissions(period['id'])
    totals = get_totals(commissions)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Sales",       f"SAR {totals['total_sales']:,.0f}")
c2.metric("Total Target",      f"SAR {totals['total_target']:,.0f}")
c3.metric("Achievement",       f"{totals['achievement']:.1f}%")
c4.metric("Final Commission",  f"SAR {totals['total_final']:,.0f}")

preview_rows = [{
    "Salesperson":  c['salesperson_name'],
    "Branch":       c['branch_name'],
    "Total Sales":  f"SAR {c['total_actual']:,.0f}",
    "Target":       f"SAR {c['total_target']:,.0f}",
    "Achievement":  f"{c['achievement']:.1f}%",
    "Base Comm.":   f"SAR {c['base_commission']:,.0f}",
    "KPI Mult.":    f"× {c['kpi_multiplier']}",
    "Final Comm.":  f"SAR {c['final_commission']:,.0f}",
} for c in commissions]

st.dataframe(pd.DataFrame(preview_rows), use_container_width=True, hide_index=True)

# ── Import / Export template ──────────────────────────────────────────────────
st.divider()
with st.expander("📥 Import from Excel / Download Template"):
    import io
    from openpyxl import Workbook
    from openpyxl.styles import PatternFill, Font

    # Template download
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
    st.download_button("📥 Download Import Template", buf.getvalue(),
                       file_name=f"Sales_Template_Q{quarter}_{year}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    uploaded = st.file_uploader("Upload filled template:", type=['xlsx'])
    if uploaded:
        import openpyxl
        wb2 = openpyxl.load_workbook(uploaded)
        ws2 = wb2.active
        hdrs = [str(c.value).strip() if c.value else '' for c in ws2[1]]
        sp_map = {s['name']: s for s in salespeople}
        cat_map = {c['name']: c for c in categories}
        errors = []
        count  = 0
        for row in ws2.iter_rows(min_row=2, values_only=True):
            if not any(row):
                continue
            d = dict(zip(hdrs, row))
            sp_name = str(d.get('Salesperson Name', '') or '').strip()
            sp = sp_map.get(sp_name)
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
        st.success(f"✅ Imported {count} records.")
        st.rerun()
