#!/usr/bin/env python3
"""
Populate the meme database from a directory of GIF/PNG files, optionally in subfolders.

Usage:
  python3 scripts/populate_memes_from_files.py path/to/memes_source
  python3 scripts/populate_memes_from_files.py path/to/memes_source --manifest manifest.csv

- Recursively finds image, video, and audio files under source_dir; subfolders are preserved under static/memes/.
- Copies files into static/memes/<subfolder>/<filename> so image_url = /memes/<subfolder>/<filename>.
- Infers day_of_week and category from folder name when using the recommended layout (e.g. sunday_faith/, monday_work_life/).
- Sets media_type (image, video, audio) from file extension so the vibe-check page can render correctly.
- Optional manifest CSV columns: filename (or path), category, caption, alt_text, day_of_week, theme, media_type.
- Uses MINGUS_MEME_DB_PATH if set. Ensures memes table exists (run 001/004/005/006 first if needed).
"""

import argparse
import csv
import os
import shutil
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
os.chdir(REPO_ROOT)

DB_PATH = os.environ.get("MINGUS_MEME_DB_PATH", str(REPO_ROOT / "mingus_memes.db"))
STATIC_MEMES = REPO_ROOT / "static" / "memes"
IMAGE_EXTENSIONS = {".gif", ".png", ".jpg", ".jpeg", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".ogg"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a", ".aac"}
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | AUDIO_EXTENSIONS
# Categories allowed in folder names and manifest; map to DB (005 allows 8)
VALID_CATEGORIES = [
    "faith", "work_life", "health", "housing",
    "transportation", "relationships", "family", "going_out",
    "friendships", "children",
]
# Map to schema after 005: friendships -> relationships, children -> family
CATEGORY_TO_DB = {
    "friendships": "relationships",
    "children": "family",
}
for c in ["faith", "work_life", "health", "housing", "transportation", "relationships", "family", "going_out"]:
    CATEGORY_TO_DB.setdefault(c, c)
DAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

# Vibe-check day themes: folder name (lowercase) -> (day_of_week 0=Mon..6=Sun, category)
FOLDER_TO_DAY_CATEGORY = {
    "sunday_faith": (6, "faith"),
    "monday_work_life": (0, "work_life"),
    "tuesday_friendships": (1, "friendships"),
    "wednesday_children": (2, "children"),
    "thursday_relationships": (3, "relationships"),
    "friday_going_out": (4, "going_out"),
    "saturday_mixed": (5, "work_life"),
    # Allow short names too
    "faith": (6, "faith"),
    "work_life": (0, "work_life"),
    "friendships": (1, "friendships"),
    "children": (2, "children"),
    "relationships": (3, "relationships"),
    "going_out": (4, "going_out"),
    "mixed": (5, "work_life"),
}


def ensure_static_memes():
    STATIC_MEMES.mkdir(parents=True, exist_ok=True)
    return STATIC_MEMES


def ensure_memes_table(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memes'")
    if cursor.fetchone():
        return
    schema_001 = REPO_ROOT / "migrations" / "001_initial_meme_schema.sql"
    if schema_001.exists():
        conn.executescript(schema_001.read_text())
        conn.commit()
    else:
        raise SystemExit("memes table missing; run migrations/001_initial_meme_schema.sql first")


def ensure_columns(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(memes)")
    cols = {row[1] for row in cursor.fetchall()}
    if "day_of_week" not in cols:
        cursor.execute("ALTER TABLE memes ADD COLUMN day_of_week INTEGER")
    if "theme" not in cols:
        cursor.execute("ALTER TABLE memes ADD COLUMN theme TEXT")
    if "media_type" not in cols:
        cursor.execute("ALTER TABLE memes ADD COLUMN media_type TEXT DEFAULT 'image'")
    conn.commit()


def media_type_from_path(path: Path) -> str:
    """Return 'image', 'video', or 'audio' from file extension."""
    ext = path.suffix.lower()
    if ext in VIDEO_EXTENSIONS:
        return "video"
    if ext in AUDIO_EXTENSIONS:
        return "audio"
    return "image"


def load_manifest(path: Path) -> dict:
    """Return dict mapping path or filename -> {category, caption, alt_text, day_of_week, theme}."""
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fn = (row.get("filename") or row.get("path") or "").strip().replace("\\", "/")
            if not fn:
                continue
            day = row.get("day_of_week", "").strip()
            try:
                day_int = int(day) if day else None
            except ValueError:
                day_int = None
            meta = {
                "category": (row.get("category") or "work_life").strip(),
                "caption": (row.get("caption") or fn).strip(),
                "alt_text": (row.get("alt_text") or fn).strip(),
                "day_of_week": day_int,
                "theme": (row.get("theme") or "").strip() or None,
            "media_type": (row.get("media_type") or "").strip().lower() or None,
            }
            out[fn] = meta
            if "/" in fn:
                out[Path(fn).name] = meta
    return out


def infer_from_folder(folder_name: str) -> tuple:
    """Return (day_of_week, category) from folder name, or (None, 'work_life') if unknown."""
    key = folder_name.lower().replace("-", "_")
    if key in FOLDER_TO_DAY_CATEGORY:
        return FOLDER_TO_DAY_CATEGORY[key]
    return (None, "work_life")


def infer_from_filename(filename: str) -> dict:
    base = Path(filename).stem.lower()
    category = "work_life"
    day_of_week = None
    for i, day in enumerate(DAY_NAMES):
        if day in base:
            day_of_week = i
            break
    if "faith" in base or "sunday" in base:
        category = "faith"
    elif "health" in base or "tuesday" in base:
        category = "health"
    elif "housing" in base or "wednesday" in base:
        category = "housing"
    elif "transport" in base or "thursday" in base:
        category = "transportation"
    elif "relationship" in base or "friday" in base:
        category = "relationships"
    elif "family" in base or "saturday" in base:
        category = "family"
    elif "friendship" in base:
        category = "friendships"
    elif "children" in base or "child" in base:
        category = "children"
    elif "going_out" in base or "going out" in base:
        category = "going_out"
    return {
        "category": category,
        "caption": f"Meme: {base.replace('_', ' ')}",
        "alt_text": base.replace("_", " "),
        "day_of_week": day_of_week,
        "theme": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Populate meme DB from GIF/PNG directory")
    parser.add_argument("source_dir", type=Path, help="Directory containing .gif/.png files")
    parser.add_argument("--manifest", "-m", type=Path, help="CSV: filename, category, caption, alt_text, day_of_week, theme")
    parser.add_argument("--copy", action="store_true", default=True, help="Copy files (default)")
    parser.add_argument("--no-copy", action="store_false", dest="copy", help="Do not copy; only insert DB rows (image_url still /memes/<name>)")
    args = parser.parse_args()

    source = args.source_dir.resolve()
    if not source.is_dir():
        print(f"Not a directory: {source}", file=sys.stderr)
        sys.exit(1)

    manifest = {}
    if args.manifest and args.manifest.exists():
        manifest = load_manifest(args.manifest)
        print(f"Loaded manifest: {args.manifest} ({len(manifest)} rows)")

    ensure_static_memes()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    ensure_memes_table(conn)
    ensure_columns(conn)

    cursor = conn.cursor()
    inserted = 0
    skipped = 0

    # Collect all image files recursively (preserve subfolders)
    files = []
    for path in source.rglob("*"):
        if path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS:
            try:
                rel = path.relative_to(source)
            except ValueError:
                continue
            files.append((path, rel))

    for path, rel in sorted(files, key=lambda x: str(x[1]).replace("\\", "/")):
        rel_str = str(rel).replace("\\", "/")
        filename = path.name
        meta = manifest.get(rel_str) or manifest.get(filename) or infer_from_filename(filename)
        day_of_week = meta.get("day_of_week")
        category = meta["category"]
        # Infer day and category from first subfolder when using recommended layout
        if len(rel.parts) > 1:
            day_infer, cat_infer = infer_from_folder(rel.parts[0])
            if day_infer is not None:
                day_of_week = day_infer
            category = cat_infer
        if category not in VALID_CATEGORIES:
            category = "work_life"
        category_db = CATEGORY_TO_DB.get(category, "work_life")
        caption = meta["caption"] or filename
        alt_text = meta["alt_text"] or filename
        theme = meta.get("theme")
        media_type = meta.get("media_type") or media_type_from_path(path)
        if media_type not in ("image", "video", "audio"):
            media_type = "image"

        dest = STATIC_MEMES / rel
        if args.copy:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if path.resolve() != dest.resolve():
                shutil.copy2(path, dest)

        image_url = f"/memes/{rel_str}"

        try:
            cursor.execute(
                """
                INSERT INTO memes (image_url, category, caption, alt_text, is_active, day_of_week, theme, media_type, created_at, updated_at)
                VALUES (?, ?, ?, ?, 1, ?, ?, ?, datetime('now'), datetime('now'))
                """,
                (image_url, category_db, caption, alt_text, day_of_week, theme, media_type),
            )
            inserted += 1
        except sqlite3.IntegrityError as e:
            print(f"Skipped {rel_str}: {e}", file=sys.stderr)
            skipped += 1

    conn.commit()
    conn.close()
    print(f"Done. Inserted {inserted} memes into {DB_PATH}. Skipped {skipped}.")
    print(f"Files in: {STATIC_MEMES} (subfolders preserved). image_url format: /memes/<path>")


if __name__ == "__main__":
    main()
