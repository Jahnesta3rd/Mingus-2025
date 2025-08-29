"""
Assessment Service

This module provides assessment calculation and processing services,
integrating with existing calculator services and database operations.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timezone, timedelta
import logging
import time
from typing import Dict, Any, List, Optional
import json

# Import existing services
from backend.services.calculator_integration_service import CalculatorIntegrationService
from backend.services.calculator_database_service import CalculatorDatabaseService

# Import models
from backend.models.assessment_models import Assessment, UserAssessment, AssessmentResult, Lead, EmailSequence, EmailLog

logger = logging.getLogger(__name__)

class AssessmentService:
    """Comprehensive assessment service for Mingus"""
    
    def __init__(self, db_session: Session, config: Dict[str, Any]):
        self.db = db_session
        self.config = config
        self.calculator_service = CalculatorIntegrationService(db_session, config)
        self.database_service = CalculatorDatabaseService(db_session, config)
    
    def get_available_assessments(self, user_authenticated: bool = False) -> List[Dict[str, Any]]:
        """Get available assessments with statistics"""
        try:
            # Query active assessments
            query = self.db.query(Assessment).filter(Assessment.is_active == True)
            
            if not user_authenticated:
                # Anonymous users only see assessments that allow anonymous access
                query = query.filter(Assessment.allow_anonymous == True)
            
            assessments = query.all()
            
            # Get completion statistics
            stats_query = self.db.query(
                Assessment.id,
                func.count(UserAssessment.id).label('total_attempts'),
                func.count(UserAssessment.id).filter(UserAssessment.is_complete == True).label('completed_attempts'),
                func.avg(UserAssessment.score).label('average_score'),
                func.avg(UserAssessment.time_spent_seconds).label('average_time_seconds')
            ).outerjoin(UserAssessment).group_by(Assessment.id)
            
            stats = {row.id: {
                'total_attempts': row.total_attempts or 0,
                'completed_attempts': row.completed_attempts or 0,
                'completion_rate': round((row.completed_attempts or 0) * 100.0 / (row.total_attempts or 1), 2),
                'average_score': round(row.average_score or 0, 1),
                'average_time_minutes': round((row.average_time_seconds or 0) / 60, 1)
            } for row in stats_query.all()}
            
            # Format response
            assessment_list = []
            for assessment in assessments:
                assessment_data = assessment.to_dict()
                assessment_data['stats'] = stats.get(assessment.id, {})
                assessment_list.append(assessment_data)
            
            return assessment_list
            
        except Exception as e:
            logger.error(f"Error getting available assessments: {e}")
            raise
    
    def validate_assessment_responses(self, responses: Dict[str, Any], assessment_type: str) -> Dict[str, Any]:
        """Validate assessment responses against schema"""
        try:
            # Get assessment template
            assessment = self.db.query(Assessment).filter(
                Assessment.type == assessment_type,
                Assessment.is_active == True
            ).first()
            
            if not assessment:
                return {'valid': False, 'error': 'Assessment not found or inactive'}
            
            # Validate responses against questions schema
            questions = assessment.questions_json
            required_questions = [q['id'] for q in questions if q.get('required', True)]
            
            # Check required questions
            for question_id in required_questions:
                if question_id not in responses:
                    return {'valid': False, 'error': f'Missing required question: {question_id}'}
            
            # Validate response types
            for question in questions:
                question_id = question['id']
                if question_id in responses:
                    response = responses[question_id]
                    question_type = question['type']
                    
                    if question_type == 'radio':
                        if not isinstance(response, str):
                            return {'valid': False, 'error': f'Invalid response type for {question_id}'}
                        valid_options = [opt['value'] for opt in question.get('options', [])]
                        if response not in valid_options:
                            return {'valid': False, 'error': f'Invalid option for {question_id}'}
                    
                    elif question_type == 'checkbox':
                        if not isinstance(response, list):
                            return {'valid': False, 'error': f'Invalid response type for {question_id}'}
                        valid_options = [opt['value'] for opt in question.get('options', [])]
                        if not all(opt in valid_options for opt in response):
                            return {'valid': False, 'error': f'Invalid option for {question_id}'}
                    
                    elif question_type == 'rating':
                        if not isinstance(response, (int, float)) or response < 1 or response > 5:
                            return {'valid': False, 'error': f'Invalid rating for {question_id}'}
            
            return {'valid': True, 'assessment': assessment}
            
        except Exception as e:
            logger.error(f"Error validating assessment responses: {e}")
            return {'valid': False, 'error': 'Validation error'}
    
    def calculate_assessment_score(self, responses: Dict[str, Any], assessment: Assessment) -> Dict[str, Any]:
        """Calculate assessment score using exact calculation logic"""
        try:
            start_time = time.time()
            
            # Use existing calculator service for scoring
            score_result = self.calculator_service._calculate_assessment_score(responses)
            
            # Determine risk level based on score
            score = score_result.get('score', 0)
            risk_level = self._determine_risk_level(score, assessment.type)
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                'score': score,
                'risk_level': risk_level,
                'segment': score_result.get('segment', 'stress-free'),
                'product_tier': score_result.get('product_tier', 'Budget ($10)'),
                'insights': score_result.get('insights', []),
                'recommendations': score_result.get('recommendations', []),
                'processing_time_ms': processing_time_ms,
                # Assessment-specific scores
                'automation_score': score_result.get('automation_score'),
                'augmentation_score': score_result.get('augmentation_score'),
                'relationship_stress_score': score_result.get('relationship_stress_score'),
                'financial_harmony_score': score_result.get('financial_harmony_score'),
                'tax_efficiency_score': score_result.get('tax_efficiency_score'),
                'potential_savings': score_result.get('potential_savings'),
                'market_position_score': score_result.get('market_position_score')
            }
            
        except Exception as e:
            logger.error(f"Error calculating assessment score: {e}")
            return {
                'score': 0,
                'risk_level': 'medium',
                'segment': 'stress-free',
                'product_tier': 'Budget ($10)',
                'insights': [],
                'recommendations': [],
                'processing_time_ms': 0
            }
    
    def _determine_risk_level(self, score: int, assessment_type: str) -> str:
        """Determine risk level based on score and assessment type"""
        if assessment_type == 'ai_job_risk':
            # AI job risk assessment - higher scores = higher risk
            if score >= 80:
                return 'critical'
            elif score >= 60:
                return 'high'
            elif score >= 40:
                return 'medium'
            else:
                return 'low'
        else:
            # Other assessments - higher scores = lower risk
            if score >= 70:
                return 'low'
            elif score >= 40:
                return 'medium'
            elif score >= 20:
                return 'high'
            else:
                return 'critical'
    
    def save_assessment_results(self, user_assessment: UserAssessment, score_result: Dict[str, Any]) -> AssessmentResult:
        """Save assessment results to database"""
        try:
            # Create assessment results record
            assessment_result = AssessmentResult(
                user_assessment_id=user_assessment.id,
                insights_json={
                    'segment': score_result['segment'],
                    'product_tier': score_result['product_tier'],
                    'insights': score_result['insights'],
                    'recommendations': score_result['recommendations']
                },
                recommendations_json={
                    'action_items': score_result['recommendations'],
                    'next_steps': [
                        'Review your personalized insights',
                        'Consider upgrading for detailed analysis',
                        'Schedule a consultation for personalized guidance'
                    ]
                },
                analysis_version='1.0',
                processing_time_ms=score_result.get('processing_time_ms', 0)
            )
            
            # Add assessment-specific scores
            assessment_type = user_assessment.assessment.type
            if assessment_type == 'ai_job_risk':
                assessment_result.automation_score = score_result.get('automation_score')
                assessment_result.augmentation_score = score_result.get('augmentation_score')
            elif assessment_type == 'relationship_impact':
                assessment_result.relationship_stress_score = score_result.get('relationship_stress_score')
                assessment_result.financial_harmony_score = score_result.get('financial_harmony_score')
            elif assessment_type == 'tax_impact':
                assessment_result.tax_efficiency_score = score_result.get('tax_efficiency_score')
                assessment_result.potential_savings = score_result.get('potential_savings')
            elif assessment_type == 'income_comparison':
                assessment_result.market_position_score = score_result.get('market_position_score')
            
            self.db.add(assessment_result)
            self.db.commit()
            
            return assessment_result
            
        except Exception as e:
            logger.error(f"Error saving assessment results: {e}")
            self.db.rollback()
            raise
    
    def create_lead_record(self, email: str, first_name: str, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create lead record for anonymous users"""
        try:
            # Check if lead already exists
            existing_lead = self.db.query(Lead).filter(Lead.email == email).first()
            
            if existing_lead:
                return {
                    'success': True,
                    'lead_id': str(existing_lead.id),
                    'existing': True
                }
            
            # Calculate lead score for sales prioritization
            lead_score = self._calculate_lead_score(assessment_data)
            
            # Create new lead record
            lead = Lead(
                email=email,
                first_name=first_name,
                assessment_type=assessment_data.get('type'),
                assessment_score=assessment_data.get('score'),
                segment=assessment_data.get('segment'),
                risk_level=assessment_data.get('risk_level'),
                lead_score=lead_score,
                source='assessment'
            )
            
            self.db.add(lead)
            self.db.commit()
            
            return {
                'success': True,
                'lead_id': str(lead.id),
                'lead_score': lead_score,
                'existing': False
            }
            
        except Exception as e:
            logger.error(f"Error creating lead record: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_lead_score(self, assessment_data: Dict[str, Any]) -> int:
        """Calculate lead score for sales prioritization"""
        lead_score = 0
        
        # Score based on assessment score
        score = assessment_data.get('score', 0)
        if score > 70:
            lead_score += 30
        elif score > 50:
            lead_score += 20
        elif score > 30:
            lead_score += 10
        
        # Score based on risk level
        risk_level = assessment_data.get('risk_level')
        if risk_level == 'critical':
            lead_score += 25
        elif risk_level == 'high':
            lead_score += 20
        elif risk_level == 'medium':
            lead_score += 15
        
        # Score based on segment
        segment = assessment_data.get('segment')
        if segment in ['emotional-manager', 'crisis-mode']:
            lead_score += 20
        elif segment == 'relationship-spender':
            lead_score += 15
        
        # Score based on assessment type
        assessment_type = assessment_data.get('type')
        if assessment_type == 'ai_job_risk':
            lead_score += 10  # High-value assessment
        elif assessment_type == 'tax_impact':
            lead_score += 8   # Financial impact assessment
        
        return min(lead_score, 100)  # Cap at 100
    
    def get_assessment_results(self, user_assessment_id: str, user_id: str, subscription_tier: str = 'free') -> Dict[str, Any]:
        """Get assessment results with tier-based access control"""
        try:
            # Get user assessment
            user_assessment = self.db.query(UserAssessment).filter(
                UserAssessment.id == user_assessment_id
            ).first()
            
            if not user_assessment:
                return {'error': 'Assessment not found'}
            
            # Check authorization
            if user_assessment.user_id != user_id:
                return {'error': 'Unauthorized access to assessment results'}
            
            # Get assessment details
            assessment = user_assessment.assessment
            
            # Get assessment results
            assessment_result = self.db.query(AssessmentResult).filter(
                AssessmentResult.user_assessment_id == user_assessment_id
            ).first()
            
            # Prepare base response
            response_data = {
                'assessment': {
                    'id': str(user_assessment.id),
                    'type': assessment.type,
                    'title': assessment.title,
                    'version': user_assessment.assessment_version,
                    'completed_at': user_assessment.completed_at.isoformat() if user_assessment.completed_at else None,
                    'time_spent_minutes': round(user_assessment.time_spent_seconds / 60, 1)
                },
                'results': {
                    'score': user_assessment.score,
                    'risk_level': user_assessment.risk_level,
                    'segment': assessment_result.insights_json.get('segment') if assessment_result else None,
                    'product_tier': assessment_result.insights_json.get('product_tier') if assessment_result else None
                }
            }
            
            # Add insights and recommendations based on subscription tier
            if subscription_tier == 'free':
                # Free tier: limited insights
                if assessment_result:
                    response_data['insights'] = assessment_result.insights_json.get('insights', [])[:3]
                    response_data['recommendations'] = assessment_result.recommendations_json.get('action_items', [])[:2]
                    response_data['upgrade_message'] = 'Upgrade to see all insights and detailed recommendations'
            else:
                # Paid tiers: full insights
                if assessment_result:
                    response_data['insights'] = assessment_result.insights_json.get('insights', [])
                    response_data['recommendations'] = assessment_result.recommendations_json.get('action_items', [])
                    response_data['detailed_analysis'] = assessment_result.insights_json
                    response_data['next_steps'] = assessment_result.recommendations_json.get('next_steps', [])
                    
                    # Add assessment-specific detailed data
                    response_data.update(self._get_assessment_specific_data(assessment_result, assessment.type))
            
            response_data['subscription_tier'] = subscription_tier
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error getting assessment results: {e}")
            return {'error': 'Failed to retrieve assessment results'}
    
    def _get_assessment_specific_data(self, assessment_result: AssessmentResult, assessment_type: str) -> Dict[str, Any]:
        """Get assessment-specific detailed data"""
        if assessment_type == 'ai_job_risk':
            return {
                'ai_analysis': {
                    'automation_score': assessment_result.automation_score,
                    'augmentation_score': assessment_result.augmentation_score,
                    'risk_factors': assessment_result.risk_factors or [],
                    'mitigation_strategies': assessment_result.mitigation_strategies or []
                }
            }
        elif assessment_type == 'tax_impact':
            return {
                'tax_analysis': {
                    'tax_efficiency_score': assessment_result.tax_efficiency_score,
                    'potential_savings': float(assessment_result.potential_savings) if assessment_result.potential_savings else 0,
                    'optimization_opportunities': assessment_result.tax_optimization_opportunities or []
                }
            }
        elif assessment_type == 'income_comparison':
            return {
                'market_analysis': {
                    'market_position_score': assessment_result.market_position_score,
                    'salary_benchmark_data': assessment_result.salary_benchmark_data or {},
                    'negotiation_leverage_points': assessment_result.negotiation_leverage_points or []
                }
            }
        elif assessment_type == 'relationship_impact':
            return {
                'relationship_analysis': {
                    'relationship_stress_score': assessment_result.relationship_stress_score,
                    'financial_harmony_score': assessment_result.financial_harmony_score,
                    'cost_projections': assessment_result.cost_projections or {},
                    'risk_factors': assessment_result.risk_factors or []
                }
            }
        
        return {}
    
    def get_assessment_stats(self) -> Dict[str, Any]:
        """Get real-time assessment statistics for social proof"""
        try:
            # Get today's date
            today = datetime.now(timezone.utc).date()
            week_ago = today - timedelta(days=7)
            
            # Calculate statistics
            today_stats = self.db.query(
                func.count(UserAssessment.id).label('total'),
                func.count(UserAssessment.id).filter(UserAssessment.is_complete == True).label('completed'),
                func.avg(UserAssessment.score).label('average_score')
            ).filter(
                func.date(UserAssessment.created_at) == today
            ).first()
            
            week_stats = self.db.query(
                func.count(UserAssessment.id).label('total'),
                func.count(UserAssessment.id).filter(UserAssessment.is_complete == True).label('completed'),
                func.avg(UserAssessment.score).label('average_score')
            ).filter(
                func.date(UserAssessment.created_at) >= week_ago
            ).first()
            
            # Get assessment type breakdown
            type_stats = self.db.query(
                Assessment.type,
                func.count(UserAssessment.id).label('total_attempts'),
                func.avg(UserAssessment.score).label('average_score')
            ).join(UserAssessment).filter(
                UserAssessment.is_complete == True
            ).group_by(Assessment.type).all()
            
            # Get risk level distribution
            risk_stats = self.db.query(
                UserAssessment.risk_level,
                func.count(UserAssessment.id).label('count')
            ).filter(
                UserAssessment.is_complete == True
            ).group_by(UserAssessment.risk_level).all()
            
            # Format response
            stats_data = {
                'today': {
                    'total_assessments': today_stats.total or 0,
                    'completed_assessments': today_stats.completed or 0,
                    'completion_rate': round((today_stats.completed or 0) * 100.0 / (today_stats.total or 1), 1),
                    'average_score': round(today_stats.average_score or 0, 1)
                },
                'this_week': {
                    'total_assessments': week_stats.total or 0,
                    'completed_assessments': week_stats.completed or 0,
                    'completion_rate': round((week_stats.completed or 0) * 100.0 / (week_stats.total or 1), 1),
                    'average_score': round(week_stats.average_score or 0, 1)
                },
                'by_assessment_type': {
                    stat.type: {
                        'total_attempts': stat.total_attempts,
                        'average_score': round(stat.average_score or 0, 1)
                    } for stat in type_stats
                },
                'risk_distribution': {
                    stat.risk_level: stat.count for stat in risk_stats
                },
                'total_users_helped': self.db.query(UserAssessment).filter(
                    UserAssessment.is_complete == True
                ).count()
            }
            
            return stats_data
            
        except Exception as e:
            logger.error(f"Error getting assessment stats: {e}")
            return {
                'error': 'Failed to retrieve statistics',
                'today': {'total_assessments': 0, 'completed_assessments': 0, 'completion_rate': 0, 'average_score': 0},
                'this_week': {'total_assessments': 0, 'completed_assessments': 0, 'completion_rate': 0, 'average_score': 0},
                'by_assessment_type': {},
                'risk_distribution': {},
                'total_users_helped': 0
            }
    
    def trigger_email_sequence(self, lead_id: str, assessment_type: str, segment: str, risk_level: str) -> bool:
        """Trigger email sequence based on assessment results"""
        try:
            # Find appropriate email sequence
            sequence = self.db.query(EmailSequence).filter(
                EmailSequence.is_active == True,
                or_(
                    EmailSequence.assessment_type == assessment_type,
                    EmailSequence.assessment_type.is_(None)
                ),
                or_(
                    EmailSequence.segment == segment,
                    EmailSequence.segment.is_(None)
                ),
                or_(
                    EmailSequence.risk_level == risk_level,
                    EmailSequence.risk_level.is_(None)
                )
            ).first()
            
            if not sequence:
                logger.info(f"No email sequence found for assessment_type={assessment_type}, segment={segment}, risk_level={risk_level}")
                return False
            
            # Create email log entries for the sequence
            for i, email_config in enumerate(sequence.emails_json):
                delay_hours = sequence.delay_hours[i] if i < len(sequence.delay_hours) else 24
                
                email_log = EmailLog(
                    lead_id=lead_id,
                    email_sequence_id=sequence.id,
                    email_type=email_config.get('type', 'follow_up'),
                    subject=email_config.get('subject', ''),
                    body=email_config.get('body', ''),
                    status='pending'
                )
                
                self.db.add(email_log)
            
            self.db.commit()
            logger.info(f"Triggered email sequence {sequence.id} for lead {lead_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error triggering email sequence: {e}")
            self.db.rollback()
            return False
