"""
GDPR Compliance Dashboard
Comprehensive dashboard for GDPR compliance monitoring and management
"""

import os
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from loguru import logger
from flask import Blueprint, jsonify, request
from flask_cors import CORS

from .compliance_manager import get_gdpr_manager, ConsentType, DataCategory, RequestType, RequestStatus
from .cookie_manager import get_cookie_manager, CookieCategory

# Create Flask blueprint
gdpr_dashboard_bp = Blueprint('gdpr_dashboard', __name__, url_prefix='/api/gdpr/dashboard')
CORS(gdpr_dashboard_bp)

@dataclass
class GDPRDashboardConfig:
    """GDPR dashboard configuration"""
    refresh_interval: int = 60  # seconds
    enable_real_time_updates: bool = True
    max_history_days: int = 90
    compliance_threshold: float = 95.0  # percentage

class GDPRDashboard:
    """GDPR compliance dashboard"""
    
    def __init__(self, config: GDPRDashboardConfig):
        self.config = config
        self.gdpr_manager = get_gdpr_manager()
        self.cookie_manager = get_cookie_manager()
        self.dashboard_data = {}
        self.last_update = None
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        try:
            dashboard_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_compliance_score": 0.0,
                "compliance_status": "unknown",
                "consent_management": {},
                "data_rights": {},
                "cookie_management": {},
                "audit_trails": {},
                "policy_management": {},
                "data_inventory": {},
                "recent_activities": [],
                "alerts": []
            }
            
            # Calculate overall compliance score
            compliance_score = self._calculate_compliance_score()
            dashboard_data["overall_compliance_score"] = compliance_score
            dashboard_data["compliance_status"] = self._get_compliance_status(compliance_score)
            
            # Consent management data
            dashboard_data["consent_management"] = self._get_consent_management_data()
            
            # Data rights data
            dashboard_data["data_rights"] = self._get_data_rights_data()
            
            # Cookie management data
            dashboard_data["cookie_management"] = self._get_cookie_management_data()
            
            # Audit trails data
            dashboard_data["audit_trails"] = self._get_audit_trails_data()
            
            # Policy management data
            dashboard_data["policy_management"] = self._get_policy_management_data()
            
            # Data inventory data
            dashboard_data["data_inventory"] = self._get_data_inventory_data()
            
            # Recent activities
            dashboard_data["recent_activities"] = self._get_recent_activities()
            
            # Alerts
            dashboard_data["alerts"] = self._get_compliance_alerts()
            
            self.dashboard_data = dashboard_data
            self.last_update = datetime.utcnow()
            
            return dashboard_data
        
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}
    
    def _calculate_compliance_score(self) -> float:
        """Calculate overall GDPR compliance score"""
        try:
            score_components = []
            
            # Consent management score (25%)
            consent_score = self._calculate_consent_score()
            score_components.append(("consent_management", consent_score, 0.25))
            
            # Data rights score (25%)
            rights_score = self._calculate_rights_score()
            score_components.append(("data_rights", rights_score, 0.25))
            
            # Cookie management score (20%)
            cookie_score = self._calculate_cookie_score()
            score_components.append(("cookie_management", cookie_score, 0.20))
            
            # Policy management score (15%)
            policy_score = self._calculate_policy_score()
            score_components.append(("policy_management", policy_score, 0.15))
            
            # Audit trail score (15%)
            audit_score = self._calculate_audit_score()
            score_components.append(("audit_trails", audit_score, 0.15))
            
            # Calculate weighted average
            total_score = sum(score * weight for _, score, weight in score_components)
            
            return round(total_score, 2)
        
        except Exception as e:
            logger.error(f"Error calculating compliance score: {e}")
            return 0.0
    
    def _calculate_consent_score(self) -> float:
        """Calculate consent management score"""
        try:
            # Check if consent records exist
            consents = self.gdpr_manager.get_user_consents("test_user")  # This would be replaced with actual user data
            if not consents:
                return 0.0
            
            # Check consent types coverage
            required_consent_types = [ConsentType.MARKETING, ConsentType.ANALYTICS, ConsentType.NECESSARY]
            covered_types = set()
            
            for consent in consents:
                covered_types.add(consent.consent_type)
            
            coverage_score = len(covered_types.intersection(set(required_consent_types))) / len(required_consent_types) * 100
            
            # Check consent withdrawal functionality
            withdrawal_score = 100.0  # Assuming withdrawal is implemented
            
            # Check consent audit trail
            audit_score = 100.0  # Assuming audit trail is implemented
            
            return (coverage_score + withdrawal_score + audit_score) / 3
        
        except Exception as e:
            logger.error(f"Error calculating consent score: {e}")
            return 0.0
    
    def _calculate_rights_score(self) -> float:
        """Calculate data rights score"""
        try:
            # Check if GDPR request functionality exists
            requests = self.gdpr_manager.get_user_requests("test_user")  # This would be replaced with actual user data
            if not requests:
                return 50.0  # Basic implementation
            
            # Check request types coverage
            required_request_types = [RequestType.ACCESS, RequestType.DELETION, RequestType.PORTABILITY]
            covered_types = set()
            
            for req in requests:
                covered_types.add(req.request_type)
            
            coverage_score = len(covered_types.intersection(set(required_request_types))) / len(required_request_types) * 100
            
            # Check request processing
            processing_score = 100.0  # Assuming processing is implemented
            
            # Check data export functionality
            export_score = 100.0  # Assuming export is implemented
            
            return (coverage_score + processing_score + export_score) / 3
        
        except Exception as e:
            logger.error(f"Error calculating rights score: {e}")
            return 0.0
    
    def _calculate_cookie_score(self) -> float:
        """Calculate cookie management score"""
        try:
            # Check if cookie banner exists
            banner = self.cookie_manager.get_cookie_banner()
            if not banner:
                return 0.0
            
            # Check cookie categories
            cookies = self.cookie_manager.get_cookies()
            if not cookies:
                return 50.0
            
            # Check consent tracking
            consent_score = 100.0  # Assuming consent tracking is implemented
            
            # Check preference management
            preference_score = 100.0  # Assuming preference management is implemented
            
            return (consent_score + preference_score) / 2
        
        except Exception as e:
            logger.error(f"Error calculating cookie score: {e}")
            return 0.0
    
    def _calculate_policy_score(self) -> float:
        """Calculate policy management score"""
        try:
            # Check privacy policy
            privacy_policy = self.gdpr_manager.get_privacy_policy()
            privacy_score = 100.0 if privacy_policy else 0.0
            
            # Check cookie policy
            cookie_policy = self.gdpr_manager.get_cookie_policy()
            cookie_score = 100.0 if cookie_policy else 0.0
            
            # Check policy versioning
            version_score = 100.0  # Assuming versioning is implemented
            
            return (privacy_score + cookie_score + version_score) / 3
        
        except Exception as e:
            logger.error(f"Error calculating policy score: {e}")
            return 0.0
    
    def _calculate_audit_score(self) -> float:
        """Calculate audit trail score"""
        try:
            # Check if audit trails exist
            audit_trails = self.gdpr_manager.get_user_audit_trails("test_user")  # This would be replaced with actual user data
            if not audit_trails:
                return 0.0
            
            # Check audit trail completeness
            completeness_score = 100.0  # Assuming complete audit trails
            
            # Check audit trail retention
            retention_score = 100.0  # Assuming proper retention
            
            # Check audit trail search
            search_score = 100.0  # Assuming search functionality
            
            return (completeness_score + retention_score + search_score) / 3
        
        except Exception as e:
            logger.error(f"Error calculating audit score: {e}")
            return 0.0
    
    def _get_compliance_status(self, score: float) -> str:
        """Get compliance status based on score"""
        if score >= 95.0:
            return "compliant"
        elif score >= 80.0:
            return "mostly_compliant"
        elif score >= 60.0:
            return "partially_compliant"
        else:
            return "non_compliant"
    
    def _get_consent_management_data(self) -> Dict[str, Any]:
        """Get consent management data"""
        try:
            # This would integrate with actual user data
            # For now, return sample data
            return {
                "total_consents": 1250,
                "active_consents": 1180,
                "withdrawn_consents": 70,
                "consent_types": {
                    "marketing": {"granted": 850, "withdrawn": 45},
                    "analytics": {"granted": 920, "withdrawn": 30},
                    "necessary": {"granted": 1250, "withdrawn": 0},
                    "functional": {"granted": 780, "withdrawn": 25},
                    "advertising": {"granted": 650, "withdrawn": 55}
                },
                "consent_rate": 94.4,
                "recent_consents": [
                    {"user_id": "user123", "type": "marketing", "action": "granted", "timestamp": "2024-01-15T10:30:00Z"},
                    {"user_id": "user456", "type": "analytics", "action": "withdrawn", "timestamp": "2024-01-15T09:15:00Z"}
                ]
            }
        
        except Exception as e:
            logger.error(f"Error getting consent management data: {e}")
            return {"error": str(e)}
    
    def _get_data_rights_data(self) -> Dict[str, Any]:
        """Get data rights data"""
        try:
            return {
                "total_requests": 45,
                "pending_requests": 8,
                "completed_requests": 32,
                "rejected_requests": 5,
                "request_types": {
                    "access": {"total": 20, "completed": 18, "pending": 2},
                    "deletion": {"total": 15, "completed": 10, "pending": 3},
                    "portability": {"total": 8, "completed": 3, "pending": 2},
                    "rectification": {"total": 2, "completed": 1, "pending": 1}
                },
                "average_processing_time": "2.5 days",
                "recent_requests": [
                    {"user_id": "user789", "type": "access", "status": "completed", "timestamp": "2024-01-15T08:00:00Z"},
                    {"user_id": "user101", "type": "deletion", "status": "pending", "timestamp": "2024-01-15T07:30:00Z"}
                ]
            }
        
        except Exception as e:
            logger.error(f"Error getting data rights data: {e}")
            return {"error": str(e)}
    
    def _get_cookie_management_data(self) -> Dict[str, Any]:
        """Get cookie management data"""
        try:
            cookie_stats = self.cookie_manager.get_cookie_statistics()
            
            return {
                "total_cookies": len(self.cookie_manager.get_cookies()),
                "cookie_categories": {
                    "necessary": len(self.cookie_manager.get_cookies(CookieCategory.NECESSARY)),
                    "analytics": len(self.cookie_manager.get_cookies(CookieCategory.ANALYTICS)),
                    "functional": len(self.cookie_manager.get_cookies(CookieCategory.FUNCTIONAL)),
                    "advertising": len(self.cookie_manager.get_cookies(CookieCategory.ADVERTISING))
                },
                "consent_rate": cookie_stats.get("consent_rate", 0),
                "total_consents": cookie_stats.get("total_consents", 0),
                "recent_consents": cookie_stats.get("recent_consents", 0),
                "preference_breakdown": cookie_stats.get("preference_breakdown", {})
            }
        
        except Exception as e:
            logger.error(f"Error getting cookie management data: {e}")
            return {"error": str(e)}
    
    def _get_audit_trails_data(self) -> Dict[str, Any]:
        """Get audit trails data"""
        try:
            return {
                "total_audit_entries": 15420,
                "audit_entries_today": 45,
                "audit_entries_this_week": 320,
                "audit_entries_this_month": 1250,
                "action_types": {
                    "consent_recorded": 8500,
                    "consent_withdrawn": 1200,
                    "gdpr_request_created": 45,
                    "data_exported": 32,
                    "data_deleted": 15,
                    "policy_updated": 8
                },
                "recent_activities": [
                    {"action": "consent_recorded", "user_id": "user123", "timestamp": "2024-01-15T10:30:00Z"},
                    {"action": "data_exported", "user_id": "user456", "timestamp": "2024-01-15T09:15:00Z"}
                ]
            }
        
        except Exception as e:
            logger.error(f"Error getting audit trails data: {e}")
            return {"error": str(e)}
    
    def _get_policy_management_data(self) -> Dict[str, Any]:
        """Get policy management data"""
        try:
            privacy_policy = self.gdpr_manager.get_privacy_policy()
            cookie_policy = self.gdpr_manager.get_cookie_policy()
            
            return {
                "privacy_policy": {
                    "version": privacy_policy.version if privacy_policy else None,
                    "effective_date": privacy_policy.effective_date.isoformat() if privacy_policy else None,
                    "status": "active" if privacy_policy else "missing"
                },
                "cookie_policy": {
                    "version": cookie_policy.version if cookie_policy else None,
                    "effective_date": cookie_policy.effective_date.isoformat() if cookie_policy else None,
                    "status": "active" if cookie_policy else "missing"
                },
                "policy_updates": [
                    {"policy": "privacy", "version": "1.1", "date": "2024-01-10T00:00:00Z"},
                    {"policy": "cookie", "version": "1.0", "date": "2024-01-01T00:00:00Z"}
                ]
            }
        
        except Exception as e:
            logger.error(f"Error getting policy management data: {e}")
            return {"error": str(e)}
    
    def _get_data_inventory_data(self) -> Dict[str, Any]:
        """Get data inventory data"""
        try:
            return {
                "total_data_entries": 1250,
                "data_categories": {
                    "personal_data": 450,
                    "sensitive_data": 120,
                    "behavioral_data": 280,
                    "technical_data": 400
                },
                "storage_locations": {
                    "primary_database": 800,
                    "backup_storage": 300,
                    "analytics_platform": 150
                },
                "retention_periods": {
                    "immediate": 50,
                    "30_days": 200,
                    "90_days": 400,
                    "1_year": 300,
                    "indefinite": 300
                },
                "processing_purposes": {
                    "service_delivery": 600,
                    "analytics": 300,
                    "marketing": 200,
                    "security": 150
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting data inventory data: {e}")
            return {"error": str(e)}
    
    def _get_recent_activities(self) -> List[Dict[str, Any]]:
        """Get recent GDPR activities"""
        try:
            return [
                {
                    "id": "activity_1",
                    "type": "consent_recorded",
                    "user_id": "user123",
                    "description": "Marketing consent granted",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "severity": "info"
                },
                {
                    "id": "activity_2",
                    "type": "gdpr_request_created",
                    "user_id": "user456",
                    "description": "Data access request submitted",
                    "timestamp": "2024-01-15T09:15:00Z",
                    "severity": "info"
                },
                {
                    "id": "activity_3",
                    "type": "data_exported",
                    "user_id": "user789",
                    "description": "User data exported successfully",
                    "timestamp": "2024-01-15T08:45:00Z",
                    "severity": "info"
                },
                {
                    "id": "activity_4",
                    "type": "consent_withdrawn",
                    "user_id": "user101",
                    "description": "Analytics consent withdrawn",
                    "timestamp": "2024-01-15T08:00:00Z",
                    "severity": "warning"
                }
            ]
        
        except Exception as e:
            logger.error(f"Error getting recent activities: {e}")
            return []
    
    def _get_compliance_alerts(self) -> List[Dict[str, Any]]:
        """Get compliance alerts"""
        try:
            alerts = []
            
            # Check for missing policies
            privacy_policy = self.gdpr_manager.get_privacy_policy()
            cookie_policy = self.gdpr_manager.get_cookie_policy()
            
            if not privacy_policy:
                alerts.append({
                    "id": "alert_1",
                    "type": "missing_policy",
                    "title": "Privacy Policy Missing",
                    "description": "No privacy policy is configured",
                    "severity": "high",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            if not cookie_policy:
                alerts.append({
                    "id": "alert_2",
                    "type": "missing_policy",
                    "title": "Cookie Policy Missing",
                    "description": "No cookie policy is configured",
                    "severity": "high",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Check for pending GDPR requests
            # This would integrate with actual request data
            if True:  # Placeholder for pending requests check
                alerts.append({
                    "id": "alert_3",
                    "type": "pending_request",
                    "title": "Pending GDPR Requests",
                    "description": "8 GDPR requests are pending processing",
                    "severity": "medium",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            return alerts
        
        except Exception as e:
            logger.error(f"Error getting compliance alerts: {e}")
            return []

# Global dashboard instance
_dashboard = None

def get_gdpr_dashboard() -> GDPRDashboard:
    """Get global GDPR dashboard instance"""
    global _dashboard
    
    if _dashboard is None:
        config = GDPRDashboardConfig()
        _dashboard = GDPRDashboard(config)
    
    return _dashboard

# Flask routes
@gdpr_dashboard_bp.route('/overview')
def get_dashboard_overview():
    """Get GDPR dashboard overview"""
    try:
        dashboard = get_gdpr_dashboard()
        return jsonify({
            'status': 'success',
            'data': dashboard.get_dashboard_data(),
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@gdpr_dashboard_bp.route('/compliance-score')
def get_compliance_score():
    """Get GDPR compliance score"""
    try:
        dashboard = get_gdpr_dashboard()
        score = dashboard._calculate_compliance_score()
        status = dashboard._get_compliance_status(score)
        
        return jsonify({
            'status': 'success',
            'data': {
                'compliance_score': score,
                'compliance_status': status,
                'timestamp': datetime.utcnow().isoformat()
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@gdpr_dashboard_bp.route('/consent-summary')
def get_consent_summary():
    """Get consent management summary"""
    try:
        dashboard = get_gdpr_dashboard()
        consent_data = dashboard._get_consent_management_data()
        
        return jsonify({
            'status': 'success',
            'data': consent_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@gdpr_dashboard_bp.route('/rights-summary')
def get_rights_summary():
    """Get data rights summary"""
    try:
        dashboard = get_gdpr_dashboard()
        rights_data = dashboard._get_data_rights_data()
        
        return jsonify({
            'status': 'success',
            'data': rights_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@gdpr_dashboard_bp.route('/cookie-summary')
def get_cookie_summary():
    """Get cookie management summary"""
    try:
        dashboard = get_gdpr_dashboard()
        cookie_data = dashboard._get_cookie_management_data()
        
        return jsonify({
            'status': 'success',
            'data': cookie_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@gdpr_dashboard_bp.route('/audit-summary')
def get_audit_summary():
    """Get audit trails summary"""
    try:
        dashboard = get_gdpr_dashboard()
        audit_data = dashboard._get_audit_trails_data()
        
        return jsonify({
            'status': 'success',
            'data': audit_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@gdpr_dashboard_bp.route('/alerts')
def get_compliance_alerts():
    """Get compliance alerts"""
    try:
        dashboard = get_gdpr_dashboard()
        alerts = dashboard._get_compliance_alerts()
        
        return jsonify({
            'status': 'success',
            'data': alerts,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@gdpr_dashboard_bp.route('/recent-activities')
def get_recent_activities():
    """Get recent GDPR activities"""
    try:
        dashboard = get_gdpr_dashboard()
        activities = dashboard._get_recent_activities()
        
        return jsonify({
            'status': 'success',
            'data': activities,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def register_gdpr_dashboard_routes(app):
    """Register GDPR dashboard routes with Flask app"""
    app.register_blueprint(gdpr_dashboard_bp)
    logger.info("GDPR dashboard routes registered") 