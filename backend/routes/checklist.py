"""
Checklist API endpoints for managing next steps and personalized tasks
"""

from flask import Blueprint, request, jsonify, g
from flask_login import login_required, current_user
from backend.services.audit_service import get_audit_service
from backend.utils.auth_decorators import require_authentication
from backend.app_factory import get_db_session
from backend.models.user import User
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List

checklist_bp = Blueprint('checklist', __name__)

@checklist_bp.route('/api/checklist/generate', methods=['POST'])
@login_required
@require_authentication
def generate_checklist():
    """
    Generate personalized checklist for user
    """
    try:
        user_id = current_user.id
        
        db_session = get_db_session()
        audit_service = get_audit_service()
        
        # Generate personalized checklist items
        checklist_items = generate_personalized_checklist(user_id, db_session)
        
        # Store checklist in database
        checklist_id = str(uuid.uuid4())
        db_session.execute(
            """
            INSERT INTO user_checklists 
            (id, user_id, items, created_at, updated_at)
            VALUES (:id, :user_id, :items, NOW(), NOW())
            """,
            {
                "id": checklist_id,
                "user_id": user_id,
                "items": json.dumps(checklist_items)
            }
        )
        
        db_session.commit()
        
        # Log checklist generation
        audit_service.log_user_action(user_id, 'CHECKLIST_GENERATED', {
            'checklist_id': checklist_id,
            'item_count': len(checklist_items)
        })
        
        return jsonify({
            "success": True,
            "checklist_id": checklist_id,
            "items": checklist_items,
            "request_id": g.get('request_id')
        }), 200
        
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": "Failed to generate checklist"}), 500

@checklist_bp.route('/api/checklist/<checklist_id>', methods=['GET'])
@login_required
@require_authentication
def get_checklist(checklist_id: str):
    """
    Get checklist by ID
    """
    try:
        user_id = current_user.id
        
        db_session = get_db_session()
        
        # Get checklist
        checklist = db_session.execute(
            "SELECT * FROM user_checklists WHERE id = :checklist_id AND user_id = :user_id",
            {"checklist_id": checklist_id, "user_id": user_id}
        ).fetchone()
        
        if not checklist:
            return jsonify({"error": "Checklist not found"}), 404
        
        items = json.loads(checklist.items or '[]')
        progress = calculate_checklist_progress(items)
        
        return jsonify({
            "success": True,
            "checklist": {
                "id": checklist.id,
                "items": items,
                "progress": progress,
                "created_at": checklist.created_at.isoformat(),
                "updated_at": checklist.updated_at.isoformat()
            },
            "request_id": g.get('request_id')
        }), 200
        
    except Exception as e:
        return jsonify({"error": "Failed to get checklist"}), 500

@checklist_bp.route('/api/checklist/<checklist_id>/progress', methods=['GET'])
@login_required
@require_authentication
def get_checklist_progress(checklist_id: str):
    """
    Get checklist progress
    """
    try:
        user_id = current_user.id
        
        db_session = get_db_session()
        
        # Get checklist
        checklist = db_session.execute(
            "SELECT * FROM user_checklists WHERE id = :checklist_id AND user_id = :user_id",
            {"checklist_id": checklist_id, "user_id": user_id}
        ).fetchone()
        
        if not checklist:
            return jsonify({"error": "Checklist not found"}), 404
        
        items = json.loads(checklist.items or '[]')
        progress = calculate_checklist_progress(items)
        
        return jsonify({
            "success": True,
            "progress": progress,
            "request_id": g.get('request_id')
        }), 200
        
    except Exception as e:
        return jsonify({"error": "Failed to get checklist progress"}), 500

@checklist_bp.route('/api/checklist/<checklist_id>/complete', methods=['POST'])
@login_required
@require_authentication
def complete_checklist_item(checklist_id: str):
    """
    Mark checklist item as completed
    """
    try:
        user_id = current_user.id
        data = request.get_json()
        item_id = data.get('item_id')
        completed = data.get('completed', True)
        
        if not item_id:
            return jsonify({"error": "Missing item_id"}), 400
        
        db_session = get_db_session()
        audit_service = get_audit_service()
        
        # Get checklist
        checklist = db_session.execute(
            "SELECT * FROM user_checklists WHERE id = :checklist_id AND user_id = :user_id",
            {"checklist_id": checklist_id, "user_id": user_id}
        ).fetchone()
        
        if not checklist:
            return jsonify({"error": "Checklist not found"}), 404
        
        # Update item completion status
        items = json.loads(checklist.items or '[]')
        updated_items = []
        
        for item in items:
            if item['id'] == item_id:
                item['completed'] = completed
                if completed:
                    item['completedAt'] = datetime.now().isoformat()
                else:
                    item.pop('completedAt', None)
            updated_items.append(item)
        
        # Update checklist in database
        db_session.execute(
            """
            UPDATE user_checklists 
            SET items = :items,
                updated_at = NOW()
            WHERE id = :checklist_id
            """,
            {"items": json.dumps(updated_items), "checklist_id": checklist_id}
        )
        
        db_session.commit()
        
        # Log item completion
        audit_service.log_user_action(user_id, 'CHECKLIST_ITEM_COMPLETED', {
            'checklist_id': checklist_id,
            'item_id': item_id,
            'completed': completed
        })
        
        # Calculate updated progress
        progress = calculate_checklist_progress(updated_items)
        
        return jsonify({
            "success": True,
            "items": updated_items,
            "progress": progress,
            "request_id": g.get('request_id')
        }), 200
        
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": "Failed to complete checklist item"}), 500

@checklist_bp.route('/api/checklist/<checklist_id>/encouragement', methods=['GET'])
@login_required
@require_authentication
def get_encouragement(checklist_id: str):
    """
    Get encouragement message based on checklist progress
    """
    try:
        user_id = current_user.id
        
        db_session = get_db_session()
        
        # Get checklist
        checklist = db_session.execute(
            "SELECT * FROM user_checklists WHERE id = :checklist_id AND user_id = :user_id",
            {"checklist_id": checklist_id, "user_id": user_id}
        ).fetchone()
        
        if not checklist:
            return jsonify({"error": "Checklist not found"}), 404
        
        items = json.loads(checklist.items or '[]')
        progress = calculate_checklist_progress(items)
        
        encouragement = get_encouragement_message(progress)
        
        return jsonify({
            "success": True,
            "encouragement": encouragement,
            "progress": progress,
            "request_id": g.get('request_id')
        }), 200
        
    except Exception as e:
        return jsonify({"error": "Failed to get encouragement"}), 500

def generate_personalized_checklist(user_id: str, db_session) -> List[Dict[str, Any]]:
    """
    Generate personalized checklist items based on user data
    """
    base_items = get_base_checklist_items()
    personalized_items = add_personalized_items(user_id, base_items, db_session)
    
    return personalized_items

def get_base_checklist_items() -> List[Dict[str, Any]]:
    """
    Get base checklist items
    """
    return [
        {
            "id": "complete-profile",
            "title": "Complete Your Profile",
            "description": "Add your employment details, income sources, and financial goals for personalized insights.",
            "category": "profile",
            "priority": "high",
            "completed": False,
            "action": {
                "type": "navigate",
                "target": "/profile",
                "text": "Complete Profile"
            },
            "estimatedTime": 5,
            "userSpecific": False
        },
        {
            "id": "connect-bank",
            "title": "Connect Your Bank Account",
            "description": "Link your primary bank account for automatic expense tracking and cash flow analysis.",
            "category": "accounts",
            "priority": "high",
            "completed": False,
            "action": {
                "type": "modal",
                "target": "connect-accounts",
                "text": "Connect Account"
            },
            "estimatedTime": 3,
            "userSpecific": False
        },
        {
            "id": "setup-notifications",
            "title": "Set Up Notifications",
            "description": "Choose your preferred notification settings to stay updated on your progress and insights.",
            "category": "notifications",
            "priority": "medium",
            "completed": False,
            "action": {
                "type": "modal",
                "target": "notification-settings",
                "text": "Set Up Notifications"
            },
            "estimatedTime": 2,
            "userSpecific": False
        },
        {
            "id": "join-community",
            "title": "Join Community Event",
            "description": "Connect with others on similar financial journeys. Share experiences and get support.",
            "category": "community",
            "priority": "medium",
            "completed": False,
            "action": {
                "type": "navigate",
                "target": "/community",
                "text": "Join Event"
            },
            "estimatedTime": 10,
            "userSpecific": True
        },
        {
            "id": "set-emergency-goal",
            "title": "Set Emergency Fund Goal",
            "description": "Define your emergency fund target based on your job security and monthly expenses.",
            "category": "goals",
            "priority": "high",
            "completed": False,
            "dependencies": ["complete-profile"],
            "action": {
                "type": "navigate",
                "target": "/goals",
                "text": "Set Goal"
            },
            "estimatedTime": 3,
            "userSpecific": True
        },
        {
            "id": "review-insights",
            "title": "Review Your Insights",
            "description": "Check out your personalized financial insights and recommendations.",
            "category": "insights",
            "priority": "low",
            "completed": False,
            "dependencies": ["complete-profile"],
            "action": {
                "type": "navigate",
                "target": "/insights",
                "text": "View Insights"
            },
            "estimatedTime": 5,
            "userSpecific": True
        }
    ]

def add_personalized_items(user_id: str, base_items: List[Dict[str, Any]], db_session) -> List[Dict[str, Any]]:
    """
    Add personalized items based on user data
    """
    personalized_items = base_items.copy()
    
    # Check if user has job security concerns
    has_job_security_concerns = check_job_security_concerns(user_id, db_session)
    if has_job_security_concerns:
        personalized_items.append({
            "id": "job-security-plan",
            "title": "Create Job Security Plan",
            "description": "Develop a plan to improve your job security and career stability.",
            "category": "goals",
            "priority": "high",
            "completed": False,
            "action": {
                "type": "navigate",
                "target": "/job-security/plan",
                "text": "Create Plan"
            },
            "estimatedTime": 8,
            "userSpecific": True
        })
    
    # Check if user has debt
    has_debt = check_user_debt(user_id, db_session)
    if has_debt:
        personalized_items.append({
            "id": "debt-payoff-plan",
            "title": "Create Debt Payoff Plan",
            "description": "Develop a strategy to pay off your debts efficiently and save on interest.",
            "category": "goals",
            "priority": "high",
            "completed": False,
            "action": {
                "type": "navigate",
                "target": "/debt/plan",
                "text": "Create Plan"
            },
            "estimatedTime": 6,
            "userSpecific": True
        })
    
    # Check if user has investment accounts
    has_investments = check_investment_accounts(user_id, db_session)
    if has_investments:
        personalized_items.append({
            "id": "review-investments",
            "title": "Review Investment Portfolio",
            "description": "Analyze your investment portfolio and get personalized recommendations.",
            "category": "insights",
            "priority": "medium",
            "completed": False,
            "action": {
                "type": "navigate",
                "target": "/investments/portfolio",
                "text": "Review Portfolio"
            },
            "estimatedTime": 7,
            "userSpecific": True
        })
    
    return personalized_items

def check_job_security_concerns(user_id: str, db_session) -> bool:
    """
    Check if user has job security concerns
    """
    try:
        # This would check user's job security assessment
        # For now, return a default value
        return True
    except Exception:
        return False

def check_user_debt(user_id: str, db_session) -> bool:
    """
    Check if user has debt accounts
    """
    try:
        # Check if user has debt accounts
        debt_accounts = db_session.execute(
            "SELECT COUNT(*) as count FROM encrypted_debt_accounts WHERE user_id = :user_id AND is_active = TRUE",
            {"user_id": user_id}
        ).fetchone()
        
        return debt_accounts.count > 0 if debt_accounts else False
    except Exception:
        return False

def check_investment_accounts(user_id: str, db_session) -> bool:
    """
    Check if user has investment accounts
    """
    try:
        # This would check if user has investment accounts
        # For now, return a default value
        return False
    except Exception:
        return False

def calculate_checklist_progress(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate checklist progress
    """
    total_items = len(items)
    completed_items = len([item for item in items if item.get('completed', False)])
    progress_percentage = (completed_items / total_items * 100) if total_items > 0 else 0
    
    # Calculate estimated time remaining
    remaining_items = [item for item in items if not item.get('completed', False)]
    estimated_time_remaining = sum(item.get('estimatedTime', 0) for item in remaining_items)
    
    # Find next priority item
    next_priority_item = None
    for item in remaining_items:
        if can_complete_item(item, items):
            if not next_priority_item or get_priority_value(item['priority']) > get_priority_value(next_priority_item['priority']):
                next_priority_item = item
    
    # Calculate category progress
    categories = {}
    category_groups = {}
    for item in items:
        category = item['category']
        if category not in category_groups:
            category_groups[category] = []
        category_groups[category].append(item)
    
    for category, category_items in category_groups.items():
        total = len(category_items)
        completed = len([item for item in category_items if item.get('completed', False)])
        percentage = (completed / total * 100) if total > 0 else 0
        
        categories[category] = {
            "total": total,
            "completed": completed,
            "percentage": percentage
        }
    
    return {
        "totalItems": total_items,
        "completedItems": completed_items,
        "progressPercentage": progress_percentage,
        "estimatedTimeRemaining": estimated_time_remaining,
        "nextPriorityItem": next_priority_item,
        "categories": categories
    }

def can_complete_item(item: Dict[str, Any], all_items: List[Dict[str, Any]]) -> bool:
    """
    Check if an item can be completed based on dependencies
    """
    dependencies = item.get('dependencies', [])
    if not dependencies:
        return True
    
    for dep_id in dependencies:
        dependency = next((item for item in all_items if item['id'] == dep_id), None)
        if not dependency or not dependency.get('completed', False):
            return False
    
    return True

def get_priority_value(priority: str) -> int:
    """
    Get numeric value for priority
    """
    priority_values = {"high": 3, "medium": 2, "low": 1}
    return priority_values.get(priority, 0)

def get_encouragement_message(progress: Dict[str, Any]) -> str:
    """
    Get encouragement message based on progress
    """
    percentage = progress.get('progressPercentage', 0)
    
    if percentage == 0:
        return "Let's get started! Every journey begins with a single step. 💪"
    elif percentage < 25:
        return "Great start! You're building momentum. Keep going! 🚀"
    elif percentage < 50:
        return "You're making excellent progress! You're almost halfway there! ✨"
    elif percentage < 75:
        return "Fantastic work! You're in the home stretch now! 🎯"
    elif percentage < 100:
        return "Almost there! Just a few more steps to complete your setup! 🏁"
    else:
        return "Congratulations! You've completed all your next steps! 🎉" 