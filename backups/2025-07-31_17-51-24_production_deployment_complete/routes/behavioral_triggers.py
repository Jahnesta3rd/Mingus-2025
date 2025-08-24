"""
Behavioral Trigger API Routes
Handles trigger management, effectiveness tracking, and trigger event processing
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import joinedload
import uuid

from ..services.behavioral_trigger_service import behavioral_trigger_service
from ..models.behavioral_triggers import (
    BehavioralTrigger, TriggerEvent, TriggerEffectiveness, UserBehaviorPattern,
    MLModel, TriggerTemplate, TriggerSchedule, TriggerType, TriggerCategory,
    TriggerStatus, TriggerPriority
)
from ..models.user import User
from ..database import get_db_session

logger = logging.getLogger(__name__)

behavioral_triggers_bp = Blueprint('behavioral_triggers', __name__, url_prefix='/api/behavioral-triggers')

# Schemas
class BehavioralTriggerSchema(Schema):
    id = fields.Str(dump_only=True)
    trigger_name = fields.Str(required=True)
    trigger_type = fields.Str(required=True)
    trigger_category = fields.Str(required=True)
    trigger_conditions = fields.Dict(required=True)
    trigger_thresholds = fields.Dict()
    trigger_frequency = fields.Str()
    sms_template = fields.Str()
    email_template = fields.Str()
    communication_delay_minutes = fields.Int()
    priority = fields.Str()
    status = fields.Str()
    target_user_segments = fields.List(fields.Str())
    target_user_tiers = fields.List(fields.Str())
    exclusion_conditions = fields.Dict()
    ml_model_enabled = fields.Bool()
    ml_model_name = fields.Str()
    ml_confidence_threshold = fields.Float()
    success_rate = fields.Float(dump_only=True)
    engagement_rate = fields.Float(dump_only=True)
    conversion_rate = fields.Float(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class TriggerEventSchema(Schema):
    id = fields.Str(dump_only=True)
    trigger_id = fields.Str(required=True)
    user_id = fields.Str(required=True)
    event_type = fields.Str()
    event_data = fields.Dict()
    detection_method = fields.Str()
    confidence_score = fields.Float()
    trigger_conditions_met = fields.Dict()
    sms_sent = fields.Bool()
    email_sent = fields.Bool()
    user_engaged = fields.Bool()
    engagement_type = fields.Str()
    engagement_time_minutes = fields.Int()
    conversion_achieved = fields.Bool()
    conversion_type = fields.Str()
    conversion_value = fields.Decimal()
    triggered_at = fields.DateTime(dump_only=True)
    sent_at = fields.DateTime()
    engaged_at = fields.DateTime()
    converted_at = fields.DateTime()

class TriggerTemplateSchema(Schema):
    id = fields.Str(dump_only=True)
    template_name = fields.Str(required=True)
    template_type = fields.Str(required=True)
    trigger_category = fields.Str(required=True)
    subject_line = fields.Str()
    message_content = fields.Str(required=True)
    personalization_variables = fields.List(fields.Str())
    character_limit = fields.Int()
    call_to_action = fields.Str()
    urgency_level = fields.Str()
    is_ab_test_enabled = fields.Bool()
    ab_test_variants = fields.Dict()
    avg_engagement_rate = fields.Float(dump_only=True)
    avg_conversion_rate = fields.Float(dump_only=True)
    total_uses = fields.Int(dump_only=True)
    is_active = fields.Bool()
    is_default = fields.Bool()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class MLModelSchema(Schema):
    id = fields.Str(dump_only=True)
    model_name = fields.Str(required=True)
    model_type = fields.Str(required=True)
    model_version = fields.Str(required=True)
    model_config = fields.Dict(required=True)
    feature_columns = fields.List(fields.Str(), required=True)
    target_column = fields.Str(required=True)
    accuracy_score = fields.Float()
    precision_score = fields.Float()
    recall_score = fields.Float()
    f1_score = fields.Float()
    training_data_size = fields.Int()
    training_date = fields.DateTime()
    training_duration_minutes = fields.Int()
    is_active = fields.Bool()
    is_production = fields.Bool()
    model_file_path = fields.Str()
    model_metadata = fields.Dict()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

# Routes
@behavioral_triggers_bp.route('/triggers', methods=['GET'])
@jwt_required()
def get_triggers():
    """Get all behavioral triggers"""
    try:
        db = get_db_session()
        
        # Get query parameters
        trigger_type = request.args.get('trigger_type')
        trigger_category = request.args.get('trigger_category')
        status = request.args.get('status')
        priority = request.args.get('priority')
        
        # Build query
        query = db.query(BehavioralTrigger)
        
        if trigger_type:
            query = query.filter(BehavioralTrigger.trigger_type == TriggerType(trigger_type))
        if trigger_category:
            query = query.filter(BehavioralTrigger.trigger_category == TriggerCategory(trigger_category))
        if status:
            query = query.filter(BehavioralTrigger.status == TriggerStatus(status))
        if priority:
            query = query.filter(BehavioralTrigger.priority == TriggerPriority(priority))
        
        triggers = query.order_by(BehavioralTrigger.created_at.desc()).all()
        
        schema = BehavioralTriggerSchema(many=True)
        return jsonify({
            'success': True,
            'triggers': schema.dump(triggers)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting triggers: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve triggers'
        }), 500

@behavioral_triggers_bp.route('/triggers', methods=['POST'])
@jwt_required()
def create_trigger():
    """Create a new behavioral trigger"""
    try:
        db = get_db_session()
        current_user_id = get_jwt_identity()
        
        # Validate request data
        schema = BehavioralTriggerSchema()
        data = schema.load(request.json)
        
        # Create trigger
        trigger = BehavioralTrigger(
            id=str(uuid.uuid4()),
            trigger_name=data['trigger_name'],
            trigger_type=TriggerType(data['trigger_type']),
            trigger_category=TriggerCategory(data['trigger_category']),
            trigger_conditions=data['trigger_conditions'],
            trigger_thresholds=data.get('trigger_thresholds'),
            trigger_frequency=data.get('trigger_frequency', 'once'),
            sms_template=data.get('sms_template'),
            email_template=data.get('email_template'),
            communication_delay_minutes=data.get('communication_delay_minutes', 0),
            priority=TriggerPriority(data.get('priority', 'medium')),
            status=TriggerStatus(data.get('status', 'active')),
            target_user_segments=data.get('target_user_segments'),
            target_user_tiers=data.get('target_user_tiers'),
            exclusion_conditions=data.get('exclusion_conditions'),
            ml_model_enabled=data.get('ml_model_enabled', False),
            ml_model_name=data.get('ml_model_name'),
            ml_confidence_threshold=data.get('ml_confidence_threshold', 0.7),
            created_by=current_user_id
        )
        
        db.add(trigger)
        db.commit()
        
        # Create default schedule
        schedule = TriggerSchedule(
            id=str(uuid.uuid4()),
            trigger_id=trigger.id,
            schedule_type='immediate',
            delay_minutes=0,
            optimal_hours=[9, 10, 11, 18, 19, 20],
            optimal_days=[0, 1, 2, 3, 4, 5, 6],
            timezone_aware=True,
            max_triggers_per_day=3,
            max_triggers_per_week=10,
            max_triggers_per_month=30,
            cooldown_hours=24,
            cooldown_days=7,
            respect_user_preferences=True,
            adaptive_scheduling=True
        )
        
        db.add(schedule)
        db.commit()
        
        schema = BehavioralTriggerSchema()
        return jsonify({
            'success': True,
            'trigger': schema.dump(trigger)
        }), 201
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'Validation error',
            'details': e.messages
        }), 400
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating trigger: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to create trigger'
        }), 500

@behavioral_triggers_bp.route('/triggers/<trigger_id>', methods=['GET'])
@jwt_required()
def get_trigger(trigger_id):
    """Get a specific behavioral trigger"""
    try:
        db = get_db_session()
        
        trigger = db.query(BehavioralTrigger).filter(
            BehavioralTrigger.id == trigger_id
        ).first()
        
        if not trigger:
            return jsonify({
                'success': False,
                'error': 'Trigger not found'
            }), 404
        
        schema = BehavioralTriggerSchema()
        return jsonify({
            'success': True,
            'trigger': schema.dump(trigger)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting trigger {trigger_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve trigger'
        }), 500

@behavioral_triggers_bp.route('/triggers/<trigger_id>', methods=['PUT'])
@jwt_required()
def update_trigger(trigger_id):
    """Update a behavioral trigger"""
    try:
        db = get_db_session()
        
        trigger = db.query(BehavioralTrigger).filter(
            BehavioralTrigger.id == trigger_id
        ).first()
        
        if not trigger:
            return jsonify({
                'success': False,
                'error': 'Trigger not found'
            }), 404
        
        # Validate request data
        schema = BehavioralTriggerSchema()
        data = schema.load(request.json, partial=True)
        
        # Update trigger fields
        for field, value in data.items():
            if hasattr(trigger, field):
                if field in ['trigger_type', 'trigger_category', 'priority', 'status']:
                    # Handle enum fields
                    if field == 'trigger_type':
                        setattr(trigger, field, TriggerType(value))
                    elif field == 'trigger_category':
                        setattr(trigger, field, TriggerCategory(value))
                    elif field == 'priority':
                        setattr(trigger, field, TriggerPriority(value))
                    elif field == 'status':
                        setattr(trigger, field, TriggerStatus(value))
                else:
                    setattr(trigger, field, value)
        
        trigger.updated_at = datetime.utcnow()
        db.commit()
        
        schema = BehavioralTriggerSchema()
        return jsonify({
            'success': True,
            'trigger': schema.dump(trigger)
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'Validation error',
            'details': e.messages
        }), 400
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating trigger {trigger_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update trigger'
        }), 500

@behavioral_triggers_bp.route('/triggers/<trigger_id>', methods=['DELETE'])
@jwt_required()
def delete_trigger(trigger_id):
    """Delete a behavioral trigger"""
    try:
        db = get_db_session()
        
        trigger = db.query(BehavioralTrigger).filter(
            BehavioralTrigger.id == trigger_id
        ).first()
        
        if not trigger:
            return jsonify({
                'success': False,
                'error': 'Trigger not found'
            }), 404
        
        db.delete(trigger)
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Trigger deleted successfully'
        }), 200
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting trigger {trigger_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete trigger'
        }), 500

@behavioral_triggers_bp.route('/triggers/<trigger_id>/effectiveness', methods=['GET'])
@jwt_required()
def get_trigger_effectiveness(trigger_id):
    """Get effectiveness metrics for a specific trigger"""
    try:
        time_period = request.args.get('time_period', '30d')
        
        effectiveness = behavioral_trigger_service.get_trigger_effectiveness(
            trigger_id=trigger_id, 
            time_period=time_period
        )
        
        return jsonify({
            'success': True,
            'effectiveness': effectiveness
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting trigger effectiveness {trigger_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve trigger effectiveness'
        }), 500

@behavioral_triggers_bp.route('/events', methods=['GET'])
@jwt_required()
def get_trigger_events():
    """Get trigger events"""
    try:
        db = get_db_session()
        
        # Get query parameters
        user_id = request.args.get('user_id')
        trigger_id = request.args.get('trigger_id')
        event_type = request.args.get('event_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query
        query = db.query(TriggerEvent).options(
            joinedload(TriggerEvent.trigger),
            joinedload(TriggerEvent.user)
        )
        
        if user_id:
            query = query.filter(TriggerEvent.user_id == user_id)
        if trigger_id:
            query = query.filter(TriggerEvent.trigger_id == trigger_id)
        if event_type:
            query = query.filter(TriggerEvent.event_type == event_type)
        if start_date:
            query = query.filter(TriggerEvent.triggered_at >= start_date)
        if end_date:
            query = query.filter(TriggerEvent.triggered_at <= end_date)
        
        events = query.order_by(TriggerEvent.triggered_at.desc()).limit(100).all()
        
        schema = TriggerEventSchema(many=True)
        return jsonify({
            'success': True,
            'events': schema.dump(events)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting trigger events: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve trigger events'
        }), 500

@behavioral_triggers_bp.route('/events/<event_id>/process', methods=['POST'])
@jwt_required()
def process_trigger_event(event_id):
    """Process a trigger event"""
    try:
        db = get_db_session()
        
        event = db.query(TriggerEvent).filter(
            TriggerEvent.id == event_id
        ).first()
        
        if not event:
            return jsonify({
                'success': False,
                'error': 'Trigger event not found'
            }), 404
        
        # Process the event
        success = behavioral_trigger_service.process_trigger_event(event)
        
        return jsonify({
            'success': True,
            'processed': success,
            'message': 'Trigger event processed successfully' if success else 'Trigger event processing failed'
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing trigger event {event_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to process trigger event'
        }), 500

@behavioral_triggers_bp.route('/templates', methods=['GET'])
@jwt_required()
def get_trigger_templates():
    """Get trigger templates"""
    try:
        db = get_db_session()
        
        # Get query parameters
        template_type = request.args.get('template_type')
        trigger_category = request.args.get('trigger_category')
        is_active = request.args.get('is_active')
        
        # Build query
        query = db.query(TriggerTemplate)
        
        if template_type:
            query = query.filter(TriggerTemplate.template_type == template_type)
        if trigger_category:
            query = query.filter(TriggerTemplate.trigger_category == TriggerCategory(trigger_category))
        if is_active is not None:
            query = query.filter(TriggerTemplate.is_active == (is_active.lower() == 'true'))
        
        templates = query.order_by(TriggerTemplate.created_at.desc()).all()
        
        schema = TriggerTemplateSchema(many=True)
        return jsonify({
            'success': True,
            'templates': schema.dump(templates)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting trigger templates: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve trigger templates'
        }), 500

@behavioral_triggers_bp.route('/templates', methods=['POST'])
@jwt_required()
def create_trigger_template():
    """Create a new trigger template"""
    try:
        db = get_db_session()
        current_user_id = get_jwt_identity()
        
        # Validate request data
        schema = TriggerTemplateSchema()
        data = schema.load(request.json)
        
        # Create template
        template = TriggerTemplate(
            id=str(uuid.uuid4()),
            template_name=data['template_name'],
            template_type=data['template_type'],
            trigger_category=TriggerCategory(data['trigger_category']),
            subject_line=data.get('subject_line'),
            message_content=data['message_content'],
            personalization_variables=data.get('personalization_variables'),
            character_limit=data.get('character_limit'),
            call_to_action=data.get('call_to_action'),
            urgency_level=data.get('urgency_level', 'normal'),
            is_ab_test_enabled=data.get('is_ab_test_enabled', False),
            ab_test_variants=data.get('ab_test_variants'),
            is_active=data.get('is_active', True),
            is_default=data.get('is_default', False),
            created_by=current_user_id
        )
        
        db.add(template)
        db.commit()
        
        schema = TriggerTemplateSchema()
        return jsonify({
            'success': True,
            'template': schema.dump(template)
        }), 201
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'Validation error',
            'details': e.messages
        }), 400
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating trigger template: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to create trigger template'
        }), 500

@behavioral_triggers_bp.route('/ml-models', methods=['GET'])
@jwt_required()
def get_ml_models():
    """Get machine learning models"""
    try:
        db = get_db_session()
        
        # Get query parameters
        model_type = request.args.get('model_type')
        is_active = request.args.get('is_active')
        is_production = request.args.get('is_production')
        
        # Build query
        query = db.query(MLModel)
        
        if model_type:
            query = query.filter(MLModel.model_type == model_type)
        if is_active is not None:
            query = query.filter(MLModel.is_active == (is_active.lower() == 'true'))
        if is_production is not None:
            query = query.filter(MLModel.is_production == (is_production.lower() == 'true'))
        
        models = query.order_by(MLModel.created_at.desc()).all()
        
        schema = MLModelSchema(many=True)
        return jsonify({
            'success': True,
            'models': schema.dump(models)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting ML models: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve ML models'
        }), 500

@behavioral_triggers_bp.route('/ml-models', methods=['POST'])
@jwt_required()
def train_ml_model():
    """Train a new machine learning model"""
    try:
        current_user_id = get_jwt_identity()
        
        # Validate request data
        schema = MLModelSchema()
        data = schema.load(request.json)
        
        # Train the model
        model = behavioral_trigger_service.train_ml_model(
            model_name=data['model_name'],
            model_type=data['model_type'],
            training_data={
                'config': data['model_config'],
                'features': data['feature_columns'],
                'target': data['target_column'],
                'data_size': data.get('training_data_size', 0),
                'duration_minutes': data.get('training_duration_minutes', 0),
                'accuracy': data.get('accuracy_score', 0.0),
                'precision': data.get('precision_score', 0.0),
                'recall': data.get('recall_score', 0.0),
                'f1': data.get('f1_score', 0.0)
            }
        )
        
        schema = MLModelSchema()
        return jsonify({
            'success': True,
            'model': schema.dump(model)
        }), 201
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'Validation error',
            'details': e.messages
        }), 400
    except Exception as e:
        logger.error(f"Error training ML model: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to train ML model'
        }), 500

@behavioral_triggers_bp.route('/patterns/<user_id>', methods=['GET'])
@jwt_required()
def get_user_patterns(user_id):
    """Get user behavior patterns"""
    try:
        db = get_db_session()
        
        pattern_type = request.args.get('pattern_type')
        
        query = db.query(UserBehaviorPattern).filter(
            UserBehaviorPattern.user_id == user_id
        )
        
        if pattern_type:
            query = query.filter(UserBehaviorPattern.pattern_type == pattern_type)
        
        patterns = query.order_by(UserBehaviorPattern.pattern_last_updated.desc()).all()
        
        return jsonify({
            'success': True,
            'patterns': [{
                'id': p.id,
                'pattern_type': p.pattern_type,
                'pattern_name': p.pattern_name,
                'pattern_confidence': p.pattern_confidence,
                'baseline_value': p.baseline_value,
                'variance_threshold': p.variance_threshold,
                'trend_direction': p.trend_direction,
                'pattern_last_updated': p.pattern_last_updated.isoformat() if p.pattern_last_updated else None
            } for p in patterns]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user patterns for {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve user patterns'
        }), 500

@behavioral_triggers_bp.route('/patterns/<user_id>', methods=['POST'])
@jwt_required()
def update_user_patterns(user_id):
    """Update user behavior patterns"""
    try:
        data = request.json
        pattern_type = data.get('pattern_type')
        pattern_data = data.get('pattern_data')
        
        if not pattern_type or not pattern_data:
            return jsonify({
                'success': False,
                'error': 'pattern_type and pattern_data are required'
            }), 400
        
        behavioral_trigger_service.update_user_behavior_patterns(
            user_id=user_id,
            pattern_type=pattern_type,
            pattern_data=pattern_data
        )
        
        return jsonify({
            'success': True,
            'message': 'User behavior patterns updated successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating user patterns for {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update user patterns'
        }), 500

@behavioral_triggers_bp.route('/detect/<user_id>', methods=['POST'])
@jwt_required()
def detect_triggers(user_id):
    """Detect triggers for a user based on provided data"""
    try:
        data = request.json
        trigger_types = data.get('trigger_types', [])
        
        triggered_events = []
        
        # Detect financial triggers
        if 'financial' in trigger_types and 'financial_data' in data:
            events = behavioral_trigger_service.detect_financial_triggers(
                user_id, data['financial_data']
            )
            triggered_events.extend(events)
        
        # Detect health/wellness triggers
        if 'health_wellness' in trigger_types and 'health_data' in data and 'financial_data' in data:
            events = behavioral_trigger_service.detect_health_wellness_triggers(
                user_id, data['health_data'], data['financial_data']
            )
            triggered_events.extend(events)
        
        # Detect career triggers
        if 'career' in trigger_types and 'career_data' in data:
            events = behavioral_trigger_service.detect_career_triggers(
                user_id, data['career_data']
            )
            triggered_events.extend(events)
        
        # Detect life event triggers
        if 'life_event' in trigger_types and 'user_profile' in data:
            events = behavioral_trigger_service.detect_life_event_triggers(
                user_id, data['user_profile']
            )
            triggered_events.extend(events)
        
        # Detect engagement triggers
        if 'engagement' in trigger_types and 'engagement_data' in data:
            events = behavioral_trigger_service.detect_engagement_triggers(
                user_id, data['engagement_data']
            )
            triggered_events.extend(events)
        
        schema = TriggerEventSchema(many=True)
        return jsonify({
            'success': True,
            'triggered_events': schema.dump(triggered_events),
            'count': len(triggered_events)
        }), 200
        
    except Exception as e:
        logger.error(f"Error detecting triggers for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to detect triggers'
        }), 500

@behavioral_triggers_bp.route('/effectiveness', methods=['GET'])
@jwt_required()
def get_overall_effectiveness():
    """Get overall trigger effectiveness metrics"""
    try:
        time_period = request.args.get('time_period', '30d')
        
        effectiveness = behavioral_trigger_service.get_trigger_effectiveness(
            time_period=time_period
        )
        
        return jsonify({
            'success': True,
            'effectiveness': effectiveness
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting overall effectiveness: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve effectiveness metrics'
        }), 500 