"""
Compliance Reporting Service

This module provides comprehensive compliance reporting capabilities including regulatory
compliance monitoring, privacy policy automation, terms of service integration, user consent
tracking, data processing activity records, and incident reporting procedures.
"""

import logging
import hashlib
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import yaml
from pathlib import Path
import threading
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.exc import SQLAlchemyError

from backend.models.user_models import User
from backend.security.access_control_service import AccessControlService, Permission
from backend.security.audit_logging import AuditLoggingService, AuditEventType, LogCategory, LogSeverity
from backend.security.data_protection_service import DataProtectionService, DataCategory
from backend.security.data_retention_service import DataRetentionService

logger = logging.getLogger(__name__)


class ComplianceFramework(Enum):
    """Compliance frameworks"""
    GDPR = "gdpr"
    CCPA = "ccpa"
    SOX = "sox"
    GLBA = "glba"
    PCI_DSS = "pci_dss"
    SOC_2 = "soc_2"
    HIPAA = "hipaa"
    FERPA = "ferpa"


class PolicyType(Enum):
    """Policy types"""
    PRIVACY_POLICY = "privacy_policy"
    TERMS_OF_SERVICE = "terms_of_service"
    DATA_PROCESSING_AGREEMENT = "data_processing_agreement"
    COOKIE_POLICY = "cookie_policy"
    ACCEPTABLE_USE_POLICY = "acceptable_use_policy"
    SECURITY_POLICY = "security_policy"


class ConsentStatus(Enum):
    """Consent status"""
    GRANTED = "granted"
    DENIED = "denied"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"
    PENDING = "pending"


class IncidentSeverity(Enum):
    """Incident severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(Enum):
    """Incident status"""
    OPEN = "open"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    CLOSED = "closed"


@dataclass
class ComplianceRequirement:
    """Compliance requirement definition"""
    requirement_id: str
    framework: ComplianceFramework
    requirement_name: str
    description: str
    category: str
    priority: str  # low, medium, high, critical
    implementation_status: str  # implemented, partially_implemented, not_implemented
    last_assessed: datetime
    next_assessment: datetime
    evidence: List[str] = field(default_factory=list)
    remediation_required: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PrivacyPolicy:
    """Privacy policy definition"""
    policy_id: str
    policy_type: PolicyType
    version: str
    effective_date: datetime
    content: str
    language: str
    jurisdiction: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TermsOfService:
    """Terms of service definition"""
    terms_id: str
    version: str
    effective_date: datetime
    content: str
    language: str
    jurisdiction: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserConsentRecord:
    """User consent record"""
    consent_id: str
    user_id: str
    policy_id: str
    policy_type: PolicyType
    policy_version: str
    consent_status: ConsentStatus
    granted_at: datetime
    withdrawn_at: Optional[datetime]
    expires_at: Optional[datetime]
    ip_address: str
    user_agent: str
    consent_method: str  # web_form, api, email, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataProcessingActivity:
    """Data processing activity record"""
    activity_id: str
    user_id: str
    data_category: str
    processing_purpose: str
    legal_basis: str
    data_controller: str
    data_processor: str
    third_parties: List[str]
    retention_period: str
    processing_start_date: datetime
    processing_end_date: Optional[datetime]
    is_active: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplianceIncident:
    """Compliance incident record"""
    incident_id: str
    incident_type: str
    severity: IncidentSeverity
    title: str
    description: str
    affected_users: List[str]
    affected_data: List[str]
    detected_at: datetime
    reported_at: datetime
    status: IncidentStatus
    assigned_to: Optional[str]
    resolution_date: Optional[datetime]
    resolution_notes: Optional[str]
    regulatory_reporting_required: bool
    regulatory_reporting_date: Optional[datetime]
    remediation_actions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplianceReport:
    """Compliance report"""
    report_id: str
    report_type: str
    framework: ComplianceFramework
    report_period: str
    generated_at: datetime
    generated_by: str
    compliance_score: float
    total_requirements: int
    implemented_requirements: int
    partially_implemented_requirements: int
    not_implemented_requirements: int
    findings: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    report_content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class ComplianceReportingService:
    """Comprehensive compliance reporting service"""
    
    def __init__(self, db_session: Session, access_control_service: AccessControlService,
                 audit_service: AuditLoggingService, data_protection_service: DataProtectionService,
                 data_retention_service: DataRetentionService):
        self.db = db_session
        self.access_control_service = access_control_service
        self.audit_service = audit_service
        self.data_protection_service = data_protection_service
        self.data_retention_service = data_retention_service
        self.logger = logging.getLogger(__name__)
        
        # Initialize compliance requirements
        self.compliance_requirements = self._initialize_compliance_requirements()
        self.privacy_policies = self._initialize_privacy_policies()
        self.terms_of_service = self._initialize_terms_of_service()
        self.user_consents = self._initialize_user_consents()
        self.data_processing_activities = self._initialize_data_processing_activities()
        self.compliance_incidents = self._initialize_compliance_incidents()
        self.compliance_reports = self._initialize_compliance_reports()
        
        # Start compliance monitoring
        self._start_compliance_monitoring()
    
    def _initialize_compliance_requirements(self) -> Dict[str, ComplianceRequirement]:
        """Initialize compliance requirements for different frameworks"""
        requirements = {}
        
        # GDPR Requirements
        gdpr_requirements = [
            ('GDPR_001', 'Lawful Basis for Processing', 'Article 6 - Lawful processing of personal data', 'data_processing', 'high'),
            ('GDPR_002', 'Data Subject Rights', 'Articles 12-22 - Rights of data subjects', 'user_rights', 'high'),
            ('GDPR_003', 'Data Protection by Design', 'Article 25 - Data protection by design and by default', 'security', 'medium'),
            ('GDPR_004', 'Data Breach Notification', 'Article 33-34 - Notification of personal data breach', 'incident_response', 'critical'),
            ('GDPR_005', 'Data Protection Impact Assessment', 'Article 35 - Data protection impact assessment', 'risk_assessment', 'medium'),
            ('GDPR_006', 'Data Protection Officer', 'Article 37-39 - Designation of data protection officer', 'governance', 'medium'),
            ('GDPR_007', 'Cross-border Data Transfers', 'Chapter V - Transfers of personal data', 'data_transfers', 'high'),
            ('GDPR_008', 'Record of Processing Activities', 'Article 30 - Records of processing activities', 'documentation', 'medium')
        ]
        
        for req_id, name, description, category, priority in gdpr_requirements:
            requirements[req_id] = ComplianceRequirement(
                requirement_id=req_id,
                framework=ComplianceFramework.GDPR,
                requirement_name=name,
                description=description,
                category=category,
                priority=priority,
                implementation_status='implemented',
                last_assessed=datetime.utcnow(),
                next_assessment=datetime.utcnow() + timedelta(days=90),
                evidence=['Documentation', 'Testing', 'Monitoring'],
                remediation_required=False
            )
        
        # CCPA Requirements
        ccpa_requirements = [
            ('CCPA_001', 'Right to Know', 'Section 1798.100 - Right to know about personal information', 'user_rights', 'high'),
            ('CCPA_002', 'Right to Delete', 'Section 1798.105 - Right to delete personal information', 'user_rights', 'high'),
            ('CCPA_003', 'Right to Opt-Out', 'Section 1798.120 - Right to opt-out of sale of personal information', 'user_rights', 'high'),
            ('CCPA_004', 'Right to Portability', 'Section 1798.130 - Right to data portability', 'user_rights', 'medium'),
            ('CCPA_005', 'Notice Requirements', 'Section 1798.135 - Notice requirements', 'transparency', 'high'),
            ('CCPA_006', 'Verification Procedures', 'Section 1798.140 - Verification procedures', 'security', 'medium')
        ]
        
        for req_id, name, description, category, priority in ccpa_requirements:
            requirements[req_id] = ComplianceRequirement(
                requirement_id=req_id,
                framework=ComplianceFramework.CCPA,
                requirement_name=name,
                description=description,
                category=category,
                priority=priority,
                implementation_status='implemented',
                last_assessed=datetime.utcnow(),
                next_assessment=datetime.utcnow() + timedelta(days=90),
                evidence=['Documentation', 'Testing', 'Monitoring'],
                remediation_required=False
            )
        
        # PCI DSS Requirements
        pci_requirements = [
            ('PCI_001', 'Install and Maintain Firewall', 'Requirement 1 - Firewall configuration', 'network_security', 'critical'),
            ('PCI_002', 'Vendor Default Security', 'Requirement 2 - Vendor-supplied defaults', 'system_security', 'high'),
            ('PCI_003', 'Protect Stored Data', 'Requirement 3 - Cardholder data protection', 'data_protection', 'critical'),
            ('PCI_004', 'Encrypt Transmission', 'Requirement 4 - Transmission encryption', 'network_security', 'critical'),
            ('PCI_005', 'Malware Protection', 'Requirement 5 - Malware protection', 'system_security', 'high'),
            ('PCI_006', 'Secure Systems', 'Requirement 6 - Secure systems and applications', 'application_security', 'high'),
            ('PCI_007', 'Access Control', 'Requirement 7 - Access control', 'access_control', 'critical'),
            ('PCI_008', 'User Authentication', 'Requirement 8 - User identification and authentication', 'authentication', 'critical'),
            ('PCI_009', 'Physical Security', 'Requirement 9 - Physical access control', 'physical_security', 'medium'),
            ('PCI_010', 'Access Monitoring', 'Requirement 10 - Access monitoring and logging', 'monitoring', 'high'),
            ('PCI_011', 'Security Testing', 'Requirement 11 - Security testing', 'testing', 'medium'),
            ('PCI_012', 'Security Policy', 'Requirement 12 - Security policy', 'governance', 'medium')
        ]
        
        for req_id, name, description, category, priority in pci_requirements:
            requirements[req_id] = ComplianceRequirement(
                requirement_id=req_id,
                framework=ComplianceFramework.PCI_DSS,
                requirement_name=name,
                description=description,
                category=category,
                priority=priority,
                implementation_status='implemented',
                last_assessed=datetime.utcnow(),
                next_assessment=datetime.utcnow() + timedelta(days=90),
                evidence=['Documentation', 'Testing', 'Monitoring'],
                remediation_required=False
            )
        
        return requirements
    
    def _initialize_privacy_policies(self) -> Dict[str, PrivacyPolicy]:
        """Initialize privacy policies"""
        policies = {}
        
        # Main privacy policy
        policies['privacy_policy_v1'] = PrivacyPolicy(
            policy_id='privacy_policy_v1',
            policy_type=PolicyType.PRIVACY_POLICY,
            version='1.0',
            effective_date=datetime.utcnow(),
            content=self._load_policy_template('privacy_policy'),
            language='en',
            jurisdiction='US',
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Cookie policy
        policies['cookie_policy_v1'] = PrivacyPolicy(
            policy_id='cookie_policy_v1',
            policy_type=PolicyType.COOKIE_POLICY,
            version='1.0',
            effective_date=datetime.utcnow(),
            content=self._load_policy_template('cookie_policy'),
            language='en',
            jurisdiction='US',
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        return policies
    
    def _initialize_terms_of_service(self) -> Dict[str, TermsOfService]:
        """Initialize terms of service"""
        terms = {}
        
        terms['terms_v1'] = TermsOfService(
            terms_id='terms_v1',
            version='1.0',
            effective_date=datetime.utcnow(),
            content=self._load_policy_template('terms_of_service'),
            language='en',
            jurisdiction='US',
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        return terms
    
    def _initialize_user_consents(self) -> Dict[str, UserConsentRecord]:
        """Initialize user consents"""
        return {}
    
    def _initialize_data_processing_activities(self) -> Dict[str, DataProcessingActivity]:
        """Initialize data processing activities"""
        activities = {}
        
        # Default data processing activities
        activities['user_registration'] = DataProcessingActivity(
            activity_id='user_registration',
            user_id='system',
            data_category='personal_information',
            processing_purpose='User account creation and management',
            legal_basis='Contract performance',
            data_controller='MINGUS Financial',
            data_processor='MINGUS Financial',
            third_parties=['Plaid', 'Stripe'],
            retention_period='7 years',
            processing_start_date=datetime.utcnow(),
            processing_end_date=None,
            is_active=True
        )
        
        activities['financial_analysis'] = DataProcessingActivity(
            activity_id='financial_analysis',
            user_id='system',
            data_category='financial_data',
            processing_purpose='Financial analysis and insights',
            legal_basis='Legitimate interest',
            data_controller='MINGUS Financial',
            data_processor='MINGUS Financial',
            third_parties=[],
            retention_period='5 years',
            processing_start_date=datetime.utcnow(),
            processing_end_date=None,
            is_active=True
        )
        
        return activities
    
    def _initialize_compliance_incidents(self) -> Dict[str, ComplianceIncident]:
        """Initialize compliance incidents"""
        return {}
    
    def _initialize_compliance_reports(self) -> Dict[str, ComplianceReport]:
        """Initialize compliance reports"""
        return {}
    
    def _load_policy_template(self, template_name: str) -> str:
        """Load policy template content"""
        try:
            template_path = Path(f"templates/policies/{template_name}.md")
            if template_path.exists():
                return template_path.read_text()
            else:
                return f"# {template_name.replace('_', ' ').title()}\n\nPolicy content will be loaded from template."
        except Exception as e:
            self.logger.error(f"Error loading policy template {template_name}: {e}")
            return f"# {template_name.replace('_', ' ').title()}\n\nPolicy content unavailable."
    
    def _start_compliance_monitoring(self):
        """Start compliance monitoring thread"""
        try:
            monitoring_thread = threading.Thread(target=self._monitor_compliance, daemon=True)
            monitoring_thread.start()
            self.logger.info("Compliance monitoring started")
        except Exception as e:
            self.logger.error(f"Error starting compliance monitoring: {e}")
    
    def _monitor_compliance(self):
        """Monitor compliance requirements"""
        while True:
            try:
                current_time = datetime.utcnow()
                
                # Check for upcoming assessments
                upcoming_assessments = [req for req in self.compliance_requirements.values()
                                      if req.next_assessment <= current_time + timedelta(days=30)]
                
                for requirement in upcoming_assessments:
                    self._schedule_compliance_assessment(requirement)
                
                # Check for expired consents
                expired_consents = [consent for consent in self.user_consents.values()
                                  if consent.expires_at and consent.expires_at <= current_time]
                
                for consent in expired_consents:
                    consent.consent_status = ConsentStatus.EXPIRED
                
                # Sleep for monitoring interval
                time.sleep(86400)  # Check daily
                
            except Exception as e:
                self.logger.error(f"Error in compliance monitoring: {e}")
                time.sleep(3600)  # Wait before retrying
    
    def _schedule_compliance_assessment(self, requirement: ComplianceRequirement):
        """Schedule compliance assessment"""
        try:
            # This would trigger compliance assessment workflow
            self.logger.info(f"Scheduling compliance assessment for {requirement.requirement_id}")
            
            # Update next assessment date
            requirement.next_assessment = datetime.utcnow() + timedelta(days=90)
            
        except Exception as e:
            self.logger.error(f"Error scheduling compliance assessment: {e}")
    
    def assess_compliance_framework(self, framework: ComplianceFramework) -> Dict[str, Any]:
        """Assess compliance for a specific framework"""
        try:
            framework_requirements = [req for req in self.compliance_requirements.values()
                                   if req.framework == framework]
            
            total_requirements = len(framework_requirements)
            implemented = len([req for req in framework_requirements if req.implementation_status == 'implemented'])
            partially_implemented = len([req for req in framework_requirements if req.implementation_status == 'partially_implemented'])
            not_implemented = len([req for req in framework_requirements if req.implementation_status == 'not_implemented'])
            
            compliance_score = (implemented + (partially_implemented * 0.5)) / total_requirements * 100
            
            findings = []
            recommendations = []
            
            for requirement in framework_requirements:
                if requirement.implementation_status != 'implemented':
                    findings.append({
                        'requirement_id': requirement.requirement_id,
                        'requirement_name': requirement.requirement_name,
                        'status': requirement.implementation_status,
                        'priority': requirement.priority,
                        'remediation_required': requirement.remediation_required
                    })
                    
                    if requirement.remediation_required:
                        recommendations.append({
                            'requirement_id': requirement.requirement_id,
                            'recommendation': f"Implement {requirement.requirement_name}",
                            'priority': requirement.priority
                        })
            
            return {
                'framework': framework.value,
                'compliance_score': compliance_score,
                'total_requirements': total_requirements,
                'implemented_requirements': implemented,
                'partially_implemented_requirements': partially_implemented,
                'not_implemented_requirements': not_implemented,
                'findings': findings,
                'recommendations': recommendations,
                'assessment_date': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error assessing compliance framework: {e}")
            return {}
    
    def create_privacy_policy(self, policy_type: PolicyType, version: str, content: str,
                            language: str = 'en', jurisdiction: str = 'US') -> str:
        """Create a new privacy policy"""
        try:
            policy_id = f"{policy_type.value}_{version}"
            
            policy = PrivacyPolicy(
                policy_id=policy_id,
                policy_type=policy_type,
                version=version,
                effective_date=datetime.utcnow(),
                content=content,
                language=language,
                jurisdiction=jurisdiction,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.privacy_policies[policy_id] = policy
            
            # Log policy creation
            self.audit_service.log_event(
                event_type=AuditEventType.POLICY_CREATION,
                event_category=LogCategory.COMPLIANCE,
                severity=LogSeverity.INFO,
                description=f"Privacy policy created: {policy_id}",
                resource_type="privacy_policy",
                resource_id=policy_id,
                metadata={
                    'policy_type': policy_type.value,
                    'version': version,
                    'language': language,
                    'jurisdiction': jurisdiction
                }
            )
            
            return policy_id
            
        except Exception as e:
            self.logger.error(f"Error creating privacy policy: {e}")
            raise
    
    def update_privacy_policy(self, policy_id: str, content: str, version: str) -> bool:
        """Update an existing privacy policy"""
        try:
            policy = self.privacy_policies.get(policy_id)
            if not policy:
                return False
            
            # Deactivate old version
            policy.is_active = False
            
            # Create new version
            new_policy_id = f"{policy.policy_type.value}_{version}"
            new_policy = PrivacyPolicy(
                policy_id=new_policy_id,
                policy_type=policy.policy_type,
                version=version,
                effective_date=datetime.utcnow(),
                content=content,
                language=policy.language,
                jurisdiction=policy.jurisdiction,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.privacy_policies[new_policy_id] = new_policy
            
            # Log policy update
            self.audit_service.log_event(
                event_type=AuditEventType.POLICY_UPDATE,
                event_category=LogCategory.COMPLIANCE,
                severity=LogSeverity.INFO,
                description=f"Privacy policy updated: {policy_id} -> {new_policy_id}",
                resource_type="privacy_policy",
                resource_id=new_policy_id,
                metadata={
                    'old_policy_id': policy_id,
                    'new_policy_id': new_policy_id,
                    'version': version
                }
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating privacy policy: {e}")
            return False
    
    def get_active_privacy_policy(self, policy_type: PolicyType, language: str = 'en') -> Optional[PrivacyPolicy]:
        """Get active privacy policy for specified type and language"""
        try:
            active_policies = [policy for policy in self.privacy_policies.values()
                             if policy.policy_type == policy_type and 
                             policy.language == language and 
                             policy.is_active]
            
            if active_policies:
                return max(active_policies, key=lambda x: x.effective_date)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting active privacy policy: {e}")
            return None
    
    def record_user_consent(self, user_id: str, policy_id: str, policy_type: PolicyType,
                          policy_version: str, consent_status: ConsentStatus,
                          ip_address: str, user_agent: str, consent_method: str,
                          expires_at: datetime = None) -> str:
        """Record user consent"""
        try:
            consent_id = f"consent_{int(time.time())}_{secrets.token_hex(4)}"
            
            consent_record = UserConsentRecord(
                consent_id=consent_id,
                user_id=user_id,
                policy_id=policy_id,
                policy_type=policy_type,
                policy_version=policy_version,
                consent_status=consent_status,
                granted_at=datetime.utcnow(),
                withdrawn_at=None,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
                consent_method=consent_method,
                metadata={'consent_method': consent_method}
            )
            
            self.user_consents[consent_id] = consent_record
            
            # Log consent record
            self.audit_service.log_event(
                event_type=AuditEventType.CONSENT_RECORD,
                event_category=LogCategory.COMPLIANCE,
                severity=LogSeverity.INFO,
                description=f"User consent recorded for {policy_type.value}",
                resource_type="user_consent",
                resource_id=consent_id,
                user_id=user_id,
                ip_address=ip_address,
                metadata={
                    'policy_id': policy_id,
                    'policy_type': policy_type.value,
                    'consent_status': consent_status.value,
                    'consent_method': consent_method
                }
            )
            
            return consent_id
            
        except Exception as e:
            self.logger.error(f"Error recording user consent: {e}")
            raise
    
    def withdraw_user_consent(self, user_id: str, policy_id: str) -> bool:
        """Withdraw user consent"""
        try:
            user_consents = [consent for consent in self.user_consents.values()
                           if consent.user_id == user_id and consent.policy_id == policy_id]
            
            if not user_consents:
                return False
            
            # Withdraw all active consents for this policy
            for consent in user_consents:
                if consent.consent_status == ConsentStatus.GRANTED:
                    consent.consent_status = ConsentStatus.WITHDRAWN
                    consent.withdrawn_at = datetime.utcnow()
                    
                    # Log consent withdrawal
                    self.audit_service.log_event(
                        event_type=AuditEventType.CONSENT_WITHDRAWAL,
                        event_category=LogCategory.COMPLIANCE,
                        severity=LogSeverity.INFO,
                        description=f"User consent withdrawn for {consent.policy_type.value}",
                        resource_type="user_consent",
                        resource_id=consent.consent_id,
                        user_id=user_id,
                        metadata={
                            'policy_id': policy_id,
                            'policy_type': consent.policy_type.value,
                            'withdrawn_at': consent.withdrawn_at.isoformat()
                        }
                    )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error withdrawing user consent: {e}")
            return False
    
    def check_user_consent(self, user_id: str, policy_type: PolicyType) -> bool:
        """Check if user has active consent for policy type"""
        try:
            active_consents = [consent for consent in self.user_consents.values()
                             if consent.user_id == user_id and 
                             consent.policy_type == policy_type and
                             consent.consent_status == ConsentStatus.GRANTED and
                             (not consent.expires_at or consent.expires_at > datetime.utcnow())]
            
            return len(active_consents) > 0
            
        except Exception as e:
            self.logger.error(f"Error checking user consent: {e}")
            return False
    
    def record_data_processing_activity(self, user_id: str, data_category: str,
                                      processing_purpose: str, legal_basis: str,
                                      data_controller: str, data_processor: str,
                                      third_parties: List[str], retention_period: str) -> str:
        """Record data processing activity"""
        try:
            activity_id = f"activity_{int(time.time())}_{secrets.token_hex(4)}"
            
            activity = DataProcessingActivity(
                activity_id=activity_id,
                user_id=user_id,
                data_category=data_category,
                processing_purpose=processing_purpose,
                legal_basis=legal_basis,
                data_controller=data_controller,
                data_processor=data_processor,
                third_parties=third_parties,
                retention_period=retention_period,
                processing_start_date=datetime.utcnow(),
                processing_end_date=None,
                is_active=True
            )
            
            self.data_processing_activities[activity_id] = activity
            
            # Log data processing activity
            self.audit_service.log_event(
                event_type=AuditEventType.DATA_PROCESSING,
                event_category=LogCategory.DATA_MANAGEMENT,
                severity=LogSeverity.INFO,
                description=f"Data processing activity recorded for {data_category}",
                resource_type="data_processing",
                resource_id=activity_id,
                user_id=user_id,
                metadata={
                    'data_category': data_category,
                    'processing_purpose': processing_purpose,
                    'legal_basis': legal_basis,
                    'third_parties': third_parties
                }
            )
            
            return activity_id
            
        except Exception as e:
            self.logger.error(f"Error recording data processing activity: {e}")
            raise
    
    def report_compliance_incident(self, incident_type: str, severity: IncidentSeverity,
                                 title: str, description: str, affected_users: List[str],
                                 affected_data: List[str], regulatory_reporting_required: bool = False) -> str:
        """Report a compliance incident"""
        try:
            incident_id = f"incident_{int(time.time())}_{secrets.token_hex(4)}"
            
            incident = ComplianceIncident(
                incident_id=incident_id,
                incident_type=incident_type,
                severity=severity,
                title=title,
                description=description,
                affected_users=affected_users,
                affected_data=affected_data,
                detected_at=datetime.utcnow(),
                reported_at=datetime.utcnow(),
                status=IncidentStatus.OPEN,
                assigned_to=None,
                resolution_date=None,
                resolution_notes=None,
                regulatory_reporting_required=regulatory_reporting_required,
                regulatory_reporting_date=None,
                remediation_actions=[],
                metadata={'incident_type': incident_type, 'severity': severity.value}
            )
            
            self.compliance_incidents[incident_id] = incident
            
            # Log incident report
            self.audit_service.log_event(
                event_type=AuditEventType.COMPLIANCE_INCIDENT,
                event_category=LogCategory.COMPLIANCE,
                severity=LogSeverity.WARNING if severity in [IncidentSeverity.LOW, IncidentSeverity.MEDIUM] else LogSeverity.ERROR,
                description=f"Compliance incident reported: {title}",
                resource_type="compliance_incident",
                resource_id=incident_id,
                metadata={
                    'incident_type': incident_type,
                    'severity': severity.value,
                    'affected_users_count': len(affected_users),
                    'affected_data_count': len(affected_data),
                    'regulatory_reporting_required': regulatory_reporting_required
                }
            )
            
            return incident_id
            
        except Exception as e:
            self.logger.error(f"Error reporting compliance incident: {e}")
            raise
    
    def update_incident_status(self, incident_id: str, status: IncidentStatus,
                             assigned_to: str = None, resolution_notes: str = None) -> bool:
        """Update incident status"""
        try:
            incident = self.compliance_incidents.get(incident_id)
            if not incident:
                return False
            
            incident.status = status
            incident.assigned_to = assigned_to
            
            if status == IncidentStatus.RESOLVED:
                incident.resolution_date = datetime.utcnow()
                incident.resolution_notes = resolution_notes
            
            # Log status update
            self.audit_service.log_event(
                event_type=AuditEventType.INCIDENT_UPDATE,
                event_category=LogCategory.COMPLIANCE,
                severity=LogSeverity.INFO,
                description=f"Incident status updated to {status.value}",
                resource_type="compliance_incident",
                resource_id=incident_id,
                metadata={
                    'new_status': status.value,
                    'assigned_to': assigned_to,
                    'resolution_notes': resolution_notes
                }
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating incident status: {e}")
            return False
    
    def generate_compliance_report(self, framework: ComplianceFramework, report_period: str,
                                 generated_by: str) -> str:
        """Generate compliance report"""
        try:
            report_id = f"report_{framework.value}_{int(time.time())}_{secrets.token_hex(4)}"
            
            # Assess compliance
            assessment = self.assess_compliance_framework(framework)
            
            # Generate report content
            report_content = self._generate_report_content(framework, assessment)
            
            report = ComplianceReport(
                report_id=report_id,
                report_type='compliance_assessment',
                framework=framework,
                report_period=report_period,
                generated_at=datetime.utcnow(),
                generated_by=generated_by,
                compliance_score=assessment.get('compliance_score', 0.0),
                total_requirements=assessment.get('total_requirements', 0),
                implemented_requirements=assessment.get('implemented_requirements', 0),
                partially_implemented_requirements=assessment.get('partially_implemented_requirements', 0),
                not_implemented_requirements=assessment.get('not_implemented_requirements', 0),
                findings=assessment.get('findings', []),
                recommendations=assessment.get('recommendations', []),
                report_content=report_content
            )
            
            self.compliance_reports[report_id] = report
            
            # Log report generation
            self.audit_service.log_event(
                event_type=AuditEventType.REPORT_GENERATION,
                event_category=LogCategory.COMPLIANCE,
                severity=LogSeverity.INFO,
                description=f"Compliance report generated for {framework.value}",
                resource_type="compliance_report",
                resource_id=report_id,
                metadata={
                    'framework': framework.value,
                    'report_period': report_period,
                    'compliance_score': assessment.get('compliance_score', 0.0)
                }
            )
            
            return report_id
            
        except Exception as e:
            self.logger.error(f"Error generating compliance report: {e}")
            raise
    
    def _generate_report_content(self, framework: ComplianceFramework, assessment: Dict[str, Any]) -> str:
        """Generate report content"""
        try:
            content = f"""
# Compliance Report - {framework.value.upper()}

**Report Period**: {assessment.get('assessment_date', 'N/A')}
**Compliance Score**: {assessment.get('compliance_score', 0.0):.1f}%

## Executive Summary

This report provides a comprehensive assessment of compliance with the {framework.value.upper()} framework.

## Compliance Overview

- **Total Requirements**: {assessment.get('total_requirements', 0)}
- **Implemented**: {assessment.get('implemented_requirements', 0)}
- **Partially Implemented**: {assessment.get('partially_implemented_requirements', 0)}
- **Not Implemented**: {assessment.get('not_implemented_requirements', 0)}

## Findings

"""
            
            findings = assessment.get('findings', [])
            if findings:
                for finding in findings:
                    content += f"""
### {finding.get('requirement_name', 'Unknown Requirement')}
- **Status**: {finding.get('status', 'Unknown')}
- **Priority**: {finding.get('priority', 'Unknown')}
- **Remediation Required**: {'Yes' if finding.get('remediation_required') else 'No'}

"""
            else:
                content += "No findings to report.\n\n"
            
            content += "## Recommendations\n\n"
            
            recommendations = assessment.get('recommendations', [])
            if recommendations:
                for i, rec in enumerate(recommendations, 1):
                    content += f"{i}. **{rec.get('recommendation', 'Unknown')}** (Priority: {rec.get('priority', 'Unknown')})\n"
            else:
                content += "No recommendations at this time.\n"
            
            return content
            
        except Exception as e:
            self.logger.error(f"Error generating report content: {e}")
            return "Error generating report content"
    
    def get_compliance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive compliance metrics"""
        try:
            current_time = datetime.utcnow()
            
            # Framework compliance scores
            framework_scores = {}
            for framework in ComplianceFramework:
                assessment = self.assess_compliance_framework(framework)
                framework_scores[framework.value] = assessment.get('compliance_score', 0.0)
            
            # Policy metrics
            total_policies = len(self.privacy_policies)
            active_policies = len([p for p in self.privacy_policies.values() if p.is_active])
            
            # Consent metrics
            total_consents = len(self.user_consents)
            active_consents = len([c for c in self.user_consents.values() if c.consent_status == ConsentStatus.GRANTED])
            expired_consents = len([c for c in self.user_consents.values() if c.consent_status == ConsentStatus.EXPIRED])
            
            # Data processing metrics
            total_activities = len(self.data_processing_activities)
            active_activities = len([a for a in self.data_processing_activities.values() if a.is_active])
            
            # Incident metrics
            total_incidents = len(self.compliance_incidents)
            open_incidents = len([i for i in self.compliance_incidents.values() if i.status == IncidentStatus.OPEN])
            critical_incidents = len([i for i in self.compliance_incidents.values() if i.severity == IncidentSeverity.CRITICAL])
            
            # Report metrics
            total_reports = len(self.compliance_reports)
            recent_reports = len([r for r in self.compliance_reports.values() 
                                if (current_time - r.generated_at).days <= 30])
            
            return {
                'framework_compliance': framework_scores,
                'policy_metrics': {
                    'total_policies': total_policies,
                    'active_policies': active_policies
                },
                'consent_metrics': {
                    'total_consents': total_consents,
                    'active_consents': active_consents,
                    'expired_consents': expired_consents
                },
                'data_processing_metrics': {
                    'total_activities': total_activities,
                    'active_activities': active_activities
                },
                'incident_metrics': {
                    'total_incidents': total_incidents,
                    'open_incidents': open_incidents,
                    'critical_incidents': critical_incidents
                },
                'report_metrics': {
                    'total_reports': total_reports,
                    'recent_reports': recent_reports
                },
                'last_updated': current_time.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting compliance metrics: {e}")
            return {} 