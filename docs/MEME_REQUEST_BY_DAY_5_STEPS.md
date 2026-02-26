# 5 Steps: Make Meme Requests Go to the Correct Database by Day

---

## Step 1. Use one “correct” database

- All meme requests use **one** SQLite database: **`mingus_memes.db`** or the path in **`MINGUS_MEME_DB_PATH`**.
- In **`backend/api/meme_endpoints.py`**, use that single `DB_PATH` for all meme DB access.
- On the server, set **`MINGUS_MEME_DB_PATH`** in the app’s environment (e.g. gunicorn).
- If **meme_selector** is used from the app, point it at the same path.

---

## Step 2. Schema so “day” is in the database

- Run **`migrations/001_initial_meme_schema.sql`** (base `memes` table).
- Run **`migrations/004_meme_day_of_week_theme.sql`** (add `day_of_week`, `theme`).
- Run **`migrations/005_unify_meme_categories.sql`** (unified categories).
- Seed with **`python3 scripts/seed_meme_by_day.py`** so there is at least one meme per weekday (aligned with meme_selector’s day→category).

---

## Step 3. API: use the day when querying

In **`get_user_meme()`** in **`backend/api/meme_endpoints.py`**:

1. Compute **today** (e.g. `datetime.utcnow().weekday()` → 0=Monday … 6=Sunday).
2. **First:** `WHERE is_active = 1 AND day_of_week = today` → return a random matching meme if any.
3. **Then (optional):** If none, use meme_selector’s **day→category** and query `WHERE category = today_category`.
4. **Finally:** Fallback to any random active meme.

Keep the same weekday convention (0=Mon … 6=Sun) everywhere.

---

## Step 4. Request path

- **Client** → `GET /api/user-meme` → **meme_endpoints** → open **DB_PATH** (the single meme DB) → run the day-based query (and fallbacks) → return the meme for “today.”

---

## Step 5. Deployment (server)

1. Create the DB file (if needed) and set **`MINGUS_MEME_DB_PATH`** in the app’s environment.
2. Run migrations **001 → 004 → 005** on that DB.
3. Run **`python3 scripts/seed_meme_by_day.py`** (with `MINGUS_MEME_DB_PATH` set).
4. Restart the app.
5. Verify: **`GET /api/user-meme`** returns 200 and a meme that matches the current day (by `day_of_week` or category).
