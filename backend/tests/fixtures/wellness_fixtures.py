"""
Reusable test data for Weekly Check-in System tests.

Sample check-ins for 4, 8, 12 weeks; sample expenses with mood tags; sample user states.
"""

from datetime import date, timedelta
from typing import Dict, Any, List

# Week-ending dates (Sundays) for building history
def week_ending_dates(count: int, end_date: date) -> List[date]:
    """Return `count` week-ending (Sunday) dates going backward from `end_date`."""
    we = end_date
    # If end_date is not Sunday, move to that week's Sunday
    days_until_sunday = (6 - we.weekday()) % 7
    we = we + timedelta(days=days_until_sunday)
    out = []
    for _ in range(count):
        out.append(we)
        we = we - timedelta(days=7)
    return out


def base_checkin(
    exercise_days: int = 3,
    exercise_intensity: str = "moderate",
    sleep_quality: int = 6,
    meditation_minutes: int = 15,
    stress_level: int = 5,
    overall_mood: int = 6,
    relationship_satisfaction: int = 7,
    social_interactions: int = 5,
    financial_stress: int = 4,
    spending_control: int = 6,
    groceries_estimate: float = 120.0,
    dining_estimate: float = 60.0,
    entertainment_estimate: float = 40.0,
    shopping_estimate: float = 50.0,
    transport_estimate: float = 30.0,
    utilities_estimate: float = 80.0,
    other_estimate: float = 20.0,
    impulse_spending: float = 0.0,
    stress_spending: float = 0.0,
    celebration_spending: float = 0.0,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Build a single check-in dict with defaults; override any field via kwargs."""
    d: Dict[str, Any] = {
        "exercise_days": exercise_days,
        "exercise_intensity": exercise_intensity,
        "sleep_quality": sleep_quality,
        "meditation_minutes": meditation_minutes,
        "stress_level": stress_level,
        "overall_mood": overall_mood,
        "relationship_satisfaction": relationship_satisfaction,
        "social_interactions": social_interactions,
        "financial_stress": financial_stress,
        "spending_control": spending_control,
        "groceries_estimate": groceries_estimate,
        "dining_estimate": dining_estimate,
        "entertainment_estimate": entertainment_estimate,
        "shopping_estimate": shopping_estimate,
        "transport_estimate": transport_estimate,
        "utilities_estimate": utilities_estimate,
        "other_estimate": other_estimate,
        "impulse_spending": impulse_spending,
        "stress_spending": stress_spending,
        "celebration_spending": celebration_spending,
    }
    d.update(kwargs)
    return d


def checkins_4_weeks(end_date: date) -> List[Dict[str, Any]]:
    """Sample check-ins for 4 weeks (min for insights)."""
    weeks = week_ending_dates(4, end_date)
    return [
        base_checkin(week_ending_date=we, stress_level=5 + (i % 2), impulse_spending=20.0 * i)
        for i, we in enumerate(weeks)
    ]


def checkins_8_weeks(end_date: date) -> List[Dict[str, Any]]:
    """Sample check-ins for 8 weeks."""
    weeks = week_ending_dates(8, end_date)
    return [
        base_checkin(
            week_ending_date=we,
            exercise_days=3 + (i % 4),
            stress_level=4 + (i % 4),
            meditation_minutes=10 + i * 5,
            impulse_spending=float(15 * (i % 3)),
        )
        for i, we in enumerate(weeks)
    ]


def checkins_12_weeks(end_date: date) -> List[Dict[str, Any]]:
    """Sample check-ins for 12 weeks (quarterly)."""
    weeks = week_ending_dates(12, end_date)
    return [
        base_checkin(
            week_ending_date=we,
            exercise_days=min(7, 2 + (i % 6)),
            sleep_quality=5 + (i % 4),
            stress_level=3 + (i % 5),
            overall_mood=5 + (i % 4),
            impulse_spending=float(10 * (i % 4)),
            stress_spending=float(25 * (i % 2)),
        )
        for i, we in enumerate(weeks)
    ]


def checkin_zero_values() -> Dict[str, Any]:
    """Check-in with minimal/zero values for edge-case testing."""
    return base_checkin(
        exercise_days=0,
        sleep_quality=1,
        meditation_minutes=0,
        stress_level=10,
        overall_mood=1,
        relationship_satisfaction=1,
        social_interactions=0,
        financial_stress=10,
        spending_control=1,
        groceries_estimate=0,
        dining_estimate=0,
        entertainment_estimate=0,
        shopping_estimate=0,
        transport_estimate=0,
        utilities_estimate=0,
        other_estimate=0,
        impulse_spending=0,
        stress_spending=0,
    )


def checkin_max_values() -> Dict[str, Any]:
    """Check-in with maximum values for edge-case testing."""
    return base_checkin(
        exercise_days=7,
        exercise_intensity="intense",
        sleep_quality=10,
        meditation_minutes=60,
        stress_level=1,
        overall_mood=10,
        relationship_satisfaction=10,
        social_interactions=10,
        financial_stress=1,
        spending_control=10,
        groceries_estimate=200,
        dining_estimate=100,
        entertainment_estimate=80,
        shopping_estimate=100,
        transport_estimate=50,
        utilities_estimate=150,
        other_estimate=50,
        impulse_spending=0,
        stress_spending=0,
    )


def sample_expenses_with_mood() -> List[Dict[str, Any]]:
    """Sample expenses with mood/trigger tags for testing."""
    return [
        {"amount": 45.0, "merchant": "Coffee Shop", "category": "dining", "mood": "treat", "trigger": "planned"},
        {"amount": 120.0, "merchant": "Grocery", "category": "groceries", "mood": "okay", "trigger": "needed"},
        {"amount": 35.0, "merchant": "Online", "category": "shopping", "mood": "meh", "trigger": "impulse"},
        {"amount": 60.0, "merchant": "Restaurant", "category": "dining", "mood": "great", "trigger": "planned"},
        {"amount": 80.0, "merchant": "Store", "category": "shopping", "mood": "meh", "trigger": "stressed"},
    ]


def sample_baselines() -> Dict[str, float]:
    """Sample spending baselines (averages) for comparison tests."""
    return {
        "avg_groceries": 110.0,
        "avg_dining": 70.0,
        "avg_entertainment": 45.0,
        "avg_shopping": 55.0,
        "avg_transport": 35.0,
        "avg_total_variable": 350.0,
        "avg_impulse": 25.0,
    }


def user_state_new() -> Dict[str, Any]:
    """User with no check-ins (new user)."""
    return {"user_id": "user_new", "total_checkins": 0, "current_streak": 0, "longest_streak": 0}


def user_state_3_weeks() -> Dict[str, Any]:
    """User with 3 weeks of check-ins (below insight threshold)."""
    return {"user_id": "user_3w", "total_checkins": 3, "current_streak": 3, "longest_streak": 3}


def user_state_streak_4() -> Dict[str, Any]:
    """User with 4-week streak (achievement threshold)."""
    return {"user_id": "user_4s", "total_checkins": 4, "current_streak": 4, "longest_streak": 4}


def user_state_streak_broken() -> Dict[str, Any]:
    """User who had a streak and missed a week."""
    return {"user_id": "user_broken", "total_checkins": 8, "current_streak": 1, "longest_streak": 5}
