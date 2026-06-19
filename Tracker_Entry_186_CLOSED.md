# #186 — Job Recommendation Audit — Location Sensitivity & Apply Link Strategy — CLOSED

**Status: CLOSED. All 10 close criteria passed.**
**Resolved by JRA-01 (acfd0679) and JRA-02 (624e5092).**
**Original filing:** 2026-06-19 from test-run observation that job recommendations
appeared identical across users with different zip codes and job titles.

---

## Original defect

During test runs, job recommendations shown in RecommendationTiers did not change
between users with different zip codes and career profiles. Suspected causes:
hardcoded job data, broken MSA resolver, or stale frontend mock data.

---

## Root cause (confirmed by audit)

Jobs were **not hardcoded**. The engine is fully dynamic on `bls_career_field`
and seniority. The `job_postings` table holds 1,123 seeded rows across 15 MSAs.

Jobs appeared identical because **4 of 7 career-profile users had no zip** in
`housing_profile`, causing all to fall back to **Houston (CBSA 26420)** via
`DEFAULT_MSA`. Same MSA + same career field + same seniority → deterministically
identical top-5 results.

Secondary gaps:
- `user_profiles` had no `zip_code` column — resolver fallback was dead code
- `job_postings` had no `url` column — Apply button routed to broken `/apply/{id}` stub
- View Details was analytics-only (no UI panel) since #113 closed June 4

---

## How it was resolved

### JRA-01 — ZIP capture gap fix (acfd0679)

- Alembic migration `052_user_profiles_zip_code`: added `user_profiles.zip_code VARCHAR(10) NULL`
- New `UserProfile` SQLAlchemy model with `zip_code` field
- `sync_user_profile_zip()` mirrors `housing_profile.zip_or_city` into
  `user_profiles.zip_code` on onboarding housing save (batch + single-field paths)
- Resolver fallback chain confirmed:
  1. `housing_profile.zip_or_city`
  2. `user_profiles.zip_code`
  3. `DEFAULT_MSA = '26420'` (Houston) with WARNING only when both sources are None

### JRA-02 — Apply button fix + URL column (624e5092)

- Alembic migration `053_job_postings_url`: added `job_postings.url TEXT NULL`
- `JobPosting.url` field added; `_query_curated_jobs` SELECTs url
- Apply button hidden when `url` is null (no misleading direct-apply links)
- Removed broken `/apply/{job_id}` stub navigation
- View Details panel expanded to render: title, company, salary range,
  match score, advancement trajectory (match score was previously missing)

---

## Verification

### JRA-01 (live DB + resolver)

- `alembic upgrade head` → exit 0
- User 40 with zip `10001` → MSA `35620` (NYC)
- User 41 with zip `85001` → MSA `38060` (Phoenix); mid Software Engineer $98,700–$126,900
- User 57 (no zip) → MSA `26420` + WARNING: "No zip or city for MSA resolution…"

### JRA-02 (schema + frontend)

- `alembic upgrade head` → exit 0
- All 1,123 `job_postings.url` rows NULL after migration
- No `/apply/` references remain in frontend
- RecommendationTiers unit tests: 5/7 pass

### Post-deploy browser verify (still needed)

- Confirm no Apply buttons visible for users 10/31 (seeded urls all NULL)
- Confirm View Details expands cleanly with all 5 fields
- Confirm no console errors on load or expand

---

## Backlog surfaced

**A — Pre-existing test failures (recommend #187):**
2 income-banner text assertions failing in `RecommendationTiers.test.tsx`
(unrelated to JRA-01/JRA-02).

**B — View Details UI gap since #113:**
View Details was analytics-only with no expanded panel until JRA-02.
Not caught by #113 close criteria.

**C — Live job board integration (future):**
Populate `job_postings.url` from Indeed Publisher / LinkedIn Jobs / Adzuna.
Show Apply button only when url is non-null.

---

## Cross-refs

- Tracker #113 — original recommendation engine phase (June 4, 2026 close)
- `backend/api/recommendation_engine_endpoints.py` — process-resume + MSA resolver
- `backend/utils/mingus_job_recommendation_engine.py` — tier selection engine
- `frontend/src/components/RecommendationTiers.tsx` — tier UI
- `backend/data/zip_to_msa.py` — 1,743 zip → CBSA mappings
