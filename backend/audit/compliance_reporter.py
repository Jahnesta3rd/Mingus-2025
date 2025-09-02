"""
MINGUS Application - Compliance Reporter
========================================

Automated compliance reporting system for financial regulations.
Generates comprehensive reports for PCI DSS, GDPR, SOX, and other
compliance frameworks with automated data collection and analysis.

Features:
- PCI DSS compliance reporting
- GDPR data access logging
- Financial regulatory reporting
- Automated report generation
- Compliance score calculation
- Risk assessment and recommendations

Author: MINGUS Development Team
Date: January 2025
License: Proprietary - MINGUS Financial Services
"""

import os
import json
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.exc import SQLAlchemyError

from .audit_logger import AuditLogger, AuditEventType, AuditCategory, AuditSeverity
from ..models.audit import (
    AuditLog, FinancialTransactionAudit, UserActivityAudit,
    SecurityEventAudit, ComplianceReport, AuditStatistics
)

logger = logging.getLogger(__name__)


class ComplianceFramework(Enum):
    """Supported compliance frameworks"""
    PCI_DSS = "pci_dss"
    GDPR = "gdpr"
    SOX = "sox"
    GLBA = "glba"
    CCPA = "ccpa"
    HIPAA = "hipaa"
    SOC2 = "soc2"
    ISO27001 = "iso27001"


class ReportType(Enum):
    """Compliance report types"""
    COMPLIANCE_ASSESSMENT = "compliance_assessment"
    RISK_ASSESSMENT = "risk_assessment"
    AUDIT_TRAIL = "audit_trail"
    DATA_BREACH = "data_breach"
    INCIDENT_RESPONSE = "incident_response"
    REGULATORY_SUBMISSION = "regulatory_submission"


class ComplianceStatus(Enum):
    """Compliance status levels"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    UNDER_REVIEW = "under_review"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class ComplianceRequirement:
    """Individual compliance requirement"""
    requirement_id: str
    framework: ComplianceFramework
    category: str
    title: str
    description: str
    criticality: str  # low, medium, high, critical
    status: ComplianceStatus
    evidence: List[str]
    gaps: List[str]
    recommendations: List[str]
    last_assessed: datetime
    next_assessment: datetime


@dataclass
class ComplianceScore:
    """Compliance scoring results"""
    overall_score: float  # 0-100
    framework_scores: Dict[str, float]
    category_scores: Dict[str, float]
    risk_level: str
    compliance_status: ComplianceStatus
    gaps_count: int
    critical_gaps: int
    last_updated: datetime


class ComplianceReporter:
    """
    Comprehensive compliance reporting system for MINGUS financial application.
    
    Generates automated compliance reports for various regulatory frameworks
    and provides continuous monitoring of compliance status.
    """
    
    def __init__(self, db_session: Session = None, audit_logger: AuditLogger = None):
        self.db_session = db_session
        self.audit_logger = audit_logger or AuditLogger()
        self.frameworks = ComplianceFramework
        self.report_types = ReportType
        
    def generate_pci_dss_report(
        self,
        start_date: datetime,
        end_date: datetime,
        merchant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate PCI DSS compliance report.
        
        Args:
            start_date: Report start date
            end_date: Report end date
            merchant_id: Specific merchant ID for filtering
        
        Returns:
            PCI DSS compliance report
        """
        try:
            report_id = str(uuid.uuid4())
            
            # Collect PCI DSS specific data
            pci_data = self._collect_pci_dss_data(start_date, end_date, merchant_id)
            
            # Calculate compliance scores
            compliance_scores = self._calculate_pci_dss_compliance(pci_data)
            
            # Generate findings and recommendations
            findings = self._analyze_pci_dss_findings(pci_data, compliance_scores)
            recommendations = self._generate_pci_dss_recommendations(findings)
            
            # Determine overall status
            overall_status = self._determine_pci_dss_status(compliance_scores)
            
            # Create report
            report = {
                'report_id': report_id,
                'report_type': ReportType.COMPLIANCE_ASSESSMENT.value,
                'framework': ComplianceFramework.PCI_DSS.value,
                'framework_version': '4.0',
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'merchant_id': merchant_id,
                'overall_status': overall_status.value,
                'compliance_score': compliance_scores.overall_score,
                'risk_level': compliance_scores.risk_level,
                'summary': {
                    'total_requirements': len(pci_data['requirements']),
                    'compliant_requirements': len([r for r in pci_data['requirements'] if r.status == ComplianceStatus.COMPLIANT]),
                    'non_compliant_requirements': len([r for r in pci_data['requirements'] if r.status == ComplianceStatus.NON_COMPLIANT]),
                    'partially_compliant_requirements': len([r for r in pci_data['requirements'] if r.status == ComplianceStatus.PARTIALLY_COMPLIANT]),
                    'critical_gaps': compliance_scores.critical_gaps,
                    'total_gaps': compliance_scores.gaps_count
                },
                'requirements': [asdict(req) for req in pci_data['requirements']],
                'findings': findings,
                'recommendations': recommendations,
                'evidence': pci_data['evidence'],
                'risk_assessment': pci_data['risk_assessment'],
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'generated_by': 'MINGUS Compliance System'
            }
            
            # Store report in database
            self._store_compliance_report(report)
            
            # Log report generation
            self.audit_logger.log_event(
                event_type=AuditEventType.COMPLIANCE_REPORT_GENERATED,
                category=AuditCategory.COMPLIANCE,
                severity=AuditSeverity.INFO,
                description=f"PCI DSS compliance report generated: {report_id}",
                data={
                    'report_id': report_id,
                    'framework': ComplianceFramework.PCI_DSS.value,
                    'overall_status': overall_status.value,
                    'compliance_score': compliance_scores.overall_score,
                    'date_range': f"{start_date.date()} to {end_date.date()}"
                }
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate PCI DSS report: {e}")
            raise
    
    def generate_gdpr_report(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate GDPR compliance report.
        
        Args:
            start_date: Report start date
            end_date: Report end date
            user_id: Specific user ID for filtering
        
        Returns:
            GDPR compliance report
        """
        try:
            report_id = str(uuid.uuid4())
            
            # Collect GDPR specific data
            gdpr_data = self._collect_gdpr_data(start_date, end_date, user_id)
            
            # Calculate compliance scores
            compliance_scores = self._calculate_gdpr_compliance(gdpr_data)
            
            # Generate findings and recommendations
            findings = self._analyze_gdpr_findings(gdpr_data, compliance_scores)
            recommendations = self._generate_gdpr_recommendations(findings)
            
            # Determine overall status
            overall_status = self._determine_gdpr_status(compliance_scores)
            
            # Create report
            report = {
                'report_id': report_id,
                'report_type': ReportType.COMPLIANCE_ASSESSMENT.value,
                'framework': ComplianceFramework.GDPR.value,
                'framework_version': '2018',
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'user_id': user_id,
                'overall_status': overall_status.value,
                'compliance_score': compliance_scores.overall_score,
                'risk_level': compliance_scores.risk_level,
                'summary': {
                    'total_data_subjects': gdpr_data['data_subjects_count'],
                    'consent_records': gdpr_data['consent_records_count'],
                    'data_access_requests': gdpr_data['access_requests_count'],
                    'data_deletion_requests': gdpr_data['deletion_requests_count'],
                    'data_breaches': gdpr_data['data_breaches_count'],
                    'privacy_impact_assessments': gdpr_data['pia_count']
                },
                'data_processing_activities': gdpr_data['processing_activities'],
                'consent_management': gdpr_data['consent_management'],
                'data_subject_rights': gdpr_data['data_subject_rights'],
                'data_breach_incidents': gdpr_data['data_breaches'],
                'findings': findings,
                'recommendations': recommendations,
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'generated_by': 'MINGUS Compliance System'
            }
            
            # Store report in database
            self._store_compliance_report(report)
            
            # Log report generation
            self.audit_logger.log_event(
                event_type=AuditEventType.COMPLIANCE_REPORT_GENERATED,
                category=AuditCategory.COMPLIANCE,
                severity=AuditSeverity.INFO,
                description=f"GDPR compliance report generated: {report_id}",
                data={
                    'report_id': report_id,
                    'framework': ComplianceFramework.GDPR.value,
                    'overall_status': overall_status.value,
                    'compliance_score': compliance_scores.overall_score,
                    'date_range': f"{start_date.date()} to {end_date.date()}"
                }
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate GDPR report: {e}")
            raise
    
    def generate_financial_regulatory_report(
        self,
        start_date: datetime,
        end_date: datetime,
        regulatory_framework: str,
        entity_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate financial regulatory compliance report.
        
        Args:
            start_date: Report start date
            end_date: Report end date
            regulatory_framework: Regulatory framework name
            entity_id: Specific entity ID for filtering
        
        Returns:
            Financial regulatory compliance report
        """
        try:
            report_id = str(uuid.uuid4())
            
            # Collect financial regulatory data
            regulatory_data = self._collect_financial_regulatory_data(
                start_date, end_date, regulatory_framework, entity_id
            )
            
            # Calculate compliance scores
            compliance_scores = self._calculate_financial_regulatory_compliance(regulatory_data)
            
            # Generate findings and recommendations
            findings = self._analyze_financial_regulatory_findings(regulatory_data, compliance_scores)
            recommendations = self._generate_financial_regulatory_recommendations(findings)
            
            # Determine overall status
            overall_status = self._determine_financial_regulatory_status(compliance_scores)
            
            # Create report
            report = {
                'report_id': report_id,
                'report_type': ReportType.REGULATORY_SUBMISSION.value,
                'framework': regulatory_framework,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'entity_id': entity_id,
                'overall_status': overall_status.value,
                'compliance_score': compliance_scores.overall_score,
                'risk_level': compliance_scores.risk_level,
                'summary': {
                    'total_transactions': regulatory_data['total_transactions'],
                    'total_volume': regulatory_data['total_volume'],
                    'suspicious_activities': regulatory_data['suspicious_activities_count'],
                    'compliance_violations': regulatory_data['compliance_violations_count'],
                    'risk_assessments': regulatory_data['risk_assessments_count']
                },
                'transaction_monitoring': regulatory_data['transaction_monitoring'],
                'risk_assessments': regulatory_data['risk_assessments'],
                'compliance_violations': regulatory_data['compliance_violations'],
                'findings': findings,
                'recommendations': recommendations,
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'generated_by': 'MINGUS Compliance System'
            }
            
            # Store report in database
            self._store_compliance_report(report)
            
            # Log report generation
            self.audit_logger.log_event(
                event_type=AuditEventType.COMPLIANCE_REPORT_GENERATED,
                category=AuditCategory.COMPLIANCE,
                severity=AuditSeverity.INFO,
                description=f"Financial regulatory report generated: {report_id}",
                data={
                    'report_id': report_id,
                    'framework': regulatory_framework,
                    'overall_status': overall_status.value,
                    'compliance_score': compliance_scores.overall_score,
                    'date_range': f"{start_date.date()} to {end_date.date()}"
                }
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate financial regulatory report: {e}")
            raise
    
    def _collect_pci_dss_data(
        self,
        start_date: datetime,
        end_date: datetime,
        merchant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Collect PCI DSS specific compliance data"""
        try:
            # Query audit logs for PCI DSS relevant events
            pci_filters = [
                AuditLog.timestamp >= start_date,
                AuditLog.timestamp <= end_date,
                AuditLog.category.in_(['payment', 'financial', 'security'])
            ]
            
            if merchant_id:
                pci_filters.append(AuditLog.data['merchant_id'].astext == merchant_id)
            
            # Get PCI DSS relevant audit logs
            pci_logs = self.db_session.query(AuditLog).filter(*pci_filters).all()
            
            # Get financial transaction audits
            transaction_filters = [
                FinancialTransactionAudit.transaction_timestamp >= start_date,
                FinancialTransactionAudit.transaction_timestamp <= end_date
            ]
            
            if merchant_id:
                transaction_filters.append(FinancialTransactionAudit.customer_id == merchant_id)
            
            financial_transactions = self.db_session.query(FinancialTransactionAudit).filter(
                *transaction_filters
            ).all()
            
            # Get security event audits
            security_filters = [
                SecurityEventAudit.event_timestamp >= start_date,
                SecurityEventAudit.event_timestamp <= end_date
            ]
            
            security_events = self.db_session.query(SecurityEventAudit).filter(
                *security_filters
            ).all()
            
            # Analyze PCI DSS requirements
            requirements = self._analyze_pci_dss_requirements(pci_logs, financial_transactions, security_events)
            
            # Collect evidence
            evidence = self._collect_pci_dss_evidence(pci_logs, financial_transactions, security_events)
            
            # Perform risk assessment
            risk_assessment = self._perform_pci_dss_risk_assessment(
                pci_logs, financial_transactions, security_events
            )
            
            return {
                'requirements': requirements,
                'evidence': evidence,
                'risk_assessment': risk_assessment,
                'audit_logs': pci_logs,
                'financial_transactions': financial_transactions,
                'security_events': security_events
            }
            
        except Exception as e:
            logger.error(f"Failed to collect PCI DSS data: {e}")
            raise
    
    def _collect_gdpr_data(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Collect GDPR specific compliance data"""
        try:
            # Query audit logs for GDPR relevant events
            gdpr_filters = [
                AuditLog.timestamp >= start_date,
                AuditLog.timestamp <= end_date,
                AuditLog.category.in_(['user_activity', 'data_access', 'compliance'])
            ]
            
            if user_id:
                gdpr_filters.append(AuditLog.user_id == user_id)
            
            gdpr_logs = self.db_session.query(AuditLog).filter(*gdpr_filters).all()
            
            # Get user activity audits
            activity_filters = [
                UserActivityAudit.activity_timestamp >= start_date,
                UserActivityAudit.activity_timestamp <= end_date
            ]
            
            if user_id:
                activity_filters.append(UserActivityAudit.user_id == user_id)
            
            user_activities = self.db_session.query(UserActivityAudit).filter(
                *activity_filters
            ).all()
            
            # Analyze GDPR compliance
            data_subjects_count = len(set(log.user_id for log in gdpr_logs if log.user_id))
            consent_records_count = len([log for log in gdpr_logs if 'consent' in log.event_type.lower()])
            access_requests_count = len([log for log in gdpr_logs if 'data_access' in log.event_type.lower()])
            deletion_requests_count = len([log for log in gdpr_logs if 'data_deletion' in log.event_type.lower()])
            data_breaches_count = len([log for log in gdpr_logs if 'breach' in log.event_type.lower()])
            pia_count = len([log for log in gdpr_logs if 'privacy_impact' in log.event_type.lower()])
            
            return {
                'data_subjects_count': data_subjects_count,
                'consent_records_count': consent_records_count,
                'access_requests_count': access_requests_count,
                'deletion_requests_count': deletion_requests_count,
                'data_breaches_count': data_breaches_count,
                'pia_count': pia_count,
                'processing_activities': self._analyze_gdpr_processing_activities(gdpr_logs),
                'consent_management': self._analyze_gdpr_consent_management(gdpr_logs),
                'data_subject_rights': self._analyze_gdpr_data_subject_rights(gdpr_logs),
                'data_breaches': self._analyze_gdpr_data_breaches(gdpr_logs),
                'audit_logs': gdpr_logs,
                'user_activities': user_activities
            }
            
        except Exception as e:
            logger.error(f"Failed to collect GDPR data: {e}")
            raise
    
    def _collect_financial_regulatory_data(
        self,
        start_date: datetime,
        end_date: datetime,
        regulatory_framework: str,
        entity_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Collect financial regulatory compliance data"""
        try:
            # Query audit logs for financial regulatory events
            regulatory_filters = [
                AuditLog.timestamp >= start_date,
                AuditLog.timestamp <= end_date,
                AuditLog.category.in_(['financial', 'payment', 'compliance'])
            ]
            
            if entity_id:
                regulatory_filters.append(AuditLog.user_id == entity_id)
            
            regulatory_logs = self.db_session.query(AuditLog).filter(*regulatory_filters).all()
            
            # Get financial transaction audits
            transaction_filters = [
                FinancialTransactionAudit.transaction_timestamp >= start_date,
                FinancialTransactionAudit.transaction_timestamp <= end_date
            ]
            
            if entity_id:
                transaction_filters.append(FinancialTransactionAudit.customer_id == entity_id)
            
            financial_transactions = self.db_session.query(FinancialTransactionAudit).filter(
                *transaction_filters
            ).all()
            
            # Analyze financial regulatory compliance
            total_transactions = len(financial_transactions)
            total_volume = sum(float(tx.amount) for tx in financial_transactions if tx.amount)
            suspicious_activities_count = len([log for log in regulatory_logs if 'suspicious' in log.event_type.lower()])
            compliance_violations_count = len([log for log in regulatory_logs if 'violation' in log.event_type.lower()])
            risk_assessments_count = len([log for log in regulatory_logs if 'risk_assessment' in log.event_type.lower()])
            
            return {
                'total_transactions': total_transactions,
                'total_volume': total_volume,
                'suspicious_activities_count': suspicious_activities_count,
                'compliance_violations_count': compliance_violations_count,
                'risk_assessments_count': risk_assessments_count,
                'transaction_monitoring': self._analyze_transaction_monitoring(financial_transactions),
                'risk_assessments': self._analyze_risk_assessments(regulatory_logs),
                'compliance_violations': self._analyze_compliance_violations(regulatory_logs),
                'audit_logs': regulatory_logs,
                'financial_transactions': financial_transactions
            }
            
        except Exception as e:
            logger.error(f"Failed to collect financial regulatory data: {e}")
            raise
    
    def _store_compliance_report(self, report: Dict[str, Any]):
        """Store compliance report in database"""
        try:
            if not self.db_session:
                logger.warning("No database session available for storing compliance report")
                return
            
            # Create compliance report record
            compliance_report = ComplianceReport(
                report_id=report['report_id'],
                report_type=report['report_type'],
                report_name=f"{report['framework']} Compliance Report",
                framework=report['framework'],
                start_date=datetime.fromisoformat(report['start_date']),
                end_date=datetime.fromisoformat(report['end_date']),
                report_data=report,
                summary=report.get('summary', {}),
                findings=report.get('findings', []),
                recommendations=report.get('recommendations', []),
                overall_status=report['overall_status'],
                risk_level=report.get('risk_level', 'unknown'),
                compliance_score=report.get('compliance_score', 0),
                generated_by=report.get('generated_by', 'MINGUS Compliance System'),
                generation_timestamp=datetime.now(timezone.utc)
            )
            
            self.db_session.add(compliance_report)
            self.db_session.commit()
            
            logger.info(f"Stored compliance report: {report['report_id']}")
            
        except SQLAlchemyError as e:
            logger.error(f"Database error storing compliance report: {e}")
            self.db_session.rollback()
            raise
        except Exception as e:
            logger.error(f"Failed to store compliance report: {e}")
            raise
    
    # Additional helper methods would be implemented here for:
    # - _analyze_pci_dss_requirements()
    # - _calculate_pci_dss_compliance()
    # - _analyze_pci_dss_findings()
    # - _generate_pci_dss_recommendations()
    # - _determine_pci_dss_status()
    # - And similar methods for GDPR and financial regulatory frameworks
    
    def get_compliance_summary(
        self,
        framework: Optional[ComplianceFramework] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get overall compliance summary.
        
        Args:
            framework: Specific compliance framework
            start_date: Start date for filtering
            end_date: End date for filtering
        
        Returns:
            Compliance summary
        """
        try:
            # Build query filters
            filters = []
            if framework:
                filters.append(ComplianceReport.framework == framework.value)
            if start_date:
                filters.append(ComplianceReport.generation_timestamp >= start_date)
            if end_date:
                filters.append(ComplianceReport.generation_timestamp <= end_date)
            
            # Query compliance reports
            reports = self.db_session.query(ComplianceReport).filter(*filters).all()
            
            if not reports:
                return {"message": "No compliance reports found"}
            
            # Calculate summary statistics
            total_reports = len(reports)
            compliant_reports = len([r for r in reports if r.overall_status == 'compliant'])
            non_compliant_reports = len([r for r in reports if r.overall_status == 'non_compliant'])
            partially_compliant_reports = len([r for r in reports if r.overall_status == 'partially_compliant'])
            
            avg_compliance_score = sum(r.compliance_score or 0 for r in reports) / total_reports
            
            # Group by framework
            framework_summary = {}
            for report in reports:
                framework_name = report.framework
                if framework_name not in framework_summary:
                    framework_summary[framework_name] = {
                        'total_reports': 0,
                        'compliant_reports': 0,
                        'non_compliant_reports': 0,
                        'partially_compliant_reports': 0,
                        'avg_compliance_score': 0,
                        'total_score': 0
                    }
                
                framework_summary[framework_name]['total_reports'] += 1
                framework_summary[framework_name]['total_score'] += report.compliance_score or 0
                
                if report.overall_status == 'compliant':
                    framework_summary[framework_name]['compliant_reports'] += 1
                elif report.overall_status == 'non_compliant':
                    framework_summary[framework_name]['non_compliant_reports'] += 1
                elif report.overall_status == 'partially_compliant':
                    framework_summary[framework_name]['partially_compliant_reports'] += 1
            
            # Calculate average scores per framework
            for framework_name, data in framework_summary.items():
                if data['total_reports'] > 0:
                    data['avg_compliance_score'] = data['total_score'] / data['total_reports']
            
            return {
                'total_reports': total_reports,
                'overall_compliance_score': round(avg_compliance_score, 2),
                'compliant_reports': compliant_reports,
                'non_compliant_reports': non_compliant_reports,
                'partially_compliant_reports': partially_compliant_reports,
                'compliance_rate': round((compliant_reports / total_reports) * 100, 2),
                'framework_summary': framework_summary,
                'date_range': {
                    'start': start_date.isoformat() if start_date else None,
                    'end': end_date.isoformat() if end_date else None
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get compliance summary: {e}")
            return {"error": str(e)}


# Global compliance reporter instance
compliance_reporter = ComplianceReporter()

# Convenience functions
def generate_pci_dss_report(start_date: datetime, end_date: datetime, merchant_id: Optional[str] = None):
    """Generate PCI DSS compliance report"""
    return compliance_reporter.generate_pci_dss_report(start_date, end_date, merchant_id)

def generate_gdpr_report(start_date: datetime, end_date: datetime, user_id: Optional[str] = None):
    """Generate GDPR compliance report"""
    return compliance_reporter.generate_gdpr_report(start_date, end_date, user_id)

def generate_financial_regulatory_report(start_date: datetime, end_date: datetime, regulatory_framework: str, entity_id: Optional[str] = None):
    """Generate financial regulatory compliance report"""
    return compliance_reporter.generate_financial_regulatory_report(start_date, end_date, regulatory_framework, entity_id)

def get_compliance_summary(framework: Optional[ComplianceFramework] = None, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
    """Get overall compliance summary"""
    return compliance_reporter.get_compliance_summary(framework, start_date, end_date)
