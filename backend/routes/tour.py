"""
Tour API endpoints for managing app tours and guided experiences
"""

from flask import Blueprint, request, jsonify, g
from flask_login import login_required, current_user
from backend.services.audit_service import get_audit_service
from backend.utils.auth_decorators import require_authentication
from backend.utils.encryption import encrypt_value, decrypt_value
from backend.app_factory import get_db_session
from backend.models.user import User
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List

tour_bp = Blueprint('tour', __name__)

@tour_bp.route('/api/tour/initialize', methods=['POST'])
@login_required
@require_authentication
def initialize_tour():
    """
    Initialize a new tour or resume existing tour
    """
    try:
        user_id = current_user.id
        data = request.get_json()
        tour_type = data.get('tour_type', 'dashboard')
        
        db_session = get_db_session()
        audit_service = get_audit_service()
        
        # Check if user has existing tour state
        existing_tour = db_session.execute(
            "SELECT * FROM user_tours WHERE user_id = :user_id AND tour_type = :tour_type",
            {"user_id": user_id, "tour_type": tour_type}
        ).fetchone()
        
        if existing_tour:
            # Resume existing tour
            tour_state = {
                "id": existing_tour.id,
                "userId": user_id,
                "tourType": tour_type,
                "currentStep": existing_tour.current_step,
                "completedSteps": json.loads(existing_tour.completed_steps or '[]'),
                "isCompleted": existing_tour.is_completed,
                "lastAccessed": existing_tour.last_accessed.isoformat(),
                "preferences": json.loads(existing_tour.preferences or '{}')
            }
        else:
            # Create new tour state
            tour_id = str(uuid.uuid4())
            new_tour = {
                "id": tour_id,
                "userId": user_id,
                "tourType": tour_type,
                "currentStep": 0,
                "completedSteps": [],
                "isCompleted": False,
                "lastAccessed": datetime.now().isoformat(),
                "preferences": {
                    "autoStart": True,
                    "showHints": True,
                    "skipIntro": False
                }
            }
            
            # Insert new tour record
            db_session.execute(
                """
                INSERT INTO user_tours 
                (id, user_id, tour_type, current_step, completed_steps, is_completed, 
                 last_accessed, preferences, created_at, updated_at)
                VALUES (:id, :user_id, :tour_type, :current_step, :completed_steps, 
                        :is_completed, :last_accessed, :preferences, NOW(), NOW())
                """,
                {
                    "id": tour_id,
                    "user_id": user_id,
                    "tour_type": tour_type,
                    "current_step": 0,
                    "completed_steps": json.dumps([]),
                    "is_completed": False,
                    "last_accessed": datetime.now(),
                    "preferences": json.dumps(new_tour["preferences"])
                }
            )
            
            tour_state = new_tour
        
        db_session.commit()
        
        # Log tour initialization
        audit_service.log_user_action(user_id, 'TOUR_INITIALIZED', {
            'tour_type': tour_type,
            'tour_id': tour_state["id"]
        })
        
        return jsonify({
            "success": True,
            "tour": tour_state,
            "request_id": g.get('request_id')
        }), 200
        
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": "Failed to initialize tour"}), 500

@tour_bp.route('/api/tour/progress', methods=['POST'])
@login_required
@require_authentication
def update_tour_progress():
    """
    Update tour progress for a specific step
    """
    try:
        user_id = current_user.id
        data = request.get_json()
        step_id = data.get('step_id')
        completed = data.get('completed', True)
        tour_id = data.get('tour_id')
        
        if not step_id or not tour_id:
            return jsonify({"error": "Missing required fields"}), 400
        
        db_session = get_db_session()
        audit_service = get_audit_service()
        
        # Get current tour state
        tour = db_session.execute(
            "SELECT * FROM user_tours WHERE id = :tour_id AND user_id = :user_id",
            {"tour_id": tour_id, "user_id": user_id}
        ).fetchone()
        
        if not tour:
            return jsonify({"error": "Tour not found"}), 404
        
        # Update completed steps
        completed_steps = json.loads(tour.completed_steps or '[]')
        if completed:
            if step_id not in completed_steps:
                completed_steps.append(step_id)
        else:
            completed_steps = [step for step in completed_steps if step != step_id]
        
        # Update tour progress
        db_session.execute(
            """
            UPDATE user_tours 
            SET completed_steps = :completed_steps,
                current_step = :current_step,
                last_accessed = NOW(),
                updated_at = NOW()
            WHERE id = :tour_id
            """,
            {
                "completed_steps": json.dumps(completed_steps),
                "current_step": tour.current_step + 1,
                "tour_id": tour_id
            }
        )
        
        db_session.commit()
        
        # Log progress update
        audit_service.log_user_action(user_id, 'TOUR_PROGRESS_UPDATED', {
            'tour_id': tour_id,
            'step_id': step_id,
            'completed': completed
        })
        
        return jsonify({
            "success": True,
            "completed_steps": completed_steps,
            "request_id": g.get('request_id')
        }), 200
        
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": "Failed to update tour progress"}), 500

@tour_bp.route('/api/tour/complete', methods=['POST'])
@login_required
@require_authentication
def complete_tour():
    """
    Mark tour as completed
    """
    try:
        user_id = current_user.id
        data = request.get_json()
        tour_id = data.get('tour_id')
        
        if not tour_id:
            return jsonify({"error": "Missing tour_id"}), 400
        
        db_session = get_db_session()
        audit_service = get_audit_service()
        
        # Update tour completion status
        result = db_session.execute(
            """
            UPDATE user_tours 
            SET is_completed = TRUE,
                last_accessed = NOW(),
                updated_at = NOW()
            WHERE id = :tour_id AND user_id = :user_id
            """,
            {"tour_id": tour_id, "user_id": user_id}
        )
        
        if result.rowcount == 0:
            return jsonify({"error": "Tour not found"}), 404
        
        db_session.commit()
        
        # Log tour completion
        audit_service.log_user_action(user_id, 'TOUR_COMPLETED', {
            'tour_id': tour_id
        })
        
        return jsonify({
            "success": True,
            "message": "Tour completed successfully",
            "request_id": g.get('request_id')
        }), 200
        
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": "Failed to complete tour"}), 500

@tour_bp.route('/api/tour/skip', methods=['POST'])
@login_required
@require_authentication
def skip_tour():
    """
    Skip tour and mark as completed
    """
    try:
        user_id = current_user.id
        data = request.get_json()
        tour_id = data.get('tour_id')
        
        if not tour_id:
            return jsonify({"error": "Missing tour_id"}), 400
        
        db_session = get_db_session()
        audit_service = get_audit_service()
        
        # Mark tour as completed (skipped)
        result = db_session.execute(
            """
            UPDATE user_tours 
            SET is_completed = TRUE,
                last_accessed = NOW(),
                updated_at = NOW()
            WHERE id = :tour_id AND user_id = :user_id
            """,
            {"tour_id": tour_id, "user_id": user_id}
        )
        
        if result.rowcount == 0:
            return jsonify({"error": "Tour not found"}), 404
        
        db_session.commit()
        
        # Log tour skip
        audit_service.log_user_action(user_id, 'TOUR_SKIPPED', {
            'tour_id': tour_id
        })
        
        return jsonify({
            "success": True,
            "message": "Tour skipped successfully",
            "request_id": g.get('request_id')
        }), 200
        
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": "Failed to skip tour"}), 500

@tour_bp.route('/api/tour/preferences', methods=['PUT'])
@login_required
@require_authentication
def update_tour_preferences():
    """
    Update tour preferences
    """
    try:
        user_id = current_user.id
        data = request.get_json()
        tour_id = data.get('tour_id')
        preferences = data.get('preferences', {})
        
        if not tour_id:
            return jsonify({"error": "Missing tour_id"}), 400
        
        db_session = get_db_session()
        audit_service = get_audit_service()
        
        # Update tour preferences
        result = db_session.execute(
            """
            UPDATE user_tours 
            SET preferences = :preferences,
                last_accessed = NOW(),
                updated_at = NOW()
            WHERE id = :tour_id AND user_id = :user_id
            """,
            {"preferences": json.dumps(preferences), "tour_id": tour_id, "user_id": user_id}
        )
        
        if result.rowcount == 0:
            return jsonify({"error": "Tour not found"}), 404
        
        db_session.commit()
        
        # Log preferences update
        audit_service.log_user_action(user_id, 'TOUR_PREFERENCES_UPDATED', {
            'tour_id': tour_id,
            'preferences': preferences
        })
        
        return jsonify({
            "success": True,
            "preferences": preferences,
            "request_id": g.get('request_id')
        }), 200
        
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": "Failed to update tour preferences"}), 500

@tour_bp.route('/api/tour/steps/<tour_type>', methods=['GET'])
@login_required
@require_authentication
def get_tour_steps(tour_type: str):
    """
    Get tour steps for a specific tour type
    """
    try:
        user_id = current_user.id
        
        # Get personalized tour steps based on tour type and user data
        if tour_type == 'dashboard':
            steps = get_dashboard_tour_steps(user_id)
        elif tour_type == 'onboarding':
            steps = get_onboarding_tour_steps(user_id)
        elif tour_type == 'features':
            steps = get_features_tour_steps(user_id)
        else:
            return jsonify({"error": "Invalid tour type"}), 400
        
        return jsonify({
            "success": True,
            "steps": steps,
            "request_id": g.get('request_id')
        }), 200
        
    except Exception as e:
        return jsonify({"error": "Failed to get tour steps"}), 500

@tour_bp.route('/api/tour/status/<tour_type>', methods=['GET'])
@login_required
@require_authentication
def get_tour_status(tour_type: str):
    """
    Get tour status for a specific tour type
    """
    try:
        user_id = current_user.id
        
        db_session = get_db_session()
        
        # Get tour status
        tour = db_session.execute(
            "SELECT * FROM user_tours WHERE user_id = :user_id AND tour_type = :tour_type",
            {"user_id": user_id, "tour_type": tour_type}
        ).fetchone()
        
        if not tour:
            return jsonify({
                "success": True,
                "shouldShow": True,
                "isCompleted": False,
                "currentStep": 0
            }), 200
        
        return jsonify({
            "success": True,
            "shouldShow": not tour.is_completed,
            "isCompleted": tour.is_completed,
            "currentStep": tour.current_step,
            "completedSteps": json.loads(tour.completed_steps or '[]'),
            "preferences": json.loads(tour.preferences or '{}'),
            "request_id": g.get('request_id')
        }), 200
        
    except Exception as e:
        return jsonify({"error": "Failed to get tour status"}), 500

def get_dashboard_tour_steps(user_id: str) -> List[Dict[str, Any]]:
    """
    Get personalized dashboard tour steps
    """
    return [
        {
            "id": "welcome",
            "title": "Welcome to Your Dashboard!",
            "description": "This is your financial wellness command center. Let's explore the key features that will help you achieve your goals.",
            "target": ".dashboard-container",
            "position": "center",
            "required": True,
            "skipable": False
        },
        {
            "id": "job-security",
            "title": "Job Security Score",
            "description": "Your career stability score helps you understand your professional situation and plan for the future. Higher scores mean more stability.",
            "target": "#job-security-card",
            "position": "bottom",
            "action": {
                "type": "highlight",
                "text": "Click to see detailed insights"
            },
            "required": False,
            "skipable": True
        },
        {
            "id": "emergency-fund",
            "title": "Emergency Fund Tracker",
            "description": "Track your emergency savings progress. This helps you build financial security for unexpected expenses.",
            "target": "#emergency-fund-card",
            "position": "bottom",
            "action": {
                "type": "highlight",
                "text": "View your savings progress"
            },
            "required": False,
            "skipable": True
        },
        {
            "id": "cash-flow",
            "title": "Cash Flow Insights",
            "description": "Monitor your income and expenses to understand your spending patterns and identify opportunities to save.",
            "target": "#cash-flow-card",
            "position": "top",
            "action": {
                "type": "highlight",
                "text": "Analyze your spending"
            },
            "required": False,
            "skipable": True
        },
        {
            "id": "community",
            "title": "Community Features",
            "description": "Connect with others on similar financial journeys. Share experiences and get support from the community.",
            "target": "#community-card",
            "position": "left",
            "action": {
                "type": "highlight",
                "text": "Join community discussions"
            },
            "required": False,
            "skipable": True
        },
        {
            "id": "notifications",
            "title": "Stay Updated",
            "description": "Set up notifications to get personalized insights, goal reminders, and important updates.",
            "target": ".notification-settings",
            "position": "right",
            "action": {
                "type": "click",
                "target": ".notification-settings",
                "text": "Set up notifications"
            },
            "required": False,
            "skipable": True
        },
        {
            "id": "accounts",
            "title": "Connect Your Accounts",
            "description": "Link your bank accounts for automatic tracking and more accurate insights.",
            "target": ".account-connection",
            "position": "left",
            "action": {
                "type": "click",
                "target": ".account-connection",
                "text": "Connect accounts"
            },
            "required": False,
            "skipable": True
        },
        {
            "id": "complete",
            "title": "You're All Set!",
            "description": "You now know your way around the dashboard. Start exploring and take control of your financial wellness journey!",
            "target": ".dashboard-container",
            "position": "center",
            "required": True,
            "skipable": False
        }
    ]

def get_onboarding_tour_steps(user_id: str) -> List[Dict[str, Any]]:
    """
    Get onboarding tour steps
    """
    return [
        {
            "id": "welcome",
            "title": "Welcome to Mingus!",
            "description": "Let's get you set up with your personalized financial wellness journey.",
            "target": ".onboarding-container",
            "position": "center",
            "required": True,
            "skipable": False
        }
        # Add more onboarding-specific steps as needed
    ]

def get_features_tour_steps(user_id: str) -> List[Dict[str, Any]]:
    """
    Get features tour steps
    """
    return [
        {
            "id": "features-overview",
            "title": "Discover Mingus Features",
            "description": "Explore the powerful features that will help you achieve financial wellness.",
            "target": ".features-container",
            "position": "center",
            "required": True,
            "skipable": False
        }
        # Add more feature-specific steps as needed
    ] 