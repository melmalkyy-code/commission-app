import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import streamlit as st
import pandas as pd
from src.startup import init_db
from src.auth import require_login, logout_button
init_db()
require_login()
from src.models import get_setting, get_audit_logs

PRIMARY = get_setting('primary_color', '#354f61')
st.set_page_config(page_title="Audit Log", layout="wide")
st.markdown(
    f"<h1 style='color:{PRIMARY};margin-bottom:2px'>Audit Log</h1>"
    f"<p style='color:#5a7080;margin-top:0'>Complete trail of all data changes and actions</p>",
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)
action_filter = col1.selectbox("Filter by Action", [
    "All", "SALES_SAVE_ALL", "KPI_SAVE_ALL", "SETTINGS_CHANGE",
    "ADD_BRANCH", "EDIT_BRANCH", "ADD_SALESPERSON", "QUARTER_LOCK", "QUARTER_UNLOCK",
])
entity_filter = col2.selectbox("Filter by Entity", [
    "All", "sales_records", "kpi_records", "branch",
    "salesperson", "settings", "period",
])
limit = col3.selectbox("Max Records", [100, 250, 500, 1000], index=1)

action_arg = None if action_filter == "All" else action_filter
entity_arg = None if entity_filter == "All" else entity_filter
logs = get_audit_logs(action_type=action_arg, entity_type=entity_arg, limit=limit)

st.divider()
st.markdown(f"**{len(logs)}** records found")

if logs:
    df = pd.DataFrame([{
        "Time":        r.get('timestamp', ''),
        "Action":      r.get('action_type', ''),
        "Entity":      r.get('entity_type', ''),
        "Name":        r.get('entity_name', ''),
        "Old Value":   r.get('old_value', ''),
        "New Value":   r.get('new_value', ''),
        "Notes":       r.get('notes', ''),
        "User":        r.get('username', ''),
    } for r in logs])
    st.dataframe(df, use_container_width=True, hide_index=True)

    import io
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    st.download_button(
        "Download Audit Log (Excel)",
        data=buf.getvalue(),
        file_name="audit_log.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
else:
    st.info("No audit records match the current filters.")

logout_button()
