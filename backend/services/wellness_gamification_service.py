#!/usr/bin/env python3
"""
Wellness Check-in Streak and Achievement Service

Streak tracking and gamification for weekly check-in engagement.
Uses WellnessCheckinStreak (weekly_checkin_streaks) and UserAchievement (user_achievements).
"""

import logging
from datetime import datetime, date, timedelta, timezone
from typing import Dict, List, Any, Optional

from backend.models.database import db
from backend.models.user_models import User
from backend.models.wellness import (
    WeeklyCheckin,
    WellnessCheckinStreak,
    UserAchievement,
)
from backend.services.wellness_score_service import WellnessScoreCalculator

logger = logging.getLogger(__name__)


def _week_ending(d: date) -> date:
    return WellnessScoreCalculator.get_week_ending_date(d)


def _resolve_user_id(user_id: str) -> Optional[int]:
    """Resolve string user_id (JWT/sub) to internal User.id."""
    user = User.query.filter_by(user_id=user_id).first()
    return user.id if user else None


# =============================================================================
# STREAK SERVICE
# =============================================================================

class StreakService:
    """
    Weekly check-in streak: update on submit, get info, at-risk check,
    and recalculate from history.
    """

    @staticmethod
    def update_streak(user_id: str, checkin_date: date) -> Dict[str, Any]:
        """
        Called after each check-in submission. checkin_date is the week-ending (Sunday).
        Returns current_streak, longest_streak, streak_increased, new_record.
        """
        uid = _resolve_user_id(user_id)
        if uid is None:
            return {
                'current_streak': 0,
                'longest_streak': 0,
                'streak_increased': False,
                'new_record': False,
            }
        week_ending = _week_ending(checkin_date)
        row = WellnessCheckinStreak.query.filter_by(user_id=uid).first()
        prev_longest = (row.longest_streak or 0) if row else 0
        prev_current = (row.current_streak or 0) if row else 0

        if row is None:
            row = WellnessCheckinStreak(
                user_id=uid,
                current_streak=1,
                longest_streak=1,
                last_checkin_date=week_ending,
                total_checkins=1,
            )
            db.session.add(row)
            streak_increased = True
            new_record = True
        else:
            row.total_checkins = (row.total_checkins or 0) + 1
            last = row.last_checkin_date
            if last is None:
                row.current_streak = 1
                streak_increased = True
            else:
                prev_sunday = last - timedelta(days=7)
                if week_ending == prev_sunday:
                    row.current_streak = (row.current_streak or 0) + 1
                    streak_increased = row.current_streak > prev_current
                else:
                    row.current_streak = 1
                    streak_increased = False
            row.longest_streak = max(row.longest_streak or 0, row.current_streak)
            row.last_checkin_date = week_ending
            new_record = (row.longest_streak or 0) > prev_longest
        db.session.flush()
        return {
            'current_streak': row.current_streak,
            'longest_streak': row.longest_streak,
            'streak_increased': streak_increased,
            'new_record': new_record,
        }

    @staticmethod
    def get_streak_info(user_id: str) -> Dict[str, Any]:
        """Return current streak info with days_until_deadline (next Sunday end of week)."""
        uid = _resolve_user_id(user_id)
        if uid is None:
            return {
                'current_streak': 0,
                'longest_streak': 0,
                'total_checkins': 0,
                'days_until_deadline': None,
                'last_checkin_date': None,
            }
        row = WellnessCheckinStreak.query.filter_by(user_id=uid).first()
        if not row:
            return {
                'current_streak': 0,
                'longest_streak': 0,
                'total_checkins': 0,
                'days_until_deadline': _days_until_week_end(),
                'last_checkin_date': None,
            }
        today = date.today()
        week_end = _week_ending(today)
        days_until = (week_end - today).days
        return {
            'current_streak': row.current_streak or 0,
            'longest_streak': row.longest_streak or 0,
            'total_checkins': row.total_checkins or 0,
            'days_until_deadline': days_until,
            'last_checkin_date': row.last_checkin_date.isoformat() if row.last_checkin_date else None,
        }

    @staticmethod
    def is_streak_at_risk(user_id: str) -> bool:
        """True if streak > 0 and less than 24 hours until week ends without check-in."""
        info = StreakService.get_streak_info(user_id)
        if (info['current_streak'] or 0) == 0:
            return False
        # Check if current week is already completed
        uid = _resolve_user_id(user_id)
        if uid is None:
            return False
        week_ending = _week_ending(date.today())
        completed = WeeklyCheckin.query.filter_by(
            user_id=uid, week_ending_date=week_ending
        ).filter(WeeklyCheckin.completed_at.isnot(None)).first()
        if completed:
            return False
        days = info.get('days_until_deadline')
        if days is None:
            return True
        return days <= 1  # within 1 day of Sunday = at risk

    @staticmethod
    def calculate_streak_from_history(checkins: List[Dict[str, Any]]) -> int:
        """
        Recalculate current streak from a list of check-ins (each with 'week_ending_date' or 'week_ending').
        Expects checkins sorted by week_ending descending (most recent first).
        """
        if not checkins:
            return 0
        week_dates = []
        for c in checkins:
            we = c.get('week_ending_date') or c.get('week_ending')
            if we is None:
                continue
            if isinstance(we, str):
                we = date.fromisoformat(we.split('T')[0])
            week_dates.append(we)
        if not week_dates:
            return 0
        week_dates = sorted(set(week_dates), reverse=True)
        streak = 1
        for i in range(1, len(week_dates)):
            if (week_dates[i - 1] - week_dates[i]).days == 7:
                streak += 1
            else:
                break
        return streak


def _days_until_week_end() -> int:
    """Days from today to the week-ending Sunday (inclusive)."""
    today = date.today()
    week_end = _week_ending(today)
    return (week_end - today).days


# =============================================================================
# ACHIEVEMENT SERVICE
# =============================================================================

ACHIEVEMENTS = {
    'first_checkin': {
        'name': 'Getting Started',
        'description': 'Complete your first check-in',
        'icon': '🌱',
    },
    'streak_4': {
        'name': 'Consistency Champion',
        'description': '4-week check-in streak',
        'icon': '🔥',
    },
    'streak_12': {
        'name': 'Quarterly Commitment',
        'description': '12-week check-in streak',
        'icon': '💎',
    },
    'streak_26': {
        'name': 'Half-Year Hero',
        'description': '26-week check-in streak',
        'icon': '🏆',
    },
    'perfect_wellness_75': {
        'name': 'Thriving',
        'description': 'Achieve 75+ wellness score',
        'icon': '⭐',
    },
    'meditation_streak_4': {
        'name': 'Mindful Month',
        'description': '4 weeks of 30+ min meditation',
        'icon': '🧘',
    },
    'exercise_5_days': {
        'name': 'Fitness Five',
        'description': 'Hit 5+ exercise days in a week',
        'icon': '💪',
    },
    'insight_unlocked': {
        'name': 'Pattern Finder',
        'description': 'Unlock your first wellness-finance insight',
        'icon': '🔍',
    },
}


class AchievementService:
    """Check and store wellness check-in achievements."""

    @staticmethod
    def _unlocked_keys(user_id: str) -> set:
        uid = _resolve_user_id(user_id)
        if uid is None:
            return set()
        rows = UserAchievement.query.filter_by(user_id=uid).all()
        return {r.achievement_key for r in rows}

    @staticmethod
    def _unlock(user_id: str, achievement_key: str) -> bool:
        uid = _resolve_user_id(user_id)
        if uid is None or achievement_key not in ACHIEVEMENTS:
            return False
        existing = UserAchievement.query.filter_by(
            user_id=uid, achievement_key=achievement_key
        ).first()
        if existing:
            return False
        db.session.add(UserAchievement(
            user_id=uid,
            achievement_key=achievement_key,
            unlocked_at=datetime.now(timezone.utc),
        ))
        db.session.flush()
        return True

    @staticmethod
    def check_achievements(
        user_id: str, checkin: Dict[str, Any], streak: int
    ) -> List[str]:
        """
        Check all achievement conditions after check-in. Unlock and persist new ones.
        checkin: dict with keys like overall_wellness_score, exercise_days, meditation_minutes, etc.
        Returns list of newly unlocked achievement keys.
        """
        newly = []
        unlocked = AchievementService._unlocked_keys(user_id)

        # first_checkin
        if 'first_checkin' not in unlocked:
            if AchievementService._unlock(user_id, 'first_checkin'):
                newly.append('first_checkin')

        # streak milestones
        for key, threshold in [('streak_4', 4), ('streak_12', 12), ('streak_26', 26)]:
            if key not in unlocked and streak >= threshold:
                if AchievementService._unlock(user_id, key):
                    newly.append(key)

        # perfect_wellness_75
        overall = checkin.get('overall_wellness_score')
        if overall is not None:
            try:
                score = float(overall)
                if 'perfect_wellness_75' not in unlocked and score >= 75:
                    if AchievementService._unlock(user_id, 'perfect_wellness_75'):
                        newly.append('perfect_wellness_75')
            except (TypeError, ValueError):
                pass

        # meditation_streak_4: 4 weeks of 30+ min — requires history; simplified: this week 30+
        med = checkin.get('meditation_minutes')
        if med is not None and int(med) >= 30 and 'meditation_streak_4' not in unlocked:
            uid = _resolve_user_id(user_id)
            if uid:
                recent = (
                    WeeklyCheckin.query.filter_by(user_id=uid)
                    .order_by(WeeklyCheckin.week_ending_date.desc())
                    .limit(4)
                    .all()
                )
                if len(recent) >= 4 and all(
                    (r.meditation_minutes or 0) >= 30 for r in recent
                ):
                    if AchievementService._unlock(user_id, 'meditation_streak_4'):
                        newly.append('meditation_streak_4')

        # exercise_5_days
        ex_days = checkin.get('exercise_days')
        if ex_days is not None and 'exercise_5_days' not in unlocked and int(ex_days) >= 5:
            if AchievementService._unlock(user_id, 'exercise_5_days'):
                newly.append('exercise_5_days')

        # insight_unlocked: unlocked when user has 4+ weeks and insights exist (caller can pass or we check)
        if checkin.get('insight_unlocked') and 'insight_unlocked' not in unlocked:
            if AchievementService._unlock(user_id, 'insight_unlocked'):
                newly.append('insight_unlocked')

        return newly

    @staticmethod
    def get_user_achievements(user_id: str) -> List[Dict[str, Any]]:
        """Return all achievements with unlocked status and unlocked_at for user."""
        unlocked_map = {}
        uid = _resolve_user_id(user_id)
        if uid is not None:
            for r in UserAchievement.query.filter_by(user_id=uid).all():
                unlocked_map[r.achievement_key] = r.unlocked_at.isoformat() if r.unlocked_at else None

        result = []
        for key, meta in ACHIEVEMENTS.items():
            result.append({
                'key': key,
                'name': meta['name'],
                'description': meta['description'],
                'icon': meta['icon'],
                'unlocked': key in unlocked_map,
                'unlocked_at': unlocked_map.get(key),
            })
        return result

    @staticmethod
    def get_next_achievements(user_id: str) -> List[Dict[str, Any]]:
        """Achievements user is close to unlocking, with progress message."""
        info = StreakService.get_streak_info(user_id)
        current_streak = info.get('current_streak') or 0
        total = info.get('total_checkins') or 0
        unlocked = AchievementService._unlocked_keys(user_id)
        next_list = []

        for key, threshold in [('streak_4', 4), ('streak_12', 12), ('streak_26', 26)]:
            if key in unlocked:
                continue
            meta = ACHIEVEMENTS.get(key)
            if not meta:
                continue
            need = threshold - current_streak
            if need <= 0:
                next_list.append({
                    'key': key,
                    'name': meta['name'],
                    'description': meta['description'],
                    'icon': meta['icon'],
                    'message': f"Unlock now! You've hit a {current_streak}-week streak.",
                })
            elif need == 1:
                next_list.append({
                    'key': key,
                    'name': meta['name'],
                    'description': meta['description'],
                    'icon': meta['icon'],
                    'message': f"1 more week to unlock '{meta['name']}'!",
                })
            elif need <= 3:
                next_list.append({
                    'key': key,
                    'name': meta['name'],
                    'description': meta['description'],
                    'icon': meta['icon'],
                    'message': f"{need} more weeks to unlock '{meta['name']}'!",
                })

        if 'first_checkin' not in unlocked and total == 0:
            next_list.append({
                'key': 'first_checkin',
                'name': ACHIEVEMENTS['first_checkin']['name'],
                'description': ACHIEVEMENTS['first_checkin']['description'],
                'icon': ACHIEVEMENTS['first_checkin']['icon'],
                'message': "Complete your first check-in to unlock!",
            })

        return next_list[:5]  # cap 5 next achievements
