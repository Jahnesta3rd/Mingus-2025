# Vibe-Check Meme Not Loading – Troubleshooting

When the vibe-check page shows **"Could not load vibe check"** or the meme never appears, the backend `/api/user-meme` endpoint is failing (usually returning **500** with "Failed to fetch meme"). This is almost always because the **meme SQLite database** is missing, has no schema, or has no active memes on the server.

---

## Why it fails

1. **`/api/user-meme`** is implemented in `backend/api/meme_endpoints.py`.
2. It reads from a **SQLite** database: **`mingus_memes.db`** at the **repo root** (same directory as `app.py`).
3. The repo **ignores** `*.db` in `.gitignore`, so **the database is not deployed** to the server.
4. If the file is missing, the `memes` table doesn’t exist, or there are no rows with `is_active = 1`, the code raises and returns **500 – "Failed to fetch meme"**.

---

## Steps to fix (on the test server: test.mingusapp.com)

Run these on the server (e.g. `ssh test.mingusapp.com`) or from your Mac via SSH one-liners. Replace `REPO_DIR` with the actual app directory on the server (e.g. `/home/mingus-app/mingus-app` from `DEPLOY_NOW.sh`).

### Step 1: Confirm the database is missing or empty

SSH in and run:

```bash
REPO_DIR=/home/mingus-app/mingus-app   # or your repo path
cd $REPO_DIR

# Does the DB file exist?
ls -la mingus_memes.db 2>/dev/null || echo "Database file not found"

# If it exists, does it have the memes table and any active memes?
sqlite3 mingus_memes.db "SELECT COUNT(*) AS active_memes FROM memes WHERE is_active = 1;" 2>/dev/null || echo "Database missing or table not found"
```

- If you see **"Database file not found"** or **"table memes already exists" / "no such table"** → continue to Step 2.
- If **active_memes** is **0** → skip to Step 3 to add memes.

---

### Step 2: Create the database and schema

From the repo root on the server:

```bash
cd $REPO_DIR

# Create DB and tables using the migration schema
sqlite3 mingus_memes.db < migrations/001_initial_meme_schema.sql

# Or, if that file isn’t in the repo on server, use the main schema:
# sqlite3 mingus_memes.db < meme_database_schema.sql

# Verify table exists
sqlite3 mingus_memes.db ".tables"
# You should see: memes  user_meme_history  user_mood_data  (and possibly meme_analytics later)
```

Ensure the process that runs the app (e.g. `www-data` or `mingus-app`) can **read and write** this file:

```bash
# If the app runs as www-data:
sudo chown www-data:www-data mingus_memes.db
# Or if it runs as the same user that owns REPO_DIR, no change needed.
```

---

### Step 3: Add at least one active meme

The vibe-check only returns a meme when `memes` has at least one row with **`is_active = 1`**. You can add a placeholder meme directly in SQLite:

```bash
cd $REPO_DIR
sqlite3 mingus_memes.db "
INSERT INTO memes (image_url, category, caption, alt_text, is_active, created_at, updated_at)
VALUES (
  'https://via.placeholder.com/400/1a1a2e/eee?text=Vibe+Check',
  'work_life',
  'Welcome to your vibe check.',
  'Vibe check placeholder',
  1,
  datetime('now'),
  datetime('now')
);
"

# Verify
sqlite3 mingus_memes.db "SELECT id, category, is_active FROM memes;"
```

- **image_url** must be a URL the frontend can load (HTTPS in production). Use a real image URL or a placeholder service that allows hotlinking.
- For more memes, use the repo’s **populate script** with a CSV (see [Populate from CSV](#optional-populate-from-csv)) or the meme admin app.

---

### Step 4: Restart the backend

So the app picks up the new or changed DB:

```bash
# If using gunicorn (as in DEPLOY_NOW.sh):
sudo pkill -f 'gunicorn.*app:app' 2>/dev/null || true
sleep 2
cd $REPO_DIR
PYTHONPATH=$REPO_DIR nohup /opt/mingus-test/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 --timeout 120 app:app >> /tmp/gunicorn.log 2>&1 &
```

Adjust paths if your deploy uses a different venv or command.

---

### Step 5: Verify the API

From the server or your Mac (with a valid session cookie or no auth if the endpoint allows):

```bash
# From server (after login cookie or if endpoint doesn’t require auth):
curl -s "https://test.mingusapp.com/api/user-meme" -w "\nHTTP:%{http_code}\n"
```

- **HTTP:200** and a JSON object with `id`, `image_url`, `caption`, etc. → meme loading is fixed.
- **HTTP:500** → check backend logs (e.g. `/tmp/gunicorn.log` or your app logs) for the exact exception (e.g. "no such table", "unable to open database file", permission error).

---

## Optional: Use a persistent DB path (e.g. `/var/lib/mingus`)

So the DB isn’t inside the repo (and won’t be overwritten by deploys), you can:

1. Create a directory and DB on the server:

   ```bash
   sudo mkdir -p /var/lib/mingus
   sudo touch /var/lib/mingus/mingus_memes.db
   sudo chown www-data:www-data /var/lib/mingus/mingus_memes.db
   sqlite3 /var/lib/mingus/mingus_memes.db < $REPO_DIR/migrations/001_initial_meme_schema.sql
   # Add at least one meme (Step 3 above) into /var/lib/mingus/mingus_memes.db
   ```

2. Point the app at it with an env var. The app supports **`MINGUS_MEME_DB_PATH`** (used by `backend/api/meme_endpoints.py` and `weekly_checkin_endpoints.py`). For example, before starting gunicorn:

   ```bash
   export MINGUS_MEME_DB_PATH=/var/lib/mingus/mingus_memes.db
   ```

   Then restart the backend. If you use a process manager or systemd, set this env var there so it persists across restarts.

---

## Optional: Populate from CSV

If you have a CSV of memes (e.g. from the meme admin or export):

```bash
cd $REPO_DIR
# Ensure mingus_memes.db and schema exist (Step 2), then:
python scripts/populate_meme_database.py path/to/memes.csv
```

Then run the Step 3 verification query to ensure you have rows with `is_active = 1`.

---

## Summary checklist

| Step | Action |
|------|--------|
| 1 | Confirm `mingus_memes.db` is missing or has no active memes. |
| 2 | Create DB and run `migrations/001_initial_meme_schema.sql` (or `meme_database_schema.sql`). |
| 3 | Insert at least one row into `memes` with `is_active = 1`. |
| 4 | Restart the backend (e.g. gunicorn). |
| 5 | Call `GET /api/user-meme` and confirm 200 + JSON. |

After that, the vibe-check page should load the meme instead of "Could not load vibe check."

**Day-themed sample memes (one per weekday):** See **`docs/MEME_DAY_THEME_TESTING.md`** and `scripts/seed_meme_by_day.py` for storing and seeding memes by day/theme for testing.
