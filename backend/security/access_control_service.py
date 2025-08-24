"""
Access Control and Monitoring Service

This module provides comprehensive access control and monitoring including role-based access control,
audit logging, real-time security monitoring, suspicious activity detection, data breach prevention,
and user consent management.
"""

import logging
import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import re
from collections import defaultdict, deque
import threading
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.exc import SQLAlchemyError

from backend.models.user_models import User
from backend.models.bank_account_models import BankAccount, PlaidConnection
from backend.security.banking_compliance import BankingComplianceService
from backend.security.audit_logging import AuditLoggingService, AuditEventType, LogCategory, LogSeverity
from backend.security.data_protection_service import DataProtectionService

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """User roles for access control"""
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"
    SUPPORT = "support"
    USER = "user"
    READ_ONLY = "read_only"


class Permission(Enum):
    """Permissions for different operations"""
    # User management
    CREATE_USER = "create_user"
    READ_USER = "read_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    
    # Banking data
    READ_BANK_DATA = "read_bank_data"
    WRITE_BANK_DATA = "write_bank_data"
    DELETE_BANK_DATA = "delete_bank_data"
    EXPORT_BANK_DATA = "export_bank_data"
    
    # Financial operations
    VIEW_BALANCES = "view_balances"
    VIEW_TRANSACTIONS = "view_transactions"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_ACCOUNTS = "manage_accounts"
    
    # System administration
    SYSTEM_ADMIN = "system_admin"
    SECURITY_ADMIN = "security_admin"
    COMPLIANCE_ADMIN = "compliance_admin"
    
    # Audit and monitoring
    VIEW_AUDIT_LOGS = "view_audit_logs"
    VIEW_SECURITY_ALERTS = "view_security_alerts"
    MANAGE_MONITORING = "manage_monitoring"


class SecurityLevel(Enum):
    """Security levels for different operations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActivityType(Enum):
    """Types of user activities for monitoring"""
    LOGIN = "login"
    LOGOUT = "logout"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    ACCOUNT_CREATION = "account_creation"
    ACCOUNT_DELETION = "account_deletion"
    PERMISSION_CHANGE = "permission_change"
    ROLE_CHANGE = "role_change"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SECURITY_VIOLATION = "security_violation"


class ConsentType(Enum):
    """Types of user consent"""
    DATA_COLLECTION = "data_collection"
    DATA_PROCESSING = "data_processing"
    DATA_SHARING = "data_sharing"
    MARKETING = "marketing"
    THIRD_PARTY = "third_party"
    AUTOMATED_DECISIONS = "automated_decisions"


@dataclass
class Role:
    """Role definition with permissions"""
    role_id: str
    name: UserRole
    description: str
    permissions: Set[Permission]
    security_level: SecurityLevel
    created_at: datetime
    updated_at: datetime
    is_active: bool = True


@dataclass
class UserAccess:
    """User access information"""
    user_id: str
    role: UserRole
    permissions: Set[Permission]
    security_level: SecurityLevel
    last_login: datetime
    login_count: int
    failed_attempts: int
    is_locked: bool
    mfa_enabled: bool
    ip_whitelist: List[str] = field(default_factory=list)
    session_timeout: int = 30  # minutes


@dataclass
class SecurityAlert:
    """Security alert data structure"""
    alert_id: str
    alert_type: str
    severity: str  # low, medium, high, critical
    title: str
    description: str
    user_id: Optional[str]
    ip_address: str
    timestamp: datetime
    status: str  # open, investigating, resolved, false_positive
    evidence: Dict[str, Any] = field(default_factory=dict)
    remediation_steps: List[str] = field(default_factory=list)


@dataclass
class UserActivity:
    """User activity data structure"""
    activity_id: str
    user_id: str
    activity_type: ActivityType
    resource_type: str
    resource_id: Optional[str]
    ip_address: str
    user_agent: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    risk_score: float = 0.0


@dataclass
class UserConsent:
    """User consent data structure"""
    consent_id: str
    user_id: str
    consent_type: ConsentType
    granted: bool
    granted_at: datetime
    expires_at: Optional[datetime]
    version: str
    ip_address: str
    user_agent: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataBreachIncident:
    """Data breach incident data structure"""
    incident_id: str
    incident_type: str
    severity: str  # low, medium, high, critical
    description: str
    affected_users: List[str]
    affected_data: List[str]
    detected_at: datetime
    status: str  # detected, investigating, contained, resolved
    containment_actions: List[str] = field(default_factory=list)
    notification_sent: bool = False
    regulatory_reporting: bool = False


class AccessControlService:
    """Comprehensive access control and monitoring service"""
    
    def __init__(self, db_session: Session, compliance_service: BankingComplianceService,
                 audit_service: AuditLoggingService, data_protection_service: DataProtectionService):
        self.db = db_session
        self.compliance_service = compliance_service
        self.audit_service = audit_service
        self.data_protection_service = data_protection_service
        self.logger = logging.getLogger(__name__)
        
        # Initialize role-based access control
        self.roles = self._initialize_roles()
        self.user_access = self._initialize_user_access()
        
        # Initialize monitoring systems
        self.security_alerts = self._initialize_security_alerts()
        self.user_activities = self._initialize_user_activities()
        self.user_consents = self._initialize_user_consents()
        self.data_breach_incidents = self._initialize_data_breach_incidents()
        
        # Real-time monitoring
        self.activity_monitor = ActivityMonitor(self)
        self.suspicious_activity_detector = SuspiciousActivityDetector(self)
        self.breach_prevention_system = BreachPreventionSystem(self)
        
        # Start monitoring threads
        self._start_monitoring_threads()
    
    def _initialize_roles(self) -> Dict[str, Role]:
        """Initialize role-based access control roles"""
        roles = {}
        
        # Admin role
        roles['admin'] = Role(
            role_id='admin',
            name=UserRole.ADMIN,
            description='System administrator with full access',
            permissions={
                Permission.CREATE_USER, Permission.READ_USER, Permission.UPDATE_USER, Permission.DELETE_USER,
                Permission.READ_BANK_DATA, Permission.WRITE_BANK_DATA, Permission.DELETE_BANK_DATA, Permission.EXPORT_BANK_DATA,
                Permission.VIEW_BALANCES, Permission.VIEW_TRANSACTIONS, Permission.VIEW_ANALYTICS, Permission.MANAGE_ACCOUNTS,
                Permission.SYSTEM_ADMIN, Permission.SECURITY_ADMIN, Permission.COMPLIANCE_ADMIN,
                Permission.VIEW_AUDIT_LOGS, Permission.VIEW_SECURITY_ALERTS, Permission.MANAGE_MONITORING
            },
            security_level=SecurityLevel.CRITICAL,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Manager role
        roles['manager'] = Role(
            role_id='manager',
            name=UserRole.MANAGER,
            description='Manager with elevated access',
            permissions={
                Permission.READ_USER, Permission.UPDATE_USER,
                Permission.READ_BANK_DATA, Permission.VIEW_BALANCES, Permission.VIEW_TRANSACTIONS, Permission.VIEW_ANALYTICS,
                Permission.VIEW_AUDIT_LOGS, Permission.VIEW_SECURITY_ALERTS
            },
            security_level=SecurityLevel.HIGH,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Analyst role
        roles['analyst'] = Role(
            role_id='analyst',
            name=UserRole.ANALYST,
            description='Data analyst with read access',
            permissions={
                Permission.READ_BANK_DATA, Permission.VIEW_BALANCES, Permission.VIEW_TRANSACTIONS, Permission.VIEW_ANALYTICS,
                Permission.VIEW_AUDIT_LOGS
            },
            security_level=SecurityLevel.MEDIUM,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Support role
        roles['support'] = Role(
            role_id='support',
            name=UserRole.SUPPORT,
            description='Customer support with limited access',
            permissions={
                Permission.READ_USER, Permission.READ_BANK_DATA, Permission.VIEW_BALANCES
            },
            security_level=SecurityLevel.MEDIUM,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # User role
        roles['user'] = Role(
            role_id='user',
            name=UserRole.USER,
            description='Standard user with basic access',
            permissions={
                Permission.READ_BANK_DATA, Permission.VIEW_BALANCES, Permission.VIEW_TRANSACTIONS
            },
            security_level=SecurityLevel.LOW,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Read-only role
        roles['read_only'] = Role(
            role_id='read_only',
            name=UserRole.READ_ONLY,
            description='Read-only access for viewing',
            permissions={
                Permission.READ_BANK_DATA, Permission.VIEW_BALANCES
            },
            security_level=SecurityLevel.LOW,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        return roles
    
    def _initialize_user_access(self) -> Dict[str, UserAccess]:
        """Initialize user access information"""
        return {}
    
    def _initialize_security_alerts(self) -> Dict[str, SecurityAlert]:
        """Initialize security alerts storage"""
        return {}
    
    def _initialize_user_activities(self) -> Dict[str, UserActivity]:
        """Initialize user activities storage"""
        return {}
    
    def _initialize_user_consents(self) -> Dict[str, UserConsent]:
        """Initialize user consents storage"""
        return {}
    
    def _initialize_data_breach_incidents(self) -> Dict[str, DataBreachIncident]:
        """Initialize data breach incidents storage"""
        return {}
    
    def _start_monitoring_threads(self):
        """Start real-time monitoring threads"""
        try:
            # Start activity monitoring
            activity_thread = threading.Thread(target=self.activity_monitor.start_monitoring, daemon=True)
            activity_thread.start()
            
            # Start suspicious activity detection
            detection_thread = threading.Thread(target=self.suspicious_activity_detector.start_detection, daemon=True)
            detection_thread.start()
            
            # Start breach prevention monitoring
            breach_thread = threading.Thread(target=self.breach_prevention_system.start_monitoring, daemon=True)
            breach_thread.start()
            
            self.logger.info("Real-time monitoring threads started")
            
        except Exception as e:
            self.logger.error(f"Error starting monitoring threads: {e}")
    
    def check_permission(self, user_id: str, permission: Permission, 
                        resource_type: str = None, resource_id: str = None) -> bool:
        """Check if user has permission for specific operation"""
        try:
            # Get user access information
            user_access = self.user_access.get(user_id)
            if not user_access:
                return False
            
            # Check if user is locked
            if user_access.is_locked:
                self._log_security_violation(user_id, f"Locked user attempted {permission.value}")
                return False
            
            # Check if user has the permission
            if permission not in user_access.permissions:
                self._log_security_violation(user_id, f"Unauthorized access attempt: {permission.value}")
                return False
            
            # Check resource-specific permissions
            if resource_type and resource_id:
                if not self._check_resource_permission(user_id, permission, resource_type, resource_id):
                    return False
            
            # Log successful permission check
            self._log_activity(user_id, ActivityType.DATA_ACCESS, resource_type, resource_id, {
                'permission': permission.value,
                'granted': True
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking permission: {e}")
            return False
    
    def _check_resource_permission(self, user_id: str, permission: Permission, 
                                 resource_type: str, resource_id: str) -> bool:
        """Check resource-specific permissions"""
        try:
            # For banking data, check ownership
            if resource_type == 'bank_account':
                return self.compliance_service.validate_bank_data_access(
                    user_id=user_id,
                    bank_account_id=resource_id,
                    access_type=permission.value,
                    ip_address="system",
                    user_agent="system"
                )
            
            # For user data, check if user is accessing their own data or has admin rights
            if resource_type == 'user':
                user_access = self.user_access.get(user_id)
                if user_id == resource_id or Permission.SYSTEM_ADMIN in user_access.permissions:
                    return True
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking resource permission: {e}")
            return False
    
    def assign_role(self, user_id: str, role_name: UserRole, assigned_by: str) -> bool:
        """Assign role to user"""
        try:
            # Check if assigner has permission
            if not self.check_permission(assigned_by, Permission.SYSTEM_ADMIN):
                return False
            
            # Get role
            role = None
            for r in self.roles.values():
                if r.name == role_name:
                    role = r
                    break
            
            if not role:
                return False
            
            # Update user access
            self.user_access[user_id] = UserAccess(
                user_id=user_id,
                role=role.name,
                permissions=role.permissions,
                security_level=role.security_level,
                last_login=datetime.utcnow(),
                login_count=0,
                failed_attempts=0,
                is_locked=False,
                mfa_enabled=False
            )
            
            # Log role assignment
            self._log_activity(assigned_by, ActivityType.ROLE_CHANGE, 'user', user_id, {
                'new_role': role_name.value,
                'assigned_by': assigned_by
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error assigning role: {e}")
            return False
    
    def revoke_permission(self, user_id: str, permission: Permission, revoked_by: str) -> bool:
        """Revoke specific permission from user"""
        try:
            # Check if revoker has permission
            if not self.check_permission(revoked_by, Permission.SYSTEM_ADMIN):
                return False
            
            # Get user access
            user_access = self.user_access.get(user_id)
            if not user_access:
                return False
            
            # Remove permission
            if permission in user_access.permissions:
                user_access.permissions.remove(permission)
                
                # Log permission revocation
                self._log_activity(revoked_by, ActivityType.PERMISSION_CHANGE, 'user', user_id, {
                    'revoked_permission': permission.value,
                    'revoked_by': revoked_by
                })
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error revoking permission: {e}")
            return False
    
    def record_login_attempt(self, user_id: str, ip_address: str, user_agent: str, 
                           success: bool) -> bool:
        """Record login attempt and handle security measures"""
        try:
            user_access = self.user_access.get(user_id)
            if not user_access:
                # Create new user access for first login
                user_access = UserAccess(
                    user_id=user_id,
                    role=UserRole.USER,
                    permissions=self.roles['user'].permissions,
                    security_level=SecurityLevel.LOW,
                    last_login=datetime.utcnow(),
                    login_count=0,
                    failed_attempts=0,
                    is_locked=False,
                    mfa_enabled=False
                )
                self.user_access[user_id] = user_access
            
            if success:
                # Successful login
                user_access.last_login = datetime.utcnow()
                user_access.login_count += 1
                user_access.failed_attempts = 0
                
                # Log successful login
                self._log_activity(user_id, ActivityType.LOGIN, 'system', None, {
                    'ip_address': ip_address,
                    'user_agent': user_agent
                })
                
            else:
                # Failed login
                user_access.failed_attempts += 1
                
                # Lock account after 5 failed attempts
                if user_access.failed_attempts >= 5:
                    user_access.is_locked = True
                    self._create_security_alert(
                        alert_type='account_locked',
                        severity='high',
                        title=f'Account locked for user {user_id}',
                        description=f'Account locked due to {user_access.failed_attempts} failed login attempts',
                        user_id=user_id,
                        ip_address=ip_address
                    )
                
                # Log failed login
                self._log_activity(user_id, ActivityType.LOGIN, 'system', None, {
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'failed_attempts': user_access.failed_attempts
                })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error recording login attempt: {e}")
            return False
    
    def _log_activity(self, user_id: str, activity_type: ActivityType, resource_type: str,
                     resource_id: str, metadata: Dict[str, Any]):
        """Log user activity"""
        try:
            activity = UserActivity(
                activity_id=f"activity_{int(time.time())}_{secrets.token_hex(4)}",
                user_id=user_id,
                activity_type=activity_type,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=metadata.get('ip_address', 'unknown'),
                user_agent=metadata.get('user_agent', 'unknown'),
                timestamp=datetime.utcnow(),
                metadata=metadata,
                risk_score=self._calculate_risk_score(user_id, activity_type, metadata)
            )
            
            # Store activity
            self.user_activities[activity.activity_id] = activity
            
            # Log to audit service
            self.audit_service.log_event(
                event_type=AuditEventType.DATA_ACCESS if activity_type == ActivityType.DATA_ACCESS else AuditEventType.AUTHENTICATION,
                event_category=LogCategory.AUTHENTICATION if activity_type in [ActivityType.LOGIN, ActivityType.LOGOUT] else LogCategory.DATA_ACCESS,
                severity=LogSeverity.INFO,
                description=f"User activity: {activity_type.value}",
                resource_type=resource_type,
                resource_id=resource_id,
                user_id=user_id,
                ip_address=activity.ip_address,
                user_agent=activity.user_agent,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Error logging activity: {e}")
    
    def _log_security_violation(self, user_id: str, description: str):
        """Log security violation"""
        try:
            self._log_activity(user_id, ActivityType.SECURITY_VIOLATION, 'security', None, {
                'description': description,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Create security alert
            self._create_security_alert(
                alert_type='security_violation',
                severity='high',
                title=f'Security violation for user {user_id}',
                description=description,
                user_id=user_id,
                ip_address='unknown'
            )
            
        except Exception as e:
            self.logger.error(f"Error logging security violation: {e}")
    
    def _calculate_risk_score(self, user_id: str, activity_type: ActivityType, 
                            metadata: Dict[str, Any]) -> float:
        """Calculate risk score for activity"""
        try:
            risk_score = 0.0
            
            # Base risk scores for different activity types
            base_risks = {
                ActivityType.LOGIN: 1.0,
                ActivityType.DATA_ACCESS: 2.0,
                ActivityType.DATA_MODIFICATION: 5.0,
                ActivityType.ACCOUNT_CREATION: 3.0,
                ActivityType.ACCOUNT_DELETION: 8.0,
                ActivityType.PERMISSION_CHANGE: 7.0,
                ActivityType.ROLE_CHANGE: 8.0,
                ActivityType.SUSPICIOUS_ACTIVITY: 10.0,
                ActivityType.SECURITY_VIOLATION: 10.0
            }
            
            risk_score += base_risks.get(activity_type, 1.0)
            
            # Additional risk factors
            if metadata.get('failed_attempts', 0) > 0:
                risk_score += metadata['failed_attempts'] * 2.0
            
            if metadata.get('ip_address') and self._is_suspicious_ip(metadata['ip_address']):
                risk_score += 5.0
            
            if metadata.get('unusual_time', False):
                risk_score += 3.0
            
            return min(risk_score, 10.0)  # Cap at 10.0
            
        except Exception as e:
            self.logger.error(f"Error calculating risk score: {e}")
            return 5.0  # Default medium risk
    
    def _is_suspicious_ip(self, ip_address: str) -> bool:
        """Check if IP address is suspicious"""
        try:
            # In a real implementation, this would check against threat intelligence feeds
            suspicious_patterns = [
                r'^0\.0\.0\.',  # Reserved
                r'^127\.',      # Loopback
                r'^10\.',       # Private network
                r'^172\.(1[6-9]|2[0-9]|3[0-1])\.',  # Private network
                r'^192\.168\.'  # Private network
            ]
            
            for pattern in suspicious_patterns:
                if re.match(pattern, ip_address):
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking suspicious IP: {e}")
            return False
    
    def _create_security_alert(self, alert_type: str, severity: str, title: str, 
                             description: str, user_id: str, ip_address: str):
        """Create security alert"""
        try:
            alert = SecurityAlert(
                alert_id=f"alert_{int(time.time())}_{secrets.token_hex(4)}",
                alert_type=alert_type,
                severity=severity,
                title=title,
                description=description,
                user_id=user_id,
                ip_address=ip_address,
                timestamp=datetime.utcnow(),
                status='open',
                evidence={'alert_type': alert_type, 'severity': severity},
                remediation_steps=self._get_remediation_steps(alert_type)
            )
            
            self.security_alerts[alert.alert_id] = alert
            
            # Log security alert
            self.audit_service.log_event(
                event_type=AuditEventType.SECURITY_INCIDENT,
                event_category=LogCategory.SECURITY,
                severity=LogSeverity.WARNING if severity in ['low', 'medium'] else LogSeverity.ERROR,
                description=f"Security alert: {title}",
                resource_type="security_alert",
                resource_id=alert.alert_id,
                user_id=user_id,
                ip_address=ip_address,
                metadata={'alert_type': alert_type, 'severity': severity}
            )
            
        except Exception as e:
            self.logger.error(f"Error creating security alert: {e}")
    
    def _get_remediation_steps(self, alert_type: str) -> List[str]:
        """Get remediation steps for alert type"""
        remediation_steps = {
            'account_locked': [
                'Verify user identity',
                'Reset password if necessary',
                'Review login attempts',
                'Consider additional authentication factors'
            ],
            'security_violation': [
                'Investigate the violation',
                'Review user permissions',
                'Consider account suspension',
                'Update security policies if needed'
            ],
            'suspicious_activity': [
                'Monitor user activity',
                'Review access patterns',
                'Consider additional monitoring',
                'Investigate potential threats'
            ],
            'data_breach': [
                'Contain the breach',
                'Assess affected data',
                'Notify affected users',
                'Report to authorities if required',
                'Implement additional security measures'
            ]
        }
        
        return remediation_steps.get(alert_type, ['Investigate and remediate'])
    
    def manage_user_consent(self, user_id: str, consent_type: ConsentType, granted: bool,
                          ip_address: str, user_agent: str, expires_at: datetime = None) -> str:
        """Manage user consent"""
        try:
            consent_id = f"consent_{int(time.time())}_{secrets.token_hex(4)}"
            
            consent = UserConsent(
                consent_id=consent_id,
                user_id=user_id,
                consent_type=consent_type,
                granted=granted,
                granted_at=datetime.utcnow(),
                expires_at=expires_at,
                version="1.0",
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={'consent_type': consent_type.value, 'granted': granted}
            )
            
            self.user_consents[consent_id] = consent
            
            # Log consent management
            self._log_activity(user_id, ActivityType.DATA_ACCESS, 'consent', consent_id, {
                'consent_type': consent_type.value,
                'granted': granted,
                'ip_address': ip_address
            })
            
            return consent_id
            
        except Exception as e:
            self.logger.error(f"Error managing user consent: {e}")
            raise
    
    def check_user_consent(self, user_id: str, consent_type: ConsentType) -> bool:
        """Check if user has granted consent"""
        try:
            # Get latest consent for this type
            user_consents = [c for c in self.user_consents.values() 
                           if c.user_id == user_id and c.consent_type == consent_type]
            
            if not user_consents:
                return False
            
            # Get most recent consent
            latest_consent = max(user_consents, key=lambda x: x.granted_at)
            
            # Check if consent is still valid
            if latest_consent.expires_at and datetime.utcnow() > latest_consent.expires_at:
                return False
            
            return latest_consent.granted
            
        except Exception as e:
            self.logger.error(f"Error checking user consent: {e}")
            return False
    
    def get_access_control_metrics(self) -> Dict[str, Any]:
        """Get access control and monitoring metrics"""
        try:
            current_time = datetime.utcnow()
            
            # User access metrics
            total_users = len(self.user_access)
            active_users = len([u for u in self.user_access.values() if not u.is_locked])
            locked_users = len([u for u in self.user_access.values() if u.is_locked])
            
            # Role distribution
            role_distribution = defaultdict(int)
            for user_access in self.user_access.values():
                role_distribution[user_access.role.value] += 1
            
            # Security alerts
            total_alerts = len(self.security_alerts)
            open_alerts = len([a for a in self.security_alerts.values() if a.status == 'open'])
            critical_alerts = len([a for a in self.security_alerts.values() if a.severity == 'critical'])
            
            # User activities
            recent_activities = [a for a in self.user_activities.values() 
                               if (current_time - a.timestamp).days <= 7]
            high_risk_activities = len([a for a in recent_activities if a.risk_score >= 7.0])
            
            # Consent metrics
            total_consents = len(self.user_consents)
            active_consents = len([c for c in self.user_consents.values() 
                                 if c.granted and (not c.expires_at or current_time <= c.expires_at)])
            
            return {
                'user_metrics': {
                    'total_users': total_users,
                    'active_users': active_users,
                    'locked_users': locked_users,
                    'role_distribution': dict(role_distribution)
                },
                'security_metrics': {
                    'total_alerts': total_alerts,
                    'open_alerts': open_alerts,
                    'critical_alerts': critical_alerts,
                    'recent_activities': len(recent_activities),
                    'high_risk_activities': high_risk_activities
                },
                'consent_metrics': {
                    'total_consents': total_consents,
                    'active_consents': active_consents
                },
                'last_updated': current_time.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting access control metrics: {e}")
            return {}


class ActivityMonitor:
    """Real-time activity monitoring system"""
    
    def __init__(self, access_control_service: AccessControlService):
        self.access_control_service = access_control_service
        self.logger = logging.getLogger(__name__)
        self.monitoring_active = False
        self.activity_queue = deque(maxlen=1000)
    
    def start_monitoring(self):
        """Start real-time activity monitoring"""
        self.monitoring_active = True
        self.logger.info("Activity monitoring started")
        
        while self.monitoring_active:
            try:
                # Process activity queue
                while self.activity_queue:
                    activity = self.activity_queue.popleft()
                    self._process_activity(activity)
                
                # Sleep for monitoring interval
                time.sleep(1)  # 1 second interval
                
            except Exception as e:
                self.logger.error(f"Error in activity monitoring: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _process_activity(self, activity: UserActivity):
        """Process individual activity"""
        try:
            # Check for unusual patterns
            if self._is_unusual_activity(activity):
                self.access_control_service._create_security_alert(
                    alert_type='unusual_activity',
                    severity='medium',
                    title=f'Unusual activity detected for user {activity.user_id}',
                    description=f'Unusual {activity.activity_type.value} activity detected',
                    user_id=activity.user_id,
                    ip_address=activity.ip_address
                )
            
            # Check for rapid activity
            if self._is_rapid_activity(activity):
                self.access_control_service._create_security_alert(
                    alert_type='rapid_activity',
                    severity='high',
                    title=f'Rapid activity detected for user {activity.user_id}',
                    description=f'Rapid {activity.activity_type.value} activity detected',
                    user_id=activity.user_id,
                    ip_address=activity.ip_address
                )
                
        except Exception as e:
            self.logger.error(f"Error processing activity: {e}")
    
    def _is_unusual_activity(self, activity: UserActivity) -> bool:
        """Check if activity is unusual"""
        try:
            # Check for unusual time (outside business hours)
            hour = activity.timestamp.hour
            if hour < 6 or hour > 22:  # Outside 6 AM - 10 PM
                return True
            
            # Check for unusual IP
            if self.access_control_service._is_suspicious_ip(activity.ip_address):
                return True
            
            # Check for high-risk activities
            if activity.risk_score >= 8.0:
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking unusual activity: {e}")
            return False
    
    def _is_rapid_activity(self, activity: UserActivity) -> bool:
        """Check if activity is happening too rapidly"""
        try:
            # Count recent activities for this user
            recent_activities = [a for a in self.access_control_service.user_activities.values()
                               if a.user_id == activity.user_id and 
                               (activity.timestamp - a.timestamp).seconds <= 60]
            
            # If more than 10 activities in the last minute, it's rapid
            return len(recent_activities) > 10
            
        except Exception as e:
            self.logger.error(f"Error checking rapid activity: {e}")
            return False


class SuspiciousActivityDetector:
    """Suspicious activity detection system"""
    
    def __init__(self, access_control_service: AccessControlService):
        self.access_control_service = access_control_service
        self.logger = logging.getLogger(__name__)
        self.detection_active = False
    
    def start_detection(self):
        """Start suspicious activity detection"""
        self.detection_active = True
        self.logger.info("Suspicious activity detection started")
        
        while self.detection_active:
            try:
                # Analyze recent activities for patterns
                self._analyze_activity_patterns()
                
                # Sleep for detection interval
                time.sleep(30)  # 30 second interval
                
            except Exception as e:
                self.logger.error(f"Error in suspicious activity detection: {e}")
                time.sleep(60)  # Wait before retrying
    
    def _analyze_activity_patterns(self):
        """Analyze activity patterns for suspicious behavior"""
        try:
            current_time = datetime.utcnow()
            recent_activities = [a for a in self.access_control_service.user_activities.values()
                               if (current_time - a.timestamp).hours <= 1]
            
            # Group activities by user
            user_activities = defaultdict(list)
            for activity in recent_activities:
                user_activities[activity.user_id].append(activity)
            
            # Analyze each user's activities
            for user_id, activities in user_activities.items():
                if self._is_suspicious_pattern(activities):
                    self.access_control_service._create_security_alert(
                        alert_type='suspicious_pattern',
                        severity='high',
                        title=f'Suspicious activity pattern detected for user {user_id}',
                        description=f'Suspicious activity pattern detected in recent activities',
                        user_id=user_id,
                        ip_address=activities[-1].ip_address
                    )
                    
        except Exception as e:
            self.logger.error(f"Error analyzing activity patterns: {e}")
    
    def _is_suspicious_pattern(self, activities: List[UserActivity]) -> bool:
        """Check if activity pattern is suspicious"""
        try:
            if len(activities) < 3:
                return False
            
            # Check for rapid role changes
            role_changes = [a for a in activities if a.activity_type == ActivityType.ROLE_CHANGE]
            if len(role_changes) > 1:
                return True
            
            # Check for multiple failed login attempts
            failed_logins = [a for a in activities if a.activity_type == ActivityType.LOGIN and 
                           a.metadata.get('failed_attempts', 0) > 0]
            if len(failed_logins) > 3:
                return True
            
            # Check for unusual data access patterns
            data_access = [a for a in activities if a.activity_type == ActivityType.DATA_ACCESS]
            if len(data_access) > 20:  # More than 20 data access attempts in an hour
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking suspicious pattern: {e}")
            return False


class BreachPreventionSystem:
    """Data breach prevention and response system"""
    
    def __init__(self, access_control_service: AccessControlService):
        self.access_control_service = access_control_service
        self.logger = logging.getLogger(__name__)
        self.monitoring_active = False
    
    def start_monitoring(self):
        """Start breach prevention monitoring"""
        self.monitoring_active = True
        self.logger.info("Breach prevention monitoring started")
        
        while self.monitoring_active:
            try:
                # Check for potential breaches
                self._check_for_breaches()
                
                # Sleep for monitoring interval
                time.sleep(60)  # 1 minute interval
                
            except Exception as e:
                self.logger.error(f"Error in breach prevention monitoring: {e}")
                time.sleep(120)  # Wait before retrying
    
    def _check_for_breaches(self):
        """Check for potential data breaches"""
        try:
            current_time = datetime.utcnow()
            
            # Check for unauthorized data access
            recent_activities = [a for a in self.access_control_service.user_activities.values()
                               if a.activity_type == ActivityType.DATA_ACCESS and
                               (current_time - a.timestamp).minutes <= 5]
            
            for activity in recent_activities:
                if not self.access_control_service.check_permission(
                    activity.user_id, Permission.READ_BANK_DATA, 
                    activity.resource_type, activity.resource_id
                ):
                    self._handle_potential_breach(activity)
            
            # Check for unusual data export patterns
            export_activities = [a for a in recent_activities 
                               if a.metadata.get('permission') == Permission.EXPORT_BANK_DATA.value]
            
            if len(export_activities) > 5:  # More than 5 exports in 5 minutes
                self._handle_potential_breach(export_activities[0])
                
        except Exception as e:
            self.logger.error(f"Error checking for breaches: {e}")
    
    def _handle_potential_breach(self, activity: UserActivity):
        """Handle potential data breach"""
        try:
            # Create breach incident
            incident_id = f"breach_{int(time.time())}_{secrets.token_hex(4)}"
            
            incident = DataBreachIncident(
                incident_id=incident_id,
                incident_type='unauthorized_access',
                severity='high',
                description=f'Potential data breach detected for user {activity.user_id}',
                affected_users=[activity.user_id],
                affected_data=[activity.resource_type],
                detected_at=datetime.utcnow(),
                status='detected',
                containment_actions=[
                    'Immediate account suspension',
                    'Review access logs',
                    'Assess data exposure',
                    'Implement additional monitoring'
                ]
            )
            
            self.access_control_service.data_breach_incidents[incident_id] = incident
            
            # Create security alert
            self.access_control_service._create_security_alert(
                alert_type='data_breach',
                severity='critical',
                title=f'Potential data breach detected',
                description=f'Potential data breach detected for user {activity.user_id}',
                user_id=activity.user_id,
                ip_address=activity.ip_address
            )
            
            # Log breach incident
            self.access_control_service.audit_service.log_event(
                event_type=AuditEventType.SECURITY_INCIDENT,
                event_category=LogCategory.SECURITY,
                severity=LogSeverity.CRITICAL,
                description=f"Data breach incident detected: {incident_id}",
                resource_type="data_breach",
                resource_id=incident_id,
                user_id=activity.user_id,
                ip_address=activity.ip_address,
                metadata={'incident_type': incident.incident_type, 'severity': incident.severity}
            )
            
        except Exception as e:
            self.logger.error(f"Error handling potential breach: {e}") 