# Meme category mismatch: recommended approach (6 vs 7 categories)

## The mismatch

| Source | Count | Categories |
|--------|--------|------------|
| **001 / meme_database_schema / meme_admin** | 6 | faith, work_life, **friendships**, **children**, relationships, **going_out** |
| **meme_selector** (day→category) | 7 | faith, work_life, **health**, **housing**, **transportation**, relationships, **family** |

So we have two different category sets. The vibe-check API and day-theme seed need to work with the same list as the day-of-week logic.

---

## Recommended option: **unify on the 7-category set (meme_selector)**

**Use the 7 categories from `meme_selector.py` as the single canonical set**, and treat the old 6 as legacy.

### Why 7 (meme_selector) instead of 6 (001)

1. **Day-of-week logic is already defined there** — Mon=work_life, Tue=health, Wed=housing, Thu=transportation, Fri=relationships, Sat=family, Sun=faith. That matches the product idea of one theme per day.
2. **Richer themes** — health, housing, transportation, and family are distinct; folding them into the 6 would lose that.
3. **One place to look** — All code (migrations, seed, meme_selector, future features) can assume the same 7 (+ optional legacy `going_out` for existing data).

### Mapping from old 6 to the canonical 7

| Old (6)   | New (7)       | Note |
|-----------|---------------|------|
| faith     | faith         | same |
| work_life | work_life     | same |
| friendships | relationships | merge into relationships |
| children  | family        | same intent |
| relationships | relationships | same |
| going_out | *(keep as 8th for legacy)* or relationships | optional |

So the **canonical list** is the 7 from meme_selector. For backward compatibility with existing rows, the schema can allow an **8th** value, **going_out**, and not use it for new content.

---

## Implementation options

### Option A — **Expand schema to 8 allowed categories (recommended)**

- **Allowed categories:** faith, work_life, health, housing, transportation, relationships, family, going_out.
- **New content and day-theme seed:** use only the 7 (meme_selector set).
- **Existing rows:** keep as-is; map only when convenient (e.g. friendships→relationships, children→family) so day logic and reporting are consistent.
- **How:** run **`migrations/005_unify_meme_categories.sql`**. It recreates `memes` with a CHECK that allows all 8 categories and copies existing rows (friendships→relationships, children→family; going_out unchanged). Run after 001; 004 can be run before or after 005.

**Pros:** One schema, works with existing DBs, day-theme seed and meme_selector align.  
**Cons:** One-time migration required.

### Option B — **Keep 6 categories and map days to them**

- Leave 001 schema as-is (6 categories).
- In meme_selector (or a shared mapping), map the 7 days onto 6 categories (e.g. two days share one category).
- Day-theme seed uses only the 6 categories.

**Pros:** No migration.  
**Cons:** Two days share a category; product intent (one theme per day) is diluted; meme_selector’s 7-category logic and DB CHECK stay out of sync.

### Option C — **Drop CHECK and enforce in app**

- Schema: `category TEXT NOT NULL` (no CHECK).
- App and seed script only use the 7 canonical values; legacy data can keep old strings.

**Pros:** Flexible, no SQLite migration for CHECK.  
**Cons:** Invalid categories only surface at runtime; no DB-level guarantee.

---

## Recommendation summary

- **Best option:** **Option A** — expand to **8 allowed categories** (7 canonical + going_out), migrate existing data from the old 6 into that set, and use the **7-category set** everywhere for day-of-week and new content.
- **Canonical 7:** faith, work_life, health, housing, transportation, relationships, family.
- **Legacy:** going_out remains allowed; friendships→relationships, children→family in a one-time migration.
- **Single source of truth:** `meme_selector.DAY_CATEGORY_MAP` (and docs) define day→category; migrations and seed script use the same 7 (plus optional going_out in schema only).

After applying the migration and updating any remaining references to the old 6 categories, both “6-category” and “7-category” concerns are resolved with one schema and one convention.

---

## Applying Option A (migration 005)

```bash
# From repo root, with mingus_memes.db present (e.g. after 001 and optionally 004)
sqlite3 mingus_memes.db < migrations/005_unify_meme_categories.sql
```

Then use the **7 canonical categories** for day-theme seed and meme_selector; **going_out** remains allowed in the schema for legacy rows only.
