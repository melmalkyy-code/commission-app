from __future__ import annotations
from src.db import execute, fetchone, fetchall, is_postgres


def seed():
    _seed_settings()
    _seed_categories()
    _seed_tiers()
    _seed_branches()
    _seed_kpi()
    _seed_brackets()
    _seed_salespersons()
    _seed_period()
    _seed_sample_data()
    from src.auth import ensure_default_admin
    ensure_default_admin()


def _ins_ignore(table, cols, vals, conflict_col=None):
    """Insert ignoring conflicts — works on both PostgreSQL and SQLite."""
    placeholders = ', '.join(['%s'] * len(vals))
    col_str = ', '.join(cols)
    if is_postgres():
        if conflict_col:
            sql = f"INSERT INTO {table} ({col_str}) VALUES ({placeholders}) ON CONFLICT ({conflict_col}) DO NOTHING"
        else:
            sql = f"INSERT INTO {table} ({col_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
    else:
        sql = f"INSERT OR IGNORE INTO {table} ({col_str}) VALUES ({placeholders})"
    execute(sql, tuple(vals))


def _seed_settings():
    defaults = {
        'company_name':       'Surveying Experts',
        'primary_color':      '#354f61',
        'accent_color':       '#f6ba3b',
        'bg_color':           '#ffffff',
        'report_header':      'Surveying Experts - Quarterly Sales Commission Report',
        'report_footer':      'Confidential - For Internal Use Only',
        'company_website':    'www.surveyingexperts.com',
        'company_phone':      '',
        'global_calc_method': 'flat',
    }
    for k, v in defaults.items():
        _ins_ignore('settings', ['key', 'value'], [k, v], 'key')


def _seed_categories():
    cats = [('GPS / GNSS', 0), ('Total Station', 1), ('Accessories', 2), ('Rentals', 3), ('High Solutions', 4)]
    for name, order in cats:
        _ins_ignore('categories', ['name', 'display_order'], [name, order], 'name')


def _seed_tiers():
    for name, desc in [('Tier 1', 'Entry level'), ('Tier 2', 'Mid level'), ('Tier 3', 'Senior level')]:
        _ins_ignore('target_tiers', ['name', 'description'], [name, desc], 'name')

    tier_targets = {
        'Tier 1': {'GPS / GNSS': 500000, 'Total Station': 300000, 'Accessories': 100000, 'Rentals': 80000,  'High Solutions': 150000},
        'Tier 2': {'GPS / GNSS': 800000, 'Total Station': 500000, 'Accessories': 150000, 'Rentals': 120000, 'High Solutions': 250000},
        'Tier 3': {'GPS / GNSS': 1200000,'Total Station': 800000, 'Accessories': 200000, 'Rentals': 180000, 'High Solutions': 400000},
    }
    for tier_name, targets in tier_targets.items():
        tier = fetchone("SELECT id FROM target_tiers WHERE name=%s", (tier_name,))
        if not tier:
            continue
        for cat_name, amount in targets.items():
            cat = fetchone("SELECT id FROM categories WHERE name=%s", (cat_name,))
            if cat:
                _ins_ignore('tier_category_targets',
                            ['tier_id', 'category_id', 'target_amount'],
                            [tier['id'], cat['id'], amount],
                            'tier_id, category_id')


def _seed_branches():
    for name, region in [('Riyadh', 'Central Region'), ('Jeddah', 'Western Region'), ('Dammam', 'Eastern Region')]:
        _ins_ignore('branches', ['name', 'region'], [name, region], 'name')


def _seed_kpi():
    items = [
        ('Exam Score',                      20.0, 100, 0),
        ('Branch Manager Evaluation',       25.0, 100, 1),
        ('Overall Target Achievement',      30.0, 100, 2),
        ('New Product Target Achievement',  15.0, 100, 3),
        ('Rental Collection Achievement',   10.0, 100, 4),
    ]
    for name, weight, max_score, sort_order in items:
        existing = fetchone("SELECT id FROM kpi_items WHERE name=%s", (name,))
        if not existing:
            execute("INSERT INTO kpi_items (name, weight, max_score, sort_order) VALUES (%s, %s, %s, %s)",
                    (name, weight, max_score, sort_order))

    rules = [(0, 69, 0.7, 0), (70, 79, 0.8, 1), (80, 89, 0.9, 2), (90, 99, 1.0, 3), (100, None, 1.2, 4)]
    count = fetchone("SELECT COUNT(*) as c FROM kpi_multiplier_rules", ())
    if count and count['c'] == 0:
        for frm, to, mult, sort in rules:
            unlimited = 1 if to is None else 0
            execute("INSERT INTO kpi_multiplier_rules (score_from, score_to, multiplier, is_unlimited, sort_order) VALUES (%s, %s, %s, %s, %s)",
                    (frm, to, mult, unlimited, sort))


def _seed_brackets():
    bracket_data = {
        'GPS / GNSS':    [(0, 250000, 0.0), (250000, 500000, 1.0), (500000, 1000000, 2.0), (1000000, None, 3.0)],
        'Total Station': [(0, 150000, 0.0), (150000, 300000, 1.0), (300000, 600000,  2.0), (600000,  None, 3.0)],
        'Accessories':   [(0, 50000,  0.0), (50000,  100000, 1.5), (100000, 200000,  2.5), (200000,  None, 3.5)],
        'Rentals':       [(0, 40000,  0.0), (40000,  80000,  2.0), (80000,  150000,  3.0), (150000,  None, 4.0)],
        'High Solutions':[(0, 75000,  0.0), (75000,  150000, 1.5), (150000, 300000,  2.5), (300000,  None, 3.5)],
    }
    for cat_name, brackets in bracket_data.items():
        cat = fetchone("SELECT id FROM categories WHERE name=%s", (cat_name,))
        if not cat:
            continue
        count = fetchone("SELECT COUNT(*) as c FROM commission_brackets WHERE category_id=%s", (cat['id'],))
        if count and count['c'] > 0:
            continue
        for i, (frm, to, rate) in enumerate(brackets):
            try:
                execute(
                    "INSERT INTO commission_brackets "
                    "(category_id, from_amount, to_amount, commission_rate, is_unlimited, sort_order) "
                    "VALUES (%s,%s,%s,%s,%s,%s)",
                    (cat['id'], frm, to, rate, 1 if to is None else 0, i)
                )
            except Exception:
                pass  # skip if already exists or FK not yet satisfied


def _seed_salespersons():
    salespeople = [
        ('Ahmed Al-Rashid',   'Riyadh', 'Tier 1'),
        ('Mohamed Al-Ghamdi', 'Riyadh', 'Tier 2'),
        ('Ali Al-Zahrani',    'Jeddah', 'Tier 2'),
        ('Hassan Al-Qahtani', 'Dammam', 'Tier 3'),
        ('Khalid Al-Otaibi',  'Jeddah', 'Tier 1'),
        ('Omar Al-Shehri',    'Dammam', 'Tier 2'),
    ]
    for name, br_name, tier_name in salespeople:
        br   = fetchone("SELECT id FROM branches WHERE name=%s", (br_name,))
        tier = fetchone("SELECT id FROM target_tiers WHERE name=%s", (tier_name,))
        if br and tier:
            _ins_ignore('salespersons', ['name', 'branch_id', 'tier_id'],
                        [name, br['id'], tier['id']], 'name')


def _seed_period():
    _ins_ignore('periods', ['year', 'quarter', 'is_current'], [2026, 2, 1], 'year, quarter')


def _seed_sample_data():
    period = fetchone("SELECT id FROM periods WHERE year=2026 AND quarter=2", ())
    if not period:
        return

    sample_sales = {
        'Ahmed Al-Rashid':   {'GPS / GNSS': 320000, 'Total Station': 180000, 'Accessories': 65000,  'Rentals': 55000,  'High Solutions': 90000},
        'Mohamed Al-Ghamdi': {'GPS / GNSS': 750000, 'Total Station': 420000, 'Accessories': 110000, 'Rentals': 95000,  'High Solutions': 200000},
        'Ali Al-Zahrani':    {'GPS / GNSS': 680000, 'Total Station': 390000, 'Accessories': 130000, 'Rentals': 85000,  'High Solutions': 175000},
        'Hassan Al-Qahtani': {'GPS / GNSS': 1100000,'Total Station': 720000, 'Accessories': 170000, 'Rentals': 160000, 'High Solutions': 350000},
        'Khalid Al-Otaibi':  {'GPS / GNSS': 280000, 'Total Station': 150000, 'Accessories': 45000,  'Rentals': 40000,  'High Solutions': 70000},
        'Omar Al-Shehri':    {'GPS / GNSS': 620000, 'Total Station': 350000, 'Accessories': 120000, 'Rentals': 100000, 'High Solutions': 160000},
    }
    for sp_name, cat_sales in sample_sales.items():
        sp = fetchone("SELECT id FROM salespersons WHERE name=%s", (sp_name,))
        if not sp:
            continue
        for cat_name, amount in cat_sales.items():
            cat = fetchone("SELECT id FROM categories WHERE name=%s", (cat_name,))
            if cat:
                _ins_ignore('sales_records',
                            ['period_id', 'salesperson_id', 'category_id', 'actual_sales'],
                            [period['id'], sp['id'], cat['id'], amount],
                            'period_id, salesperson_id, category_id')

    sample_kpi = {
        'Ahmed Al-Rashid':   {'Exam Score': 78, 'Branch Manager Evaluation': 82, 'Overall Target Achievement': 70, 'New Product Target Achievement': 65, 'Rental Collection Achievement': 80},
        'Mohamed Al-Ghamdi': {'Exam Score': 90, 'Branch Manager Evaluation': 88, 'Overall Target Achievement': 92, 'New Product Target Achievement': 85, 'Rental Collection Achievement': 90},
        'Ali Al-Zahrani':    {'Exam Score': 85, 'Branch Manager Evaluation': 80, 'Overall Target Achievement': 88, 'New Product Target Achievement': 75, 'Rental Collection Achievement': 85},
        'Hassan Al-Qahtani': {'Exam Score': 95, 'Branch Manager Evaluation': 92, 'Overall Target Achievement': 95, 'New Product Target Achievement': 90, 'Rental Collection Achievement': 95},
        'Khalid Al-Otaibi':  {'Exam Score': 72, 'Branch Manager Evaluation': 70, 'Overall Target Achievement': 62, 'New Product Target Achievement': 60, 'Rental Collection Achievement': 65},
        'Omar Al-Shehri':    {'Exam Score': 88, 'Branch Manager Evaluation': 85, 'Overall Target Achievement': 85, 'New Product Target Achievement': 80, 'Rental Collection Achievement': 88},
    }
    for sp_name, scores in sample_kpi.items():
        sp = fetchone("SELECT id FROM salespersons WHERE name=%s", (sp_name,))
        if not sp:
            continue
        for item_name, score in scores.items():
            item = fetchone("SELECT id FROM kpi_items WHERE name=%s", (item_name,))
            if item:
                _ins_ignore('kpi_records',
                            ['period_id', 'salesperson_id', 'kpi_item_id', 'score'],
                            [period['id'], sp['id'], item['id'], score],
                            'period_id, salesperson_id, kpi_item_id')
