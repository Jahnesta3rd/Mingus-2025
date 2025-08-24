"""
User Privacy Dashboard
Comprehensive dashboard for users to manage their privacy settings, view their data, and exercise their rights
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
from flask import Blueprint, request, jsonify, current_app
from flask_cors import CORS

from .privacy_controls import get_privacy_manager, DataPurpose, DataAccuracyLevel

# Create Flask blueprint
user_privacy_bp = Blueprint('user_privacy', __name__, url_prefix='/api/user/privacy')
CORS(user_privacy_bp)

class PrivacyDashboardSection(Enum):
    """Privacy dashboard sections"""
    OVERVIEW = "overview"
    DATA_INVENTORY = "data_inventory"
    CONSENT_MANAGEMENT = "consent_management"
    DATA_RIGHTS = "data_rights"
    PRIVACY_SETTINGS = "privacy_settings"
    AUDIT_TRAIL = "audit_trail"
    NOTIFICATIONS = "notifications"

@dataclass
class UserPrivacyProfile:
    """User privacy profile structure"""
    user_id: str
    privacy_score: float
    data_sharing_preferences: Dict[str, bool]
    notification_preferences: Dict[str, bool]
    last_privacy_review: datetime
    privacy_settings_version: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UserDataInventory:
    """User data inventory structure"""
    user_id: str
    data_category: str
    data_type: str
    collection_date: datetime
    purpose: str
    retention_period: str
    accuracy_score: Optional[float] = None
    last_verified: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UserConsentRecord:
    """User consent record structure"""
    user_id: str
    consent_type: str
    granted: bool
    granted_at: datetime
    withdrawn_at: Optional[datetime] = None
    purpose: str
    third_parties: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class UserPrivacyDashboard:
    """User privacy dashboard manager"""
    
    def __init__(self, db_path: str = "/var/lib/mingus/user_privacy.db"):
        self.db_path = db_path
        self.privacy_manager = get_privacy_manager()
        
        self._init_database()
        self._load_default_profiles()
    
    def _init_database(self):
        """Initialize user privacy dashboard database"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                # User privacy profiles table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_privacy_profiles (
                        user_id TEXT PRIMARY KEY,
                        privacy_score REAL DEFAULT 0.0,
                        data_sharing_preferences TEXT,
                        notification_preferences TEXT,
                        last_privacy_review TEXT,
                        privacy_settings_version TEXT DEFAULT '1.0',
                        metadata TEXT
                    )
                """)
                
                # User data inventory table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_data_inventory (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        data_category TEXT NOT NULL,
                        data_type TEXT NOT NULL,
                        collection_date TEXT NOT NULL,
                        purpose TEXT NOT NULL,
                        retention_period TEXT NOT NULL,
                        accuracy_score REAL,
                        last_verified TEXT,
                        metadata TEXT
                    )
                """)
                
                # User consent records table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_consent_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        consent_type TEXT NOT NULL,
                        granted INTEGER NOT NULL,
                        granted_at TEXT NOT NULL,
                        withdrawn_at TEXT,
                        purpose TEXT NOT NULL,
                        third_parties TEXT,
                        metadata TEXT
                    )
                """)
                
                # User privacy settings table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_privacy_settings (
                        user_id TEXT PRIMARY KEY,
                        profile_visibility TEXT DEFAULT 'private',
                        data_sharing_level TEXT DEFAULT 'minimal',
                        marketing_communications INTEGER DEFAULT 0,
                        analytics_tracking INTEGER DEFAULT 0,
                        third_party_sharing INTEGER DEFAULT 0,
                        automated_decision_making INTEGER DEFAULT 0,
                        data_retention_preference TEXT DEFAULT 'standard',
                        notification_frequency TEXT DEFAULT 'important_only',
                        last_updated TEXT,
                        metadata TEXT
                    )
                """)
                
                # User privacy notifications table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_privacy_notifications (
                        notification_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        notification_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        message TEXT NOT NULL,
                        priority TEXT DEFAULT 'medium',
                        read INTEGER DEFAULT 0,
                        created_at TEXT NOT NULL,
                        action_required INTEGER DEFAULT 0,
                        action_url TEXT,
                        metadata TEXT
                    )
                """)
                
                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_profile_user ON user_privacy_profiles(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_inventory_user ON user_data_inventory(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_inventory_category ON user_data_inventory(data_category)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_consent_user ON user_consent_records(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_consent_type ON user_consent_records(consent_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_settings_user ON user_privacy_settings(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user ON user_privacy_notifications(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_notifications_read ON user_privacy_notifications(read)")
        
        except Exception as e:
            logger.error(f"Error initializing user privacy database: {e}")
    
    def _load_default_profiles(self):
        """Load default privacy profiles"""
        try:
            # Default privacy settings
            default_settings = {
                "profile_visibility": "private",
                "data_sharing_level": "minimal",
                "marketing_communications": 0,
                "analytics_tracking": 0,
                "third_party_sharing": 0,
                "automated_decision_making": 0,
                "data_retention_preference": "standard",
                "notification_frequency": "important_only"
            }
            
            logger.info("Default privacy profiles loaded")
        
        except Exception as e:
            logger.error(f"Error loading default profiles: {e}")
    
    def get_user_dashboard_overview(self, user_id: str) -> Dict[str, Any]:
        """Get user privacy dashboard overview"""
        try:
            overview = {
                "user_id": user_id,
                "privacy_score": self._calculate_privacy_score(user_id),
                "data_summary": self._get_data_summary(user_id),
                "consent_summary": self._get_consent_summary(user_id),
                "recent_activity": self._get_recent_activity(user_id),
                "privacy_alerts": self._get_privacy_alerts(user_id),
                "recommendations": self._get_privacy_recommendations(user_id),
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return overview
        
        except Exception as e:
            logger.error(f"Error getting user dashboard overview: {e}")
            return {"error": str(e)}
    
    def _calculate_privacy_score(self, user_id: str) -> float:
        """Calculate user privacy score"""
        try:
            score = 100.0
            
            # Check data sharing preferences
            settings = self.get_user_privacy_settings(user_id)
            if settings:
                if settings.get("data_sharing_level") == "minimal":
                    score += 10
                elif settings.get("data_sharing_level") == "standard":
                    score += 5
                
                if not settings.get("marketing_communications"):
                    score += 10
                
                if not settings.get("analytics_tracking"):
                    score += 10
                
                if not settings.get("third_party_sharing"):
                    score += 15
            
            # Check consent management
            consents = self.get_user_consents(user_id)
            active_consents = [c for c in consents if c.granted and not c.withdrawn_at]
            if len(active_consents) <= 2:  # Minimal consents
                score += 10
            
            # Check data accuracy
            inventory = self.get_user_data_inventory(user_id)
            high_accuracy_count = sum(1 for item in inventory if item.accuracy_score and item.accuracy_score >= 95)
            if inventory:
                accuracy_ratio = high_accuracy_count / len(inventory)
                score += accuracy_ratio * 15
            
            return min(score, 100.0)
        
        except Exception as e:
            logger.error(f"Error calculating privacy score: {e}")
            return 75.0  # Default score
    
    def _get_data_summary(self, user_id: str) -> Dict[str, Any]:
        """Get user data summary"""
        try:
            inventory = self.get_user_data_inventory(user_id)
            
            summary = {
                "total_data_types": len(inventory),
                "data_categories": {},
                "retention_summary": {},
                "accuracy_summary": {
                    "high_accuracy": 0,
                    "medium_accuracy": 0,
                    "low_accuracy": 0,
                    "unverified": 0
                }
            }
            
            for item in inventory:
                # Count by category
                category = item.data_category
                summary["data_categories"][category] = summary["data_categories"].get(category, 0) + 1
                
                # Count by retention period
                retention = item.retention_period
                summary["retention_summary"][retention] = summary["retention_summary"].get(retention, 0) + 1
                
                # Count by accuracy
                if item.accuracy_score:
                    if item.accuracy_score >= 95:
                        summary["accuracy_summary"]["high_accuracy"] += 1
                    elif item.accuracy_score >= 80:
                        summary["accuracy_summary"]["medium_accuracy"] += 1
                    else:
                        summary["accuracy_summary"]["low_accuracy"] += 1
                else:
                    summary["accuracy_summary"]["unverified"] += 1
            
            return summary
        
        except Exception as e:
            logger.error(f"Error getting data summary: {e}")
            return {}
    
    def _get_consent_summary(self, user_id: str) -> Dict[str, Any]:
        """Get user consent summary"""
        try:
            consents = self.get_user_consents(user_id)
            
            summary = {
                "total_consents": len(consents),
                "active_consents": len([c for c in consents if c.granted and not c.withdrawn_at]),
                "withdrawn_consents": len([c for c in consents if c.withdrawn_at]),
                "consent_types": {},
                "recent_activity": []
            }
            
            for consent in consents:
                consent_type = consent.consent_type
                summary["consent_types"][consent_type] = summary["consent_types"].get(consent_type, 0) + 1
            
            # Get recent consent activity
            recent_consents = sorted(consents, key=lambda x: x.granted_at, reverse=True)[:5]
            for consent in recent_consents:
                summary["recent_activity"].append({
                    "type": consent.consent_type,
                    "action": "withdrawn" if consent.withdrawn_at else "granted",
                    "date": consent.withdrawn_at.isoformat() if consent.withdrawn_at else consent.granted_at.isoformat()
                })
            
            return summary
        
        except Exception as e:
            logger.error(f"Error getting consent summary: {e}")
            return {}
    
    def _get_recent_activity(self, user_id: str) -> List[Dict[str, Any]]:
        """Get recent privacy activity"""
        try:
            # This would integrate with the main privacy controls system
            recent_activity = [
                {
                    "activity_type": "consent_granted",
                    "description": "Granted analytics consent",
                    "timestamp": (datetime.utcnow() - timedelta(days=2)).isoformat(),
                    "impact": "low"
                },
                {
                    "activity_type": "data_export",
                    "description": "Exported personal data",
                    "timestamp": (datetime.utcnow() - timedelta(days=5)).isoformat(),
                    "impact": "medium"
                },
                {
                    "activity_type": "privacy_settings_updated",
                    "description": "Updated privacy preferences",
                    "timestamp": (datetime.utcnow() - timedelta(days=7)).isoformat(),
                    "impact": "low"
                }
            ]
            
            return recent_activity
        
        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return []
    
    def _get_privacy_alerts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get privacy alerts for user"""
        try:
            alerts = []
            
            # Check for data accuracy issues
            inventory = self.get_user_data_inventory(user_id)
            low_accuracy_data = [item for item in inventory if item.accuracy_score and item.accuracy_score < 80]
            
            if low_accuracy_data:
                alerts.append({
                    "alert_type": "data_accuracy",
                    "severity": "medium",
                    "title": "Data Accuracy Issues",
                    "message": f"You have {len(low_accuracy_data)} data items with accuracy below 80%",
                    "action_required": True,
                    "action_url": f"/api/user/privacy/data-accuracy/{user_id}"
                })
            
            # Check for expired data
            expired_data = [item for item in inventory if item.collection_date < datetime.utcnow() - timedelta(days=365)]
            
            if expired_data:
                alerts.append({
                    "alert_type": "expired_data",
                    "severity": "low",
                    "title": "Expired Data",
                    "message": f"You have {len(expired_data)} data items that may be expired",
                    "action_required": False,
                    "action_url": f"/api/user/privacy/data-inventory/{user_id}"
                })
            
            # Check for missing consents
            consents = self.get_user_consents(user_id)
            essential_consents = ["necessary", "functional"]
            missing_consents = [consent_type for consent_type in essential_consents 
                              if not any(c.consent_type == consent_type and c.granted and not c.withdrawn_at 
                                       for c in consents)]
            
            if missing_consents:
                alerts.append({
                    "alert_type": "missing_consent",
                    "severity": "high",
                    "title": "Missing Essential Consents",
                    "message": f"You are missing consents for: {', '.join(missing_consents)}",
                    "action_required": True,
                    "action_url": f"/api/user/privacy/consent-management/{user_id}"
                })
            
            return alerts
        
        except Exception as e:
            logger.error(f"Error getting privacy alerts: {e}")
            return []
    
    def _get_privacy_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get privacy recommendations for user"""
        try:
            recommendations = []
            
            # Check privacy score and provide recommendations
            privacy_score = self._calculate_privacy_score(user_id)
            
            if privacy_score < 80:
                recommendations.append({
                    "type": "privacy_score",
                    "priority": "high",
                    "title": "Improve Privacy Score",
                    "description": "Your privacy score is below 80. Consider reviewing your privacy settings.",
                    "action": "Review privacy settings",
                    "action_url": f"/api/user/privacy/settings/{user_id}"
                })
            
            # Check data sharing preferences
            settings = self.get_user_privacy_settings(user_id)
            if settings and settings.get("data_sharing_level") != "minimal":
                recommendations.append({
                    "type": "data_sharing",
                    "priority": "medium",
                    "title": "Reduce Data Sharing",
                    "description": "Consider setting data sharing to minimal for better privacy.",
                    "action": "Update data sharing preferences",
                    "action_url": f"/api/user/privacy/settings/{user_id}"
                })
            
            # Check for marketing communications
            if settings and settings.get("marketing_communications"):
                recommendations.append({
                    "type": "marketing_opt_out",
                    "priority": "low",
                    "title": "Opt Out of Marketing",
                    "description": "You're currently receiving marketing communications. Consider opting out.",
                    "action": "Update communication preferences",
                    "action_url": f"/api/user/privacy/settings/{user_id}"
                })
            
            return recommendations
        
        except Exception as e:
            logger.error(f"Error getting privacy recommendations: {e}")
            return []
    
    def get_user_data_inventory(self, user_id: str) -> List[UserDataInventory]:
        """Get user's data inventory"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT user_id, data_category, data_type, collection_date, purpose,
                           retention_period, accuracy_score, last_verified, metadata
                    FROM user_data_inventory 
                    WHERE user_id = ?
                    ORDER BY collection_date DESC
                """, (user_id,))
                
                inventory = []
                for row in cursor.fetchall():
                    item = UserDataInventory(
                        user_id=row[0],
                        data_category=row[1],
                        data_type=row[2],
                        collection_date=datetime.fromisoformat(row[3]),
                        purpose=row[4],
                        retention_period=row[5],
                        accuracy_score=row[6],
                        last_verified=datetime.fromisoformat(row[7]) if row[7] else None,
                        metadata=json.loads(row[8]) if row[8] else {}
                    )
                    inventory.append(item)
                
                return inventory
        
        except Exception as e:
            logger.error(f"Error getting user data inventory: {e}")
            return []
    
    def add_user_data_inventory_item(self, item: UserDataInventory) -> bool:
        """Add item to user data inventory"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO user_data_inventory 
                    (user_id, data_category, data_type, collection_date, purpose,
                     retention_period, accuracy_score, last_verified, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.user_id,
                    item.data_category,
                    item.data_type,
                    item.collection_date.isoformat(),
                    item.purpose,
                    item.retention_period,
                    item.accuracy_score,
                    item.last_verified.isoformat() if item.last_verified else None,
                    json.dumps(item.metadata)
                ))
            
            logger.info(f"Data inventory item added for user {item.user_id}: {item.data_type}")
            return True
        
        except Exception as e:
            logger.error(f"Error adding data inventory item: {e}")
            return False
    
    def get_user_consents(self, user_id: str) -> List[UserConsentRecord]:
        """Get user's consent records"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT user_id, consent_type, granted, granted_at, withdrawn_at,
                           purpose, third_parties, metadata
                    FROM user_consent_records 
                    WHERE user_id = ?
                    ORDER BY granted_at DESC
                """, (user_id,))
                
                consents = []
                for row in cursor.fetchall():
                    consent = UserConsentRecord(
                        user_id=row[0],
                        consent_type=row[1],
                        granted=bool(row[2]),
                        granted_at=datetime.fromisoformat(row[3]),
                        withdrawn_at=datetime.fromisoformat(row[4]) if row[4] else None,
                        purpose=row[5],
                        third_parties=json.loads(row[6]) if row[6] else [],
                        metadata=json.loads(row[7]) if row[7] else {}
                    )
                    consents.append(consent)
                
                return consents
        
        except Exception as e:
            logger.error(f"Error getting user consents: {e}")
            return []
    
    def add_user_consent(self, consent: UserConsentRecord) -> bool:
        """Add user consent record"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO user_consent_records 
                    (user_id, consent_type, granted, granted_at, withdrawn_at,
                     purpose, third_parties, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    consent.user_id,
                    consent.consent_type,
                    1 if consent.granted else 0,
                    consent.granted_at.isoformat(),
                    consent.withdrawn_at.isoformat() if consent.withdrawn_at else None,
                    consent.purpose,
                    json.dumps(consent.third_parties),
                    json.dumps(consent.metadata)
                ))
            
            logger.info(f"Consent record added for user {consent.user_id}: {consent.consent_type}")
            return True
        
        except Exception as e:
            logger.error(f"Error adding user consent: {e}")
            return False
    
    def get_user_privacy_settings(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user privacy settings"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT profile_visibility, data_sharing_level, marketing_communications,
                           analytics_tracking, third_party_sharing, automated_decision_making,
                           data_retention_preference, notification_frequency, last_updated, metadata
                    FROM user_privacy_settings 
                    WHERE user_id = ?
                """, (user_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        "profile_visibility": row[0],
                        "data_sharing_level": row[1],
                        "marketing_communications": bool(row[2]),
                        "analytics_tracking": bool(row[3]),
                        "third_party_sharing": bool(row[4]),
                        "automated_decision_making": bool(row[5]),
                        "data_retention_preference": row[6],
                        "notification_frequency": row[7],
                        "last_updated": row[8],
                        "metadata": json.loads(row[9]) if row[9] else {}
                    }
                
                return None
        
        except Exception as e:
            logger.error(f"Error getting user privacy settings: {e}")
            return None
    
    def update_user_privacy_settings(self, user_id: str, settings: Dict[str, Any]) -> bool:
        """Update user privacy settings"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO user_privacy_settings 
                    (user_id, profile_visibility, data_sharing_level, marketing_communications,
                     analytics_tracking, third_party_sharing, automated_decision_making,
                     data_retention_preference, notification_frequency, last_updated, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    settings.get("profile_visibility", "private"),
                    settings.get("data_sharing_level", "minimal"),
                    1 if settings.get("marketing_communications", False) else 0,
                    1 if settings.get("analytics_tracking", False) else 0,
                    1 if settings.get("third_party_sharing", False) else 0,
                    1 if settings.get("automated_decision_making", False) else 0,
                    settings.get("data_retention_preference", "standard"),
                    settings.get("notification_frequency", "important_only"),
                    datetime.utcnow().isoformat(),
                    json.dumps(settings.get("metadata", {}))
                ))
            
            logger.info(f"Privacy settings updated for user {user_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error updating user privacy settings: {e}")
            return False
    
    def get_user_notifications(self, user_id: str, unread_only: bool = False) -> List[Dict[str, Any]]:
        """Get user privacy notifications"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT notification_id, notification_type, title, message, priority,
                           read, created_at, action_required, action_url, metadata
                    FROM user_privacy_notifications 
                    WHERE user_id = ?
                """
                
                if unread_only:
                    query += " AND read = 0"
                
                query += " ORDER BY created_at DESC"
                
                cursor = conn.execute(query, (user_id,))
                
                notifications = []
                for row in cursor.fetchall():
                    notification = {
                        "notification_id": row[0],
                        "notification_type": row[1],
                        "title": row[2],
                        "message": row[3],
                        "priority": row[4],
                        "read": bool(row[5]),
                        "created_at": row[6],
                        "action_required": bool(row[7]),
                        "action_url": row[8],
                        "metadata": json.loads(row[9]) if row[9] else {}
                    }
                    notifications.append(notification)
                
                return notifications
        
        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            return []
    
    def mark_notification_read(self, notification_id: str) -> bool:
        """Mark notification as read"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE user_privacy_notifications 
                    SET read = 1
                    WHERE notification_id = ?
                """, (notification_id,))
            
            logger.info(f"Notification marked as read: {notification_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False

# Global user privacy dashboard instance
_user_dashboard = None

def get_user_privacy_dashboard() -> UserPrivacyDashboard:
    """Get global user privacy dashboard instance"""
    global _user_dashboard
    
    if _user_dashboard is None:
        _user_dashboard = UserPrivacyDashboard()
    
    return _user_dashboard

# Flask routes
@user_privacy_bp.route('/dashboard/<user_id>')
def get_user_dashboard(user_id):
    """Get user privacy dashboard"""
    try:
        dashboard = get_user_privacy_dashboard()
        overview = dashboard.get_user_dashboard_overview(user_id)
        
        return jsonify({
            'status': 'success',
            'data': overview,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_privacy_bp.route('/data-inventory/<user_id>')
def get_user_data_inventory_route(user_id):
    """Get user data inventory"""
    try:
        dashboard = get_user_privacy_dashboard()
        inventory = dashboard.get_user_data_inventory(user_id)
        
        inventory_data = []
        for item in inventory:
            inventory_data.append({
                "data_category": item.data_category,
                "data_type": item.data_type,
                "collection_date": item.collection_date.isoformat(),
                "purpose": item.purpose,
                "retention_period": item.retention_period,
                "accuracy_score": item.accuracy_score,
                "last_verified": item.last_verified.isoformat() if item.last_verified else None
            })
        
        return jsonify({
            'status': 'success',
            'data': inventory_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_privacy_bp.route('/consents/<user_id>')
def get_user_consents_route(user_id):
    """Get user consent records"""
    try:
        dashboard = get_user_privacy_dashboard()
        consents = dashboard.get_user_consents(user_id)
        
        consent_data = []
        for consent in consents:
            consent_data.append({
                "consent_type": consent.consent_type,
                "granted": consent.granted,
                "granted_at": consent.granted_at.isoformat(),
                "withdrawn_at": consent.withdrawn_at.isoformat() if consent.withdrawn_at else None,
                "purpose": consent.purpose,
                "third_parties": consent.third_parties
            })
        
        return jsonify({
            'status': 'success',
            'data': consent_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_privacy_bp.route('/settings/<user_id>', methods=['GET'])
def get_user_privacy_settings_route(user_id):
    """Get user privacy settings"""
    try:
        dashboard = get_user_privacy_dashboard()
        settings = dashboard.get_user_privacy_settings(user_id)
        
        if settings:
            return jsonify({
                'status': 'success',
                'data': settings,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Privacy settings not found'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_privacy_bp.route('/settings/<user_id>', methods=['PUT'])
def update_user_privacy_settings_route(user_id):
    """Update user privacy settings"""
    try:
        data = request.get_json()
        dashboard = get_user_privacy_dashboard()
        
        success = dashboard.update_user_privacy_settings(user_id, data)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Privacy settings updated successfully',
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Failed to update privacy settings'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_privacy_bp.route('/notifications/<user_id>')
def get_user_notifications_route(user_id):
    """Get user notifications"""
    try:
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        dashboard = get_user_privacy_dashboard()
        notifications = dashboard.get_user_notifications(user_id, unread_only)
        
        return jsonify({
            'status': 'success',
            'data': notifications,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_privacy_bp.route('/notifications/<notification_id>/read', methods=['PUT'])
def mark_notification_read_route(notification_id):
    """Mark notification as read"""
    try:
        dashboard = get_user_privacy_dashboard()
        success = dashboard.mark_notification_read(notification_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Notification marked as read',
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Failed to mark notification as read'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def register_user_privacy_routes(app):
    """Register user privacy routes with Flask app"""
    app.register_blueprint(user_privacy_bp)
    logger.info("User privacy dashboard routes registered") 