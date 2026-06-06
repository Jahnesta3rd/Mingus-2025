"""Backfill users.user_profiles emails truncated by DOMPurify paste bug (Tier 1 #83).

Emails pasted with a stray `<` before the final `m` (e.g. `...@gmail.co<m`) were run
through DOMPurify, producing `...@gmail.co`. Restore by appending `m` where the
address ends with `@gmail.co` but should be `@gmail.com`.

Revision ID: 036_backfill_gmail_co_truncation_bug
Revises: 855fe9836baf
Create Date: 2026-05-01
"""

from alembic import op

revision = "036_backfill_gmail_co_truncation_bug"
down_revision = "855fe9836baf"
branch_labels = None
depends_on = None


def upgrade():
    # Suffix-only match: valid ...@gmail.com addresses must not match @gmail.co$
    op.execute(
        r"""
        UPDATE user_profiles
        SET email = email || 'm'
        WHERE email ~ '@gmail\.co$';
        """
    )
    op.execute(
        r"""
        UPDATE users
        SET email = email || 'm'
        WHERE email ~ '@gmail\.co$';
        """
    )


def downgrade():
    # Not safely reversible (would strip `m` from legitimate ...@gmail.co if any)
    pass
