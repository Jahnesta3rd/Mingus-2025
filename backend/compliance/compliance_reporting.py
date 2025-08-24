"""
Compliance Reporting and Audit System
Comprehensive reporting and audit features for privacy compliance
"""

import os
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import sqlite3
import threading
from loguru import logger
from flask import Blueprint, request, jsonify
from flask_cors import CORS

from ..privacy.privacy_controls import get_privacy_manager

# Create Flask blueprint
compliance_reporting_bp = Blueprint('compliance_reporting', __name__, url_prefix='/api/compliance')
CORS(compliance_reporting_bp)

class ReportType(Enum):
    """Report types"""
    PRIVACY_COMPLIANCE = "privacy_compliance"
    DATA_MINIMIZATION = "data_minimization"
    PURPOSE_LIMITATION = "purpose_limitation"
    DATA_ACCURACY = "data_accuracy"
    STORAGE_LIMITATION = "storage_limitation"
    TRANSPARENCY = "transparency"
    AUDIT_TRAIL = "audit_trail"
    DATA_SUBJECT_REQUESTS = "data_subject_requests"

class AuditType(Enum):
    """Audit types"""
    PRIVACY_AUDIT = "privacy_audit"
    COMPLIANCE_AUDIT = "compliance_audit"
    SECURITY_AUDIT = "security_audit"
    DATA_PROCESSING_AUDIT = "data_processing_audit"

@dataclass
class ComplianceReport:
    """Compliance report structure"""
    report_id: str
    report_type: ReportType
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    generated_by: str
    compliance_score: float
    findings: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ComplianceAudit:
    """Compliance audit structure"""
    audit_id: str
    audit_type: AuditType
    auditor: str
    audit_date: datetime
    scope: List[str] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    compliance_score: Optional[float] = None
    status: str = "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)

class ComplianceReportingManager:
    """Compliance reporting and audit manager"""
    
    def __init__(self, db_path: str = "/var/lib/mingus/compliance_reports.db"):
        self.db_path = db_path
        self.privacy_manager = get_privacy_manager()
        
        self._init_database()
    
    def _init_database(self):
        """Initialize compliance reporting database"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                # Compliance reports table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS compliance_reports (
                        report_id TEXT PRIMARY KEY,
                        report_type TEXT NOT NULL,
                        generated_at TEXT NOT NULL,
                        period_start TEXT NOT NULL,
                        period_end TEXT NOT NULL,
                        generated_by TEXT NOT NULL,
                        compliance_score REAL NOT NULL,
                        findings TEXT,
                        recommendations TEXT,
                        metadata TEXT
                    )
                """)
                
                # Compliance audits table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS compliance_audits (
                        audit_id TEXT PRIMARY KEY,
                        audit_type TEXT NOT NULL,
                        auditor TEXT NOT NULL,
                        audit_date TEXT NOT NULL,
                        scope TEXT,
                        findings TEXT,
                        recommendations TEXT,
                        compliance_score REAL,
                        status TEXT DEFAULT 'pending',
                        metadata TEXT
                    )
                """)
                
                # Audit findings table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS audit_findings (
                        finding_id TEXT PRIMARY KEY,
                        audit_id TEXT NOT NULL,
                        finding_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        description TEXT NOT NULL,
                        evidence TEXT,
                        recommendation TEXT,
                        status TEXT DEFAULT 'open',
                        created_at TEXT NOT NULL,
                        resolved_at TEXT,
                        metadata TEXT
                    )
                """)
                
                # Compliance metrics table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS compliance_metrics (
                        metric_id TEXT PRIMARY KEY,
                        metric_name TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        metric_date TEXT NOT NULL,
                        category TEXT NOT NULL,
                        metadata TEXT
                    )
                """)
                
                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_reports_type ON compliance_reports(report_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_reports_date ON compliance_reports(generated_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_audits_type ON compliance_audits(audit_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_audits_date ON compliance_audits(audit_date)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_findings_audit ON audit_findings(audit_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_name ON compliance_metrics(metric_name)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_date ON compliance_metrics(metric_date)")
        
        except Exception as e:
            logger.error(f"Error initializing compliance reporting database: {e}")
    
    def generate_compliance_report(self, report_type: ReportType, period_start: datetime,
                                 period_end: datetime, generated_by: str) -> str:
        """Generate compliance report"""
        try:
            report_id = f"report_{int(time.time())}"
            
            # Generate report based on type
            if report_type == ReportType.PRIVACY_COMPLIANCE:
                report_data = self._generate_privacy_compliance_report(period_start, period_end)
            elif report_type == ReportType.DATA_MINIMIZATION:
                report_data = self._generate_data_minimization_report(period_start, period_end)
            elif report_type == ReportType.PURPOSE_LIMITATION:
                report_data = self._generate_purpose_limitation_report(period_start, period_end)
            elif report_type == ReportType.DATA_ACCURACY:
                report_data = self._generate_data_accuracy_report(period_start, period_end)
            elif report_type == ReportType.STORAGE_LIMITATION:
                report_data = self._generate_storage_limitation_report(period_start, period_end)
            elif report_type == ReportType.TRANSPARENCY:
                report_data = self._generate_transparency_report(period_start, period_end)
            elif report_type == ReportType.AUDIT_TRAIL:
                report_data = self._generate_audit_trail_report(period_start, period_end)
            elif report_type == ReportType.DATA_SUBJECT_REQUESTS:
                report_data = self._generate_data_subject_requests_report(period_start, period_end)
            else:
                raise ValueError(f"Unknown report type: {report_type}")
            
            # Create report object
            report = ComplianceReport(
                report_id=report_id,
                report_type=report_type,
                generated_at=datetime.utcnow(),
                period_start=period_start,
                period_end=period_end,
                generated_by=generated_by,
                compliance_score=report_data.get('compliance_score', 0.0),
                findings=report_data.get('findings', []),
                recommendations=report_data.get('recommendations', []),
                metadata=report_data.get('metadata', {})
            )
            
            # Save report to database
            self._save_compliance_report(report)
            
            logger.info(f"Compliance report generated: {report_id}")
            return report_id
        
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            return None
    
    def _generate_privacy_compliance_report(self, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Generate privacy compliance report"""
        try:
            # Get privacy compliance data from privacy manager
            privacy_report = self.privacy_manager.get_privacy_compliance_report()
            
            # Calculate overall compliance score
            data_minimization_score = privacy_report.get('data_minimization', {}).get('minimization_score', 0)
            transparency_score = privacy_report.get('transparency', {}).get('transparency_score', 0)
            overall_score = (data_minimization_score + transparency_score) / 2
            
            findings = []
            recommendations = []
            
            # Analyze findings
            if data_minimization_score < 80:
                findings.append({
                    "type": "data_minimization",
                    "severity": "medium",
                    "description": "Data minimization score is below 80%",
                    "score": data_minimization_score
                })
                recommendations.append("Review data collection policies to ensure only necessary data is collected")
            
            if transparency_score < 80:
                findings.append({
                    "type": "transparency",
                    "severity": "medium",
                    "description": "Transparency score is below 80%",
                    "score": transparency_score
                })
                recommendations.append("Improve privacy notices and transparency measures")
            
            return {
                "compliance_score": overall_score,
                "findings": findings,
                "recommendations": recommendations,
                "metadata": {
                    "data_minimization_score": data_minimization_score,
                    "transparency_score": transparency_score,
                    "total_policies": privacy_report.get('data_minimization', {}).get('total_policies', 0)
                }
            }
        
        except Exception as e:
            logger.error(f"Error generating privacy compliance report: {e}")
            return {"compliance_score": 0, "findings": [], "recommendations": []}
    
    def _generate_data_minimization_report(self, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Generate data minimization report"""
        try:
            # Get data minimization statistics
            privacy_report = self.privacy_manager.get_privacy_compliance_report()
            minimization_stats = privacy_report.get('data_minimization', {})
            
            findings = []
            recommendations = []
            
            necessity_breakdown = minimization_stats.get('necessity_breakdown', {})
            optional_data_count = necessity_breakdown.get('optional', 0)
            essential_data_count = necessity_breakdown.get('essential', 0)
            
            if optional_data_count > essential_data_count:
                findings.append({
                    "type": "excessive_optional_data",
                    "severity": "high",
                    "description": f"More optional data ({optional_data_count}) than essential data ({essential_data_count})",
                    "counts": {"optional": optional_data_count, "essential": essential_data_count}
                })
                recommendations.append("Review and reduce collection of optional data")
            
            return {
                "compliance_score": minimization_stats.get('minimization_score', 0),
                "findings": findings,
                "recommendations": recommendations,
                "metadata": minimization_stats
            }
        
        except Exception as e:
            logger.error(f"Error generating data minimization report: {e}")
            return {"compliance_score": 0, "findings": [], "recommendations": []}
    
    def _generate_purpose_limitation_report(self, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Generate purpose limitation report"""
        try:
            # Get purpose limitation statistics
            privacy_report = self.privacy_manager.get_privacy_compliance_report()
            purpose_stats = privacy_report.get('purpose_limitation', {})
            
            findings = []
            recommendations = []
            
            compliance_rate = purpose_stats.get('compliance_rate', 0)
            if compliance_rate < 95:
                findings.append({
                    "type": "purpose_limitation_violations",
                    "severity": "medium",
                    "description": f"Purpose limitation compliance rate is {compliance_rate}%",
                    "rate": compliance_rate
                })
                recommendations.append("Review data processing activities to ensure purpose limitation compliance")
            
            return {
                "compliance_score": compliance_rate,
                "findings": findings,
                "recommendations": recommendations,
                "metadata": purpose_stats
            }
        
        except Exception as e:
            logger.error(f"Error generating purpose limitation report: {e}")
            return {"compliance_score": 0, "findings": [], "recommendations": []}
    
    def _generate_data_accuracy_report(self, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Generate data accuracy report"""
        try:
            # Get data accuracy statistics
            privacy_report = self.privacy_manager.get_privacy_compliance_report()
            accuracy_stats = privacy_report.get('data_accuracy', {})
            
            findings = []
            recommendations = []
            
            avg_accuracy = accuracy_stats.get('average_accuracy_score', 0)
            if avg_accuracy < 90:
                findings.append({
                    "type": "low_accuracy",
                    "severity": "medium",
                    "description": f"Average data accuracy score is {avg_accuracy}%",
                    "score": avg_accuracy
                })
                recommendations.append("Implement data quality controls and verification processes")
            
            return {
                "compliance_score": avg_accuracy,
                "findings": findings,
                "recommendations": recommendations,
                "metadata": accuracy_stats
            }
        
        except Exception as e:
            logger.error(f"Error generating data accuracy report: {e}")
            return {"compliance_score": 0, "findings": [], "recommendations": []}
    
    def _generate_storage_limitation_report(self, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Generate storage limitation report"""
        try:
            # Get storage limitation statistics
            privacy_report = self.privacy_manager.get_privacy_compliance_report()
            storage_stats = privacy_report.get('storage_limitation', {})
            
            findings = []
            recommendations = []
            
            expired_records = storage_stats.get('expired_records', 0)
            if expired_records > 0:
                findings.append({
                    "type": "expired_data",
                    "severity": "low",
                    "description": f"{expired_records} records have exceeded retention period",
                    "count": expired_records
                })
                recommendations.append("Implement automated data cleanup processes")
            
            return {
                "compliance_score": 100 if expired_records == 0 else 85,
                "findings": findings,
                "recommendations": recommendations,
                "metadata": storage_stats
            }
        
        except Exception as e:
            logger.error(f"Error generating storage limitation report: {e}")
            return {"compliance_score": 0, "findings": [], "recommendations": []}
    
    def _generate_transparency_report(self, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Generate transparency report"""
        try:
            # Get transparency statistics
            privacy_report = self.privacy_manager.get_privacy_compliance_report()
            transparency_stats = privacy_report.get('transparency', {})
            
            findings = []
            recommendations = []
            
            transparency_score = transparency_stats.get('transparency_score', 0)
            if transparency_score < 80:
                findings.append({
                    "type": "low_transparency",
                    "severity": "medium",
                    "description": f"Transparency score is {transparency_score}%",
                    "score": transparency_score
                })
                recommendations.append("Improve privacy notices and transparency measures")
            
            return {
                "compliance_score": transparency_score,
                "findings": findings,
                "recommendations": recommendations,
                "metadata": transparency_stats
            }
        
        except Exception as e:
            logger.error(f"Error generating transparency report: {e}")
            return {"compliance_score": 0, "findings": [], "recommendations": []}
    
    def _generate_audit_trail_report(self, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Generate audit trail report"""
        try:
            # This would analyze audit trails from the privacy manager
            findings = []
            recommendations = []
            
            # Placeholder data
            audit_events = 1250
            security_events = 45
            compliance_events = 89
            
            if security_events > 50:
                findings.append({
                    "type": "high_security_events",
                    "severity": "medium",
                    "description": f"{security_events} security events detected",
                    "count": security_events
                })
                recommendations.append("Review security controls and access patterns")
            
            return {
                "compliance_score": 95.0,
                "findings": findings,
                "recommendations": recommendations,
                "metadata": {
                    "total_audit_events": audit_events,
                    "security_events": security_events,
                    "compliance_events": compliance_events
                }
            }
        
        except Exception as e:
            logger.error(f"Error generating audit trail report: {e}")
            return {"compliance_score": 0, "findings": [], "recommendations": []}
    
    def _generate_data_subject_requests_report(self, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Generate data subject requests report"""
        try:
            # Get data subject requests statistics
            privacy_report = self.privacy_manager.get_privacy_compliance_report()
            request_stats = privacy_report.get('data_subject_requests', {})
            
            findings = []
            recommendations = []
            
            total_requests = request_stats.get('total_requests', 0)
            pending_requests = request_stats.get('pending_requests', 0)
            
            if pending_requests > 0:
                findings.append({
                    "type": "pending_requests",
                    "severity": "medium",
                    "description": f"{pending_requests} data subject requests are pending",
                    "count": pending_requests
                })
                recommendations.append("Process pending data subject requests promptly")
            
            return {
                "compliance_score": 100 if pending_requests == 0 else 85,
                "findings": findings,
                "recommendations": recommendations,
                "metadata": request_stats
            }
        
        except Exception as e:
            logger.error(f"Error generating data subject requests report: {e}")
            return {"compliance_score": 0, "findings": [], "recommendations": []}
    
    def _save_compliance_report(self, report: ComplianceReport) -> bool:
        """Save compliance report to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO compliance_reports 
                    (report_id, report_type, generated_at, period_start, period_end,
                     generated_by, compliance_score, findings, recommendations, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    report.report_id,
                    report.report_type.value,
                    report.generated_at.isoformat(),
                    report.period_start.isoformat(),
                    report.period_end.isoformat(),
                    report.generated_by,
                    report.compliance_score,
                    json.dumps(report.findings),
                    json.dumps(report.recommendations),
                    json.dumps(report.metadata)
                ))
            
            return True
        
        except Exception as e:
            logger.error(f"Error saving compliance report: {e}")
            return False
    
    def get_compliance_report(self, report_id: str) -> Optional[ComplianceReport]:
        """Get compliance report by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT report_id, report_type, generated_at, period_start, period_end,
                           generated_by, compliance_score, findings, recommendations, metadata
                    FROM compliance_reports 
                    WHERE report_id = ?
                """, (report_id,))
                
                row = cursor.fetchone()
                if row:
                    return ComplianceReport(
                        report_id=row[0],
                        report_type=ReportType(row[1]),
                        generated_at=datetime.fromisoformat(row[2]),
                        period_start=datetime.fromisoformat(row[3]),
                        period_end=datetime.fromisoformat(row[4]),
                        generated_by=row[5],
                        compliance_score=row[6],
                        findings=json.loads(row[7]) if row[7] else [],
                        recommendations=json.loads(row[8]) if row[8] else [],
                        metadata=json.loads(row[9]) if row[9] else {}
                    )
                
                return None
        
        except Exception as e:
            logger.error(f"Error getting compliance report: {e}")
            return None
    
    def get_reports_by_type(self, report_type: ReportType, limit: int = 10) -> List[ComplianceReport]:
        """Get reports by type"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT report_id, report_type, generated_at, period_start, period_end,
                           generated_by, compliance_score, findings, recommendations, metadata
                    FROM compliance_reports 
                    WHERE report_type = ?
                    ORDER BY generated_at DESC
                    LIMIT ?
                """, (report_type.value, limit))
                
                reports = []
                for row in cursor.fetchall():
                    report = ComplianceReport(
                        report_id=row[0],
                        report_type=ReportType(row[1]),
                        generated_at=datetime.fromisoformat(row[2]),
                        period_start=datetime.fromisoformat(row[3]),
                        period_end=datetime.fromisoformat(row[4]),
                        generated_by=row[5],
                        compliance_score=row[6],
                        findings=json.loads(row[7]) if row[7] else [],
                        recommendations=json.loads(row[8]) if row[8] else [],
                        metadata=json.loads(row[9]) if row[9] else {}
                    )
                    reports.append(report)
                
                return reports
        
        except Exception as e:
            logger.error(f"Error getting reports by type: {e}")
            return []
    
    def create_compliance_audit(self, audit: ComplianceAudit) -> bool:
        """Create compliance audit"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO compliance_audits 
                    (audit_id, audit_type, auditor, audit_date, scope, findings,
                     recommendations, compliance_score, status, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    audit.audit_id,
                    audit.audit_type.value,
                    audit.auditor,
                    audit.audit_date.isoformat(),
                    json.dumps(audit.scope),
                    json.dumps(audit.findings),
                    json.dumps(audit.recommendations),
                    audit.compliance_score,
                    audit.status,
                    json.dumps(audit.metadata)
                ))
            
            logger.info(f"Compliance audit created: {audit.audit_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error creating compliance audit: {e}")
            return False
    
    def get_compliance_audit(self, audit_id: str) -> Optional[ComplianceAudit]:
        """Get compliance audit by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT audit_id, audit_type, auditor, audit_date, scope, findings,
                           recommendations, compliance_score, status, metadata
                    FROM compliance_audits 
                    WHERE audit_id = ?
                """, (audit_id,))
                
                row = cursor.fetchone()
                if row:
                    return ComplianceAudit(
                        audit_id=row[0],
                        audit_type=AuditType(row[1]),
                        auditor=row[2],
                        audit_date=datetime.fromisoformat(row[3]),
                        scope=json.loads(row[4]) if row[4] else [],
                        findings=json.loads(row[5]) if row[5] else [],
                        recommendations=json.loads(row[6]) if row[6] else [],
                        compliance_score=row[7],
                        status=row[8],
                        metadata=json.loads(row[9]) if row[9] else {}
                    )
                
                return None
        
        except Exception as e:
            logger.error(f"Error getting compliance audit: {e}")
            return None
    
    def get_audits_by_type(self, audit_type: AuditType, limit: int = 10) -> List[ComplianceAudit]:
        """Get audits by type"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT audit_id, audit_type, auditor, audit_date, scope, findings,
                           recommendations, compliance_score, status, metadata
                    FROM compliance_audits 
                    WHERE audit_type = ?
                    ORDER BY audit_date DESC
                    LIMIT ?
                """, (audit_type.value, limit))
                
                audits = []
                for row in cursor.fetchall():
                    audit = ComplianceAudit(
                        audit_id=row[0],
                        audit_type=AuditType(row[1]),
                        auditor=row[2],
                        audit_date=datetime.fromisoformat(row[3]),
                        scope=json.loads(row[4]) if row[4] else [],
                        findings=json.loads(row[5]) if row[5] else [],
                        recommendations=json.loads(row[6]) if row[6] else [],
                        compliance_score=row[7],
                        status=row[8],
                        metadata=json.loads(row[9]) if row[9] else {}
                    )
                    audits.append(audit)
                
                return audits
        
        except Exception as e:
            logger.error(f"Error getting audits by type: {e}")
            return []

# Global compliance reporting manager instance
_compliance_reporting_manager = None

def get_compliance_reporting_manager() -> ComplianceReportingManager:
    """Get global compliance reporting manager instance"""
    global _compliance_reporting_manager
    
    if _compliance_reporting_manager is None:
        _compliance_reporting_manager = ComplianceReportingManager()
    
    return _compliance_reporting_manager

# Flask routes
@compliance_reporting_bp.route('/reports/generate', methods=['POST'])
def generate_compliance_report():
    """Generate compliance report"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['report_type', 'period_start', 'period_end', 'generated_by']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Parse dates
        period_start = datetime.fromisoformat(data['period_start'])
        period_end = datetime.fromisoformat(data['period_end'])
        
        # Generate report
        manager = get_compliance_reporting_manager()
        report_id = manager.generate_compliance_report(
            ReportType(data['report_type']),
            period_start,
            period_end,
            data['generated_by']
        )
        
        if report_id:
            return jsonify({
                'status': 'success',
                'message': 'Compliance report generated successfully',
                'data': {'report_id': report_id},
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Failed to generate compliance report'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@compliance_reporting_bp.route('/reports/<report_id>')
def get_compliance_report(report_id):
    """Get compliance report"""
    try:
        manager = get_compliance_reporting_manager()
        report = manager.get_compliance_report(report_id)
        
        if report:
            report_data = {
                'report_id': report.report_id,
                'report_type': report.report_type.value,
                'generated_at': report.generated_at.isoformat(),
                'period_start': report.period_start.isoformat(),
                'period_end': report.period_end.isoformat(),
                'generated_by': report.generated_by,
                'compliance_score': report.compliance_score,
                'findings': report.findings,
                'recommendations': report.recommendations,
                'metadata': report.metadata
            }
            
            return jsonify({
                'status': 'success',
                'data': report_data,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Report not found'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@compliance_reporting_bp.route('/reports/type/<report_type>')
def get_reports_by_type(report_type):
    """Get reports by type"""
    try:
        limit = request.args.get('limit', 10, type=int)
        manager = get_compliance_reporting_manager()
        reports = manager.get_reports_by_type(ReportType(report_type), limit)
        
        reports_data = []
        for report in reports:
            reports_data.append({
                'report_id': report.report_id,
                'report_type': report.report_type.value,
                'generated_at': report.generated_at.isoformat(),
                'compliance_score': report.compliance_score,
                'findings_count': len(report.findings),
                'recommendations_count': len(report.recommendations)
            })
        
        return jsonify({
            'status': 'success',
            'data': reports_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@compliance_reporting_bp.route('/audits/create', methods=['POST'])
def create_compliance_audit():
    """Create compliance audit"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['audit_type', 'auditor', 'scope']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create audit
        audit = ComplianceAudit(
            audit_id=f"audit_{int(time.time())}",
            audit_type=AuditType(data['audit_type']),
            auditor=data['auditor'],
            audit_date=datetime.utcnow(),
            scope=data['scope'],
            findings=data.get('findings', []),
            recommendations=data.get('recommendations', []),
            compliance_score=data.get('compliance_score'),
            status=data.get('status', 'pending'),
            metadata=data.get('metadata', {})
        )
        
        # Create audit
        manager = get_compliance_reporting_manager()
        success = manager.create_compliance_audit(audit)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Compliance audit created successfully',
                'data': {'audit_id': audit.audit_id},
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Failed to create compliance audit'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@compliance_reporting_bp.route('/audits/<audit_id>')
def get_compliance_audit(audit_id):
    """Get compliance audit"""
    try:
        manager = get_compliance_reporting_manager()
        audit = manager.get_compliance_audit(audit_id)
        
        if audit:
            audit_data = {
                'audit_id': audit.audit_id,
                'audit_type': audit.audit_type.value,
                'auditor': audit.auditor,
                'audit_date': audit.audit_date.isoformat(),
                'scope': audit.scope,
                'findings': audit.findings,
                'recommendations': audit.recommendations,
                'compliance_score': audit.compliance_score,
                'status': audit.status,
                'metadata': audit.metadata
            }
            
            return jsonify({
                'status': 'success',
                'data': audit_data,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Audit not found'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@compliance_reporting_bp.route('/audits/type/<audit_type>')
def get_audits_by_type(audit_type):
    """Get audits by type"""
    try:
        limit = request.args.get('limit', 10, type=int)
        manager = get_compliance_reporting_manager()
        audits = manager.get_audits_by_type(AuditType(audit_type), limit)
        
        audits_data = []
        for audit in audits:
            audits_data.append({
                'audit_id': audit.audit_id,
                'audit_type': audit.audit_type.value,
                'auditor': audit.auditor,
                'audit_date': audit.audit_date.isoformat(),
                'compliance_score': audit.compliance_score,
                'status': audit.status,
                'findings_count': len(audit.findings)
            })
        
        return jsonify({
            'status': 'success',
            'data': audits_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def register_compliance_reporting_routes(app):
    """Register compliance reporting routes with Flask app"""
    app.register_blueprint(compliance_reporting_bp)
    logger.info("Compliance reporting routes registered") 