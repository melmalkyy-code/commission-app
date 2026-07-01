import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import streamlit as st
from src.startup import init_db
from src.auth import require_login, logout_button
init_db()
require_login()
import pandas as pd
from src.models import get_setting, get_audit_logs

PRIMARY = get_setting('primary_color', '#354f61')
st.set_page_config(page_title="Audit Log", layout="wide")
st.markdown(f"<h1 style='color:{PRIMARY}'>?? Audit Log</h1>", unsafe_allow_html=True)
st.caption("Complete trail of all data changes and actions. Records are permanent.")

col1, col2, col3 = st.columns(3)
action_filter = col1.selectbox("Filter by Action", ["All", "SALES_SAVE_ALL", "KPI_SAVE_ALL",
                                                      "SETTINGS_CHANGE", "ADD_BRANCH", "EDIT_BRANCH",
                                                      "ADD_SALESPERSON", "QUARTER_LOCK", "QUARTER_UNLOCK"])
entity_filter = col2.selectbox("Filter by Entity", ["All", "sales_records", "kpi_records",
                                                      "branch", "salesperson", "settings", "period"])
limit = col3.selectbox("Max Records", [100, 250, 500, 1000], index=1)

action_arg = None if action_filter == "All" else action_filter
entity_arg = None if entity_filter == "All" else entity_filter
logs = get_audit_logs(action_type=action_arg, entity_type=entity_arg, limit=limit)

st.divider()
st.markdown(f"**{len(logs)}** records found")

if logs:
    df = pd.DataFrame([{
        "Timestamp":   l['timestamp'],
        "Action":      l['action_type'],
        "Entity":      l.get('entity_type',''),
        "Name":        l.get('entity_name',''),
        "Old Value":   (l.get('old_value','') or '')[:50],
        "New Value":   (l.get('new_value','') or '')[:50],
        "Notes":       (l.get('notes','') or '')[:80],
        "User":        l.get('username',''),
    } for l in logs])
    st.dataframe(df, use_container_width=True, hide_index=True)

    import io
    from openpyxl import Workbook
    wb = Workbook(); ws = wb.active
    ws.append(list(df.columns))
    for _, row in df.iterrows():
        ws.append(list(row))
    buf = io.BytesIO(); wb.save(buf)
    st.download_button("?? Export to Excel", buf.getvalue(), "Audit_Log.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
else:
    st.info("No audit records found.")
