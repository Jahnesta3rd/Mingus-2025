# #133 — run_commit_module missing housing / career / roster branches — CLOSED

**Tier: 1 — was Pre-beta blocker.**
**Status: CLOSED. Resolved by F3-series commits, May 2026.**
**Original filing:** 2026-05-17 from May 16-17 onboarding investigation.

---

## Original defect

run_commit_module in backend/routes/_modular_onboarding_gc2_commit.py had
dispatch branches for only four of seven modules: income, recurring_expenses,
milestones, vehicle. When the wizard POSTed commit-module for housing, career,
or roster, the dispatcher matched no branch, skipped the commit block entirely,
fell through to completed_modules bookkeeping, marked the module complete,
and advanced the wizard — while writing zero rows to the database.

Silent data loss. No error surfaced to the user or logs. Confirmed on user 65:
housing_profile 0 rows, career_profile 0 rows, vibe_tracked_people only
a junk placeholder row.

---

## How it was resolved

The F3-series commits added the missing branches and their backing commit functions:

| Commit | What it added |
|---|---|
| ef416ae1 | F3: real Housing, Vehicle, Roster, Career, Milestones step components |
| 50c75c29 | F3.5: vehicle persistence, milestones logging, housing split_share_pct default |
| e089d01c | F3.6: remove duplicate commit-module POSTs + last-step data bypass fix |
| 2553534e | F3.7: surface milestones + vehicle validation failures in logs and to user |

The per-MODULE dispatch now has branches for all seven modules, each calling a
dedicated commit function that validates fields, upserts into the target table
in a single transaction, and returns the failed_fields shape the wizard expects.

Note: Roster relationship_type and estimated_monthly_cost collection was split
into tracker entry #136 because it required new frontend collection UI in addition
to the backend handler. #136 was closed separately by Stage 3-A (commit 580daefd).
See Tracker_Entry_136_CLOSED.md.

---

## Verification

- End-to-end verification (May 7, users 24-30): fresh signups walked the full
  7-module wizard; all 7 tables populated with real data. No zero-row tables.
- 5-run matrix (May 19-21): 5 consecutive fresh budget-tier signups, throttled
  network, DB-checked each. All modules persisted correctly.
- Cloud DB verification run (2026-06-03): users 37 and 38 on DigitalOcean
  managed PostgreSQL (defaultdb). completed_modules = all 7 for both users.
  completed_at populated. Roster rows fully populated (see #136 closure).

---

## Cross-refs

- Tracker_Entry_133.md — original spec and root cause analysis
- Tracker_Entry_136_CLOSED.md — roster relationship/cost half split from #133
- Stage_2B_Closure.md — session-readiness fix that made this verifiable
- Outstanding_Bugs_2026-05-17.md — original May 17 bug list
