"""End-to-end CRUD audit for the rewritten db layer. Run: python test_db_audit.py"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

# Use a throwaway SQLite file so we don't touch dev data
import src.db as db
import sqlite3, tempfile

_test_path = os.path.join(tempfile.gettempdir(), 'commission_audit_test.db')
if os.path.exists(_test_path):
    os.remove(_test_path)

def _open_test_sqlite():
    conn = sqlite3.connect(_test_path, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

db._open_sqlite = _open_test_sqlite
db._detected = True   # force: no PG URL => SQLite path
db._DB_URL = None

failures = []

def check(label, cond, detail=""):
    mark = "PASS" if cond else "FAIL"
    print(f"[{mark}] {label}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(label)

# 1. dialect decision is deterministic BEFORE any connection exists
check("is_postgres() callable before get_conn()", db.is_postgres() == False)

# 2. schema + seed
from src.schema import create_schema
from src.seed import seed
create_schema()
seed()
check("schema + seed completed", True)

from src.models import (
    get_branches, add_branch, update_branch, delete_branch,
    get_kpi_items, add_kpi_item, update_kpi_item, delete_kpi_item,
    add_salesperson, get_salespersons, delete_salesperson,
    get_multiplier_rules, add_multiplier_rule, delete_multiplier_rule,
    set_setting, get_setting,
)

# Streamlit cache decorators no-op outside a running app? They work via st.cache_data
# which functions in bare-script mode too, but clear between steps to be safe.
import streamlit as st

# 3. Branch CRUD
st.cache_data.clear()
n_before = len(get_branches())
new_id = add_branch("Audit Test Branch", "Test Region")
check("add_branch returns valid id", isinstance(new_id, int) and new_id > 0, f"got {new_id!r}")
st.cache_data.clear()
rows = [b for b in get_branches() if b['name'] == "Audit Test Branch"]
check("branch persisted after add", len(rows) == 1)
update_branch(new_id, "Audit Test Branch v2", "Test Region 2", True)
st.cache_data.clear()
row = [b for b in get_branches() if b['id'] == new_id][0]
check("branch update persisted", row['name'] == "Audit Test Branch v2" and row['region'] == "Test Region 2")
delete_branch(new_id)
st.cache_data.clear()
check("branch delete persisted", not [b for b in get_branches() if b['id'] == new_id])

# 4. KPI item CRUD
kid = add_kpi_item("Audit KPI", 15.0, 100.0, 9)
check("add_kpi_item returns valid id", isinstance(kid, int) and kid > 0, f"got {kid!r}")
st.cache_data.clear()
items = [k for k in get_kpi_items() if k['id'] == kid]
check("kpi item persisted after add", len(items) == 1)
update_kpi_item(kid, "Audit KPI v2", 20.0, 90.0, False, 3)
st.cache_data.clear()
item = [k for k in get_kpi_items() if k['id'] == kid][0]
check("kpi item update persisted",
      item['name'] == "Audit KPI v2" and float(item['weight']) == 20.0
      and float(item['max_score']) == 90.0 and not item['is_active']
      and int(item['sort_order']) == 3)
delete_kpi_item(kid)
st.cache_data.clear()
check("kpi item delete persisted", not [k for k in get_kpi_items() if k['id'] == kid])

# 5. Multiplier rule CRUD
rid = add_multiplier_rule(50.0, 60.0, 0.75, False)
check("add_multiplier_rule returns valid id", isinstance(rid, int) and rid > 0)
st.cache_data.clear()
check("rule persisted", any(r['id'] == rid for r in get_multiplier_rules(active_only=False)))
delete_multiplier_rule(rid)
st.cache_data.clear()
check("rule delete persisted", not any(r['id'] == rid for r in get_multiplier_rules(active_only=False)))

# 6. Settings upsert (ON CONFLICT path)
set_setting("audit_test_key", "v1")
set_setting("audit_test_key", "v2")
st.cache_data.clear()
check("setting upsert works", get_setting("audit_test_key") == "v2")

# 7. Salesperson CRUD (FK columns)
st.cache_data.clear()
br = get_branches(active_only=True)
sid = add_salesperson("Audit Person", br[0]['id'], 1, "a@b.c")
check("add_salesperson returns valid id", isinstance(sid, int) and sid > 0)
delete_salesperson(sid)
st.cache_data.clear()
check("salesperson delete persisted", not any(s['id'] == sid for s in get_salespersons()))

# 8. Auth round trip (login-critical path)
from src.auth import get_user, verify_password
u = get_user("admin")
check("default admin exists", u is not None)
check("admin password verifies", u and verify_password("admin123", u['password_hash']))

# 9. execute_insert PG branch builds correct SQL (static check)
import inspect
src = inspect.getsource(db.execute_insert)
check("execute_insert decides via is_postgres()", "is_postgres()" in src)
check("no silent sqlite fallback remains", "_thread_fallback_to_sqlite" not in open(
    os.path.join(os.path.dirname(__file__), 'src', 'db.py')).read())

print()
if failures:
    print(f"AUDIT FAILED — {len(failures)} failure(s): {failures}")
    sys.exit(1)
print("AUDIT PASSED — all checks green.")
