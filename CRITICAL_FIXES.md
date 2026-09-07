# Critical commission protections — 7 September 2026

Release: critical period protections, 7 September 2026. Supabase service was resumed before this update.

## Changes

- Database triggers reject inserts, updates, moves and deletes affecting locked sales, KPI and adjustment records. SQLite also enables foreign-key enforcement.
- Entry saves check the period inside a transaction and bulk saves roll back together. Transaction failures are not automatically replayed.
- KPI entry stops on locked quarters.
- Approval captures the calculation, source sales and reference rules together with the reviewer and revision. Snapshot records reject updates and deletes. PostgreSQL snapshots have row-level security enabled.
- Locked calculations and reports read the snapshot rather than current employees, targets and rules.
- Reopening requires a reason, retains old revisions and permits a new approval revision.
- Legacy locked quarters without snapshots stop with a reconciliation message. They are never silently certified from today's rules.
- Removed outer dashboard/commission caches that could bypass current lock status. Entry writes invalidate calculation caches.

## Verification

- Seven SQLite regression tests cover entry paths, direct SQL mutations, historical stability, immutable snapshots, revision retention, legacy handling, approval rollback and atomic bulk saves.
- Nine PostgreSQL checks passed in disposable schemas through the dedicated session endpoint, including approval during a concurrent save and snapshot row-level security. The first test run encountered a transaction-pooler test-configuration issue; the isolated rerun passed and the leftover test schema was removed.
- Streamlit AppTest rendered Home and all six pages with synthetic in-memory data successfully. This is not a visual browser test.
- GitHub HEAD matched the original local revision `9f518682839e081abc2628863b1276d76abceb03` before these edits.
- Source backup is outside this repository under `_Company Knowledge/CommissionApp-Fix-2026-09-07`.
- A read-only export of all 17 production application tables (331 records) was saved and verified before deployment. Business tables were subsequently compared to the export with no differences. No locked periods existed at preflight.
- The working deployment connection was saved in the local, Git-ignored secrets file. Credentials and production records are excluded from this commit.

## Before deployment

1. Deploy the tested commit through the existing GitHub main branch.
2. Verify the deployed revision, read-only page access, snapshot table and lock triggers. Do not test approval or sample writes against real payout records.
3. For future legacy migrations, reconcile any locked quarters without snapshots against approved reports. Reopening and reapproving is an explicit administrative decision, not an automatic migration step.

The other high-priority audit findings (authentication, import preview/validation, bracket and KPI policy validation, and full audit coverage) remain separate work. These changes do not certify commission policy correctness.
