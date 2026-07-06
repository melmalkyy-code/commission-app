from __future__ import annotations
"""All data models for the web app."""
from typing import Optional
import streamlit as st
from src.db import execute, fetchall, fetchone, execute_insert


# â”€â”€ Settings â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@st.cache_data(ttl=300)
def get_setting(key: str, default: str = "") -> str:
    row = fetchone("SELECT value FROM settings WHERE key=%s", (key,))
    return row['value'] if row else default


def set_setting(key: str, value: str):
    execute("INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value=%s, updated_at=CURRENT_TIMESTAMP", (key, value, value))


@st.cache_data(ttl=300)
def get_all_settings() -> dict:
    return {r['key']: r['value'] for r in fetchall("SELECT key, value FROM settings")}


# â”€â”€ Branches â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@st.cache_data(ttl=300)
def get_branches(active_only=False) -> list[dict]:
    sql = "SELECT id, name, region, is_active FROM branches"
    if active_only:
        sql += " WHERE is_active=1"
    return fetchall(sql + " ORDER BY name")


def add_branch(name: str, region: str) -> int:
    return execute_insert(
        "INSERT INTO branches (name, region) VALUES (%s, %s)", (name, region)
    )


def update_branch(bid: int, name: str, region: str, is_active: bool):
    execute("UPDATE branches SET name=%s, region=%s, is_active=%s WHERE id=%s", (name, region, int(is_active), bid))


def delete_branch(bid: int):
    execute("DELETE FROM branches WHERE id=%s", (bid,))


# â”€â”€ Categories â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@st.cache_data(ttl=300)
def get_categories(active_only=False) -> list[dict]:
    sql = "SELECT id, name, display_order, include_in_target, include_in_commission, include_in_kpi, is_active FROM categories"
    if active_only:
        sql += " WHERE is_active=1"
    return fetchall(sql + " ORDER BY display_order, name")


def add_category(name: str, order: int = 0) -> int:
    return execute_insert(
        "INSERT INTO categories (name, display_order) VALUES (%s, %s)", (name, order)
    )


def update_category(cid: int, name: str, order: int, in_target: bool, in_comm: bool, in_kpi: bool, is_active: bool):
    execute("UPDATE categories SET name=%s, display_order=%s, include_in_target=%s, include_in_commission=%s, include_in_kpi=%s, is_active=%s WHERE id=%s",
            (name, order, int(in_target), int(in_comm), int(in_kpi), int(is_active), cid))


def delete_category(cid: int):
    execute("DELETE FROM categories WHERE id=%s", (cid,))


# â”€â”€ Target Tiers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@st.cache_data(ttl=300)
def get_tiers(active_only=False) -> list[dict]:
    sql = "SELECT id, name, description, is_active FROM target_tiers"
    if active_only:
        sql += " WHERE is_active=1"
    tiers = fetchall(sql + " ORDER BY name")
    for t in tiers:
        rows = fetchall("SELECT category_id, target_amount FROM tier_category_targets WHERE tier_id=%s", (t['id'],))
        t['targets'] = {r['category_id']: r['target_amount'] for r in rows}
    return tiers


def add_tier(name: str, desc: str = "") -> int:
    return execute_insert(
        "INSERT INTO target_tiers (name, description) VALUES (%s, %s)", (name, desc)
    )


def update_tier(tid: int, name: str, desc: str, is_active: bool):
    execute("UPDATE target_tiers SET name=%s, description=%s, is_active=%s WHERE id=%s", (name, desc, int(is_active), tid))


def set_tier_target(tid: int, cat_id: int, amount: float):
    execute("INSERT INTO tier_category_targets (tier_id, category_id, target_amount) VALUES (%s,%s,%s) ON CONFLICT (tier_id, category_id) DO UPDATE SET target_amount=%s", (tid, cat_id, amount, amount))


def delete_tier(tid: int):
    execute("DELETE FROM target_tiers WHERE id=%s", (tid,))


@st.cache_data(ttl=300)
def get_tier_target(tier_id: int, cat_id: int) -> float:
    row = fetchone("SELECT target_amount FROM tier_category_targets WHERE tier_id=%s AND category_id=%s", (tier_id, cat_id))
    return row['target_amount'] if row else 0.0


# â”€â”€ Salespersons â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@st.cache_data(ttl=300)
def get_salespersons(active_only=False, branch_id=None) -> list[dict]:
    sql = """SELECT s.id, s.name, s.branch_id, b.name as branch_name,
                    s.tier_id, t.name as tier_name, s.email, s.is_active
             FROM salespersons s
             LEFT JOIN branches b ON s.branch_id=b.id
             LEFT JOIN target_tiers t ON s.tier_id=t.id
             WHERE 1=1"""
    params = []
    if active_only:
        sql += " AND s.is_active=1"
    if branch_id:
        sql += " AND s.branch_id=%s"
        params.append(branch_id)
    return fetchall(sql + " ORDER BY s.name", tuple(params))


def add_salesperson(name: str, branch_id: int, tier_id: int, email: str = "") -> int:
    return execute_insert(
        "INSERT INTO salespersons (name, branch_id, tier_id, email) VALUES (%s,%s,%s,%s)",
        (name, branch_id, tier_id, email),
    )


def update_salesperson(sid: int, name: str, branch_id: int, tier_id: int, email: str, is_active: bool):
    execute("UPDATE salespersons SET name=%s, branch_id=%s, tier_id=%s, email=%s, is_active=%s WHERE id=%s", (name, branch_id, tier_id, email, int(is_active), sid))


def delete_salesperson(sid: int):
    execute("DELETE FROM salespersons WHERE id=%s", (sid,))


# â”€â”€ Commission Brackets â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@st.cache_data(ttl=300)
def get_brackets(cat_id: int, active_only=True) -> list[dict]:
    sql = "SELECT id, category_id, from_amount, to_amount, commission_rate, is_unlimited, is_active, sort_order FROM commission_brackets WHERE category_id=%s"
    if active_only:
        sql += " AND is_active=1"
    return fetchall(sql + " ORDER BY sort_order, from_amount", (cat_id,))


def add_bracket(cat_id: int, from_amt: float, to_amt: Optional[float], rate: float, unlimited: bool, sort: int = 0):
    execute("INSERT INTO commission_brackets (category_id, from_amount, to_amount, commission_rate, is_unlimited, sort_order) VALUES (%s,%s,%s,%s,%s,%s)", (cat_id, from_amt, to_amt, rate, int(unlimited), sort))


def update_bracket(bid: int, from_amt: float, to_amt: Optional[float], rate: float, unlimited: bool, is_active: bool, sort: int):
    execute("UPDATE commission_brackets SET from_amount=%s, to_amount=%s, commission_rate=%s, is_unlimited=%s, is_active=%s, sort_order=%s WHERE id=%s", (from_amt, to_amt, rate, int(unlimited), int(is_active), sort, bid))


def delete_bracket(bid: int):
    execute("DELETE FROM commission_brackets WHERE id=%s", (bid,))


@st.cache_data(ttl=300)
def get_calc_method(cat_id: Optional[int] = None) -> str:
    if cat_id:
        row = fetchone("SELECT method FROM commission_calc_settings WHERE category_id=%s", (cat_id,))
        if row:
            return row['method']
    return get_setting('global_calc_method', 'flat')


# â”€â”€ KPI â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@st.cache_data(ttl=300)
def get_kpi_items(active_only=False) -> list[dict]:
    sql = """SELECT k.id, k.name, k.weight, k.max_score, k.is_active, k.sort_order,
                    k.linked_category_id, c.name as linked_category_name
             FROM kpi_items k
             LEFT JOIN categories c ON k.linked_category_id = c.id"""
    if active_only:
        sql += " WHERE k.is_active=1"
    return fetchall(sql + " ORDER BY k.sort_order")


def add_kpi_item(name: str, weight: float, max_score: float, sort_order: int = 0) -> int:
    return execute_insert(
        "INSERT INTO kpi_items (name, weight, max_score, sort_order) VALUES (%s,%s,%s,%s)",
        (name, weight, max_score, sort_order),
    )


def update_kpi_item(item_id: int, name: str, weight: float, max_score: float,
                    is_active: bool, sort_order: int):
    execute(
        "UPDATE kpi_items SET name=%s, weight=%s, max_score=%s, is_active=%s, sort_order=%s WHERE id=%s",
        (name, weight, max_score, int(is_active), sort_order, item_id),
    )


def delete_kpi_item(item_id: int):
    execute("DELETE FROM kpi_items WHERE id=%s", (item_id,))


def set_kpi_linked_category(item_id: int, cat_id):
    execute("UPDATE kpi_items SET linked_category_id=%s WHERE id=%s", (cat_id, item_id))


def get_category_achievement(period_id: int, sp_id: int, cat_id: int) -> float:
    sp = fetchone("SELECT tier_id FROM salespersons WHERE id=%s", (sp_id,))
    if not sp or not sp['tier_id']:
        return 0.0
    actual_row = fetchone(
        "SELECT actual_sales FROM sales_records WHERE period_id=%s AND salesperson_id=%s AND category_id=%s",
        (period_id, sp_id, cat_id))
    actual = actual_row['actual_sales'] if actual_row else 0.0
    target_row = fetchone(
        "SELECT target_amount FROM tier_category_targets WHERE tier_id=%s AND category_id=%s",
        (sp['tier_id'], cat_id))
    target = target_row['target_amount'] if target_row else 0.0
    return min((actual / target * 100) if target else 0.0, 100.0)


@st.cache_data(ttl=300)
def get_multiplier_rules(active_only=True) -> list[dict]:
    sql = "SELECT id, score_from, score_to, multiplier, is_unlimited, is_active FROM kpi_multiplier_rules"
    if active_only:
        sql += " WHERE is_active=1"
    return fetchall(sql + " ORDER BY score_from")


def add_multiplier_rule(score_from: float, score_to: Optional[float], multiplier: float, unlimited: bool, sort_order: int = 0) -> int:
    return execute_insert(
        "INSERT INTO kpi_multiplier_rules (score_from, score_to, multiplier, is_unlimited, sort_order) VALUES (%s,%s,%s,%s,%s)",
        (score_from, score_to, multiplier, int(unlimited), sort_order),
    )


def delete_multiplier_rule(rule_id: int):
    execute("DELETE FROM kpi_multiplier_rules WHERE id=%s", (rule_id,))


def get_kpi_score(period_id: int, sp_id: int, item_id: int) -> float:
    row = fetchone("SELECT score FROM kpi_records WHERE period_id=%s AND salesperson_id=%s AND kpi_item_id=%s", (period_id, sp_id, item_id))
    return row['score'] if row else 0.0


def save_kpi_score(period_id: int, sp_id: int, item_id: int, score: float):
    execute("INSERT INTO kpi_records (period_id, salesperson_id, kpi_item_id, score) VALUES (%s,%s,%s,%s) ON CONFLICT (period_id, salesperson_id, kpi_item_id) DO UPDATE SET score=%s, updated_at=CURRENT_TIMESTAMP", (period_id, sp_id, item_id, score, score))


def save_kpi_scores_bulk(period_id: int, items):
    """Upsert many KPI scores in one round-trip. items: iterable of
    (salesperson_id, kpi_item_id, score). Only pass the cells that changed."""
    from src.db import execute_many
    rows = [(period_id, sp_id, item_id, score) for (sp_id, item_id, score) in items]
    execute_many(
        "INSERT INTO kpi_records (period_id, salesperson_id, kpi_item_id, score) "
        "VALUES (%s,%s,%s,%s) "
        "ON CONFLICT (period_id, salesperson_id, kpi_item_id) "
        "DO UPDATE SET score=EXCLUDED.score, updated_at=CURRENT_TIMESTAMP",
        rows,
    )


def get_kpi_adjustment(period_id: int, sp_id: int) -> dict:
    row = fetchone("SELECT bonus_points, penalty_points, notes FROM kpi_adjustments WHERE period_id=%s AND salesperson_id=%s", (period_id, sp_id))
    return row if row else {'bonus_points': 0.0, 'penalty_points': 0.0, 'notes': ''}


def save_kpi_adjustment(period_id: int, sp_id: int, bonus: float, penalty: float, notes: str = ""):
    execute("INSERT INTO kpi_adjustments (period_id, salesperson_id, bonus_points, penalty_points, notes) VALUES (%s,%s,%s,%s,%s) ON CONFLICT (period_id, salesperson_id) DO UPDATE SET bonus_points=%s, penalty_points=%s, notes=%s", (period_id, sp_id, bonus, penalty, notes, bonus, penalty, notes))


# â”€â”€ Periods â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def get_periods() -> list[dict]:
    return fetchall("SELECT id, year, quarter, is_locked, is_current, locked_at FROM periods ORDER BY year DESC, quarter DESC")


def get_period(year: int, quarter: int) -> dict | None:
    """Return the period row if it exists, otherwise None (never inserts)."""
    return fetchone(
        "SELECT id, year, quarter, is_locked, is_current FROM periods "
        "WHERE year=%s AND quarter=%s",
        (year, quarter),
    )


def get_or_create_period(year: int, quarter: int) -> dict:
    row = get_period(year, quarter)
    if row:
        return row
    # Portable INSERT — works on SQLite 3.24+ and PostgreSQL 9.5+
    # Avoids RETURNING which is PostgreSQL-only in older SQLite builds
    execute(
        "INSERT INTO periods (year, quarter) VALUES (%s, %s) "
        "ON CONFLICT (year, quarter) DO NOTHING",
        (year, quarter),
    )
    return get_period(year, quarter)


def lock_period(pid: int):
    execute("UPDATE periods SET is_locked=1, locked_at=CURRENT_TIMESTAMP WHERE id=%s", (pid,))


def unlock_period(pid: int):
    execute("UPDATE periods SET is_locked=0, locked_at=NULL WHERE id=%s", (pid,))


# â”€â”€ Sales Records â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def get_sales(period_id: int, sp_id: int = None) -> list[dict]:
    sql = """SELECT sr.salesperson_id, sr.category_id, sr.actual_sales,
                    s.name as sp_name, b.name as branch_name,
                    c.name as cat_name, c.include_in_commission,
                    s.tier_id, t.name as tier_name
             FROM sales_records sr
             JOIN salespersons s ON sr.salesperson_id=s.id
             JOIN categories c ON sr.category_id=c.id
             LEFT JOIN branches b ON s.branch_id=b.id
             LEFT JOIN target_tiers t ON s.tier_id=t.id
             WHERE sr.period_id=%s"""
    params = [period_id]
    if sp_id:
        sql += " AND sr.salesperson_id=%s"
        params.append(sp_id)
    return fetchall(sql, tuple(params))


def save_sale(period_id: int, sp_id: int, cat_id: int, amount: float):
    execute("INSERT INTO sales_records (period_id, salesperson_id, category_id, actual_sales) VALUES (%s,%s,%s,%s) ON CONFLICT (period_id, salesperson_id, category_id) DO UPDATE SET actual_sales=%s, updated_at=CURRENT_TIMESTAMP", (period_id, sp_id, cat_id, amount, amount))


def save_sales_bulk(period_id: int, items):
    """Upsert many sales cells in one round-trip. items: iterable of
    (salesperson_id, category_id, amount). Only pass the cells that changed."""
    from src.db import execute_many
    rows = [(period_id, sp_id, cat_id, amount) for (sp_id, cat_id, amount) in items]
    execute_many(
        "INSERT INTO sales_records (period_id, salesperson_id, category_id, actual_sales) "
        "VALUES (%s,%s,%s,%s) "
        "ON CONFLICT (period_id, salesperson_id, category_id) "
        "DO UPDATE SET actual_sales=EXCLUDED.actual_sales, updated_at=CURRENT_TIMESTAMP",
        rows,
    )


# â”€â”€ Audit Log â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def log_action(action_type: str, entity_type: str = "", entity_id: int = None, entity_name: str = "", old_val: str = "", new_val: str = "", notes: str = "", username: str = "user"):
    execute("INSERT INTO audit_logs (action_type, entity_type, entity_id, entity_name, old_value, new_value, notes, username) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", (action_type, entity_type, entity_id, entity_name, old_val, new_val, notes, username))


def get_audit_logs(action_type=None, entity_type=None, limit=500) -> list[dict]:
    sql = "SELECT id, timestamp, action_type, entity_type, entity_id, entity_name, old_value, new_value, notes, username FROM audit_logs WHERE 1=1"
    params = []
    if action_type:
        sql += " AND action_type=%s"; params.append(action_type)
    if entity_type:
        sql += " AND entity_type=%s"; params.append(entity_type)
    return fetchall(sql + f" ORDER BY timestamp DESC LIMIT {limit}", tuple(params))

