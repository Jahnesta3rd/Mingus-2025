# Meme schema verification – no prior day_of_week/theme columns

Verification that **no previously established schema** for meme data defined **day_of_week** or **theme** on the `memes` table. Migration 004 and the day-theme seed are additive only.

---

## Canonical meme table definitions checked

| Source | memes columns | day_of_week / theme |
|--------|----------------|---------------------|
| **migrations/001_initial_meme_schema.sql** | id, image_url, category, caption, alt_text, is_active, created_at, updated_at | ❌ Not present |
| **meme_database_schema.sql** | Same as 001 | ❌ Not present |
| **meme_admin_app.py** (init_database) | Same as 001 | ❌ Not present |
| **meme_selector.py** (CREATE TABLE when table missing) | Same + different category CHECK (see below) | ❌ Not present |
| **operating manual/MEME_DATABASE_UPDATE_SUMMARY.md** | id, image_url, caption, alt_text, category, is_active, created_at, updated_at | ❌ Not present |
| **operating manual/MEME_SELECTOR_README.md** | id, image_url, category, caption, alt_text, is_active, created_at, updated_at | ❌ Not present |
| **tests/meme_splash/** (fixtures, test_meme_api_endpoints, test_meme_selector_unit) | Same core columns | ❌ Not present |

**Conclusion:** No existing schema defines **day_of_week** or **theme** on `memes`. Migration **004_meme_day_of_week_theme.sql** is the only place that adds these columns; it does not conflict with any prior schema.

---

## Pre-existing inconsistency (unchanged by 004): category CHECK

- **001 / meme_database_schema.sql / meme_admin_app:**  
  `category` CHECK: `faith`, `work_life`, `friendships`, `children`, `relationships`, `going_out` (6 values).
- **meme_selector.py** (when it creates the table):  
  `category` CHECK: `faith`, `work_life`, `health`, `housing`, `transportation`, `relationships`, `family` (7 values; different set).
- **MEME_DATABASE_UPDATE_SUMMARY / production-style docs:**  
  `category` as TEXT (no CHECK); in use: work_life, relationships, health, faith, transportation, housing, family.

This category mismatch predates migration 004. The day-theme seed script uses the **001** category set (e.g. `work_life`, `faith`, `going_out`) so it stays consistent with the migrations and `meme_endpoints.py`.

---

## “Day of week” in existing code (logic only, not schema)

- **MEME_SELECTOR_README.md** describes “Day-of-Week Logic - Different categories for each day” as **application behavior** (selector chooses category by day), not a table column.
- **meme_selector.py** logs `day_of_week: datetime.now().weekday()` in **analytics_data** (logging only); it does not read or write a `day_of_week` column on `memes`.

So “day of week” existed only in app logic and logs; the **schema** had no such column until 004.

---

## Day-of-week → category mapping (meme_selector.py)

The **pre-existing** day→category relationship is defined in **`meme_selector.py`** as `DAY_CATEGORY_MAP`. The selector uses **0=Sunday … 6=Saturday** internally and converts from Python’s weekday (0=Monday … 6=Sunday) via `our_weekday = (python_weekday + 1) % 7`.

| Day (Python weekday) | meme_selector internal (0=Sun) | Category        |
|----------------------|---------------------------------|-----------------|
| 0 (Monday)           | 1                               | work_life       |
| 1 (Tuesday)          | 2                               | health          |
| 2 (Wednesday)        | 3                               | housing         |
| 3 (Thursday)         | 4                               | transportation  |
| 4 (Friday)           | 5                               | relationships   |
| 5 (Saturday)         | 6                               | family          |
| 6 (Sunday)           | 0                               | faith           |

Source (meme_selector.py):

```python
DAY_CATEGORY_MAP = {
    0: 'faith',           # Sunday
    1: 'work_life',       # Monday
    2: 'health',          # Tuesday - Health/Working out
    3: 'housing',         # Wednesday - Housing
    4: 'transportation',  # Thursday - Transportation
    5: 'relationships',   # Friday - Relationships
    6: 'family'           # Saturday - Kids/Family
}
```

The day-theme seed script (`scripts/seed_meme_by_day.py`) uses **Python weekday** (0=Monday … 6=Sunday) and is aligned to this mapping so seeded memes match the intended day/category.

---

## Summary

- **No prior meme schema** in the repo defined **day_of_week** or **theme** on the `memes` table.
- **004 and the day-theme seed** are additive and do not conflict with any established meme schema.
- The **day → category** relationship is defined in **meme_selector.py** (`DAY_CATEGORY_MAP`); the seed script uses the same mapping (in Python weekday).
- The only pre-existing schema inconsistency is the **category** enum/CHECK differing between 001 vs meme_selector vs docs; that is unrelated to 004.
