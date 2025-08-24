"""
Enhanced Security Awareness and Training Routes
Comprehensive routes for security best practices, incident response training, and culture development
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

from ..security_best_practices import (
    SecurityBestPracticesSystem,
    SecurityBestPractice,
    SecurityChecklist,
    BestPracticeCategory,
    PracticeLevel,
    ImplementationStatus
)

from ..incident_response_training import (
    IncidentResponseTrainingSystem,
    IncidentResponseScenario,
    IncidentResponseProcedure,
    IncidentType,
    IncidentSeverity,
    TrainingScenarioType
)

from ..security_culture_development import (
    SecurityCultureDevelopmentSystem,
    SecurityCultureAssessment,
    SecurityCultureInitiative,
    CultureDimension,
    AssessmentType,
    MaturityLevel
)

logger = logging.getLogger(__name__)

# Create blueprint
enhanced_security_bp = Blueprint('enhanced_security', __name__, url_prefix='/api/enhanced-security')

# Global system instances
training_system = None
best_practices_system = None
incident_response_system = None
culture_development_system = None

def get_training_system():
    """Get or create training system instance"""
    global training_system
    if training_system is None:
        training_system = SecurityAwarenessTrainingSystem()
    return training_system

def get_best_practices_system():
    """Get or create best practices system instance"""
    global best_practices_system
    if best_practices_system is None:
        best_practices_system = SecurityBestPracticesSystem()
    return best_practices_system

def get_incident_response_system():
    """Get or create incident response system instance"""
    global incident_response_system
    if incident_response_system is None:
        incident_response_system = IncidentResponseTrainingSystem()
    return incident_response_system

def get_culture_development_system():
    """Get or create culture development system instance"""
    global culture_development_system
    if culture_development_system is None:
        culture_development_system = SecurityCultureDevelopmentSystem()
    return culture_development_system

# =============================================================================
# Security Best Practices Routes
# =============================================================================

@enhanced_security_bp.route('/best-practices', methods=['GET'])
@cross_origin()
def get_best_practices():
    """Get security best practices"""
    try:
        system = get_best_practices_system()
        category = request.args.get('category')
        level = request.args.get('level')
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        practices = system.get_best_practices(
            category=BestPracticeCategory(category) if category else None,
            level=PracticeLevel(level) if level else None,
            active_only=active_only
        )
        
        return jsonify({
            'success': True,
            'best_practices': [practice.to_dict() for practice in practices],
            'total_count': len(practices)
        })
    except Exception as e:
        logger.error(f"Error getting best practices: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve best practices'
        }), 500

@enhanced_security_bp.route('/best-practices/<practice_id>', methods=['GET'])
@cross_origin()
def get_best_practice(practice_id: str):
    """Get specific best practice"""
    try:
        system = get_best_practices_system()
        practices = system.get_best_practices()
        
        practice = next((p for p in practices if p.practice_id == practice_id), None)
        if not practice:
            return jsonify({
                'success': False,
                'error': 'Best practice not found'
            }), 404
        
        return jsonify({
            'success': True,
            'best_practice': practice.to_dict()
        })
    except Exception as e:
        logger.error(f"Error getting best practice {practice_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve best practice'
        }), 500

@enhanced_security_bp.route('/checklists', methods=['GET'])
@cross_origin()
def get_security_checklists():
    """Get security checklists"""
    try:
        system = get_best_practices_system()
        category = request.args.get('category')
        frequency = request.args.get('frequency')
        target_audience = request.args.get('target_audience')
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        checklists = system.get_security_checklists(
            category=BestPracticeCategory(category) if category else None,
            frequency=frequency,
            target_audience=target_audience,
            active_only=active_only
        )
        
        return jsonify({
            'success': True,
            'checklists': [checklist.to_dict() for checklist in checklists],
            'total_count': len(checklists)
        })
    except Exception as e:
        logger.error(f"Error getting checklists: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve checklists'
        }), 500

@enhanced_security_bp.route('/checklists/<checklist_id>/submit', methods=['POST'])
@cross_origin()
def submit_checklist_response(checklist_id: str):
    """Submit checklist response"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        user_id = data.get('user_id')
        responses = data.get('responses', [])
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User ID is required'
            }), 400
        
        from ..security_best_practices import ChecklistResponse
        
        response = ChecklistResponse(
            response_id=str(uuid.uuid4()),
            checklist_id=checklist_id,
            user_id=user_id,
            completed_date=datetime.utcnow(),
            responses=responses
        )
        
        system = get_best_practices_system()
        success = system.submit_checklist_response(response)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Checklist response submitted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to submit checklist response'
            }), 500
    except Exception as e:
        logger.error(f"Error submitting checklist response: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to submit checklist response'
        }), 500

# =============================================================================
# Incident Response Training Routes
# =============================================================================

@enhanced_security_bp.route('/incident-response/scenarios', methods=['GET'])
@cross_origin()
def get_incident_scenarios():
    """Get incident response scenarios"""
    try:
        system = get_incident_response_system()
        incident_type = request.args.get('incident_type')
        severity = request.args.get('severity')
        scenario_type = request.args.get('scenario_type')
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        scenarios = system.get_scenarios(
            incident_type=IncidentType(incident_type) if incident_type else None,
            severity=IncidentSeverity(severity) if severity else None,
            scenario_type=TrainingScenarioType(scenario_type) if scenario_type else None,
            active_only=active_only
        )
        
        return jsonify({
            'success': True,
            'scenarios': [scenario.to_dict() for scenario in scenarios],
            'total_count': len(scenarios)
        })
    except Exception as e:
        logger.error(f"Error getting scenarios: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve scenarios'
        }), 500

@enhanced_security_bp.route('/incident-response/procedures', methods=['GET'])
@cross_origin()
def get_incident_procedures():
    """Get incident response procedures"""
    try:
        system = get_incident_response_system()
        incident_type = request.args.get('incident_type')
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        procedures = system.get_procedures(
            incident_type=IncidentType(incident_type) if incident_type else None,
            active_only=active_only
        )
        
        return jsonify({
            'success': True,
            'procedures': [procedure.to_dict() for procedure in procedures],
            'total_count': len(procedures)
        })
    except Exception as e:
        logger.error(f"Error getting procedures: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve procedures'
        }), 500

@enhanced_security_bp.route('/incident-response/scenarios/<scenario_id>/execute', methods=['POST'])
@cross_origin()
def execute_scenario(scenario_id: str):
    """Execute a training scenario"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        facilitator = data.get('facilitator')
        participants = data.get('participants', [])
        
        if not facilitator:
            return jsonify({
                'success': False,
                'error': 'Facilitator is required'
            }), 400
        
        from ..incident_response_training import ScenarioExecution
        
        execution = ScenarioExecution(
            execution_id=str(uuid.uuid4()),
            scenario_id=scenario_id,
            facilitator=facilitator,
            participants=participants,
            start_time=datetime.utcnow(),
            status="in_progress"
        )
        
        system = get_incident_response_system()
        success = system.execute_scenario(execution)
        
        if success:
            return jsonify({
                'success': True,
                'execution_id': execution.execution_id,
                'message': 'Scenario execution started successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to execute scenario'
            }), 500
    except Exception as e:
        logger.error(f"Error executing scenario: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to execute scenario'
        }), 500

# =============================================================================
# Security Culture Development Routes
# =============================================================================

@enhanced_security_bp.route('/culture/assessments', methods=['GET'])
@cross_origin()
def get_culture_assessments():
    """Get security culture assessments"""
    try:
        system = get_culture_development_system()
        assessment_type = request.args.get('assessment_type')
        target_audience = request.args.get('target_audience')
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        assessments = system.get_assessments(
            assessment_type=AssessmentType(assessment_type) if assessment_type else None,
            target_audience=target_audience,
            active_only=active_only
        )
        
        return jsonify({
            'success': True,
            'assessments': [assessment.to_dict() for assessment in assessments],
            'total_count': len(assessments)
        })
    except Exception as e:
        logger.error(f"Error getting assessments: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve assessments'
        }), 500

@enhanced_security_bp.route('/culture/assessments/<assessment_id>/submit', methods=['POST'])
@cross_origin()
def submit_culture_assessment(assessment_id: str):
    """Submit culture assessment response"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        participant_id = data.get('participant_id')
        department = data.get('department')
        role = data.get('role')
        responses = data.get('responses', [])
        
        if not participant_id:
            return jsonify({
                'success': False,
                'error': 'Participant ID is required'
            }), 400
        
        from ..security_culture_development import AssessmentResponse
        
        response = AssessmentResponse(
            response_id=str(uuid.uuid4()),
            assessment_id=assessment_id,
            participant_id=participant_id,
            department=department,
            role=role,
            responses=responses,
            completion_date=datetime.utcnow()
        )
        
        system = get_culture_development_system()
        success = system.submit_assessment_response(response)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Assessment response submitted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to submit assessment response'
            }), 500
    except Exception as e:
        logger.error(f"Error submitting assessment response: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to submit assessment response'
        }), 500

@enhanced_security_bp.route('/culture/initiatives', methods=['GET'])
@cross_origin()
def get_culture_initiatives():
    """Get security culture initiatives"""
    try:
        system = get_culture_development_system()
        target_dimension = request.args.get('target_dimension')
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        initiatives = system.get_initiatives(
            target_dimension=CultureDimension(target_dimension) if target_dimension else None,
            active_only=active_only
        )
        
        return jsonify({
            'success': True,
            'initiatives': [initiative.to_dict() for initiative in initiatives],
            'total_count': len(initiatives)
        })
    except Exception as e:
        logger.error(f"Error getting initiatives: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve initiatives'
        }), 500

@enhanced_security_bp.route('/culture/metrics', methods=['GET'])
@cross_origin()
def get_culture_metrics():
    """Get security culture metrics"""
    try:
        system = get_culture_development_system()
        dimension = request.args.get('dimension')
        department = request.args.get('department')
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
        
        metrics = system.get_culture_metrics(
            dimension=CultureDimension(dimension) if dimension else None,
            department=department,
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )
        
        return jsonify({
            'success': True,
            'metrics': [metric.to_dict() for metric in metrics],
            'total_count': len(metrics)
        })
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve metrics'
        }), 500

# =============================================================================
# Comprehensive Dashboard Routes
# =============================================================================

@enhanced_security_bp.route('/dashboard/comprehensive', methods=['GET'])
@cross_origin()
def get_comprehensive_dashboard():
    """Get comprehensive security dashboard data"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User ID is required'
            }), 400
        
        # Get data from all systems
        training_system = get_training_system()
        best_practices_system = get_best_practices_system()
        incident_response_system = get_incident_response_system()
        culture_development_system = get_culture_development_system()
        
        # Training status
        training_status = training_system.get_user_training_status(user_id)
        
        # Best practices
        best_practices = best_practices_system.get_best_practices(active_only=True)
        user_checklist_responses = best_practices_system.get_user_checklist_responses(user_id)
        
        # Incident response scenarios
        scenarios = incident_response_system.get_scenarios(active_only=True)
        procedures = incident_response_system.get_procedures(active_only=True)
        
        # Culture assessments
        assessments = culture_development_system.get_assessments(active_only=True)
        initiatives = culture_development_system.get_initiatives(active_only=True)
        
        # Calculate comprehensive metrics
        comprehensive_metrics = {
            'training_completion_rate': training_status.get('completion_percentage', 0),
            'best_practices_implemented': len([p for p in best_practices if p.practice_level == PracticeLevel.BASIC]),
            'checklist_completion_rate': len(user_checklist_responses),
            'scenarios_available': len(scenarios),
            'procedures_available': len(procedures),
            'assessments_available': len(assessments),
            'active_initiatives': len(initiatives),
            'overall_security_maturity': self._calculate_security_maturity(
                training_status, best_practices, user_checklist_responses
            )
        }
        
        return jsonify({
            'success': True,
            'dashboard': {
                'training_status': training_status,
                'best_practices': [practice.to_dict() for practice in best_practices[:5]],  # Top 5
                'checklist_responses': [response.to_dict() for response in user_checklist_responses[:5]],  # Recent 5
                'scenarios': [scenario.to_dict() for scenario in scenarios[:5]],  # Top 5
                'procedures': [procedure.to_dict() for procedure in procedures[:5]],  # Top 5
                'assessments': [assessment.to_dict() for assessment in assessments[:5]],  # Top 5
                'initiatives': [initiative.to_dict() for initiative in initiatives[:5]],  # Top 5
                'comprehensive_metrics': comprehensive_metrics
            }
        })
    except Exception as e:
        logger.error(f"Error getting comprehensive dashboard: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve dashboard data'
        }), 500
    
    def _calculate_security_maturity(self, training_status, best_practices, checklist_responses):
        """Calculate overall security maturity score"""
        try:
            # Training maturity (30% weight)
            training_score = training_status.get('completion_percentage', 0) * 0.3
            
            # Best practices maturity (25% weight)
            basic_practices = len([p for p in best_practices if p.practice_level == PracticeLevel.BASIC])
            intermediate_practices = len([p for p in best_practices if p.practice_level == PracticeLevel.INTERMEDIATE])
            advanced_practices = len([p for p in best_practices if p.practice_level == PracticeLevel.ADVANCED])
            
            practices_score = (basic_practices * 0.3 + intermediate_practices * 0.5 + advanced_practices * 0.8) * 0.25
            
            # Checklist completion maturity (25% weight)
            checklist_score = min(len(checklist_responses) * 10, 100) * 0.25
            
            # Compliance maturity (20% weight)
            compliance_score = 80 if training_status.get('compliance_status') == 'compliant' else 40
            compliance_score *= 0.2
            
            total_maturity = training_score + practices_score + checklist_score + compliance_score
            
            # Map to maturity levels
            if total_maturity >= 80:
                return "optimizing"
            elif total_maturity >= 60:
                return "managed"
            elif total_maturity >= 40:
                return "defined"
            elif total_maturity >= 20:
                return "developing"
            else:
                return "initial"
                
        except Exception as e:
            logger.error(f"Error calculating security maturity: {e}")
            return "initial"

# =============================================================================
# Reporting Routes
# =============================================================================

@enhanced_security_bp.route('/reports/comprehensive', methods=['GET'])
@cross_origin()
def generate_comprehensive_report():
    """Generate comprehensive security report"""
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
        
        # Generate reports from all systems
        training_system = get_training_system()
        best_practices_system = get_best_practices_system()
        incident_response_system = get_incident_response_system()
        culture_development_system = get_culture_development_system()
        
        training_report = training_system.generate_training_report(
            user_id=user_id,
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )
        
        best_practices_report = best_practices_system.generate_best_practices_report(
            user_id=user_id,
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )
        
        execution_history = incident_response_system.get_execution_history(
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )
        
        culture_report = culture_development_system.generate_culture_report(
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )
        
        comprehensive_report = {
            'report_generated_at': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            },
            'training_report': training_report,
            'best_practices_report': best_practices_report,
            'incident_response_report': {
                'execution_history': [execution.to_dict() for execution in execution_history]
            },
            'culture_report': culture_report,
            'summary': {
                'total_training_completions': training_report.get('training_statistics', {}).get('completed_trainings', 0),
                'total_best_practices': best_practices_report.get('best_practices_statistics', {}).get('total_practices', 0),
                'total_scenario_executions': len(execution_history),
                'total_culture_assessments': culture_report.get('assessment_statistics', {}).get('total_assessments', 0)
            }
        }
        
        return jsonify({
            'success': True,
            'report': comprehensive_report
        })
    except Exception as e:
        logger.error(f"Error generating comprehensive report: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate report'
        }), 500

# =============================================================================
# Health Check Route
# =============================================================================

@enhanced_security_bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """Health check endpoint for all enhanced security systems"""
    try:
        # Test all systems
        training_system = get_training_system()
        best_practices_system = get_best_practices_system()
        incident_response_system = get_incident_response_system()
        culture_development_system = get_culture_development_system()
        
        # Test basic functionality
        training_policies = training_system.get_security_policies()
        best_practices = best_practices_system.get_best_practices()
        scenarios = incident_response_system.get_scenarios()
        assessments = culture_development_system.get_assessments()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'service': 'enhanced_security_awareness',
            'systems': {
                'security_awareness_training': {
                    'status': 'healthy',
                    'policies_count': len(training_policies)
                },
                'security_best_practices': {
                    'status': 'healthy',
                    'practices_count': len(best_practices)
                },
                'incident_response_training': {
                    'status': 'healthy',
                    'scenarios_count': len(scenarios)
                },
                'security_culture_development': {
                    'status': 'healthy',
                    'assessments_count': len(assessments)
                }
            },
            'database': 'connected'
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# Import uuid for response IDs
import uuid 