#!/usr/bin/env python3
"""User todo / action items (e.g. from weekly check-in wisdom calls)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Index

from .database import db


class Todo(db.Model):
    """One actionable todo item owned by a user."""

    __tablename__ = "todos"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending")
    priority = db.Column(db.String(20), nullable=False, default="medium")
    domain = db.Column(db.String(50), nullable=True)
    week_created = db.Column(db.Integer, nullable=True, index=True)
    due_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", backref=db.backref("todos", lazy="dynamic"))

    __table_args__ = (
        Index("ix_todos_user_id_status", "user_id", "status"),
        Index("ix_todos_user_id_week_created", "user_id", "week_created"),
    )

    def __repr__(self) -> str:
        return (
            f"<Todo id={self.id!r} user_id={self.user_id!r} "
            f"status={self.status!r} title={self.title!r}>"
        )
