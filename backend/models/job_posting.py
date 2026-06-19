#!/usr/bin/env python3
"""Curated job postings for Mingus recommendation engine (#113 Phase A2)."""

from datetime import datetime

from sqlalchemy import CheckConstraint

from .database import db

_CAREER_FIELD_CHECK = (
    "career_field IN ("
    "'Technology', "
    "'Healthcare (Clinical)', "
    "'Healthcare (Admin/Ops)', "
    "'Finance & Accounting', "
    "'Legal', "
    "'Marketing & Communications', "
    "'Sales', "
    "'Education & Training', "
    "'Engineering (Civil/Mech/Ind)', "
    "'Creative & Design', "
    "'Operations & Supply Chain', "
    "'Human Resources', "
    "'Real Estate', "
    "'Social Services & Nonprofit', "
    "'Government & Public Policy', "
    "'Hospitality & Food Service', "
    "'Retail & Consumer', "
    "'Construction & Trades', "
    "'Media & Journalism', "
    "'Science & Research', "
    "'Military / Veterans', "
    "'Self-Employed / Entrepreneurship'"
    ")"
)


class JobPosting(db.Model):
    """Seeded and live job posting row for recommendation matching."""

    __tablename__ = "job_postings"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    career_field = db.Column(db.String(100), nullable=False)
    msa_code = db.Column(db.String(20), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(2), nullable=False)
    salary_min = db.Column(db.Integer, nullable=False)
    salary_max = db.Column(db.Integer, nullable=False)
    seniority_level = db.Column(db.String(20), nullable=False)
    is_management = db.Column(db.Boolean, nullable=False, default=False)
    advancement_trajectory = db.Column(db.String(300), nullable=False)
    url = db.Column(db.Text, nullable=True)
    source = db.Column(db.String(50), nullable=False, default="seed_2026")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint(_CAREER_FIELD_CHECK, name="ck_job_postings_career_field"),
        CheckConstraint(
            "seniority_level IN ('entry', 'mid', 'senior', 'director')",
            name="ck_job_postings_seniority_level",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<JobPosting id={self.id} title={self.title!r} "
            f"field={self.career_field!r} msa={self.msa_code!r}>"
        )
