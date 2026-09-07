"""Database-enforced period locks and append-only commission snapshots."""
from contextlib import contextmanager
import json

from src.db import get_conn, is_postgres, fetchone, fetchall, execute

INPUT_TABLES = ('sales_records', 'kpi_records', 'kpi_adjustments')
SOURCE_TABLES = ('settings', 'branches', 'categories', 'target_tiers',
                 'tier_category_targets', 'salespersons', 'commission_brackets',
                 'commission_calc_settings', 'kpi_items', 'kpi_multiplier_rules')


@contextmanager
def atomic():
    """Never replay part of a transaction after a connection failure."""
    from src.db import _local
    if getattr(_local, 'in_transaction', False):
        yield
        return
    conn = get_conn()
    _local.in_transaction = True
    try:
        conn.cursor().execute('BEGIN' if is_postgres() else 'BEGIN IMMEDIATE')
        yield
        conn.cursor().execute('COMMIT')
    except BaseException:
        try:
            conn.cursor().execute('ROLLBACK')
        except Exception:
            pass
        raise
    finally:
        _local.in_transaction = False


def install_protections():
    execute('''CREATE TABLE IF NOT EXISTS commission_snapshots (
        period_id INTEGER NOT NULL REFERENCES periods(id),
        revision INTEGER NOT NULL,
        payload TEXT NOT NULL,
        created_by TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(period_id, revision)
    )''')
    if is_postgres():
        # Snapshots contain internal financial data, never public API data.
        execute('ALTER TABLE commission_snapshots ENABLE ROW LEVEL SECURITY')
        execute('''CREATE OR REPLACE FUNCTION protect_commission_inputs()
        RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE pid INTEGER; locked INTEGER;
        BEGIN
          IF TG_OP <> 'INSERT' THEN
            SELECT is_locked INTO locked FROM periods WHERE id=OLD.period_id FOR UPDATE;
            IF locked=1 THEN RAISE EXCEPTION 'This quarter is locked.'; END IF;
          END IF;
          IF TG_OP <> 'DELETE' THEN
            SELECT is_locked INTO locked FROM periods WHERE id=NEW.period_id FOR UPDATE;
            IF locked=1 THEN RAISE EXCEPTION 'This quarter is locked.'; END IF;
            RETURN NEW;
          END IF;
          RETURN OLD;
        END $$''')
        for table in INPUT_TABLES:
            execute(f'DROP TRIGGER IF EXISTS protect_period ON {table}')
            execute(f'''CREATE TRIGGER protect_period BEFORE INSERT OR UPDATE OR DELETE
                        ON {table} FOR EACH ROW EXECUTE FUNCTION protect_commission_inputs()''')
        execute('''CREATE OR REPLACE FUNCTION protect_commission_snapshot()
        RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
          RAISE EXCEPTION 'Approved snapshots are immutable.';
        END $$''')
        execute('DROP TRIGGER IF EXISTS immutable_snapshot ON commission_snapshots')
        execute('''CREATE TRIGGER immutable_snapshot BEFORE UPDATE OR DELETE ON commission_snapshots
                   FOR EACH ROW EXECUTE FUNCTION protect_commission_snapshot()''')
    else:
        for table in INPUT_TABLES:
            for action in ('INSERT', 'UPDATE', 'DELETE'):
                refs = ['NEW'] if action == 'INSERT' else ['OLD'] if action == 'DELETE' else ['OLD', 'NEW']
                condition = ' OR '.join(f'(SELECT is_locked FROM periods WHERE id={r}.period_id)=1' for r in refs)
                execute(f'''CREATE TRIGGER IF NOT EXISTS protect_{table}_{action}
                    BEFORE {action} ON {table} WHEN {condition}
                    BEGIN SELECT RAISE(ABORT, 'This quarter is locked.'); END''')
        for action in ('UPDATE', 'DELETE'):
            execute(f'''CREATE TRIGGER IF NOT EXISTS immutable_snapshot_{action}
                BEFORE {action} ON commission_snapshots
                BEGIN SELECT RAISE(ABORT, 'Approved snapshots are immutable.'); END''')


def frozen_payload(period_id):
    period = fetchone('SELECT is_locked FROM periods WHERE id=%s', (period_id,))
    if not period or not period['is_locked']:
        return None
    row = fetchone('SELECT payload FROM commission_snapshots WHERE period_id=%s ORDER BY revision DESC LIMIT 1', (period_id,))
    if row:
        return json.loads(row['payload'])
    # Never manufacture an approval for a legacy locked quarter.
    raise ValueError('This locked quarter has no verified snapshot. An administrator must reconcile it against the approved report before reopening and approving it again.')


def approve_period(period_id, username):
    import streamlit as st
    from src.calculations import _compute_commissions
    from src.models import get_sales
    with atomic():
        if is_postgres():
            # Freeze reference data and inputs before capturing a consistent result.
            # Table locks precede the period-row lock to avoid lock-order deadlocks.
            execute('LOCK TABLE ' + ', '.join(SOURCE_TABLES + INPUT_TABLES) + ' IN SHARE MODE')
        suffix = ' FOR UPDATE' if is_postgres() else ''
        period = fetchone('SELECT * FROM periods WHERE id=%s' + suffix, (period_id,))
        if not period:
            raise ValueError('Period not found.')
        if period['is_locked']:
            raise ValueError('Quarter already locked. Reconcile legacy periods before reopening.')
        st.cache_data.clear()
        results = _compute_commissions(period_id)
        payload = {'version': 1, 'period': period, 'commissions': results,
                   'sales': get_sales(period_id),
                   'reference': {table: fetchall(f'SELECT * FROM {table}') for table in SOURCE_TABLES}}
        revision = fetchone('SELECT COALESCE(MAX(revision),0)+1 AS n FROM commission_snapshots WHERE period_id=%s', (period_id,))['n']
        execute('INSERT INTO commission_snapshots(period_id,revision,payload,created_by) VALUES (%s,%s,%s,%s)',
                (period_id, revision, json.dumps(payload, default=str, allow_nan=False), username))
        execute('UPDATE periods SET is_locked=1, locked_at=CURRENT_TIMESTAMP WHERE id=%s', (period_id,))
        from src.models import log_action
        log_action('QUARTER_APPROVED', 'period', period_id, new_val=str(revision), username=username)
    st.cache_data.clear()


def reopen_period(period_id, username, reason):
    if not reason or not reason.strip():
        raise ValueError('A reason is required to reopen a quarter.')
    with atomic():
        execute('UPDATE periods SET is_locked=0, locked_at=NULL WHERE id=%s', (period_id,))
        from src.models import log_action
        log_action('QUARTER_REOPENED', 'period', period_id, notes=reason.strip(), username=username)
    import streamlit as st
    st.cache_data.clear()


def period_branches(period_id):
    payload = frozen_payload(period_id)
    if payload is not None:
        return payload['reference']['branches']
    from src.models import get_branches
    return get_branches()


def period_write(fn):
    """Check and save within one transaction; roll back an entire bulk save."""
    from functools import wraps
    @wraps(fn)
    def guarded(period_id, *args, **kwargs):
        with atomic():
            suffix = ' FOR UPDATE' if is_postgres() else ''
            # Take input table locks first, matching approval's lock ordering.
            if is_postgres():
                execute('LOCK TABLE ' + ', '.join(INPUT_TABLES) + ' IN ROW EXCLUSIVE MODE')
            row = fetchone('SELECT is_locked FROM periods WHERE id=%s' + suffix, (period_id,))
            if not row or row['is_locked']:
                raise ValueError('This quarter is locked or no longer exists.')
            result = fn(period_id, *args, **kwargs)
        import streamlit as st
        st.cache_data.clear()
        return result
    return guarded
