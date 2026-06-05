from src.db import execute, is_postgres


def _serial(col: str) -> str:
    return f"{col} SERIAL PRIMARY KEY" if is_postgres() else f"{col} INTEGER PRIMARY KEY AUTOINCREMENT"


def _upsert_ignore() -> str:
    return "ON CONFLICT DO NOTHING" if is_postgres() else "OR IGNORE"


TABLES = [
    """CREATE TABLE IF NOT EXISTS settings (
        key   TEXT PRIMARY KEY,
        value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS branches (
        id         {serial},
        name       TEXT NOT NULL UNIQUE,
        city       TEXT,
        is_active  INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS categories (
        id                    {serial},
        name                  TEXT NOT NULL UNIQUE,
        display_order         INTEGER DEFAULT 0,
        include_in_target     INTEGER DEFAULT 1,
        include_in_commission INTEGER DEFAULT 1,
        include_in_kpi        INTEGER DEFAULT 1,
        is_active             INTEGER DEFAULT 1
    )""",
    """CREATE TABLE IF NOT EXISTS target_tiers (
        id          {serial},
        name        TEXT NOT NULL UNIQUE,
        description TEXT,
        is_active   INTEGER DEFAULT 1
    )""",
    """CREATE TABLE IF NOT EXISTS tier_category_targets (
        id            {serial},
        tier_id       INTEGER NOT NULL REFERENCES target_tiers(id) ON DELETE CASCADE,
        category_id   INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
        target_amount REAL DEFAULT 0,
        UNIQUE(tier_id, category_id)
    )""",
    """CREATE TABLE IF NOT EXISTS salespersons (
        id         {serial},
        name       TEXT NOT NULL UNIQUE,
        branch_id  INTEGER REFERENCES branches(id),
        tier_id    INTEGER REFERENCES target_tiers(id),
        email      TEXT,
        is_active  INTEGER DEFAULT 1
    )""",
    """CREATE TABLE IF NOT EXISTS commission_brackets (
        id              {serial},
        category_id     INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
        from_amount     REAL NOT NULL DEFAULT 0,
        to_amount       REAL,
        commission_rate REAL NOT NULL DEFAULT 0,
        is_unlimited    INTEGER DEFAULT 0,
        is_active       INTEGER DEFAULT 1,
        sort_order      INTEGER DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS commission_calc_settings (
        id          {serial},
        category_id INTEGER UNIQUE REFERENCES categories(id) ON DELETE CASCADE,
        method      TEXT NOT NULL DEFAULT 'flat'
    )""",
    """CREATE TABLE IF NOT EXISTS kpi_items (
        id          {serial},
        name        TEXT NOT NULL,
        weight      REAL DEFAULT 0,
        max_score   REAL DEFAULT 100,
        is_active   INTEGER DEFAULT 1,
        sort_order  INTEGER DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS kpi_multiplier_rules (
        id           {serial},
        score_from   REAL NOT NULL,
        score_to     REAL,
        multiplier   REAL NOT NULL,
        is_unlimited INTEGER DEFAULT 0,
        is_active    INTEGER DEFAULT 1,
        sort_order   INTEGER DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS periods (
        id         {serial},
        year       INTEGER NOT NULL,
        quarter    INTEGER NOT NULL,
        is_locked  INTEGER DEFAULT 0,
        is_current INTEGER DEFAULT 0,
        locked_at  TIMESTAMP,
        UNIQUE(year, quarter)
    )""",
    """CREATE TABLE IF NOT EXISTS sales_records (
        id              {serial},
        period_id       INTEGER NOT NULL REFERENCES periods(id) ON DELETE CASCADE,
        salesperson_id  INTEGER NOT NULL REFERENCES salespersons(id) ON DELETE CASCADE,
        category_id     INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
        actual_sales    REAL DEFAULT 0,
        target_override REAL,
        updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(period_id, salesperson_id, category_id)
    )""",
    """CREATE TABLE IF NOT EXISTS kpi_records (
        id             {serial},
        period_id      INTEGER NOT NULL REFERENCES periods(id) ON DELETE CASCADE,
        salesperson_id INTEGER NOT NULL REFERENCES salespersons(id) ON DELETE CASCADE,
        kpi_item_id    INTEGER NOT NULL REFERENCES kpi_items(id) ON DELETE CASCADE,
        score          REAL DEFAULT 0,
        updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(period_id, salesperson_id, kpi_item_id)
    )""",
    """CREATE TABLE IF NOT EXISTS kpi_adjustments (
        id             {serial},
        period_id      INTEGER NOT NULL REFERENCES periods(id) ON DELETE CASCADE,
        salesperson_id INTEGER NOT NULL REFERENCES salespersons(id) ON DELETE CASCADE,
        bonus_points   REAL DEFAULT 0,
        penalty_points REAL DEFAULT 0,
        notes          TEXT,
        UNIQUE(period_id, salesperson_id)
    )""",
    """CREATE TABLE IF NOT EXISTS audit_logs (
        id          {serial},
        timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        action_type TEXT NOT NULL,
        entity_type TEXT,
        entity_id   INTEGER,
        entity_name TEXT,
        old_value   TEXT,
        new_value   TEXT,
        notes       TEXT,
        username    TEXT DEFAULT 'user'
    )""",
]


def create_schema():
    serial_def = "id SERIAL PRIMARY KEY" if is_postgres() else "id INTEGER PRIMARY KEY AUTOINCREMENT"
    for tbl in TABLES:
        sql = tbl.replace("{serial}", serial_def)
        execute(sql)
