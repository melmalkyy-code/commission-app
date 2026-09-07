"""Regression tests. Uses an in-memory SQLite database; never reads secrets."""
import sqlite3
import unittest
import streamlit as st
import src.db as db

db._detected = True
db._DB_URL = None

from src.schema import create_schema
from src.seed import seed
from src.models import (get_or_create_period, save_sale, save_sales_bulk,
                        save_kpi_score, save_kpi_scores_bulk, save_kpi_adjustment)
from src.period_safety import approve_period, reopen_period, frozen_payload, atomic
from src.calculations import calc_all_commissions


class PeriodSafetyTests(unittest.TestCase):
    def setUp(self):
        st.cache_data.clear()
        db._local.conn = sqlite3.connect(':memory:', isolation_level=None)
        db._local.conn.row_factory = sqlite3.Row
        db._local.conn.execute('PRAGMA foreign_keys=ON')
        create_schema()
        seed()
        self.pid = get_or_create_period(2026, 2)['id']

    def tearDown(self):
        db._local.conn.close()
        db._local.conn = None
        st.cache_data.clear()

    def test_all_entry_paths_reject_locked_quarter(self):
        approve_period(self.pid, 'reviewer')
        writers = [lambda: save_sale(self.pid, 1, 1, 1),
                   lambda: save_sales_bulk(self.pid, [(1, 1, 1)]),
                   lambda: save_kpi_score(self.pid, 1, 1, 1),
                   lambda: save_kpi_scores_bulk(self.pid, [(1, 1, 1)]),
                   lambda: save_kpi_adjustment(self.pid, 1, 5, 0)]
        for writer in writers:
            with self.subTest(writer=writer), self.assertRaisesRegex(Exception, 'locked'):
                writer()

    def test_direct_update_delete_and_move_are_blocked(self):
        approve_period(self.pid, 'reviewer')
        other = get_or_create_period(2026, 3)['id']
        for table in ('sales_records', 'kpi_records'):
            for sql in (f'DELETE FROM {table} WHERE period_id=%s',
                        f'UPDATE {table} SET period_id={other} WHERE period_id=%s'):
                with self.assertRaisesRegex(Exception, 'locked'):
                    db.execute(sql, (self.pid,))

    def test_history_survives_rules_targets_and_employee_changes(self):
        approve_period(self.pid, 'reviewer')
        original = calc_all_commissions(self.pid)
        db.execute('UPDATE salespersons SET is_active=0, name=name || %s', (' changed',))
        db.execute('UPDATE commission_brackets SET commission_rate=99')
        db.execute('UPDATE tier_category_targets SET target_amount=1')
        db.execute('UPDATE kpi_items SET weight=0')
        st.cache_data.clear()
        self.assertEqual(original, calc_all_commissions(self.pid))
        for sql in ('DELETE FROM commission_snapshots', "UPDATE commission_snapshots SET payload='[]'"):
            with self.assertRaisesRegex(Exception, 'immutable'):
                db.execute(sql)

    def test_reopening_requires_reason_and_preserves_versions(self):
        approve_period(self.pid, 'reviewer')
        first = frozen_payload(self.pid)
        with self.assertRaises(ValueError):
            reopen_period(self.pid, 'reviewer', '')
        reopen_period(self.pid, 'reviewer', 'Correct an input after reconciliation')
        save_sale(self.pid, 1, 1, 123456)
        approve_period(self.pid, 'reviewer')
        self.assertNotEqual(first['commissions'], frozen_payload(self.pid)['commissions'])
        self.assertEqual(2, db.fetchone('SELECT COUNT(*) AS n FROM commission_snapshots')['n'])

    def test_legacy_quarter_is_not_silently_certified(self):
        db.execute('UPDATE periods SET is_locked=1 WHERE id=%s', (self.pid,))
        with self.assertRaisesRegex(ValueError, 'no verified snapshot'):
            frozen_payload(self.pid)
        self.assertEqual(0, db.fetchone('SELECT COUNT(*) AS n FROM commission_snapshots')['n'])

    def test_failed_approval_rolls_back_snapshot_and_lock(self):
        from unittest.mock import patch
        with patch('src.models.log_action', side_effect=RuntimeError('audit failed')):
            with self.assertRaisesRegex(RuntimeError, 'audit failed'):
                approve_period(self.pid, 'reviewer')
        self.assertEqual(0, db.fetchone('SELECT COUNT(*) AS n FROM commission_snapshots')['n'])
        self.assertEqual(0, db.fetchone('SELECT is_locked FROM periods WHERE id=%s', (self.pid,))['is_locked'])

    def test_bulk_save_is_atomic_when_a_row_is_invalid(self):
        before = db.fetchone('SELECT actual_sales FROM sales_records WHERE period_id=%s AND salesperson_id=1 AND category_id=1', (self.pid,))
        with self.assertRaises(Exception):
            save_sales_bulk(self.pid, [(1, 1, 99), (999999, 1, 10)])
        after = db.fetchone('SELECT actual_sales FROM sales_records WHERE period_id=%s AND salesperson_id=1 AND category_id=1', (self.pid,))
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
