"""
Monitoring Dashboard Service

This module provides a comprehensive monitoring dashboard for real-time security monitoring,
suspicious activity detection, data breach prevention and response, and user consent management.
"""

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from collections import defaultdict, deque
import threading

from backend.security.access_control_service import AccessControlService, UserRole, Permission, SecurityLevel
from backend.security.banking_compliance import BankingComplianceService
from backend.security.audit_logging import AuditLoggingService
from backend.security.data_protection_service import DataProtectionService

logger = logging.getLogger(__name__)


class DashboardWidgetType(Enum):
    """Types of monitoring dashboard widgets"""
    SECURITY_ALERTS = "security_alerts"
    USER_ACTIVITY = "user_activity"
    ACCESS_CONTROL = "access_control"
    COMPLIANCE_STATUS = "compliance_status"
    DATA_PROTECTION = "data_protection"
    CONSENT_MANAGEMENT = "consent_management"
    BREACH_PREVENTION = "breach_prevention"
    REAL_TIME_MONITORING = "real_time_monitoring"


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityMetrics:
    """Security metrics data structure"""
    total_alerts: int
    open_alerts: int
    critical_alerts: int
    resolved_alerts: int
    alert_trend: str  # increasing, decreasing, stable
    average_response_time: float  # minutes
    security_score: float  # 0-100


@dataclass
class UserActivityMetrics:
    """User activity metrics data structure"""
    total_users: int
    active_users: int
    locked_users: int
    failed_login_attempts: int
    suspicious_activities: int
    high_risk_activities: int
    activity_trend: str  # increasing, decreasing, stable


@dataclass
class AccessControlMetrics:
    """Access control metrics data structure"""
    total_permissions: int
    granted_permissions: int
    denied_permissions: int
    role_distribution: Dict[str, int]
    permission_requests: int
    access_violations: int


@dataclass
class ComplianceMetrics:
    """Compliance metrics data structure"""
    pci_dss_score: float
    soc2_status: str
    ccpa_compliance: bool
    gdpr_compliance: bool
    audit_findings: int
    remediation_required: int
    compliance_score: float


@dataclass
class DataProtectionMetrics:
    """Data protection metrics data structure"""
    encrypted_data_sets: int
    encryption_coverage: float  # percentage
    key_rotation_status: str
    token_management: Dict[str, int]
    data_breach_incidents: int
    protection_score: float


@dataclass
class ConsentMetrics:
    """Consent management metrics data structure"""
    total_consents: int
    active_consents: int
    expired_consents: int
    consent_types: Dict[str, int]
    consent_requests: int
    consent_compliance: float


@dataclass
class RealTimeEvent:
    """Real-time event data structure"""
    event_id: str
    event_type: str
    severity: AlertSeverity
    title: str
    description: str
    user_id: Optional[str]
    ip_address: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class MonitoringDashboardService:
    """Comprehensive monitoring dashboard service"""
    
    def __init__(self, access_control_service: AccessControlService,
                 compliance_service: BankingComplianceService,
                 audit_service: AuditLoggingService,
                 data_protection_service: DataProtectionService):
        self.access_control_service = access_control_service
        self.compliance_service = compliance_service
        self.audit_service = audit_service
        self.data_protection_service = data_protection_service
        self.logger = logging.getLogger(__name__)
        
        # Real-time monitoring
        self.real_time_events = deque(maxlen=1000)
        self.monitoring_active = False
        
        # Start real-time monitoring
        self._start_real_time_monitoring()
    
    def _start_real_time_monitoring(self):
        """Start real-time monitoring thread"""
        try:
            monitoring_thread = threading.Thread(target=self._monitor_real_time_events, daemon=True)
            monitoring_thread.start()
            self.monitoring_active = True
            self.logger.info("Real-time monitoring started")
        except Exception as e:
            self.logger.error(f"Error starting real-time monitoring: {e}")
    
    def _monitor_real_time_events(self):
        """Monitor real-time events"""
        while self.monitoring_active:
            try:
                # Monitor security alerts
                self._monitor_security_alerts()
                
                # Monitor user activities
                self._monitor_user_activities()
                
                # Monitor access control
                self._monitor_access_control()
                
                # Monitor compliance
                self._monitor_compliance()
                
                # Monitor data protection
                self._monitor_data_protection()
                
                # Sleep for monitoring interval
                time.sleep(5)  # 5 second interval
                
            except Exception as e:
                self.logger.error(f"Error in real-time monitoring: {e}")
                time.sleep(10)  # Wait before retrying
    
    def _monitor_security_alerts(self):
        """Monitor security alerts for real-time events"""
        try:
            current_time = datetime.utcnow()
            recent_alerts = [alert for alert in self.access_control_service.security_alerts.values()
                           if (current_time - alert.timestamp).minutes <= 5]
            
            for alert in recent_alerts:
                if alert.status == 'open':
                    event = RealTimeEvent(
                        event_id=f"alert_{alert.alert_id}",
                        event_type="security_alert",
                        severity=AlertSeverity(alert.severity),
                        title=alert.title,
                        description=alert.description,
                        user_id=alert.user_id,
                        ip_address=alert.ip_address,
                        timestamp=alert.timestamp,
                        metadata={'alert_type': alert.alert_type, 'status': alert.status}
                    )
                    self.real_time_events.append(event)
                    
        except Exception as e:
            self.logger.error(f"Error monitoring security alerts: {e}")
    
    def _monitor_user_activities(self):
        """Monitor user activities for real-time events"""
        try:
            current_time = datetime.utcnow()
            recent_activities = [activity for activity in self.access_control_service.user_activities.values()
                               if (current_time - activity.timestamp).minutes <= 5]
            
            for activity in recent_activities:
                if activity.risk_score >= 7.0:  # High-risk activities
                    event = RealTimeEvent(
                        event_id=f"activity_{activity.activity_id}",
                        event_type="high_risk_activity",
                        severity=AlertSeverity.HIGH if activity.risk_score >= 8.0 else AlertSeverity.MEDIUM,
                        title=f"High-risk activity detected for user {activity.user_id}",
                        description=f"High-risk {activity.activity_type.value} activity detected",
                        user_id=activity.user_id,
                        ip_address=activity.ip_address,
                        timestamp=activity.timestamp,
                        metadata={'activity_type': activity.activity_type.value, 'risk_score': activity.risk_score}
                    )
                    self.real_time_events.append(event)
                    
        except Exception as e:
            self.logger.error(f"Error monitoring user activities: {e}")
    
    def _monitor_access_control(self):
        """Monitor access control for real-time events"""
        try:
            # Monitor for access violations
            current_time = datetime.utcnow()
            recent_activities = [activity for activity in self.access_control_service.user_activities.values()
                               if activity.activity_type.value == 'security_violation' and
                               (current_time - activity.timestamp).minutes <= 5]
            
            for activity in recent_activities:
                event = RealTimeEvent(
                    event_id=f"access_{activity.activity_id}",
                    event_type="access_violation",
                    severity=AlertSeverity.HIGH,
                    title=f"Access violation for user {activity.user_id}",
                    description=activity.metadata.get('description', 'Access violation detected'),
                    user_id=activity.user_id,
                    ip_address=activity.ip_address,
                    timestamp=activity.timestamp,
                    metadata={'violation_type': 'access_control'}
                )
                self.real_time_events.append(event)
                
        except Exception as e:
            self.logger.error(f"Error monitoring access control: {e}")
    
    def _monitor_compliance(self):
        """Monitor compliance for real-time events"""
        try:
            # This would integrate with compliance monitoring systems
            # For now, we'll simulate compliance monitoring
            pass
        except Exception as e:
            self.logger.error(f"Error monitoring compliance: {e}")
    
    def _monitor_data_protection(self):
        """Monitor data protection for real-time events"""
        try:
            # Monitor for data breach incidents
            current_time = datetime.utcnow()
            recent_incidents = [incident for incident in self.access_control_service.data_breach_incidents.values()
                              if (current_time - incident.detected_at).minutes <= 5]
            
            for incident in recent_incidents:
                event = RealTimeEvent(
                    event_id=f"breach_{incident.incident_id}",
                    event_type="data_breach",
                    severity=AlertSeverity.CRITICAL,
                    title=f"Data breach incident detected",
                    description=incident.description,
                    user_id=incident.affected_users[0] if incident.affected_users else None,
                    ip_address="unknown",
                    timestamp=incident.detected_at,
                    metadata={'incident_type': incident.incident_type, 'severity': incident.severity}
                )
                self.real_time_events.append(event)
                
        except Exception as e:
            self.logger.error(f"Error monitoring data protection: {e}")
    
    def get_security_metrics(self) -> SecurityMetrics:
        """Get comprehensive security metrics"""
        try:
            alerts = self.access_control_service.security_alerts.values()
            total_alerts = len(alerts)
            open_alerts = len([a for a in alerts if a.status == 'open'])
            critical_alerts = len([a for a in alerts if a.severity == 'critical'])
            resolved_alerts = len([a for a in alerts if a.status == 'resolved'])
            
            # Calculate alert trend
            current_time = datetime.utcnow()
            recent_alerts = [a for a in alerts if (current_time - a.timestamp).hours <= 24]
            previous_alerts = [a for a in alerts if 24 < (current_time - a.timestamp).hours <= 48]
            
            if len(recent_alerts) > len(previous_alerts):
                alert_trend = "increasing"
            elif len(recent_alerts) < len(previous_alerts):
                alert_trend = "decreasing"
            else:
                alert_trend = "stable"
            
            # Calculate average response time (simulated)
            average_response_time = 15.5  # minutes
            
            # Calculate security score
            security_score = max(0, 100 - (critical_alerts * 10) - (open_alerts * 5))
            
            return SecurityMetrics(
                total_alerts=total_alerts,
                open_alerts=open_alerts,
                critical_alerts=critical_alerts,
                resolved_alerts=resolved_alerts,
                alert_trend=alert_trend,
                average_response_time=average_response_time,
                security_score=security_score
            )
            
        except Exception as e:
            self.logger.error(f"Error getting security metrics: {e}")
            return SecurityMetrics(0, 0, 0, 0, "stable", 0.0, 0.0)
    
    def get_user_activity_metrics(self) -> UserActivityMetrics:
        """Get user activity metrics"""
        try:
            user_access = self.access_control_service.user_access.values()
            total_users = len(user_access)
            active_users = len([u for u in user_access if not u.is_locked])
            locked_users = len([u for u in user_access if u.is_locked])
            
            # Calculate failed login attempts
            activities = self.access_control_service.user_activities.values()
            failed_login_attempts = len([a for a in activities 
                                       if a.activity_type.value == 'login' and 
                                       a.metadata.get('failed_attempts', 0) > 0])
            
            # Calculate suspicious activities
            suspicious_activities = len([a for a in activities 
                                       if a.activity_type.value == 'suspicious_activity'])
            
            # Calculate high-risk activities
            high_risk_activities = len([a for a in activities if a.risk_score >= 7.0])
            
            # Calculate activity trend
            current_time = datetime.utcnow()
            recent_activities = [a for a in activities if (current_time - a.timestamp).hours <= 24]
            previous_activities = [a for a in activities if 24 < (current_time - a.timestamp).hours <= 48]
            
            if len(recent_activities) > len(previous_activities):
                activity_trend = "increasing"
            elif len(recent_activities) < len(previous_activities):
                activity_trend = "decreasing"
            else:
                activity_trend = "stable"
            
            return UserActivityMetrics(
                total_users=total_users,
                active_users=active_users,
                locked_users=locked_users,
                failed_login_attempts=failed_login_attempts,
                suspicious_activities=suspicious_activities,
                high_risk_activities=high_risk_activities,
                activity_trend=activity_trend
            )
            
        except Exception as e:
            self.logger.error(f"Error getting user activity metrics: {e}")
            return UserActivityMetrics(0, 0, 0, 0, 0, 0, "stable")
    
    def get_access_control_metrics(self) -> AccessControlMetrics:
        """Get access control metrics"""
        try:
            # Get access control metrics from service
            metrics = self.access_control_service.get_access_control_metrics()
            
            # Calculate permission statistics
            total_permissions = sum(len(user.permissions) for user in self.access_control_service.user_access.values())
            granted_permissions = total_permissions  # All stored permissions are granted
            denied_permissions = 0  # Would need to track denied requests
            
            # Get role distribution
            role_distribution = metrics.get('user_metrics', {}).get('role_distribution', {})
            
            # Calculate permission requests (simulated)
            permission_requests = len([a for a in self.access_control_service.user_activities.values()
                                     if a.activity_type.value == 'permission_change'])
            
            # Calculate access violations
            access_violations = len([a for a in self.access_control_service.user_activities.values()
                                   if a.activity_type.value == 'security_violation'])
            
            return AccessControlMetrics(
                total_permissions=total_permissions,
                granted_permissions=granted_permissions,
                denied_permissions=denied_permissions,
                role_distribution=role_distribution,
                permission_requests=permission_requests,
                access_violations=access_violations
            )
            
        except Exception as e:
            self.logger.error(f"Error getting access control metrics: {e}")
            return AccessControlMetrics(0, 0, 0, {}, 0, 0)
    
    def get_compliance_metrics(self) -> ComplianceMetrics:
        """Get compliance metrics"""
        try:
            # Get PCI DSS compliance
            pci_compliance = self.data_protection_service.assess_pci_dss_compliance()
            pci_dss_score = pci_compliance.get('overall_score', 0.0)
            
            # Get SOC 2 preparation status
            soc2_preparation = self.data_protection_service.prepare_soc2_type2_audit()
            soc2_status = "prepared" if soc2_preparation else "not_prepared"
            
            # CCPA compliance (simulated)
            ccpa_compliance = True
            
            # GDPR compliance (simulated)
            gdpr_compliance = True
            
            # Calculate audit findings
            audit_findings = len(pci_compliance.get('findings', []))
            remediation_required = len([f for f in pci_compliance.get('findings', [])
                                      if f.get('severity') in ['high', 'critical']])
            
            # Calculate overall compliance score
            compliance_score = (pci_dss_score + (100 if ccpa_compliance else 0) + 
                              (100 if gdpr_compliance else 0)) / 3
            
            return ComplianceMetrics(
                pci_dss_score=pci_dss_score,
                soc2_status=soc2_status,
                ccpa_compliance=ccpa_compliance,
                gdpr_compliance=gdpr_compliance,
                audit_findings=audit_findings,
                remediation_required=remediation_required,
                compliance_score=compliance_score
            )
            
        except Exception as e:
            self.logger.error(f"Error getting compliance metrics: {e}")
            return ComplianceMetrics(0.0, "unknown", False, False, 0, 0, 0.0)
    
    def get_data_protection_metrics(self) -> DataProtectionMetrics:
        """Get data protection metrics"""
        try:
            # Get data protection metrics from service
            metrics = self.data_protection_service.get_data_protection_metrics()
            
            # Extract metrics
            encryption_metrics = metrics.get('encryption_metrics', {})
            token_metrics = metrics.get('token_metrics', {})
            
            encrypted_data_sets = encryption_metrics.get('active_keys', 0)
            encryption_coverage = 95.0  # Simulated coverage percentage
            key_rotation_status = "up_to_date"  # Simulated status
            
            # Get token management metrics
            token_management = {
                'active_tokens': token_metrics.get('active_tokens', 0),
                'expired_tokens': token_metrics.get('expired_tokens', 0),
                'tokens_by_type': token_metrics.get('tokens_by_type', {})
            }
            
            # Get data breach incidents
            data_breach_incidents = len(self.access_control_service.data_breach_incidents)
            
            # Calculate protection score
            protection_score = max(0, 100 - (data_breach_incidents * 20))
            
            return DataProtectionMetrics(
                encrypted_data_sets=encrypted_data_sets,
                encryption_coverage=encryption_coverage,
                key_rotation_status=key_rotation_status,
                token_management=token_management,
                data_breach_incidents=data_breach_incidents,
                protection_score=protection_score
            )
            
        except Exception as e:
            self.logger.error(f"Error getting data protection metrics: {e}")
            return DataProtectionMetrics(0, 0.0, "unknown", {}, 0, 0.0)
    
    def get_consent_metrics(self) -> ConsentMetrics:
        """Get consent management metrics"""
        try:
            # Get consent metrics from access control service
            metrics = self.access_control_service.get_access_control_metrics()
            consent_metrics = metrics.get('consent_metrics', {})
            
            total_consents = consent_metrics.get('total_consents', 0)
            active_consents = consent_metrics.get('active_consents', 0)
            expired_consents = total_consents - active_consents
            
            # Calculate consent types distribution
            consent_types = {}
            for consent in self.access_control_service.user_consents.values():
                consent_type = consent.consent_type.value
                consent_types[consent_type] = consent_types.get(consent_type, 0) + 1
            
            # Calculate consent requests (simulated)
            consent_requests = len([a for a in self.access_control_service.user_activities.values()
                                  if a.activity_type.value == 'data_access' and 
                                  'consent' in a.metadata])
            
            # Calculate consent compliance
            consent_compliance = (active_consents / total_consents * 100) if total_consents > 0 else 100.0
            
            return ConsentMetrics(
                total_consents=total_consents,
                active_consents=active_consents,
                expired_consents=expired_consents,
                consent_types=consent_types,
                consent_requests=consent_requests,
                consent_compliance=consent_compliance
            )
            
        except Exception as e:
            self.logger.error(f"Error getting consent metrics: {e}")
            return ConsentMetrics(0, 0, 0, {}, 0, 0.0)
    
    def get_real_time_events(self, limit: int = 50) -> List[RealTimeEvent]:
        """Get real-time events"""
        try:
            # Get recent events from the queue
            events = list(self.real_time_events)
            events.sort(key=lambda x: x.timestamp, reverse=True)
            return events[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting real-time events: {e}")
            return []
    
    def get_dashboard_data(self, widget_type: DashboardWidgetType) -> Dict[str, Any]:
        """Get dashboard data for specific widget type"""
        try:
            if widget_type == DashboardWidgetType.SECURITY_ALERTS:
                return self._get_security_alerts_data()
            elif widget_type == DashboardWidgetType.USER_ACTIVITY:
                return self._get_user_activity_data()
            elif widget_type == DashboardWidgetType.ACCESS_CONTROL:
                return self._get_access_control_data()
            elif widget_type == DashboardWidgetType.COMPLIANCE_STATUS:
                return self._get_compliance_status_data()
            elif widget_type == DashboardWidgetType.DATA_PROTECTION:
                return self._get_data_protection_data()
            elif widget_type == DashboardWidgetType.CONSENT_MANAGEMENT:
                return self._get_consent_management_data()
            elif widget_type == DashboardWidgetType.BREACH_PREVENTION:
                return self._get_breach_prevention_data()
            elif widget_type == DashboardWidgetType.REAL_TIME_MONITORING:
                return self._get_real_time_monitoring_data()
            else:
                return {'error': 'Unknown widget type'}
                
        except Exception as e:
            self.logger.error(f"Error getting dashboard data: {e}")
            return {'error': str(e)}
    
    def _get_security_alerts_data(self) -> Dict[str, Any]:
        """Get security alerts dashboard data"""
        try:
            metrics = self.get_security_metrics()
            recent_alerts = list(self.access_control_service.security_alerts.values())[-10:]
            
            return {
                'metrics': {
                    'total_alerts': metrics.total_alerts,
                    'open_alerts': metrics.open_alerts,
                    'critical_alerts': metrics.critical_alerts,
                    'security_score': metrics.security_score,
                    'alert_trend': metrics.alert_trend
                },
                'recent_alerts': [
                    {
                        'id': alert.alert_id,
                        'type': alert.alert_type,
                        'severity': alert.severity,
                        'title': alert.title,
                        'timestamp': alert.timestamp.isoformat(),
                        'status': alert.status
                    }
                    for alert in recent_alerts
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting security alerts data: {e}")
            return {}
    
    def _get_user_activity_data(self) -> Dict[str, Any]:
        """Get user activity dashboard data"""
        try:
            metrics = self.get_user_activity_metrics()
            recent_activities = list(self.access_control_service.user_activities.values())[-20:]
            
            return {
                'metrics': {
                    'total_users': metrics.total_users,
                    'active_users': metrics.active_users,
                    'locked_users': metrics.locked_users,
                    'suspicious_activities': metrics.suspicious_activities,
                    'activity_trend': metrics.activity_trend
                },
                'recent_activities': [
                    {
                        'id': activity.activity_id,
                        'user_id': activity.user_id,
                        'type': activity.activity_type.value,
                        'resource_type': activity.resource_type,
                        'risk_score': activity.risk_score,
                        'timestamp': activity.timestamp.isoformat()
                    }
                    for activity in recent_activities
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting user activity data: {e}")
            return {}
    
    def _get_access_control_data(self) -> Dict[str, Any]:
        """Get access control dashboard data"""
        try:
            metrics = self.get_access_control_metrics()
            
            return {
                'metrics': {
                    'total_permissions': metrics.total_permissions,
                    'granted_permissions': metrics.granted_permissions,
                    'access_violations': metrics.access_violations,
                    'permission_requests': metrics.permission_requests
                },
                'role_distribution': metrics.role_distribution
            }
            
        except Exception as e:
            self.logger.error(f"Error getting access control data: {e}")
            return {}
    
    def _get_compliance_status_data(self) -> Dict[str, Any]:
        """Get compliance status dashboard data"""
        try:
            metrics = self.get_compliance_metrics()
            
            return {
                'metrics': {
                    'pci_dss_score': metrics.pci_dss_score,
                    'soc2_status': metrics.soc2_status,
                    'ccpa_compliance': metrics.ccpa_compliance,
                    'gdpr_compliance': metrics.gdpr_compliance,
                    'compliance_score': metrics.compliance_score
                },
                'audit_findings': metrics.audit_findings,
                'remediation_required': metrics.remediation_required
            }
            
        except Exception as e:
            self.logger.error(f"Error getting compliance status data: {e}")
            return {}
    
    def _get_data_protection_data(self) -> Dict[str, Any]:
        """Get data protection dashboard data"""
        try:
            metrics = self.get_data_protection_metrics()
            
            return {
                'metrics': {
                    'encrypted_data_sets': metrics.encrypted_data_sets,
                    'encryption_coverage': metrics.encryption_coverage,
                    'key_rotation_status': metrics.key_rotation_status,
                    'protection_score': metrics.protection_score
                },
                'token_management': metrics.token_management,
                'data_breach_incidents': metrics.data_breach_incidents
            }
            
        except Exception as e:
            self.logger.error(f"Error getting data protection data: {e}")
            return {}
    
    def _get_consent_management_data(self) -> Dict[str, Any]:
        """Get consent management dashboard data"""
        try:
            metrics = self.get_consent_metrics()
            
            return {
                'metrics': {
                    'total_consents': metrics.total_consents,
                    'active_consents': metrics.active_consents,
                    'expired_consents': metrics.expired_consents,
                    'consent_compliance': metrics.consent_compliance
                },
                'consent_types': metrics.consent_types,
                'consent_requests': metrics.consent_requests
            }
            
        except Exception as e:
            self.logger.error(f"Error getting consent management data: {e}")
            return {}
    
    def _get_breach_prevention_data(self) -> Dict[str, Any]:
        """Get breach prevention dashboard data"""
        try:
            incidents = list(self.access_control_service.data_breach_incidents.values())
            recent_incidents = [incident for incident in incidents 
                              if (datetime.utcnow() - incident.detected_at).days <= 30]
            
            return {
                'total_incidents': len(incidents),
                'recent_incidents': len(recent_incidents),
                'incidents_by_severity': {
                    'low': len([i for i in incidents if i.severity == 'low']),
                    'medium': len([i for i in incidents if i.severity == 'medium']),
                    'high': len([i for i in incidents if i.severity == 'high']),
                    'critical': len([i for i in incidents if i.severity == 'critical'])
                },
                'recent_incidents': [
                    {
                        'id': incident.incident_id,
                        'type': incident.incident_type,
                        'severity': incident.severity,
                        'description': incident.description,
                        'detected_at': incident.detected_at.isoformat(),
                        'status': incident.status
                    }
                    for incident in recent_incidents
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting breach prevention data: {e}")
            return {}
    
    def _get_real_time_monitoring_data(self) -> Dict[str, Any]:
        """Get real-time monitoring dashboard data"""
        try:
            events = self.get_real_time_events(20)
            
            return {
                'total_events': len(events),
                'events_by_severity': {
                    'low': len([e for e in events if e.severity == AlertSeverity.LOW]),
                    'medium': len([e for e in events if e.severity == AlertSeverity.MEDIUM]),
                    'high': len([e for e in events if e.severity == AlertSeverity.HIGH]),
                    'critical': len([e for e in events if e.severity == AlertSeverity.CRITICAL])
                },
                'recent_events': [
                    {
                        'id': event.event_id,
                        'type': event.event_type,
                        'severity': event.severity.value,
                        'title': event.title,
                        'user_id': event.user_id,
                        'timestamp': event.timestamp.isoformat()
                    }
                    for event in events
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting real-time monitoring data: {e}")
            return {}
    
    def get_comprehensive_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive dashboard with all metrics"""
        try:
            return {
                'security_metrics': self.get_security_metrics(),
                'user_activity_metrics': self.get_user_activity_metrics(),
                'access_control_metrics': self.get_access_control_metrics(),
                'compliance_metrics': self.get_compliance_metrics(),
                'data_protection_metrics': self.get_data_protection_metrics(),
                'consent_metrics': self.get_consent_metrics(),
                'real_time_events': self.get_real_time_events(10),
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting comprehensive dashboard: {e}")
            return {} 