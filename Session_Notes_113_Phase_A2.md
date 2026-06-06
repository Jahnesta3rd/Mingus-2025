# #113 Phase A2 — Session Notes

**Phase:** A2 — `job_postings` migration, seed script, search wiring  
**Status:** Complete (migration applied, 1,120 rows seeded, Task 4 verified)

---

## Seed coverage gap — 2 of 22 BLS fields missing

The seed inserted **20 career fields**, not all 22 allowed by the `job_postings` check constraint.

**Missing fields (0 rows seeded):**

1. **Social Services & Nonprofit**
2. **Self-Employed / Entrepreneurship**

These two fields have national salary bands in `FIELD_BASE_SALARIES` but are **not** assigned to any MSA in `MSA_STRONG_FIELDS` and have no entries in `FIELD_ROLE_TITLES`, `FIELD_COMPANIES`, or `ADVANCEMENT_BY_FIELD`. They were intentionally omitted when building per-MSA “strong field” mappings (neither maps cleanly to a single metro labor market).

**Follow-up (if needed):** Add role titles, companies, advancement copy, and MSA assignments (e.g. Social Services → DC/Boston/Cleveland; Self-Employed → all heavy MSAs or a dedicated subset), then re-run `python3 -m backend.scripts.seed_job_postings`.

---

## Verification snapshot (Task 4)

| Check | Result |
|-------|--------|
| Migration `a113a2_job_postings` | Applied |
| Rows seeded | 1,120 |
| Career fields in seed | 20 / 22 |
| MSAs in seed | 15 |
| Technology / NYC / mid tier counts | same_level=3, reach=3, conservative=5 |
| Finance & Accounting / Chicago / senior tier counts | same_level=3, reach=3, conservative=5 |
| NYC Technology senior `salary_min` > Phoenix | 193,199 > 131,600 ✓ |
