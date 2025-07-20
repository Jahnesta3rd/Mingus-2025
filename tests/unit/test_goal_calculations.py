import pytest
from datetime import date, timedelta
from backend.services.goals_service import (
    calculate_monthly_contribution_needed, analyze_goal_feasibility,
    suggest_goal_adjustments, calculate_goal_stress_impact
)

def test_calculate_monthly_contribution_needed():
    target = 12000
    current = 2000
    target_date = date.today() + timedelta(days=365)
    result = calculate_monthly_contribution_needed(target, current, target_date)
    assert result > 0
    # Edge: target date in past
    assert calculate_monthly_contribution_needed(10000, 0, date.today() - timedelta(days=1)) is None
    # Edge: current >= target
    assert calculate_monthly_contribution_needed(1000, 2000, date.today() + timedelta(days=30)) == 0

def test_analyze_goal_feasibility_feasible():
    res = analyze_goal_feasibility(5000, 3000, 6000, 12)
    assert res['feasible'] is True

def test_analyze_goal_feasibility_unfeasible():
    res = analyze_goal_feasibility(2000, 1900, 6000, 6)
    assert res['feasible'] is False
    assert '30%' in res['reason']

def test_suggest_goal_adjustments_extend_timeline():
    user_data = {'income': 2000, 'expenses': 1900}
    goal_data = {'target_amount': 6000, 'current_amount': 0, 'target_date': date.today() + timedelta(days=180)}
    suggestion = suggest_goal_adjustments(user_data, goal_data)
    assert 'timeline' in suggestion['suggestion'].lower()

def test_calculate_goal_stress_impact():
    progress = [(date(2024, 6, 1), 0.2), (date(2024, 6, 8), 0.4)]
    stress = [(date(2024, 6, 1), 7), (date(2024, 6, 8), 5)]
    result = calculate_goal_stress_impact(progress, stress)
    assert result is not None
    assert -1 <= result['correlation'] <= 1
    # Edge: not enough data
    assert calculate_goal_stress_impact([], []) is None 