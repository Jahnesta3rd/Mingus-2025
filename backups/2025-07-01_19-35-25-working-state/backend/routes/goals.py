from flask import Blueprint, request, jsonify
from backend.services.goals_service import (
    setup_goals_service, get_goals_dashboard, add_goal_service, update_goal_service,
    record_contribution_service, analyze_goal_progress_service
)
from backend.middleware.auth import login_required

# Blueprint registration

goals_bp = Blueprint('goals', __name__, url_prefix='/api/goals')

@goals_bp.route('/setup', methods=['GET', 'POST'])
@login_required
def setup_goals():
    """Initial goals setup during onboarding"""
    try:
        if request.method == 'GET':
            return setup_goals_service.get(request.user)
        else:
            data = request.json
            return setup_goals_service.post(request.user, data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@goals_bp.route('/dashboard', methods=['GET'])
@login_required
def goals_dashboard():
    """Get user's goals overview for dashboard"""
    try:
        return get_goals_dashboard(request.user)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@goals_bp.route('/add', methods=['POST'])
@login_required
def add_goal():
    """Add new financial goal"""
    try:
        data = request.json
        return add_goal_service(request.user, data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@goals_bp.route('/<goal_id>/update', methods=['PUT'])
@login_required
def update_goal(goal_id):
    """Update existing goal"""
    try:
        data = request.json
        return update_goal_service(request.user, goal_id, data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@goals_bp.route('/<goal_id>/contribute', methods=['POST'])
@login_required
def record_contribution(goal_id):
    """Record progress toward goal"""
    try:
        data = request.json
        return record_contribution_service(request.user, goal_id, data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@goals_bp.route('/progress-analysis', methods=['GET'])
@login_required
def analyze_goal_progress():
    """Analyze goal progress vs health metrics"""
    try:
        return analyze_goal_progress_service(request.user)
    except Exception as e:
        return jsonify({'error': str(e)}), 400 