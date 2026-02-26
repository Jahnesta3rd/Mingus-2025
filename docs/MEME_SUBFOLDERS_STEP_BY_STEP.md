# Step-by-Step: Organize Memes in Subfolders and Populate

Follow these steps to use **separate folders** for vibe-check memes by day, have the **populate script read from those subfolders**, and keep the **app working** as before (day-based meme selection, same API and routes).

---

## 1. Create your source folder and subfolders

Create a directory (e.g. **`memes_source`**) and one subfolder per day/theme. Use these names so the script can infer **day_of_week** and **category** automatically:

- **sunday_faith** — Sunday, faith  
- **monday_work_life** — Monday, work_life  
- **tuesday_friendships** — Tuesday, friendships  
- **wednesday_children** — Wednesday, children  
- **thursday_relationships** — Thursday, relationships  
- **friday_going_out** — Friday, going_out  
- **saturday_mixed** — Saturday, work_life  

Short names also work: `faith`, `work_life`, `friendships`, `children`, `relationships`, `going_out`, `mixed`.

**Example:**

```bash
mkdir -p memes_source/{sunday_faith,monday_work_life,tuesday_friendships,wednesday_children,thursday_relationships,friday_going_out,saturday_mixed}
```

---

## 2. Put your GIF/PNG files in the right subfolders

Copy or move your meme files into the matching folders (e.g. faith-themed memes in **sunday_faith/**, work-life in **monday_work_life/**, etc.). The script will discover all `.gif`, `.png`, `.jpg`, `.webp` files **recursively** and preserve the folder structure.

---

## 3. (Optional) Create a manifest CSV

If you want to override captions, alt text, or day/category for specific files, create a CSV with columns: **filename** (or **path**), **category**, **caption**, **alt_text**, **day_of_week**, **theme**.  
For files in subfolders, use the path: e.g. `sunday_faith/gratitude.gif`. See **docs/MEME_POPULATE_FROM_FILES.md** for the full format.

---

## 4. Ensure the meme DB and schema exist

From the **repo root**:

```bash
# If the DB doesn't exist or you're starting fresh:
sqlite3 mingus_memes.db < migrations/001_initial_meme_schema.sql
sqlite3 mingus_memes.db < migrations/004_meme_day_of_week_theme.sql
sqlite3 mingus_memes.db < migrations/005_unify_meme_categories.sql
```

(If you already ran these migrations, you can skip this step.)

---

## 5. Run the populate script

From the **repo root**:

```bash
# Copy files into static/memes/ and insert into DB (preserving subfolders)
python3 scripts/populate_memes_from_files.py memes_source --copy

# With optional manifest:
python3 scripts/populate_memes_from_files.py memes_source --manifest memes_source/manifest.csv --copy
```

The script will:

- Find all image files under **memes_source/** (including in subfolders).
- Copy them to **static/memes/** with the same structure (e.g. **static/memes/sunday_faith/gratitude.gif**).
- Insert rows into **mingus_memes.db** with **image_url** = `/memes/sunday_faith/gratitude.gif` and **day_of_week** / **category** from the folder name (or from the manifest).

Use **`MINGUS_MEME_DB_PATH`** if your DB is in a different location:

```bash
MINGUS_MEME_DB_PATH=/path/to/mingus_memes.db python3 scripts/populate_memes_from_files.py memes_source --copy
```

---

## 6. Verify the app still works

- Start the app and open the vibe-check flow.
- The API uses **day_of_week** to prefer memes for “today”; it falls back to random if none match.
- Meme images are served at **`/memes/<path>`** (e.g. `/memes/sunday_faith/gratitude.gif`). The app already has the route **`GET /memes/<path:filename>`** pointing at **static/memes/**, so no code changes are required.

**Quick checks:**

- Visit **`/memes/sunday_faith/<some_file>.gif`** (replace with a real filename) — you should see the image.
- Call **`/api/user-meme`** (with a logged-in session) — response should include an **image_url** that loads in the browser.

---

## Summary

| Step | What to do |
|------|------------|
| 1 | Create **memes_source** and subfolders: **sunday_faith**, **monday_work_life**, etc. |
| 2 | Put GIF/PNG files in the matching subfolders. |
| 3 | (Optional) Add **manifest.csv** with path, category, caption, alt_text, day_of_week, theme. |
| 4 | Apply migrations **001**, **004**, **005** if the meme DB is new. |
| 5 | Run **`python3 scripts/populate_memes_from_files.py memes_source --copy`** (and **--manifest** if you have one). |
| 6 | Confirm vibe-check and **/memes/...** URLs work in the app. |

After this, the app behavior is unchanged: it still uses the same DB, same API, and same day-based meme selection; only the **source layout** is organized into subfolders and the **populate script** reads from them and preserves paths.
