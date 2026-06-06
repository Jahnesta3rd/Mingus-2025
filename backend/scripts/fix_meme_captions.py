#!/usr/bin/env python3
"""Replace filename-style meme captions with readable display text."""

from __future__ import annotations

import os
import re
import sys

import psycopg2
import psycopg2.extras

OVERRIDES = {
    # children
    'Children 003 shoe-shopping': 'Shoe shopping with the kids',
    'Children 005 not-to-bring-it-home': "Don't bring it home",
    'Children 006 kevin-claiborne-school-supplies': 'School supply season hits different',
    'Children 007 patty-cake': 'Patty cake energy',
    'Children 010 crazy-kids-like-me': 'Crazy kids like me',
    'Children 011 baller-shotcaller': 'Baller shot caller',
    'Children 011 terrance-crawford': 'Terrance Crawford vibes',
    'Children 012 god-kids': 'God kids',
    'Children 013 mom-death-stare': 'The mom death stare',
    'Children 014 missing-Ben': 'Missing Ben',
    'Children  001 hair-done': 'Hair done right',
    'Children  002 daddy-girl': "Daddy's girl",
    'Children  004 kevin-claiborne-choc-cookie': 'Chocolate cookie energy',
    'Children  008 tutor-for-kids': 'Tutor season',
    'Children  009 ipad-issues': 'iPad issues again',
    # faith
    'Faith 001 j-cole-never-satisfied': 'Never satisfied — J. Cole',
    'Faith 002 katt-williams-confidence-in-God': 'Confidence in God — Katt Williams',
    'Faith 003 lecrae-success-quote': 'Success — Lecrae',
    'Faith 004 rev-ike': 'Rev. Ike wisdom',
}


def slug_to_caption(slug: str) -> str:
    """Convert a filename slug to a readable display caption."""
    cleaned = re.sub(r'^[A-Za-z]+\s+\d+\s+', '', slug).strip()
    cleaned = cleaned.replace('-', ' ').replace('_', ' ')
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned.title() if cleaned else slug


def main() -> None:
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print('DATABASE_URL is required', file=sys.stderr)
        sys.exit(1)

    conn = psycopg2.connect(database_url)
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, category, caption FROM memes
        WHERE caption ~ '^[A-Za-z]+ [0-9]{3} '
           OR caption ~ '_-'
        ORDER BY id
        """
    )
    rows = cur.fetchall()

    updated = 0
    for row in rows:
        raw = row['caption']
        new_caption = OVERRIDES.get(raw) or slug_to_caption(raw)
        if new_caption != raw:
            cur.execute(
                'UPDATE memes SET caption = %s WHERE id = %s',
                (new_caption, row['id']),
            )
            updated += 1
            print(
                f"  [{row['category']}] id={row['id']}: {raw!r} → {new_caption!r}"
            )

    conn.commit()
    conn.close()
    print(f'\nDone. {updated} captions updated.')


if __name__ == '__main__':
    main()
