"""
Security Awareness and Training Routes
Flask routes for security policy management and training
"""

from flask import Blueprint, request, jsonify, render_template
from flask_cors import cross_origin
import logging
from datetime import datetime
from typing import Dict, Any, List
import json

from ..security_awareness_training import (
    SecurityAwarenessTrainingSystem, 
    SecurityPolicy, 
    TrainingModule, 
    SecurityAwarenessCampaign,
    PolicyType, 
    TrainingModuleType,
    TrainingStatus
)

logger = logging.getLogger(__name__)

# Create blueprint
security_awareness_bp = Blueprint('security_awareness', __name__, url_prefix='/api/security-awareness')

# Global system instance
training_system = None

def get_training_system():
    """Get or create training system instance"""
    global training_system
    if training_system is None:
        training_system = SecurityAwarenessTrainingSystem()
    return training_system

# =============================================================================
# Security Policy Routes
# =============================================================================

@security_awareness_bp.route('/policies', methods=['GET'])
@cross_origin()
def get_policies():
    """Get all security policies"""
    try:
        system = get_training_system()
        user_role = request.args.get('user_role', 'all_users')
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        policies = system.get_security_policies(user_role=user_role, active_only=active_only)
        
        return jsonify({
            'success': True,
            'policies': [policy.to_dict() for policy in policies],
            'total_count': len(policies)
        })
    except Exception as e:
        logger.error(f"Error getting policies: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve policies'
        }), 500

@security_awareness_bp.route('/policies/<policy_id>', methods=['GET'])
@cross_origin()
def get_policy(policy_id: str):
    """Get specific security policy"""
    try:
        system = get_training_system()
        policies = system.get_security_policies()
        
        policy = next((p for p in policies if p.policy_id == policy_id), None)
        if not policy:
            return jsonify({
                'success': False,
                'error': 'Policy not found'
            }), 404
        
        return jsonify({
            'success': True,
            'policy': policy.to_dict()
        })
    except Exception as e:
        logger.error(f"Error getting policy {policy_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve policy'
        }), 500

@security_awareness_bp.route('/policies', methods=['POST'])
@cross_origin()
def create_policy():
    """Create new security policy"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['policy_type', 'title', 'description', 'content', 'version']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Create policy object
        policy = SecurityPolicy(
            policy_id=data.get('policy_id', f"POL-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"),
            policy_type=PolicyType(data['policy_type']),
            title=data['title'],
            description=data['description'],
            content=data['content'],
            version=data['version'],
            effective_date=datetime.fromisoformat(data.get('effective_date', datetime.utcnow().isoformat())),
            review_date=datetime.fromisoformat(data.get('review_date', (datetime.utcnow().replace(year=datetime.utcnow().year + 1)).isoformat())),
            applicable_to=data.get('applicable_to', ['all_users']),
            compliance_requirements=data.get('compliance_requirements', []),
            created_by=data.get('created_by', 'admin'),
            requires_acknowledgment=data.get('requires_acknowledgment', True),
            acknowledgment_deadline=datetime.fromisoformat(data['acknowledgment_deadline']) if data.get('acknowledgment_deadline') else None
        )
        
        system = get_training_system()
        success = system.create_security_policy(policy)
        
        if success:
            return jsonify({
                'success': True,
                'policy': policy.to_dict(),
                'message': 'Policy created successfully'
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create policy'
            }), 500
    except Exception as e:
        logger.error(f"Error creating policy: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to create policy'
        }), 500

@security_awareness_bp.route('/policies/<policy_id>/acknowledge', methods=['POST'])
@cross_origin()
def acknowledge_policy(policy_id: str):
    """Acknowledge a security policy"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User ID is required'
            }), 400
        
        system = get_training_system()
        success = system.acknowledge_policy(
            user_id=user_id,
            policy_id=policy_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Policy acknowledged successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to acknowledge policy'
            }), 500
    except Exception as e:
        logger.error(f"Error acknowledging policy: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to acknowledge policy'
        }), 500

# =============================================================================
# Training Module Routes
# =============================================================================

@security_awareness_bp.route('/training/modules', methods=['GET'])
@cross_origin()
def get_training_modules():
    """Get all training modules"""
    try:
        system = get_training_system()
        user_role = request.args.get('user_role', 'all_users')
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        modules = system.get_training_modules(user_role=user_role, active_only=active_only)
        
        return jsonify({
            'success': True,
            'modules': [module.to_dict() for module in modules],
            'total_count': len(modules)
        })
    except Exception as e:
        logger.error(f"Error getting training modules: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve training modules'
        }), 500

@security_awareness_bp.route('/training/modules/<module_id>', methods=['GET'])
@cross_origin()
def get_training_module(module_id: str):
    """Get specific training module"""
    try:
        system = get_training_system()
        modules = system.get_training_modules()
        
        module = next((m for m in modules if m.module_id == module_id), None)
        if not module:
            return jsonify({
                'success': False,
                'error': 'Training module not found'
            }), 404
        
        return jsonify({
            'success': True,
            'module': module.to_dict()
        })
    except Exception as e:
        logger.error(f"Error getting training module {module_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve training module'
        }), 500

@security_awareness_bp.route('/training/modules', methods=['POST'])
@cross_origin()
def create_training_module():
    """Create new training module"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['module_type', 'title', 'description', 'content', 'duration_minutes']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Create module object
        module = TrainingModule(
            module_id=data.get('module_id', f"TRAIN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"),
            module_type=TrainingModuleType(data['module_type']),
            title=data['title'],
            description=data['description'],
            content=data['content'],
            duration_minutes=data['duration_minutes'],
            difficulty_level=data.get('difficulty_level', 'beginner'),
            prerequisites=data.get('prerequisites', []),
            learning_objectives=data.get('learning_objectives', []),
            quiz_questions=data.get('quiz_questions', []),
            passing_score=data.get('passing_score', 80),
            created_by=data.get('created_by', 'admin'),
            tags=data.get('tags', [])
        )
        
        system = get_training_system()
        success = system.create_training_module(module)
        
        if success:
            return jsonify({
                'success': True,
                'module': module.to_dict(),
                'message': 'Training module created successfully'
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create training module'
            }), 500
    except Exception as e:
        logger.error(f"Error creating training module: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to create training module'
        }), 500

@security_awareness_bp.route('/training/assign', methods=['POST'])
@cross_origin()
def assign_training():
    """Assign training module to user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        user_id = data.get('user_id')
        module_id = data.get('module_id')
        due_date = data.get('due_date')
        
        if not user_id or not module_id:
            return jsonify({
                'success': False,
                'error': 'User ID and module ID are required'
            }), 400
        
        # Parse due date if provided
        parsed_due_date = None
        if due_date:
            try:
                parsed_due_date = datetime.fromisoformat(due_date)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid due date format'
                }), 400
        
        system = get_training_system()
        success = system.assign_training_to_user(
            user_id=user_id,
            module_id=module_id,
            due_date=parsed_due_date
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Training assigned successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to assign training'
            }), 500
    except Exception as e:
        logger.error(f"Error assigning training: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to assign training'
        }), 500

@security_awareness_bp.route('/training/status/<user_id>', methods=['GET'])
@cross_origin()
def get_user_training_status(user_id: str):
    """Get user's training status"""
    try:
        system = get_training_system()
        status = system.get_user_training_status(user_id)
        
        if status:
            return jsonify({
                'success': True,
                'training_status': status
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to retrieve training status'
            }), 500
    except Exception as e:
        logger.error(f"Error getting training status for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve training status'
        }), 500

# =============================================================================
# Awareness Campaign Routes
# =============================================================================

@security_awareness_bp.route('/campaigns', methods=['GET'])
@cross_origin()
def get_campaigns():
    """Get all awareness campaigns"""
    try:
        system = get_training_system()
        user_role = request.args.get('user_role', 'all_users')
        
        campaigns = system.get_active_campaigns(user_role=user_role)
        
        return jsonify({
            'success': True,
            'campaigns': [campaign.to_dict() for campaign in campaigns],
            'total_count': len(campaigns)
        })
    except Exception as e:
        logger.error(f"Error getting campaigns: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve campaigns'
        }), 500

@security_awareness_bp.route('/campaigns', methods=['POST'])
@cross_origin()
def create_campaign():
    """Create new awareness campaign"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['title', 'description', 'campaign_type', 'target_audience', 'start_date', 'end_date']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Create campaign object
        campaign = SecurityAwarenessCampaign(
            campaign_id=data.get('campaign_id', f"CAMP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"),
            title=data['title'],
            description=data['description'],
            campaign_type=data['campaign_type'],
            target_audience=data['target_audience'],
            start_date=datetime.fromisoformat(data['start_date']),
            end_date=datetime.fromisoformat(data['end_date']),
            content=data.get('content', {}),
            success_metrics=data.get('success_metrics', {}),
            created_by=data.get('created_by', 'admin')
        )
        
        system = get_training_system()
        success = system.create_awareness_campaign(campaign)
        
        if success:
            return jsonify({
                'success': True,
                'campaign': campaign.to_dict(),
                'message': 'Campaign created successfully'
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create campaign'
            }), 500
    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to create campaign'
        }), 500

# =============================================================================
# Reporting Routes
# =============================================================================

@security_awareness_bp.route('/reports/training', methods=['GET'])
@cross_origin()
def generate_training_report():
    """Generate training report"""
    try:
        user_id = request.args.get('user_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Parse dates if provided
        parsed_start_date = None
        parsed_end_date = None
        
        if start_date:
            try:
                parsed_start_date = datetime.fromisoformat(start_date)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid start date format'
                }), 400
        
        if end_date:
            try:
                parsed_end_date = datetime.fromisoformat(end_date)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid end date format'
                }), 400
        
        system = get_training_system()
        report = system.generate_training_report(
            user_id=user_id,
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )
        
        if report:
            return jsonify({
                'success': True,
                'report': report
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to generate report'
            }), 500
    except Exception as e:
        logger.error(f"Error generating training report: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate report'
        }), 500

# =============================================================================
# Dashboard Routes
# =============================================================================

@security_awareness_bp.route('/dashboard', methods=['GET'])
@cross_origin()
def get_security_awareness_dashboard():
    """Get security awareness dashboard data"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User ID is required'
            }), 400
        
        system = get_training_system()
        
        # Get user training status
        training_status = system.get_user_training_status(user_id)
        
        # Get applicable policies
        policies = system.get_security_policies(user_role='all_users', active_only=True)
        
        # Get available training modules
        modules = system.get_training_modules(user_role='all_users', active_only=True)
        
        # Get active campaigns
        campaigns = system.get_active_campaigns(user_role='all_users')
        
        # Calculate compliance metrics
        compliance_metrics = {
            'training_completion_rate': training_status.get('completion_percentage', 0),
            'policies_acknowledged': len(training_status.get('policy_acknowledgments', [])),
            'total_policies': len(policies),
            'overdue_trainings': training_status.get('overdue_count', 0),
            'active_campaigns': len(campaigns),
            'compliance_status': training_status.get('compliance_status', 'unknown')
        }
        
        return jsonify({
            'success': True,
            'dashboard': {
                'training_status': training_status,
                'policies': [policy.to_dict() for policy in policies],
                'modules': [module.to_dict() for module in modules],
                'campaigns': [campaign.to_dict() for campaign in campaigns],
                'compliance_metrics': compliance_metrics
            }
        })
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve dashboard data'
        }), 500

# =============================================================================
# Health Check Route
# =============================================================================

@security_awareness_bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """Health check endpoint"""
    try:
        system = get_training_system()
        
        # Test basic functionality
        policies = system.get_security_policies()
        modules = system.get_training_modules()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'service': 'security_awareness_training',
            'policies_count': len(policies),
            'modules_count': len(modules),
            'database': 'connected'
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# =============================================================================
# Template Routes
# =============================================================================

@security_awareness_bp.route('/policies/<policy_id>/view', methods=['GET'])
def view_policy(policy_id: str):
    """View policy in HTML format"""
    try:
        system = get_training_system()
        policies = system.get_security_policies()
        
        policy = next((p for p in policies if p.policy_id == policy_id), None)
        if not policy:
            return "Policy not found", 404
        
        return render_template(
            'security_policy.html',
            policy=policy
        )
    except Exception as e:
        logger.error(f"Error viewing policy: {e}")
        return "Error loading policy", 500

@security_awareness_bp.route('/training/modules/<module_id>/view', methods=['GET'])
def view_training_module(module_id: str):
    """View training module in HTML format"""
    try:
        system = get_training_system()
        modules = system.get_training_modules()
        
        module = next((m for m in modules if m.module_id == module_id), None)
        if not module:
            return "Training module not found", 404
        
        return render_template(
            'training_module.html',
            module=module
        )
    except Exception as e:
        logger.error(f"Error viewing training module: {e}")
        return "Error loading training module", 500 