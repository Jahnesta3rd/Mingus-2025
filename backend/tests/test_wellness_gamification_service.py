"""
Comprehensive tests for Wellness Gamification Service (StreakService, AchievementService).

Covers:
- Streak calculation (first check-in, continuation, break)
- Streak continuation (consecutive weeks)
- Streak break (missed week)
- Achievement unlocking (first_checkin, streak_4, etc.)
- Streak-at-risk detection
- calculate_streak_from_history
"""

import pytest
import sys
import os
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.services.wellness_gamification_service import (
    StreakService,
    AchievementService,
    ACHIEVEMENTS,
    _week_ending,
)


def _sunday(d: date) -> date:
    days_until_sunday = (6 - d.weekday()) % 7
    return d + timedelta(days=days_until_sunday)


# ---- Streak calculation (no DB) ----

def test_calculate_streak_from_history_empty():
    assert StreakService.calculate_streak_from_history([]) == 0


def test_calculate_streak_from_history_single():
    we = _sunday(date.today())
    checkins = [{"week_ending_date": we.isoformat()}]
    assert StreakService.calculate_streak_from_history(checkins) == 1


def test_calculate_streak_from_history_consecutive_weeks():
    we = _sunday(date.today())
    checkins = [
        {"week_ending_date": (we - timedelta(days=7 * i)).isoformat()}
        for i in range(4)
    ]
    assert StreakService.calculate_streak_from_history(checkins) == 4


def test_calculate_streak_from_history_break():
    we = _sunday(date.today())
    checkins = [
        {"week_ending_date": we.isoformat()},
        {"week_ending_date": (we - timedelta(days=14)).isoformat()},
        {"week_ending_date": (we - timedelta(days=21)).isoformat()},
    ]
    assert StreakService.calculate_streak_from_history(checkins) == 1


def test_calculate_streak_from_history_uses_week_ending_key():
    we = _sunday(date.today())
    checkins = [{"week_ending": we.isoformat()}]
    assert StreakService.calculate_streak_from_history(checkins) == 1


# ---- StreakService with mocked DB ----

@patch("backend.services.wellness_gamification_service._resolve_user_id")
def test_get_streak_info_unknown_user_returns_zeros(mock_resolve):
    mock_resolve.return_value = None
    info = StreakService.get_streak_info("unknown-user")
    assert info["current_streak"] == 0
    assert info["longest_streak"] == 0
    assert info["total_checkins"] == 0


@patch("backend.services.wellness_gamification_service.WellnessCheckinStreak")
@patch("backend.services.wellness_gamification_service._resolve_user_id")
def test_get_streak_info_with_row(mock_resolve, mock_streak_model):
    mock_resolve.return_value = 1
    row = MagicMock()
    row.current_streak = 3
    row.longest_streak = 5
    row.total_checkins = 10
    row.last_checkin_date = date(2025, 1, 19)
    mock_streak_model.query.filter_by.return_value.first.return_value = row
    info = StreakService.get_streak_info("user-1")
    assert info["current_streak"] == 3
    assert info["longest_streak"] == 5
    assert info["total_checkins"] == 10
    assert "days_until_deadline" in info


@patch("backend.services.wellness_gamification_service.WeeklyCheckin")
@patch("backend.services.wellness_gamification_service.WellnessCheckinStreak")
@patch("backend.services.wellness_gamification_service._resolve_user_id")
def test_is_streak_at_risk_zero_streak_returns_false(mock_resolve, mock_checkin, mock_streak):
    mock_resolve.return_value = 1
    row = MagicMock()
    row.current_streak = 0
    mock_streak.query.filter_by.return_value.first.return_value = row
    assert StreakService.is_streak_at_risk("user-1") is False


@patch("backend.services.wellness_gamification_service.WeeklyCheckin")
@patch("backend.services.wellness_gamification_service.WellnessCheckinStreak")
@patch("backend.services.wellness_gamification_service._resolve_user_id")
def test_is_streak_at_risk_completed_this_week_returns_false(mock_resolve, mock_checkin, mock_streak):
    mock_resolve.return_value = 1
    row = MagicMock()
    row.current_streak = 3
    mock_streak.query.filter_by.return_value.first.return_value = row
    mock_checkin.query.filter_by.return_value.filter.return_value.first.return_value = MagicMock()
    assert StreakService.is_streak_at_risk("user-1") is False


# ---- AchievementService (no DB for get_user_achievements / get_next) ----

def test_achievements_constant_has_required_keys():
    for key, meta in ACHIEVEMENTS.items():
        assert "name" in meta
        assert "description" in meta
        assert "icon" in meta


def test_get_user_achievements_unknown_user_returns_all_unlocked_false():
    with patch("backend.services.wellness_gamification_service._resolve_user_id", return_value=None):
        result = AchievementService.get_user_achievements("unknown")
    assert len(result) == len(ACHIEVEMENTS)
    for item in result:
        assert item["unlocked"] is False
        assert "key" in item
        assert "name" in item
        assert "description" in item
        assert "icon" in item


def test_check_achievements_first_checkin_unlocks():
    with patch("backend.services.wellness_gamification_service._resolve_user_id", return_value=1), \
         patch("backend.services.wellness_gamification_service.UserAchievement") as mock_ua, \
         patch("backend.services.wellness_gamification_service.AchievementService._unlocked_keys", return_value=set()), \
         patch("backend.services.wellness_gamification_service.AchievementService._unlock", side_effect=lambda uid, k: True if k == "first_checkin" else False):
        newly = AchievementService.check_achievements("user-1", {"overall_wellness_score": 50}, 0)
    assert "first_checkin" in newly


def test_check_achievements_streak_4_unlocks_at_4():
    with patch("backend.services.wellness_gamification_service._resolve_user_id", return_value=1), \
         patch("backend.services.wellness_gamification_service.AchievementService._unlocked_keys", return_value={"first_checkin"}), \
         patch("backend.services.wellness_gamification_service.AchievementService._unlock") as mock_unlock:
        mock_unlock.return_value = True
        newly = AchievementService.check_achievements("user-1", {}, 4)
    assert "streak_4" in newly


def test_get_next_achievements_returns_list():
    with patch("backend.services.wellness_gamification_service.StreakService.get_streak_info") as mock_info, \
         patch("backend.services.wellness_gamification_service.AchievementService._unlocked_keys", return_value=set()):
        mock_info.return_value = {"current_streak": 2, "total_checkins": 2}
        next_list = AchievementService.get_next_achievements("user-1")
    assert isinstance(next_list, list)
    for item in next_list:
        assert "key" in item
        assert "name" in item
        assert "message" in item


# ---- update_streak (with DB mock) ----

@patch("backend.services.wellness_gamification_service.db")
@patch("backend.services.wellness_gamification_service.WellnessCheckinStreak")
@patch("backend.services.wellness_gamification_service._resolve_user_id")
def test_update_streak_unknown_user_returns_zeros(mock_resolve, mock_streak, mock_db):
    mock_resolve.return_value = None
    result = StreakService.update_streak("unknown", date.today())
    assert result["current_streak"] == 0
    assert result["longest_streak"] == 0
    assert result["streak_increased"] is False
    assert result["new_record"] is False


@patch("backend.services.wellness_gamification_service.db")
@patch("backend.services.wellness_gamification_service.WellnessCheckinStreak")
@patch("backend.services.wellness_gamification_service._resolve_user_id")
def test_update_streak_first_checkin(mock_resolve, mock_streak, mock_db):
    mock_resolve.return_value = 1
    mock_streak.query.filter_by.return_value.first.return_value = None
    row = MagicMock()
    row.current_streak = 1
    row.longest_streak = 1
    row.total_checkins = 1
    mock_streak.return_value = row
    result = StreakService.update_streak("user-1", _sunday(date.today()))
    assert result["current_streak"] == 1
    assert result["longest_streak"] == 1
    assert result["streak_increased"] is True
    assert result["new_record"] is True
