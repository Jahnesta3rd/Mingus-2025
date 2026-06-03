# #136 — Roster collects/persists no relationship or cost data — CLOSED

**Tier: 1 — was Pre-beta blocker.**
**Status: CLOSED. Resolved by Stage 3-A, commit 580daefd.**
**Original filing:** 2026-05-17 from May 16-17 onboarding investigation.

---

## Original defect

RosterStep sent only {count} to the backend. relationship_type and
estimated_monthly_cost were never collected on the frontend and never
committed to vibe_tracked_people. Two gaps:

1. Frontend: no collection UI for relationship type or monthly cost per person
2. Backend: no _commit_roster_module handler; the per-FIELD roster path existed
   but the per-MODULE path (the one Save & Continue actually uses) had no roster branch

Result: every user roster had only a junk placeholder row with
relationship_type = NULL and estimated_monthly_cost = NULL.
Owner decision at filing: roster MUST record person + relationship + estimated
spend before beta.

Split from #133 because this required new frontend collection UI in RosterStep
in addition to the backend handler — a larger, separate scope (~5-6hr vs #133
backend-only ~3hr).

---

## How it was resolved

Commit 580daefd — "Stage 3-A: Roster augmentation + inline Relationship Check":

- Frontend (RosterSeedStep.tsx): added per-person relationship type selector
  and estimated monthly cost input. Both fields validated before submit.
  Added tier-based row caps (budget: 2, mid: 6, pro: unlimited).
  Skip button hardened to not discard entered data (follow-on fix e461ca04).
- Backend: added _commit_roster_module dispatch branch in run_commit_module.
  Enriches existing VibeTrackedPerson rows with relationship_type and
  estimated_monthly_cost. Upsert pattern — does not duplicate people.
- Inline Relationship Check: per-partner relationship assessment UI added
  alongside cost collection.

---

## Verification

- Stage 3-A verification run (2026-05-25): users 87, 88, 89 on local dev DB.
  All roster rows populated with real relationship_type and estimated_monthly_cost.
  No null fields. NOTE: this run was against a local DB, not the cloud instance.
- Cloud DB verification run (2026-06-03): users 37 and 38 on DigitalOcean
  managed PostgreSQL (defaultdb):
  - User 37: nickname Christi, relationship_type=married, estimated_monthly_cost=300
  - User 38: nickname Run2Person, relationship_type=dating, estimated_monthly_cost=450
  Both rows fully populated. Write path confirmed clean on the real production DB.
  This is the authoritative production confirmation of this fix.

---

## Note on local-vs-cloud DB

The May 25 Stage 3-A verification (users 87-90) ran against a local development
database, not the DigitalOcean cloud instance (defaultdb). The June 3 cloud
verification run (users 37-38) is the authoritative production confirmation.

---

## Cross-refs

- Tracker_Entry_136.md — original spec, design checklist, fix path
- Roster_136_Design_Checklist.md — the 6 design questions answered before coding
- Tracker_Entry_133_CLOSED.md — sibling defect (missing module branches)
- Stage_2B_Closure.md — session-readiness fix that made roster verification possible
- Open_Blockers_Consolidated_2026-05-27.md — May 27 reconciliation that flagged
  this closure entry as needed
