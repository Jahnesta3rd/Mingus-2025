#!/usr/bin/env python3
"""
Populate the Mingus Postgres memes table from /var/www/mingus/memes_source/.
Copies files to /var/www/mingus/static/memes/<folder>/<file> and inserts rows
with image_url = /static/memes/<folder>/<file>, matching the existing schema.

Safe to re-run: uses ON CONFLICT (image_url) DO NOTHING.
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

import psycopg2

REPO_ROOT = Path('/var/www/mingus')
SOURCE_DIR = REPO_ROOT / 'memes_source'
STATIC_DIR = REPO_ROOT / 'static' / 'memes'

IMAGE_EXTS = {'.gif', '.png', '.jpg', '.jpeg', '.webp'}
VIDEO_EXTS = {'.mp4', '.webm', '.mov'}
AUDIO_EXTS = {'.mp3', '.wav', '.m4a', '.aac'}
ALLOWED_EXTS = IMAGE_EXTS | VIDEO_EXTS | AUDIO_EXTS

# Folder -> (day_of_week 0=Mon..6=Sun, category)
# saturday_mixed maps to 'general' to match existing row 7 in the DB.
FOLDER_MAP = {
    'sunday_faith':           (6, 'faith'),
    'monday_work_life':       (0, 'work_life'),
    'tuesday_friendships':    (1, 'friendships'),
    'wednesday_children':     (2, 'children'),
    'thursday_relationships': (3, 'relationships'),
    'friday_going_out':       (4, 'going_out'),
    'saturday_mixed':         (5, 'general'),
}


def media_type(ext: str) -> str:
    if ext in IMAGE_EXTS: return 'image'
    if ext in VIDEO_EXTS: return 'video'
    if ext in AUDIO_EXTS: return 'audio'
    return 'image'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--dry-run', action='store_true', help='Preview only, no changes')
    p.add_argument('--no-copy', action='store_true', help='Skip file copy, only insert DB rows')
    args = p.parse_args()

    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        sys.exit('ERROR: DATABASE_URL not set. Run: set -a; source /var/www/mingus/.env; set +a')

    if not SOURCE_DIR.exists():
        sys.exit(f'ERROR: source dir not found: {SOURCE_DIR}')

    # Collect files
    files_to_process = []
    for folder_name, (dow, category) in FOLDER_MAP.items():
        folder = SOURCE_DIR / folder_name
        if not folder.is_dir():
            print(f'  skip (no folder): {folder_name}')
            continue
        for f in sorted(folder.iterdir()):
            if not f.is_file():
                continue
            ext = f.suffix.lower()
            if ext not in ALLOWED_EXTS:
                print(f'  skip (ext {ext}): {f.name}')
                continue
            files_to_process.append((f, folder_name, dow, category, ext))

    print(f'Found {len(files_to_process)} candidate files')

    if args.dry_run:
        print('--- DRY RUN: showing what would happen ---')
        for src, folder_name, dow, category, ext in files_to_process[:10]:
            url = f'/static/memes/{folder_name}/{src.name}'
            print(f'  WOULD INSERT: {url}  category={category}  dow={dow}  media={media_type(ext)}')
        if len(files_to_process) > 10:
            print(f'  ... and {len(files_to_process)-10} more')
        return

    # Copy + insert
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    inserted = skipped_existing = copied = copy_failed = 0

    if not args.no_copy:
        STATIC_DIR.mkdir(parents=True, exist_ok=True)

    for src, folder_name, dow, category, ext in files_to_process:
        url = f'/static/memes/{folder_name}/{src.name}'
        mtype = media_type(ext)

        # Copy file
        if not args.no_copy:
            dest_dir = STATIC_DIR / folder_name
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / src.name
            try:
                if not dest.exists() or dest.stat().st_size != src.stat().st_size:
                    shutil.copy2(src, dest)
                    copied += 1
            except Exception as e:
                print(f'  COPY FAILED: {src.name}: {e}')
                copy_failed += 1
                continue

        # Insert row
        cur.execute(
            '''
            INSERT INTO memes (image_url, category, caption, alt_text, day_of_week, media_type, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, 1)
            ON CONFLICT (image_url) DO NOTHING
            RETURNING id
            ''',
            (url, category, src.stem.replace('_', ' '), f'{category} meme', dow, mtype),
        )
        result = cur.fetchone()
        if result:
            inserted += 1
        else:
            skipped_existing += 1

    conn.commit()
    cur.close()
    conn.close()

    print()
    print('=== Summary ===')
    print(f'  Files copied:     {copied}')
    print(f'  Copy failures:    {copy_failed}')
    print(f'  Rows inserted:    {inserted}')
    print(f'  Rows skipped (already in DB): {skipped_existing}')


if __name__ == '__main__':
    main()
