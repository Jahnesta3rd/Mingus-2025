# Outline: Make Meme Requests Use the Correct Data by Day

Goal: when a request comes in for a meme, **given the current day**, the system uses the **correct database** (and correct query) so the response is the right meme for that day.

---

## 1. Single “correct” database for memes

- **All meme requests** (e.g. `GET /api/user-meme` for the vibe-check) should hit the **same** SQLite database: **`mingus_memes.db`** (or the path set by **`MINGUS_MEME_DB_PATH`**).
- There is only one meme DB; “correct database” here means **correct DB path** and **correct query for the day**, not choosing between multiple DBs.

**To do:**

| Step | Action |
|------|--------|
| 1.1 | Ensure **`backend/api/meme_endpoints.py`** uses **`DB_PATH`** (from `MINGUS_MEME_DB_PATH` or default repo-root `mingus_memes.db`) for all reads/writes. No hardcoded alternate paths. |
| 1.2 | On the server (e.g. test.mingusapp.com), set **`MINGUS_MEME_DB_PATH`** in the environment that runs the app (gunicorn/systemd) so production uses the intended path (e.g. `/var/lib/mingus/mingus_memes.db`). |
| 1.3 | If **meme_selector.py** is ever used from the Flask app for meme selection, configure it to use the **same** path (e.g. pass `os.environ.get("MINGUS_MEME_DB_PATH", "mingus_memes.db")` or the repo-root default). |

---

## 2. Schema so “day” has meaning in the DB

The database must support day-based selection in one (or both) of these ways:

- **Option A:** Rows with **`day_of_week`** (and optional **`theme`**) so “today’s meme” is `WHERE day_of_week = today`.
- **Option B:** Rows with **`category`** only; “today’s meme” is chosen by **day → category** (e.g. meme_selector’s map) then `WHERE category = today_category`.

**To do:**

| Step | Action |
|------|--------|
| 2.1 | Run **`migrations/001_initial_meme_schema.sql`** so the **`memes`** table exists. |
| 2.2 | Run **`migrations/004_meme_day_of_week_theme.sql`** to add **`day_of_week`** and **`theme`** (optional but recommended for day-based selection). |
| 2.3 | (Recommended) Run **`migrations/005_unify_meme_categories.sql`** so **`category`** allows the 7 day-theme categories (plus legacy `going_out`). Aligns with meme_selector’s day→category map. |
| 2.4 | Seed day-themed memes: **`python3 scripts/seed_meme_by_day.py`** so there is one meme per weekday (or more per day if desired). Uses the same day→category mapping as meme_selector. |

---

## 3. API: use the day when querying the database

The handler that serves **`GET /api/user-meme`** must use the **current day** to decide what to read from the meme DB.

**To do:**

| Step | Action |
|------|--------|
| 3.1 | In **`get_user_meme()`** (or equivalent) in **`backend/api/meme_endpoints.py`**: |
|     | (a) Compute **today** (e.g. `datetime.utcnow().weekday()` so 0=Monday, 6=Sunday). |
|     | (b) **First:** try `SELECT * FROM memes WHERE is_active = 1 AND day_of_week = ? ORDER BY RANDOM() LIMIT 1` with `today`. If a row exists, return it. |
|     | (c) **Fallback:** if no row has that `day_of_week`, optionally try “today’s category” (using meme_selector’s day→category map), e.g. `WHERE is_active = 1 AND category = ? ORDER BY RANDOM() LIMIT 1`. |
|     | (d) **Final fallback:** `SELECT * FROM memes WHERE is_active = 1 ORDER BY RANDOM() LIMIT 1`. |
| 3.2 | Ensure the same **weekday convention** everywhere (e.g. Python weekday 0=Monday, 6=Sunday). The seed script and meme_selector already use this; keep the API consistent. |
| 3.3 | (Optional) If you want “avoid recently viewed” and day→category logic from **meme_selector**, either: call **MemeSelector** from the endpoint (with the same DB path) and use its result, or reimplement that logic inside **meme_endpoints** against the same DB. |

---

## 4. Request path end-to-end

- **Client:** e.g. `GET /api/user-meme` (with credentials/cookies as required).
- **App:** Flask route → **meme_endpoints.get_user_meme_endpoint()** → **get_user_meme()**.
- **Database:** Open **`DB_PATH`** (mingus_memes.db or **MINGUS_MEME_DB_PATH**); run the day-based query (and fallbacks) above.
- **Response:** JSON meme for “today” (or fallback). No other DB should be used for this request.

So: **request + current day → one DB, one query path → correct meme for the day.**

---

## 5. Deployment checklist (server)

| Step | Action |
|------|--------|
| 5.1 | Create the DB file (if needed), e.g. `touch /var/lib/mingus/mingus_memes.db` and set ownership. |
| 5.2 | Set **`MINGUS_MEME_DB_PATH`** in the environment that starts the app (e.g. gunicorn or systemd). |
| 5.3 | Run migrations in order: **001** → **004** → **005** (005 optional but recommended). |
| 5.4 | Run **`python3 scripts/seed_meme_by_day.py`** (with **MINGUS_MEME_DB_PATH** set) so each weekday has at least one meme. |
| 5.5 | Restart the app so it picks up the env and any code changes. |
| 5.6 | Verify: `GET /api/user-meme` returns 200 and a meme; on a given day, the returned meme’s `day_of_week` or `category` matches the expected day (or today’s category). |

---

## 6. Summary

| What | Action |
|------|--------|
| **Correct database** | One SQLite DB for memes; path from **MINGUS_MEME_DB_PATH** or default; used by meme_endpoints (and meme_selector if used). |
| **Given the day** | API uses **current weekday** (0=Mon … 6=Sun): first query by **day_of_week**, then optionally by **day→category**, then random. |
| **Schema** | 001 + 004 (+ 005 for unified categories); seed script fills day-themed rows. |
| **Deployment** | Set **MINGUS_MEME_DB_PATH**, run migrations and seed, restart app. |

After this, **requests that include or imply “today” will hit the correct database and return the correct meme for that day.**
