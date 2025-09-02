"""
AI Calculator Privacy Controls

Comprehensive privacy controls for the AI Job Impact Calculator including:
- GDPR compliance with explicit consent management
- CCPA compliance for California users
- Data processing transparency
- User consent preferences
- Privacy policy enforcement
- Data subject rights management
- Privacy dashboard functionality
- Consent withdrawal mechanisms
- Data processing purpose management
"""

import logging
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_, func, desc, asc
from sqlalchemy.exc import SQLAlchemyError
from flask import request, current_app

from backend.gdpr.compliance_manager import GDPRComplianceManager, ConsentType, RequestType, RequestStatus
from backend.security.ai_calculator_audit import AICalculatorAuditService, AICalculatorAuditEventType

logger = logging.getLogger(__name__)


class PrivacyControlType(Enum):
    """Types of privacy controls"""
    CONSENT_MANAGEMENT = "consent_management"
    DATA_PROCESSING = "data_processing"
    DATA_RIGHTS = "data_rights"
    PRIVACY_POLICY = "privacy_policy"
    COOKIE_MANAGEMENT = "cookie_management"
    TRANSPARENCY = "transparency"


class DataProcessingPurpose(Enum):
    """Data processing purposes for AI Calculator"""
    ASSESSMENT_ANALYSIS = "assessment_analysis"
    PERSONALIZED_RECOMMENDATIONS = "personalized_recommendations"
    EMAIL_COMMUNICATIONS = "email_communications"
    ANALYTICS_IMPROVEMENT = "analytics_improvement"
    MARKETING = "marketing"
    CONVERSION_TRACKING = "conversion_tracking"
    SECURITY_MONITORING = "security_monitoring"
    COMPLIANCE_REPORTING = "compliance_reporting"


class UserConsentStatus(Enum):
    """User consent status"""
    GRANTED = "granted"
    WITHDRAWN = "withdrawn"
    PENDING = "pending"
    EXPIRED = "expired"
    NOT_PROVIDED = "not_provided"


@dataclass
class PrivacyPreference:
    """User privacy preference structure"""
    user_id: Optional[str]
    email: str
    consent_type: ConsentType
    purpose: DataProcessingPurpose
    granted: bool
    granted_at: datetime
    withdrawn_at: Optional[datetime] = None
    ip_address: str = ""
    user_agent: str = ""
    consent_version: str = "1.0"
    privacy_policy_version: str = "1.0"
    cookie_policy_version: str = "1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PrivacyPolicy:
    """Privacy policy structure"""
    version: str
    effective_date: datetime
    language: str = "en"
    region: str = "global"
    content: str = ""
    data_controller: str = "MINGUS"
    contact_email: str = "privacy@mingusapp.com"
    data_processing_purposes: List[DataProcessingPurpose] = field(default_factory=list)
    data_categories: List[str] = field(default_factory=list)
    user_rights: List[str] = field(default_factory=list)
    retention_periods: Dict[str, str] = field(default_factory=dict)


class AICalculatorPrivacyControls:
    """Comprehensive privacy controls for AI Calculator"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.gdpr_manager = GDPRComplianceManager(db_session)
        self.audit_service = AICalculatorAuditService(db_session)
        
        # Initialize privacy tables
        self._init_privacy_tables()
        
        # Privacy policy configuration
        self.privacy_policy = self._get_default_privacy_policy()
    
    def _init_privacy_tables(self):
        """Initialize privacy-related tables"""
        try:
            # Create privacy preferences table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS ai_calculator_privacy_preferences (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id UUID,
                    email VARCHAR(255) NOT NULL,
                    consent_type VARCHAR(50) NOT NULL,
                    purpose VARCHAR(100) NOT NULL,
                    granted BOOLEAN NOT NULL DEFAULT FALSE,
                    granted_at TIMESTAMP WITH TIME ZONE,
                    withdrawn_at TIMESTAMP WITH TIME ZONE,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    consent_version VARCHAR(20) DEFAULT '1.0',
                    privacy_policy_version VARCHAR(20) DEFAULT '1.0',
                    cookie_policy_version VARCHAR(20) DEFAULT '1.0',
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # Create indexes
            self.db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_ai_calculator_privacy_email 
                ON ai_calculator_privacy_preferences(email)
            """))
            
            self.db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_ai_calculator_privacy_user_id 
                ON ai_calculator_privacy_preferences(user_id)
            """))
            
            self.db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_ai_calculator_privacy_consent_type 
                ON ai_calculator_privacy_preferences(consent_type)
            """))
            
            self.db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_ai_calculator_privacy_granted 
                ON ai_calculator_privacy_preferences(granted)
            """))
            
            self.db.commit()
            logger.info("AI Calculator privacy tables initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize privacy tables: {e}")
            self.db.rollback()
    
    def _get_default_privacy_policy(self) -> PrivacyPolicy:
        """Get default privacy policy for AI Calculator"""
        return PrivacyPolicy(
            version="1.0",
            effective_date=datetime(2025, 1, 27, tzinfo=timezone.utc),
            language="en",
            region="global",
            data_controller="MINGUS",
            contact_email="privacy@mingusapp.com",
            data_processing_purposes=[
                DataProcessingPurpose.ASSESSMENT_ANALYSIS,
                DataProcessingPurpose.PERSONALIZED_RECOMMENDATIONS,
                DataProcessingPurpose.EMAIL_COMMUNICATIONS,
                DataProcessingPurpose.ANALYTICS_IMPROVEMENT
            ],
            data_categories=[
                "Personal identification data (name, email)",
                "Professional information (job title, industry, experience)",
                "Assessment responses and preferences",
                "Technical data (IP address, user agent, session data)",
                "Usage analytics and interaction data"
            ],
            user_rights=[
                "Right to access personal data",
                "Right to rectification of inaccurate data",
                "Right to erasure (right to be forgotten)",
                "Right to data portability",
                "Right to object to processing",
                "Right to restrict processing",
                "Right to withdraw consent",
                "Right to lodge a complaint with supervisory authority"
            ],
            retention_periods={
                "assessment_data": "2 years",
                "user_profile": "2 years",
                "analytics_data": "1 year",
                "audit_logs": "7 years",
                "consent_records": "5 years"
            }
        )
    
    def get_privacy_policy(self, language: str = "en", region: str = "global") -> Dict[str, Any]:
        """Get privacy policy for specified language and region"""
        policy = self.privacy_policy
        
        # Add region-specific modifications
        if region == "EU":
            policy.user_rights.extend([
                "Right to data portability in machine-readable format",
                "Right to compensation for damages"
            ])
        elif region == "CA":
            policy.user_rights.extend([
                "Right to know what personal information is collected",
                "Right to know whether personal information is sold or disclosed",
                "Right to say no to the sale of personal information",
                "Right to equal service and price"
            ])
        
        return {
            'version': policy.version,
            'effective_date': policy.effective_date.isoformat(),
            'language': language,
            'region': region,
            'data_controller': policy.data_controller,
            'contact_email': policy.contact_email,
            'data_processing_purposes': [p.value for p in policy.data_processing_purposes],
            'data_categories': policy.data_categories,
            'user_rights': policy.user_rights,
            'retention_periods': policy.retention_periods,
            'last_updated': datetime.now(timezone.utc).isoformat()
        }
    
    def create_consent_record(self, user_id: Optional[str], email: str,
                            consent_types: List[str], purposes: List[str],
                            ip_address: str = None, user_agent: str = None) -> bool:
        """Create consent records for AI Calculator"""
        try:
            if not ip_address:
                ip_address = request.remote_addr or 'unknown'
            if not user_agent:
                user_agent = request.headers.get('User-Agent', 'unknown')
            
            # Create consent records for each type and purpose
            for consent_type in consent_types:
                for purpose in purposes:
                    # Insert into privacy preferences table
                    self.db.execute(text("""
                        INSERT INTO ai_calculator_privacy_preferences (
                            user_id, email, consent_type, purpose, granted, granted_at,
                            ip_address, user_agent, consent_version, privacy_policy_version
                        ) VALUES (
                            :user_id, :email, :consent_type, :purpose, TRUE, :granted_at,
                            :ip_address, :user_agent, :consent_version, :privacy_policy_version
                        )
                    """), {
                        'user_id': user_id,
                        'email': email,
                        'consent_type': consent_type,
                        'purpose': purpose,
                        'granted_at': datetime.now(timezone.utc),
                        'ip_address': ip_address,
                        'user_agent': user_agent,
                        'consent_version': self.privacy_policy.version,
                        'privacy_policy_version': self.privacy_policy.version
                    })
            
            self.db.commit()
            
            # Log consent creation
            self.audit_service.log_gdpr_consent(
                user_id=user_id,
                email=email,
                consent_types=consent_types,
                granted=True,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(f"Consent records created for {email}: {consent_types}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create consent records: {e}")
            self.db.rollback()
            return False
    
    def check_consent(self, user_id: Optional[str], email: str,
                     consent_type: str, purpose: str) -> bool:
        """Check if user has granted consent for specific type and purpose"""
        try:
            result = self.db.execute(text("""
                SELECT granted, withdrawn_at 
                FROM ai_calculator_privacy_preferences 
                WHERE (user_id = :user_id OR email = :email)
                AND consent_type = :consent_type 
                AND purpose = :purpose
                ORDER BY granted_at DESC 
                LIMIT 1
            """), {
                'user_id': user_id,
                'email': email,
                'consent_type': consent_type,
                'purpose': purpose
            }).fetchone()
            
            if result:
                return result.granted and not result.withdrawn_at
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check consent: {e}")
            return False
    
    def withdraw_consent(self, user_id: Optional[str], email: str,
                        consent_types: List[str], purposes: List[str]) -> bool:
        """Withdraw user consent"""
        try:
            # Update consent records to mark as withdrawn
            for consent_type in consent_types:
                for purpose in purposes:
                    self.db.execute(text("""
                        UPDATE ai_calculator_privacy_preferences 
                        SET granted = FALSE, withdrawn_at = :withdrawn_at
                        WHERE (user_id = :user_id OR email = :email)
                        AND consent_type = :consent_type 
                        AND purpose = :purpose
                        AND granted = TRUE
                    """), {
                        'user_id': user_id,
                        'email': email,
                        'consent_type': consent_type,
                        'purpose': purpose,
                        'withdrawn_at': datetime.now(timezone.utc)
                    })
            
            self.db.commit()
            
            # Log consent withdrawal
            self.audit_service.log_gdpr_consent(
                user_id=user_id,
                email=email,
                consent_types=consent_types,
                granted=False,
                ip_address=request.remote_addr or 'unknown',
                user_agent=request.headers.get('User-Agent', 'unknown')
            )
            
            logger.info(f"Consent withdrawn for {email}: {consent_types}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to withdraw consent: {e}")
            self.db.rollback()
            return False
    
    def get_user_consent_summary(self, user_id: Optional[str], email: str) -> Dict[str, Any]:
        """Get comprehensive consent summary for user"""
        try:
            result = self.db.execute(text("""
                SELECT 
                    consent_type,
                    purpose,
                    granted,
                    granted_at,
                    withdrawn_at,
                    consent_version
                FROM ai_calculator_privacy_preferences 
                WHERE (user_id = :user_id OR email = :email)
                ORDER BY granted_at DESC
            """), {
                'user_id': user_id,
                'email': email
            }).fetchall()
            
            consent_summary = {
                'user_id': user_id,
                'email': email,
                'consents': [],
                'active_consents': [],
                'withdrawn_consents': [],
                'consent_status': {}
            }
            
            for row in result:
                consent_record = {
                    'consent_type': row.consent_type,
                    'purpose': row.purpose,
                    'granted': row.granted,
                    'granted_at': row.granted_at.isoformat() if row.granted_at else None,
                    'withdrawn_at': row.withdrawn_at.isoformat() if row.withdrawn_at else None,
                    'consent_version': row.consent_version,
                    'status': 'active' if row.granted and not row.withdrawn_at else 'withdrawn'
                }
                
                consent_summary['consents'].append(consent_record)
                
                if consent_record['status'] == 'active':
                    consent_summary['active_consents'].append(consent_record)
                else:
                    consent_summary['withdrawn_consents'].append(consent_record)
                
                # Track status by consent type
                key = f"{row.consent_type}_{row.purpose}"
                consent_summary['consent_status'][key] = consent_record['status']
            
            return consent_summary
            
        except Exception as e:
            logger.error(f"Failed to get user consent summary: {e}")
            return {}
    
    def get_privacy_dashboard_data(self, user_id: Optional[str], email: str) -> Dict[str, Any]:
        """Get privacy dashboard data for user"""
        try:
            consent_summary = self.get_user_consent_summary(user_id, email)
            
            # Get data processing summary
            processing_summary = self._get_data_processing_summary(user_id, email)
            
            # Get data retention information
            retention_info = self._get_data_retention_info(user_id, email)
            
            # Get recent privacy activities
            recent_activities = self._get_recent_privacy_activities(user_id, email)
            
            return {
                'user_id': user_id,
                'email': email,
                'consent_summary': consent_summary,
                'data_processing': processing_summary,
                'data_retention': retention_info,
                'recent_activities': recent_activities,
                'privacy_policy': self.get_privacy_policy(),
                'user_rights': self.privacy_policy.user_rights,
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get privacy dashboard data: {e}")
            return {}
    
    def _get_data_processing_summary(self, user_id: Optional[str], email: str) -> Dict[str, Any]:
        """Get data processing summary for user"""
        try:
            # Get assessment data count
            assessment_count = self.db.execute(text("""
                SELECT COUNT(*) as count 
                FROM ai_job_assessments 
                WHERE user_id = :user_id OR email = :email
            """), {
                'user_id': user_id,
                'email': email
            }).fetchone().count
            
            # Get conversion data count
            conversion_count = self.db.execute(text("""
                SELECT COUNT(*) as count 
                FROM ai_calculator_conversions 
                WHERE assessment_id IN (
                    SELECT id FROM ai_job_assessments 
                    WHERE user_id = :user_id OR email = :email
                )
            """), {
                'user_id': user_id,
                'email': email
            }).fetchone().count
            
            return {
                'assessments_processed': assessment_count,
                'conversions_tracked': conversion_count,
                'data_categories': [
                    'Personal identification data',
                    'Professional information',
                    'Assessment responses',
                    'Technical data',
                    'Usage analytics'
                ],
                'processing_purposes': [
                    'Assessment analysis',
                    'Personalized recommendations',
                    'Email communications',
                    'Analytics improvement'
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get data processing summary: {e}")
            return {}
    
    def _get_data_retention_info(self, user_id: Optional[str], email: str) -> Dict[str, Any]:
        """Get data retention information for user"""
        try:
            # Get oldest assessment
            oldest_assessment = self.db.execute(text("""
                SELECT created_at 
                FROM ai_job_assessments 
                WHERE user_id = :user_id OR email = :email
                ORDER BY created_at ASC 
                LIMIT 1
            """), {
                'user_id': user_id,
                'email': email
            }).fetchone()
            
            retention_info = {
                'retention_policies': self.privacy_policy.retention_periods,
                'data_types': {
                    'assessment_data': {
                        'retention_period': '2 years',
                        'deletion_date': None,
                        'can_be_deleted': True
                    },
                    'user_profile': {
                        'retention_period': '2 years',
                        'deletion_date': None,
                        'can_be_deleted': True
                    },
                    'analytics_data': {
                        'retention_period': '1 year',
                        'deletion_date': None,
                        'can_be_deleted': True
                    }
                }
            }
            
            if oldest_assessment:
                oldest_date = oldest_assessment.created_at
                retention_info['oldest_data_date'] = oldest_date.isoformat()
                retention_info['data_age_days'] = (datetime.now(timezone.utc) - oldest_date).days
            
            return retention_info
            
        except Exception as e:
            logger.error(f"Failed to get data retention info: {e}")
            return {}
    
    def _get_recent_privacy_activities(self, user_id: Optional[str], email: str, 
                                     days: int = 30) -> List[Dict[str, Any]]:
        """Get recent privacy activities for user"""
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            result = self.db.execute(text("""
                SELECT 
                    consent_type,
                    purpose,
                    granted,
                    granted_at,
                    withdrawn_at
                FROM ai_calculator_privacy_preferences 
                WHERE (user_id = :user_id OR email = :email)
                AND (granted_at >= :start_date OR withdrawn_at >= :start_date)
                ORDER BY COALESCE(withdrawn_at, granted_at) DESC
                LIMIT 10
            """), {
                'user_id': user_id,
                'email': email,
                'start_date': start_date
            }).fetchall()
            
            activities = []
            for row in result:
                activity = {
                    'type': 'consent_withdrawn' if row.withdrawn_at else 'consent_granted',
                    'consent_type': row.consent_type,
                    'purpose': row.purpose,
                    'timestamp': (row.withdrawn_at or row.granted_at).isoformat(),
                    'description': f"{'Withdrew' if row.withdrawn_at else 'Granted'} consent for {row.consent_type} - {row.purpose}"
                }
                activities.append(activity)
            
            return activities
            
        except Exception as e:
            logger.error(f"Failed to get recent privacy activities: {e}")
            return []
    
    def update_privacy_preferences(self, user_id: Optional[str], email: str,
                                 preferences: Dict[str, bool]) -> bool:
        """Update user privacy preferences"""
        try:
            for consent_type, granted in preferences.items():
                if granted:
                    # Grant consent for all purposes
                    purposes = [p.value for p in DataProcessingPurpose]
                    self.create_consent_record(user_id, email, [consent_type], purposes)
                else:
                    # Withdraw consent for all purposes
                    purposes = [p.value for p in DataProcessingPurpose]
                    self.withdraw_consent(user_id, email, [consent_type], purposes)
            
            logger.info(f"Privacy preferences updated for {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update privacy preferences: {e}")
            return False
    
    def get_ccpa_compliance_data(self, user_id: Optional[str], email: str) -> Dict[str, Any]:
        """Get CCPA compliance data for California users"""
        try:
            consent_summary = self.get_user_consent_summary(user_id, email)
            
            # Get data categories collected
            data_categories = self._get_data_categories_collected(user_id, email)
            
            # Get third-party sharing information
            third_party_sharing = self._get_third_party_sharing_info()
            
            return {
                'user_id': user_id,
                'email': email,
                'ccpa_rights': [
                    'Right to know what personal information is collected',
                    'Right to know whether personal information is sold or disclosed',
                    'Right to say no to the sale of personal information',
                    'Right to equal service and price'
                ],
                'data_categories_collected': data_categories,
                'data_categories_sold': [],  # AI Calculator doesn't sell data
                'data_categories_disclosed': third_party_sharing,
                'consent_status': consent_summary.get('consent_status', {}),
                'contact_information': {
                    'email': 'privacy@mingusapp.com',
                    'phone': '+1-800-MINGUS',
                    'address': 'MINGUS Privacy Team'
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get CCPA compliance data: {e}")
            return {}
    
    def _get_data_categories_collected(self, user_id: Optional[str], email: str) -> List[str]:
        """Get data categories collected for user"""
        categories = []
        
        # Check what data we have for this user
        result = self.db.execute(text("""
            SELECT 
                CASE WHEN first_name IS NOT NULL AND first_name != '' THEN TRUE ELSE FALSE END as has_name,
                CASE WHEN email IS NOT NULL AND email != '' THEN TRUE ELSE FALSE END as has_email,
                CASE WHEN location IS NOT NULL AND location != '' THEN TRUE ELSE FALSE END as has_location,
                CASE WHEN job_title IS NOT NULL AND job_title != '' THEN TRUE ELSE FALSE END as has_job_info,
                CASE WHEN industry IS NOT NULL AND industry != '' THEN TRUE ELSE FALSE END as has_industry_info
            FROM ai_job_assessments 
            WHERE user_id = :user_id OR email = :email
            LIMIT 1
        """), {
            'user_id': user_id,
            'email': email
        }).fetchone()
        
        if result:
            if result.has_name:
                categories.append('Personal identifiers')
            if result.has_email:
                categories.append('Contact information')
            if result.has_location:
                categories.append('Geographic information')
            if result.has_job_info or result.has_industry_info:
                categories.append('Professional information')
            
            # Always include these categories
            categories.extend([
                'Assessment responses',
                'Technical data (IP address, user agent)',
                'Usage analytics'
            ])
        
        return categories
    
    def _get_third_party_sharing_info(self) -> List[Dict[str, str]]:
        """Get third-party sharing information"""
        return [
            {
                'category': 'Analytics',
                'service': 'Google Analytics',
                'purpose': 'Website usage analytics',
                'data_shared': 'Anonymized usage data'
            },
            {
                'category': 'Email',
                'service': 'Resend',
                'purpose': 'Email communications',
                'data_shared': 'Email address and name'
            },
            {
                'category': 'Payments',
                'service': 'Stripe',
                'purpose': 'Payment processing',
                'data_shared': 'Payment information (if applicable)'
            }
        ]
