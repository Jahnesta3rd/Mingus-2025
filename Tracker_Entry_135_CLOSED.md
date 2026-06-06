# #135 — Vehicle commit produced zero rows — CLOSED

**Tier: 1 — was Pre-beta blocker.**
**Status: CLOSED. Resolved by Stage 2 vehicle augmentation, commit 003e3fe1.**
**Original filing:** 2026-05-17 from May 16-17 onboarding investigation.

---

## Original defect

The vehicle dispatch branch existed in run_commit_module (unlike housing/career/roster
which were missing entirely per #133), but user 65 still got zero vehicle rows after
completing onboarding. Suspected cause: _commit_vehicle_module was writing an empty
payload, OR the VehicleStep was not sending data, OR an all-or-nothing list-replace
was discarding the entry on a bad/empty field.

Distinct from #133 (missing branches) because the vehicle branch existed — the bug
was in the vehicle commit logic or the data it received.

---

## How it was resolved

Commit 003e3fe1 — "Stage 2: Vehicle augmentation — VIN, dropdowns, mileage,
garage ZIP, MSA" — rebuilt the VehicleStep frontend collection UI with full field
capture and hardened the backend _commit_vehicle_module handler.

Additional hardening in the F3-series:
- 50c75c29 (F3.5): vehicle persistence fixes and _commit_vehicle_module corrections
- e089d01c (F3.6): removed duplicate commit-module POSTs causing last-step data bypass
- 2553534e (F3.7): surfaced vehicle validation failures in logs and to the user

---

## Verification

- End-to-end verification (May 7, users 24-30): vehicles table populated with
  real rows for all test signups. No zero-row tables.
- 5-run matrix (May 19-21): vehicle data persisted correctly across all 5
  consecutive fresh signups.
- Cloud DB verification run (2026-06-03): users 37 and 38 completed the vehicle
  module (confirmed in completed_modules array).

---

## Cross-refs

- Outstanding_Bugs_2026-05-17.md — original filing
- Tracker_Entry_133_CLOSED.md — sibling defect (missing branches for other modules)
- Stage_2B_Closure.md — session-readiness fix that made vehicle verification possible
