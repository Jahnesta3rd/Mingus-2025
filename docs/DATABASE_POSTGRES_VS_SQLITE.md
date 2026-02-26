# PostgreSQL vs SQLite – Which Database to Use

## Short answer

- **PostgreSQL** is the **correct primary database** for the app in production (users, auth, core features).
- **SQLite** is currently used for **several separate feature databases** (memes, some analytics, etc.). Those are correct *for now* as implemented; production can keep using SQLite for those **or** migrate them to PostgreSQL for consistency and ops.

---

## How the app is set up

### Primary app database (PostgreSQL in production)

- **Config:** `DATABASE_URL` (e.g. `postgresql://...` with SSL on DigitalOcean).
- **Code:** `backend/models/database.py` → `init_database(app)` uses `DATABASE_URL` for Flask-SQLAlchemy `db`.
- **Used for:** Auth (login, users), vehicles, housing, daily outlook, wellness check-ins, gamification, notifications, spending baseline, and other core app data.
- **Deployment:** Production checklists (e.g. `DIGITALOCEAN_PRODUCTION_DEPLOYMENT_CHECKLIST.md`) require **PostgreSQL** for `DATABASE_URL` and running migrations on Postgres.

So for the **main application data**, **PostgreSQL is the correct database** in production.

### Feature-specific databases (SQLite today)

These use **SQLite** by design in the current codebase (separate files, not `DATABASE_URL`):

| Purpose | File / path | Used by |
|--------|-------------|--------|
| Memes / vibe-check / weekly check-in | `mingus_memes.db` (or `MINGUS_MEME_DB_PATH`) | `meme_endpoints.py`, `weekly_checkin_endpoints.py` |
| User preferences | `app.db` | `user_preferences_endpoints.py` |
| Assessments | `assessments.db` | `assessment_endpoints.py` |
| Commute | `backend/mingus_commute.db` | `commute_endpoints.py` |
| Job matching / recommendations | `backend/job_matching.db`, `backend/mingus_recommendations.db` | job/recommendation endpoints |
| Analytics / risk / A/B tests | `backend/analytics/*.db` | analytics and risk APIs |
| Other | e.g. `user_profiles.db`, `content_optimization.db`, referral DB | various services |

So for **those features**, **SQLite is what the app currently uses**. It’s “correct” in the sense that it matches the code; the only question is whether you *want* to move any of them to PostgreSQL.

---

## When to use which

| Context | Use |
|--------|-----|
| **Production primary data** (users, auth, core features) | **PostgreSQL** via `DATABASE_URL`. |
| **Local / dev** (if you don’t run Postgres) | **SQLite** is fine for the primary DB when `DATABASE_URL` is unset (default in code is SQLite). |
| **Meme/vibe-check DB** | **SQLite** is correct with the current code; ensure `mingus_memes.db` exists and has schema + data on the server (see `VIBE_CHECK_MEME_LOADING_TROUBLESHOOTING.md`). Optionally migrate to Postgres later. |
| **Other feature DBs** (preferences, assessments, commute, etc.) | **SQLite** is what the app uses now; migration to Postgres is optional and would require code/schema changes. |

---

## Summary

- **PostgreSQL** = correct and expected for the **main app database** in production (`DATABASE_URL`).
- **SQLite** = correct for the **meme DB and other feature DBs** as implemented; use it where the code expects it, and optionally migrate to PostgreSQL later if you want one database for everything.
