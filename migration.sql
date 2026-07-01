-- ============================================================
-- Surveying Experts Commission App — Full Migration
-- Run this in the new Supabase SQL Editor (us-east-1)
-- ============================================================

-- ── SCHEMA ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS settings (
    key        TEXT PRIMARY KEY,
    value      TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS branches (
    id         SERIAL PRIMARY KEY,
    name       TEXT NOT NULL UNIQUE,
    city       TEXT,
    is_active  INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS categories (
    id                    SERIAL PRIMARY KEY,
    name                  TEXT NOT NULL UNIQUE,
    display_order         INTEGER DEFAULT 0,
    include_in_target     INTEGER DEFAULT 1,
    include_in_commission INTEGER DEFAULT 1,
    include_in_kpi        INTEGER DEFAULT 1,
    is_active             INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS target_tiers (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    description TEXT,
    is_active   INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS tier_category_targets (
    id            SERIAL PRIMARY KEY,
    tier_id       INTEGER NOT NULL REFERENCES target_tiers(id) ON DELETE CASCADE,
    category_id   INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    target_amount REAL DEFAULT 0,
    UNIQUE(tier_id, category_id)
);

CREATE TABLE IF NOT EXISTS salespersons (
    id         SERIAL PRIMARY KEY,
    name       TEXT NOT NULL UNIQUE,
    branch_id  INTEGER REFERENCES branches(id),
    tier_id    INTEGER REFERENCES target_tiers(id),
    email      TEXT,
    is_active  INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS commission_brackets (
    id              SERIAL PRIMARY KEY,
    category_id     INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    from_amount     REAL NOT NULL DEFAULT 0,
    to_amount       REAL,
    commission_rate REAL NOT NULL DEFAULT 0,
    is_unlimited    INTEGER DEFAULT 0,
    is_active       INTEGER DEFAULT 1,
    sort_order      INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS commission_calc_settings (
    id          SERIAL PRIMARY KEY,
    category_id INTEGER UNIQUE REFERENCES categories(id) ON DELETE CASCADE,
    method      TEXT NOT NULL DEFAULT 'flat'
);

CREATE TABLE IF NOT EXISTS kpi_items (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    weight      REAL DEFAULT 0,
    max_score   REAL DEFAULT 100,
    is_active   INTEGER DEFAULT 1,
    sort_order  INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS kpi_multiplier_rules (
    id           SERIAL PRIMARY KEY,
    score_from   REAL NOT NULL,
    score_to     REAL,
    multiplier   REAL NOT NULL,
    is_unlimited INTEGER DEFAULT 0,
    is_active    INTEGER DEFAULT 1,
    sort_order   INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS periods (
    id         SERIAL PRIMARY KEY,
    year       INTEGER NOT NULL,
    quarter    INTEGER NOT NULL,
    is_locked  INTEGER DEFAULT 0,
    is_current INTEGER DEFAULT 0,
    locked_at  TIMESTAMP,
    UNIQUE(year, quarter)
);

CREATE TABLE IF NOT EXISTS sales_records (
    id              SERIAL PRIMARY KEY,
    period_id       INTEGER NOT NULL REFERENCES periods(id) ON DELETE CASCADE,
    salesperson_id  INTEGER NOT NULL REFERENCES salespersons(id) ON DELETE CASCADE,
    category_id     INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    actual_sales    REAL DEFAULT 0,
    target_override REAL,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(period_id, salesperson_id, category_id)
);

CREATE TABLE IF NOT EXISTS kpi_records (
    id             SERIAL PRIMARY KEY,
    period_id      INTEGER NOT NULL REFERENCES periods(id) ON DELETE CASCADE,
    salesperson_id INTEGER NOT NULL REFERENCES salespersons(id) ON DELETE CASCADE,
    kpi_item_id    INTEGER NOT NULL REFERENCES kpi_items(id) ON DELETE CASCADE,
    score          REAL DEFAULT 0,
    updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(period_id, salesperson_id, kpi_item_id)
);

CREATE TABLE IF NOT EXISTS kpi_adjustments (
    id             SERIAL PRIMARY KEY,
    period_id      INTEGER NOT NULL REFERENCES periods(id) ON DELETE CASCADE,
    salesperson_id INTEGER NOT NULL REFERENCES salespersons(id) ON DELETE CASCADE,
    bonus_points   REAL DEFAULT 0,
    penalty_points REAL DEFAULT 0,
    notes          TEXT,
    UNIQUE(period_id, salesperson_id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id          SERIAL PRIMARY KEY,
    timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action_type TEXT NOT NULL,
    entity_type TEXT,
    entity_id   INTEGER,
    entity_name TEXT,
    old_value   TEXT,
    new_value   TEXT,
    notes       TEXT,
    username    TEXT DEFAULT 'user'
);

CREATE TABLE IF NOT EXISTS app_users (
    id            SERIAL PRIMARY KEY,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name     TEXT,
    role          TEXT DEFAULT 'viewer',
    is_active     INTEGER DEFAULT 1,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ── SEED DATA ─────────────────────────────────────────────────

-- Settings
INSERT INTO settings (key, value) VALUES
  ('company_name',       'Surveying Experts'),
  ('primary_color',      '#354f61'),
  ('accent_color',       '#f6ba3b'),
  ('bg_color',           '#ffffff'),
  ('report_header',      'Surveying Experts — Quarterly Sales Commission Report'),
  ('report_footer',      'Confidential — For Internal Use Only'),
  ('company_website',    'www.surveyingexperts.com'),
  ('company_phone',      ''),
  ('global_calc_method', 'flat')
ON CONFLICT (key) DO NOTHING;

-- Categories
INSERT INTO categories (name, display_order) VALUES
  ('GPS / GNSS',    0),
  ('Total Station', 1),
  ('Accessories',   2),
  ('Rentals',       3),
  ('High Solutions',4)
ON CONFLICT (name) DO NOTHING;

-- Target Tiers
INSERT INTO target_tiers (name, description) VALUES
  ('Tier 1', 'Entry level'),
  ('Tier 2', 'Mid level'),
  ('Tier 3', 'Senior level')
ON CONFLICT (name) DO NOTHING;

-- Tier targets (using subqueries to avoid hardcoded IDs)
INSERT INTO tier_category_targets (tier_id, category_id, target_amount)
SELECT t.id, c.id, v.amount FROM (VALUES
  ('Tier 1','GPS / GNSS',500000), ('Tier 1','Total Station',300000),
  ('Tier 1','Accessories',100000),('Tier 1','Rentals',80000),
  ('Tier 1','High Solutions',150000),
  ('Tier 2','GPS / GNSS',800000), ('Tier 2','Total Station',500000),
  ('Tier 2','Accessories',150000),('Tier 2','Rentals',120000),
  ('Tier 2','High Solutions',250000),
  ('Tier 3','GPS / GNSS',1200000),('Tier 3','Total Station',800000),
  ('Tier 3','Accessories',200000),('Tier 3','Rentals',180000),
  ('Tier 3','High Solutions',400000)
) AS v(tier_name, cat_name, amount)
JOIN target_tiers t ON t.name = v.tier_name
JOIN categories   c ON c.name = v.cat_name
ON CONFLICT (tier_id, category_id) DO NOTHING;

-- Branches
INSERT INTO branches (name, city) VALUES
  ('Riyadh', 'Riyadh'),
  ('Jeddah', 'Jeddah'),
  ('Dammam', 'Dammam')
ON CONFLICT (name) DO NOTHING;

-- KPI Items
INSERT INTO kpi_items (name, weight, max_score, sort_order) VALUES
  ('Exam Score',                      20.0, 100, 0),
  ('Branch Manager Evaluation',       25.0, 100, 1),
  ('Overall Target Achievement',      30.0, 100, 2),
  ('New Product Target Achievement',  15.0, 100, 3),
  ('Rental Collection Achievement',   10.0, 100, 4);

-- KPI Multiplier Rules
INSERT INTO kpi_multiplier_rules (score_from, score_to, multiplier, is_unlimited, sort_order) VALUES
  (0,   69,   0.7, 0, 0),
  (70,  79,   0.8, 0, 1),
  (80,  89,   0.9, 0, 2),
  (90,  99,   1.0, 0, 3),
  (100, NULL, 1.2, 1, 4);

-- Commission Brackets (using subqueries)
INSERT INTO commission_brackets (category_id, from_amount, to_amount, commission_rate, is_unlimited, sort_order)
SELECT c.id, v.frm, v.to_amt, v.rate, v.unlimited, v.sort FROM (VALUES
  ('GPS / GNSS',    0,       250000,  0.0, 0, 0),
  ('GPS / GNSS',    250000,  500000,  1.0, 0, 1),
  ('GPS / GNSS',    500000,  1000000, 2.0, 0, 2),
  ('GPS / GNSS',    1000000, NULL,    3.0, 1, 3),
  ('Total Station', 0,       150000,  0.0, 0, 0),
  ('Total Station', 150000,  300000,  1.0, 0, 1),
  ('Total Station', 300000,  600000,  2.0, 0, 2),
  ('Total Station', 600000,  NULL,    3.0, 1, 3),
  ('Accessories',   0,       50000,   0.0, 0, 0),
  ('Accessories',   50000,   100000,  1.5, 0, 1),
  ('Accessories',   100000,  200000,  2.5, 0, 2),
  ('Accessories',   200000,  NULL,    3.5, 1, 3),
  ('Rentals',       0,       40000,   0.0, 0, 0),
  ('Rentals',       40000,   80000,   2.0, 0, 1),
  ('Rentals',       80000,   150000,  3.0, 0, 2),
  ('Rentals',       150000,  NULL,    4.0, 1, 3),
  ('High Solutions',0,       75000,   0.0, 0, 0),
  ('High Solutions',75000,   150000,  1.5, 0, 1),
  ('High Solutions',150000,  300000,  2.5, 0, 2),
  ('High Solutions',300000,  NULL,    3.5, 1, 3)
) AS v(cat_name, frm, to_amt, rate, unlimited, sort)
JOIN categories c ON c.name = v.cat_name;

-- Salespersons
INSERT INTO salespersons (name, branch_id, tier_id)
SELECT v.name, b.id, t.id FROM (VALUES
  ('Ahmed Al-Rashid',   'Riyadh', 'Tier 1'),
  ('Mohamed Al-Ghamdi', 'Riyadh', 'Tier 2'),
  ('Ali Al-Zahrani',    'Jeddah', 'Tier 2'),
  ('Hassan Al-Qahtani', 'Dammam', 'Tier 3'),
  ('Khalid Al-Otaibi',  'Jeddah', 'Tier 1'),
  ('Omar Al-Shehri',    'Dammam', 'Tier 2')
) AS v(name, branch_name, tier_name)
JOIN branches     b ON b.name = v.branch_name
JOIN target_tiers t ON t.name = v.tier_name
ON CONFLICT (name) DO NOTHING;

-- Period
INSERT INTO periods (year, quarter, is_current) VALUES (2026, 2, 1)
ON CONFLICT (year, quarter) DO NOTHING;

-- Sample sales records
INSERT INTO sales_records (period_id, salesperson_id, category_id, actual_sales)
SELECT p.id, s.id, c.id, v.amount FROM (VALUES
  ('Ahmed Al-Rashid',   'GPS / GNSS',     320000),
  ('Ahmed Al-Rashid',   'Total Station',  180000),
  ('Ahmed Al-Rashid',   'Accessories',     65000),
  ('Ahmed Al-Rashid',   'Rentals',         55000),
  ('Ahmed Al-Rashid',   'High Solutions',  90000),
  ('Mohamed Al-Ghamdi', 'GPS / GNSS',     750000),
  ('Mohamed Al-Ghamdi', 'Total Station',  420000),
  ('Mohamed Al-Ghamdi', 'Accessories',    110000),
  ('Mohamed Al-Ghamdi', 'Rentals',         95000),
  ('Mohamed Al-Ghamdi', 'High Solutions', 200000),
  ('Ali Al-Zahrani',    'GPS / GNSS',     680000),
  ('Ali Al-Zahrani',    'Total Station',  390000),
  ('Ali Al-Zahrani',    'Accessories',    130000),
  ('Ali Al-Zahrani',    'Rentals',         85000),
  ('Ali Al-Zahrani',    'High Solutions', 175000),
  ('Hassan Al-Qahtani', 'GPS / GNSS',    1100000),
  ('Hassan Al-Qahtani', 'Total Station',  720000),
  ('Hassan Al-Qahtani', 'Accessories',    170000),
  ('Hassan Al-Qahtani', 'Rentals',        160000),
  ('Hassan Al-Qahtani', 'High Solutions', 350000),
  ('Khalid Al-Otaibi',  'GPS / GNSS',     280000),
  ('Khalid Al-Otaibi',  'Total Station',  150000),
  ('Khalid Al-Otaibi',  'Accessories',     45000),
  ('Khalid Al-Otaibi',  'Rentals',         40000),
  ('Khalid Al-Otaibi',  'High Solutions',  70000),
  ('Omar Al-Shehri',    'GPS / GNSS',     620000),
  ('Omar Al-Shehri',    'Total Station',  350000),
  ('Omar Al-Shehri',    'Accessories',    120000),
  ('Omar Al-Shehri',    'Rentals',        100000),
  ('Omar Al-Shehri',    'High Solutions', 160000)
) AS v(sp_name, cat_name, amount)
JOIN periods      p ON p.year=2026 AND p.quarter=2
JOIN salespersons s ON s.name = v.sp_name
JOIN categories   c ON c.name = v.cat_name
ON CONFLICT (period_id, salesperson_id, category_id) DO NOTHING;

-- Sample KPI records
INSERT INTO kpi_records (period_id, salesperson_id, kpi_item_id, score)
SELECT p.id, s.id, k.id, v.score FROM (VALUES
  ('Ahmed Al-Rashid',   'Exam Score', 78),
  ('Ahmed Al-Rashid',   'Branch Manager Evaluation', 82),
  ('Ahmed Al-Rashid',   'Overall Target Achievement', 70),
  ('Ahmed Al-Rashid',   'New Product Target Achievement', 65),
  ('Ahmed Al-Rashid',   'Rental Collection Achievement', 80),
  ('Mohamed Al-Ghamdi', 'Exam Score', 90),
  ('Mohamed Al-Ghamdi', 'Branch Manager Evaluation', 88),
  ('Mohamed Al-Ghamdi', 'Overall Target Achievement', 92),
  ('Mohamed Al-Ghamdi', 'New Product Target Achievement', 85),
  ('Mohamed Al-Ghamdi', 'Rental Collection Achievement', 90),
  ('Ali Al-Zahrani',    'Exam Score', 85),
  ('Ali Al-Zahrani',    'Branch Manager Evaluation', 80),
  ('Ali Al-Zahrani',    'Overall Target Achievement', 88),
  ('Ali Al-Zahrani',    'New Product Target Achievement', 75),
  ('Ali Al-Zahrani',    'Rental Collection Achievement', 85),
  ('Hassan Al-Qahtani', 'Exam Score', 95),
  ('Hassan Al-Qahtani', 'Branch Manager Evaluation', 92),
  ('Hassan Al-Qahtani', 'Overall Target Achievement', 95),
  ('Hassan Al-Qahtani', 'New Product Target Achievement', 90),
  ('Hassan Al-Qahtani', 'Rental Collection Achievement', 95),
  ('Khalid Al-Otaibi',  'Exam Score', 72),
  ('Khalid Al-Otaibi',  'Branch Manager Evaluation', 70),
  ('Khalid Al-Otaibi',  'Overall Target Achievement', 62),
  ('Khalid Al-Otaibi',  'New Product Target Achievement', 60),
  ('Khalid Al-Otaibi',  'Rental Collection Achievement', 65),
  ('Omar Al-Shehri',    'Exam Score', 88),
  ('Omar Al-Shehri',    'Branch Manager Evaluation', 85),
  ('Omar Al-Shehri',    'Overall Target Achievement', 85),
  ('Omar Al-Shehri',    'New Product Target Achievement', 80),
  ('Omar Al-Shehri',    'Rental Collection Achievement', 88)
) AS v(sp_name, item_name, score)
JOIN periods      p ON p.year=2026 AND p.quarter=2
JOIN salespersons s ON s.name = v.sp_name
JOIN kpi_items    k ON k.name = v.item_name
ON CONFLICT (period_id, salesperson_id, kpi_item_id) DO NOTHING;

-- Admin user will be auto-created by the app on first boot (admin / admin123)
