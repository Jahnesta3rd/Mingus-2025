# Populating the Meme Database from GIF/PNG Files

Recommendation for populating the meme database when your source assets are **local GIF or PNG files**, optionally organized in **separate folders by day/theme**.

---

## Recommended approach: **subfolders + script (manifest optional)**

1. **Organize files in subfolders** — e.g. `memes_source/sunday_faith/`, `memes_source/monday_work_life/`, etc. The script **recursively** finds all GIF/PNG under the source directory and **preserves subfolder structure** under **`static/memes/`**.
2. **Optional manifest (CSV)** — one row per file: `filename` (or `path`, e.g. `sunday_faith/gratitude.gif`), `category`, `caption`, `alt_text`, `day_of_week`, `theme`. Overrides inference from folder name.
3. **Script** — Copies files into **`static/memes/<subfolder>/<filename>`** and inserts rows into **mingus_memes.db** with **image_url** = `/memes/<subfolder>/<filename>`. Infers **day_of_week** and **category** from folder name when you use the recommended folder names below.
4. **Serve the files** — The app serves **`static/memes/`** at **`/memes/<path:filename>`**, so URLs like `/memes/sunday_faith/gratitude.gif` work. The vibe-check page and API use the DB to pick the right meme by day; no change needed there.

This keeps the DB small (metadata + URLs), supports images (GIF, PNG, etc.), **video** (e.g. MP4, WebM), and **audio** (e.g. MP3, WAV) in the same folders and themes. See **docs/MEME_VIDEO_AUDIO_SUPPORT.md** for video/audio steps.

---

## Recommended folder layout (vibe-check by day)

Use **one subfolder per day/theme** under your source directory. The script infers **day_of_week** and **category** from the **folder name** (case-insensitive):

| Folder name (under source) | Day (0=Mon … 6=Sun) | Category      |
|-----------------------------|---------------------|---------------|
| `sunday_faith/`             | 6                   | faith         |
| `monday_work_life/`         | 0                   | work_life     |
| `tuesday_friendships/`     | 1                   | friendships   |
| `wednesday_children/`       | 2                   | children      |
| `thursday_relationships/`   | 3                   | relationships |
| `friday_going_out/`        | 4                   | going_out     |
| `saturday_mixed/`          | 5                   | work_life     |

Short names also work: `faith/`, `work_life/`, `friendships/`, `children/`, `relationships/`, `going_out/`, `mixed/`.

**Example layout:**

```
memes_source/
  sunday_faith/
    gratitude_01.gif
    spiritual_01.png
  monday_work_life/
    monday_motivation_01.gif
  tuesday_friendships/
    friends_01.png
  wednesday_children/
    parenting_01.gif
  thursday_relationships/
    partnership_01.png
  friday_going_out/
    self_care_01.gif
  saturday_mixed/
    catchup_01.png
```

After running the script, files appear under **`static/memes/`** with the same structure (e.g. `static/memes/sunday_faith/gratitude_01.gif`), and **image_url** in the DB is **`/memes/sunday_faith/gratitude_01.gif`**. The app already serves **`/memes/<path:filename>`**, so no code changes are required for the app to work.

---

## Step 1. Where to store the files the app serves

- **Option A (recommended):** **`static/memes/`** in the repo. Add a Flask route that serves this folder at **`/memes/<filename>`**. Then **image_url** = `/memes/filename.gif` (or full URL in production).
- **Option B:** Put files in **`frontend/public/memes/`** so they are copied into **frontend/dist** at build time and served as **`/memes/filename.gif`** by the SPA server/nginx. No Flask change; image_url = `/memes/filename.gif`.

Use one approach so every **image_url** in the DB is **`/memes/<filename>`** (and your frontend/base URL in production).

---

## Step 2. Add a route to serve meme files (if using Option A)

In **`app.py`** (or a small blueprint), add:

```python
@app.route('/memes/<path:filename>')
def serve_meme(filename):
    """Serve meme images (GIF/PNG) from static/memes/."""
    meme_dir = os.path.join(os.path.dirname(__file__), 'static', 'memes')
    return send_from_directory(meme_dir, filename)
```

Ensure **`static/memes`** exists and is writable by the populate script.

---

## Step 3. Manifest CSV (optional but recommended)

Create a CSV, e.g. **`memes_source/manifest.csv`**, with columns:

| Column       | Required | Example                | Note |
|-------------|----------|------------------------|------|
| filename or path | Yes | monday_work.gif or sunday_faith/gratitude.gif | File name only, or path with subfolder (e.g. sunday_faith/gratitude.gif). |
| category    | Yes      | work_life              | One of the 7 (or 8) allowed categories. |
| caption     | Yes      | Monday mood...         | Shown under the meme. |
| alt_text    | Yes      | Monday work meme       | Accessibility. |
| day_of_week | No       | 0                      | 0=Mon … 6=Sun; for day-themed selection. |
| theme       | No       | Monday Motivation      | Optional label. |

If you omit the manifest, the script infers **category** and **day_of_week** from the **first subfolder name** (e.g. `sunday_faith/` → day 6, faith) when you use the recommended folder layout above, or from the filename for files in the root of the source directory.

---

## Step 4. Run the populate script

From the **repo root**:

```bash
# Ensure schema (001, 004, 005) and DB exist
sqlite3 mingus_memes.db < migrations/001_initial_meme_schema.sql
sqlite3 mingus_memes.db < migrations/004_meme_day_of_week_theme.sql
sqlite3 mingus_memes.db < migrations/005_unify_meme_categories.sql

# Populate from a folder of GIF/PNG and optional manifest
python3 scripts/populate_memes_from_files.py path/to/memes_source

# Or with explicit manifest
python3 scripts/populate_memes_from_files.py path/to/memes_source --manifest path/to/manifest.csv
```

The script will:

- **Recursively** find all GIF/PNG (and jpg, webp) under the source directory.
- Copy each file into **static/memes/** **preserving subfolders** (e.g. `memes_source/sunday_faith/a.gif` → `static/memes/sunday_faith/a.gif`).
- Infer **day_of_week** and **category** from the first subfolder name when you use the recommended layout (e.g. `sunday_faith`, `monday_work_life`); override with a manifest if provided.
- Insert one row per file into **memes** with **image_url** = `/memes/<path>` (e.g. `/memes/sunday_faith/a.gif`).
- Use **MINGUS_MEME_DB_PATH** if set.

---

## Step 5. Production / deployment

- On the server, either:
  - Run the same script there (with source files and manifest), so **static/memes/** is filled and the DB has the same **image_url** values, or
  - Build **static/memes/** (or **frontend/public/memes/**) in CI and deploy it with the app so **/memes/filename.gif** resolves.
- Ensure nginx (or your app) serves **/memes/** so requests to **image_url** from the API succeed.

---

## Summary

| Step | Action |
|------|--------|
| 1 | Choose served location: **static/memes/** (Flask route) or **frontend/public/memes/** (build). |
| 2 | Add Flask route **`/memes/<path:filename>`** if using static/memes (already present in app). |
| 3 | (Optional) Create subfolders by day (e.g. **sunday_faith/**, **monday_work_life/**) and put GIF/PNG in them; script infers day and category. Optional manifest CSV overrides. |
| 4 | Run **`scripts/populate_memes_from_files.py <source_dir> [--manifest manifest.csv] [--copy]`** to copy files into **static/memes/** (preserving subfolders) and insert DB rows with **image_url** = `/memes/<path>`. |
| 5 | Deploy so **/memes/** is served and **image_url** in the DB works in production. |

This is the recommended way to populate the meme database when the sources are GIF or PNG files: files on disk, optional manifest for metadata, one script to copy and insert, and a single URL pattern (**/memes/...**) for all meme images.
