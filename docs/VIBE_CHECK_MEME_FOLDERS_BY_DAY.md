# Vibe-check meme folders by day

## Are there separate folders for each day?

**No.** Right now there are **no** separate folders that house memes by day or theme for the vibe-check page.

- **Served memes:** All meme assets live in a **single** directory, **`static/memes/`**, and are served at **`/memes/<filename>`**. The app and `scripts/populate_memes_from_files.py` use this one folder only; there are no subfolders like `static/memes/sunday/` or `static/memes/faith/`.
- **Which meme shows when:** The **database** (table **`memes`**) decides which meme is used for a given day via **`day_of_week`** and **`category`**. Files can all sit in one folder; the DB rows point to them with **`image_url`** (e.g. `/memes/sunday_faith_01.gif`).

So the vibe-check page is driven by **DB metadata** (day + category), not by folder structure.

---

## Your day themes → categories

Mapping your vibe-check themes to the categories used in the DB and scripts (and to a suggested **source** folder layout if you add one):

| Day     | Theme (vibe-check) | DB category  | Suggested source subfolder (optional) |
|---------|--------------------|--------------|----------------------------------------|
| Sunday  | Faith (motivation, gratitude, spiritual wellness) | `faith` | `faith/` or `sunday_faith/` |
| Monday  | Work Life (Monday motivation, career goals, professional growth) | `work_life` | `work_life/` or `monday_work_life/` |
| Tuesday | Friendships (social connections, support systems) | `friendships` | `friendships/` or `tuesday_friendships/` |
| Wednesday | Children (parenting, family planning, education costs) | `children` | `children/` or `wednesday_children/` |
| Thursday | Relationships (romantic relationships, partnership goals) | `relationships` | `relationships/` or `thursday_relationships/` |
| Friday  | Going Out (social life, entertainment, self-care) | `going_out` | `going_out/` or `friday_going_out/` |
| Saturday | Mixed/Catch-up (any category from user preferences) | `mixed` or any of the above | `mixed/` or `saturday_mixed/` |

**Note:** The schema and 005 migration allow **faith, work_life, health, housing, transportation, relationships, family, going_out**. Your list uses **friendships** and **children** (from the original 6-category set). To support your mapping exactly you can:

- Use **relationships** for “Friendships” and **family** for “Children” (if you’ve run 005), or  
- Ensure the meme DB schema allows **friendships** and **children** (e.g. keep or add them to the category CHECK).  

**Saturday “Mixed”:** Store as one of the existing categories or add a **mixed** category in the schema; the API can pick by user preferences or random from multiple categories when `day_of_week = 6`.

---

## Optional: separate source folders (for organization only)

You can **organize source files** (before running the populate script) in separate folders by day or category. The script and app do **not** require this; it’s for your own layout.

**Option A — One folder per day (recommended for your 7 themes):**

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

Use a **manifest CSV** with columns **filename**, **category**, **caption**, **alt_text**, **day_of_week**, **theme**. Set **filename** to the path relative to `memes_source` (e.g. `sunday_faith/gratitude_01.gif`) or copy all files into one flat directory and list only **filename** (e.g. `gratitude_01.gif`) with the right **day_of_week** and **category**. The populate script copies files into **`static/memes/`** and stores **image_url** as **`/memes/<filename>`**; the DB then selects by **day_of_week** and **category**, not by folder.

**Option B — One folder per category:**

```
memes_source/
  faith/
  work_life/
  friendships/
  children/
  relationships/
  going_out/
  mixed/
```

Again, use a manifest to set **day_of_week** and **category** per file. The script still writes everything into **`static/memes/`** (flat) unless you change it to preserve subpaths (e.g. **image_url** = `/memes/faith/gratitude_01.gif`); the app already serves **`/memes/<path:filename>`**, so subpaths work if the script writes files into **`static/memes/faith/`** etc.

---

## Summary

| Question | Answer |
|----------|--------|
| Are there separate folders for vibe-check memes today? | **No.** Only **`static/memes/`** exists; no per-day or per-category folders. |
| How does the app know which meme to show? | By **database** fields **`day_of_week`** and **`category`**, not by folder. |
| Can I use separate source folders? | **Yes**, as an optional layout (e.g. **memes_source/sunday_faith/**, …); use a manifest so the populate script sets **day_of_week** and **category** and copies into **static/memes/** (flat or with subpaths). |

Your 7-day vibe-check themes map to the categories and optional folder names in the table above; the DB and optional manifest drive which meme is used for each day.
