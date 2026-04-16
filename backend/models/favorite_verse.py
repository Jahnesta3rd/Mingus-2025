#!/usr/bin/env python3
"""Favorite verses saved from the Faith Card feature."""

from __future__ import annotations

from datetime import datetime

from .database import db


class FavoriteVerse(db.Model):
    __tablename__ = "favorite_verses"
    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "verse_reference",
            name="uq_favorite_verses_user_id_verse_reference",
        ),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    verse_reference = db.Column(db.String(100), nullable=False)
    verse_text = db.Column(db.Text, nullable=False)
    bridge_sentence = db.Column(db.Text, nullable=False)
    balance_status_at_save = db.Column(db.String(20), nullable=True)
    goal_at_save = db.Column(db.String(255), nullable=True)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<FavoriteVerse {self.user_id} {self.verse_reference!r}>"
