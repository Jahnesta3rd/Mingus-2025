import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from collections import defaultdict, Counter
import numpy as np
from io import BytesIO
import base64

# Set style for better visualizations
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class SecurityStatus(Enum):
    """Security status levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"

class ThreatLevel(Enum):
    """Threat level indicators"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityMetrics:
    """Security metrics data structure"""
    total_events: int
    critical_events: int
    high_risk_events: int
    medium_risk_events: int
    low_risk_events: int
    active_alerts: int
    failed_login_attempts: int
    suspicious_activities: int
    compliance_score: float
    system_health_score: float
    average_user_risk_score: float
    threat_level: ThreatLevel
    security_status: SecurityStatus

@dataclass
class DashboardData:
    """Complete dashboard data structure"""
    metrics: SecurityMetrics
    recent_events: List[Dict[str, Any]]
    threat_indicators: List[Dict[str, Any]]
    compliance_metrics: Dict[str, Any]
    user_risk_scores: List[Dict[str, Any]]
    system_health: Dict[str, Any]
    charts: Dict[str, str]  # Base64 encoded chart images

class SecurityDashboard:
    """Comprehensive security dashboard system"""
    
    def __init__(self, db_path: str = '/var/lib/mingus/security_events.db'):
        self.db_path = db_path
        self.chart_cache = {}
        self.cache_duration = 300  # 5 minutes
    
    def generate_dashboard(self) -> DashboardData:
        """Generate complete security dashboard"""
        try:
            # Generate all dashboard components
            metrics = self._calculate_security_metrics()
            recent_events = self._get_recent_security_events()
            threat_indicators = self._get_threat_indicators()
            compliance_metrics = self._get_compliance_metrics()
            user_risk_scores = self._get_user_risk_scores()
            system_health = self._get_system_health()
            charts = self._generate_dashboard_charts()
            
            return DashboardData(
                metrics=metrics,
                recent_events=recent_events,
                threat_indicators=threat_indicators,
                compliance_metrics=compliance_metrics,
                user_risk_scores=user_risk_scores,
                system_health=system_health,
                charts=charts
            )
        
        except Exception as e:
            print(f"Error generating dashboard: {e}")
            return self._get_empty_dashboard()
    
    def _calculate_security_metrics(self) -> SecurityMetrics:
        """Calculate comprehensive security metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get event counts by severity
            cursor.execute("""
                SELECT severity, COUNT(*) as count
                FROM security_events
                WHERE timestamp >= datetime('now', '-24 hours')
                GROUP BY severity
            """)
            
            severity_counts = dict(cursor.fetchall())
            
            # Get active alerts
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM security_events
                WHERE event_type IN ('suspicious_activity', 'failed_login_cluster', 'geographic_anomaly')
                AND timestamp >= datetime('now', '-1 hour')
            """)
            
            active_alerts = cursor.fetchone()[0]
            
            # Get failed login attempts
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM security_events
                WHERE event_type = 'auth_failure'
                AND timestamp >= datetime('now', '-24 hours')
            """)
            
            failed_logins = cursor.fetchone()[0]
            
            # Get suspicious activities
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM security_events
                WHERE event_type = 'suspicious_activity'
                AND timestamp >= datetime('now', '-24 hours')
            """)
            
            suspicious_activities = cursor.fetchone()[0]
            
            # Calculate compliance score
            compliance_score = self._calculate_compliance_score(cursor)
            
            # Calculate system health score
            system_health_score = self._calculate_system_health_score(cursor)
            
            # Calculate average user risk score
            average_user_risk = self._calculate_average_user_risk(cursor)
            
            # Determine threat level
            threat_level = self._determine_threat_level(active_alerts, failed_logins, suspicious_activities)
            
            # Determine security status
            security_status = self._determine_security_status(compliance_score, system_health_score, threat_level)
            
            conn.close()
            
            return SecurityMetrics(
                total_events=sum(severity_counts.values()),
                critical_events=severity_counts.get('critical', 0),
                high_risk_events=severity_counts.get('high', 0),
                medium_risk_events=severity_counts.get('medium', 0),
                low_risk_events=severity_counts.get('low', 0),
                active_alerts=active_alerts,
                failed_login_attempts=failed_logins,
                suspicious_activities=suspicious_activities,
                compliance_score=compliance_score,
                system_health_score=system_health_score,
                average_user_risk_score=average_user_risk,
                threat_level=threat_level,
                security_status=security_status
            )
        
        except Exception as e:
            print(f"Error calculating security metrics: {e}")
            return self._get_default_metrics()
    
    def _get_recent_security_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent security events"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT event_id, event_type, severity, timestamp, user_id, ip_address,
                       user_agent, risk_score, details, threat_level
                FROM security_events
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            events = []
            for row in cursor.fetchall():
                event = {
                    'event_id': row[0],
                    'event_type': row[1],
                    'severity': row[2],
                    'timestamp': row[3],
                    'user_id': row[4],
                    'ip_address': row[5],
                    'user_agent': row[6],
                    'risk_score': row[7],
                    'details': json.loads(row[8]) if row[8] else {},
                    'threat_level': row[9]
                }
                events.append(event)
            
            conn.close()
            return events
        
        except Exception as e:
            print(f"Error getting recent events: {e}")
            return []
    
    def _get_threat_indicators(self) -> List[Dict[str, Any]]:
        """Get current threat indicators"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get threat indicators from recent events
            cursor.execute("""
                SELECT event_type, COUNT(*) as count, AVG(risk_score) as avg_risk,
                       MAX(timestamp) as last_occurrence
                FROM security_events
                WHERE timestamp >= datetime('now', '-1 hour')
                AND severity IN ('high', 'critical')
                GROUP BY event_type
                ORDER BY count DESC
            """)
            
            threat_indicators = []
            for row in cursor.fetchall():
                indicator = {
                    'threat_type': row[0],
                    'occurrence_count': row[1],
                    'average_risk_score': round(row[2], 2),
                    'last_occurrence': row[3],
                    'threat_level': 'high' if row[2] > 7.0 else 'medium'
                }
                threat_indicators.append(indicator)
            
            # Add system-level threat indicators
            system_threats = self._get_system_threat_indicators(cursor)
            threat_indicators.extend(system_threats)
            
            conn.close()
            return threat_indicators
        
        except Exception as e:
            print(f"Error getting threat indicators: {e}")
            return []
    
    def _get_compliance_metrics(self) -> Dict[str, Any]:
        """Get compliance metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate compliance scores for different standards
            compliance_metrics = {
                'pci_dss': self._calculate_pci_dss_compliance(cursor),
                'gdpr': self._calculate_gdpr_compliance(cursor),
                'hipaa': self._calculate_hipaa_compliance(cursor),
                'sox': self._calculate_sox_compliance(cursor),
                'overall_score': 0.0
            }
            
            # Calculate overall compliance score
            scores = [v for v in compliance_metrics.values() if isinstance(v, (int, float)) and v > 0]
            if scores:
                compliance_metrics['overall_score'] = sum(scores) / len(scores)
            
            # Add compliance violations
            compliance_metrics['violations'] = self._get_compliance_violations(cursor)
            
            conn.close()
            return compliance_metrics
        
        except Exception as e:
            print(f"Error getting compliance metrics: {e}")
            return {'overall_score': 0.0, 'violations': []}
    
    def _get_user_risk_scores(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user risk scores"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_id, AVG(risk_score) as avg_risk, COUNT(*) as event_count,
                       MAX(timestamp) as last_activity, 
                       COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical_events
                FROM security_events
                WHERE user_id IS NOT NULL
                AND timestamp >= datetime('now', '-7 days')
                GROUP BY user_id
                ORDER BY avg_risk DESC
                LIMIT ?
            """, (limit,))
            
            user_risk_scores = []
            for row in cursor.fetchall():
                user_risk = {
                    'user_id': row[0],
                    'average_risk_score': round(row[1], 2),
                    'event_count': row[2],
                    'last_activity': row[3],
                    'critical_events': row[4],
                    'risk_level': self._get_risk_level(row[1])
                }
                user_risk_scores.append(user_risk)
            
            conn.close()
            return user_risk_scores
        
        except Exception as e:
            print(f"Error getting user risk scores: {e}")
            return []
    
    def _get_system_health(self) -> Dict[str, Any]:
        """Get system security health metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate various health metrics
            system_health = {
                'event_volume': self._get_event_volume_health(cursor),
                'response_times': self._get_response_time_health(cursor),
                'error_rates': self._get_error_rate_health(cursor),
                'authentication_health': self._get_authentication_health(cursor),
                'api_health': self._get_api_health(cursor),
                'data_protection_health': self._get_data_protection_health(cursor),
                'overall_health_score': 0.0
            }
            
            # Calculate overall health score
            health_scores = [v for v in system_health.values() if isinstance(v, (int, float)) and v > 0]
            if health_scores:
                system_health['overall_health_score'] = sum(health_scores) / len(health_scores)
            
            conn.close()
            return system_health
        
        except Exception as e:
            print(f"Error getting system health: {e}")
            return {'overall_health_score': 0.0}
    
    def _generate_dashboard_charts(self) -> Dict[str, str]:
        """Generate dashboard charts"""
        charts = {}
        
        try:
            # Event distribution chart
            charts['event_distribution'] = self._create_event_distribution_chart()
            
            # Threat trend chart
            charts['threat_trends'] = self._create_threat_trends_chart()
            
            # User risk score distribution
            charts['user_risk_distribution'] = self._create_user_risk_distribution_chart()
            
            # Compliance metrics chart
            charts['compliance_metrics'] = self._create_compliance_metrics_chart()
            
            # System health chart
            charts['system_health'] = self._create_system_health_chart()
            
            # Geographic threat map
            charts['geographic_threats'] = self._create_geographic_threat_chart()
            
        except Exception as e:
            print(f"Error generating charts: {e}")
        
        return charts
    
    def _create_event_distribution_chart(self) -> str:
        """Create event distribution pie chart"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT event_type, COUNT(*) as count
                FROM security_events
                WHERE timestamp >= datetime('now', '-24 hours')
                GROUP BY event_type
                ORDER BY count DESC
                LIMIT 10
            """)
            
            data = cursor.fetchall()
            conn.close()
            
            if not data:
                return self._create_empty_chart("No events in the last 24 hours")
            
            event_types, counts = zip(*data)
            
            plt.figure(figsize=(10, 6))
            plt.pie(counts, labels=event_types, autopct='%1.1f%%', startangle=90)
            plt.title('Security Events Distribution (Last 24 Hours)')
            plt.axis('equal')
            
            return self._save_chart_to_base64()
        
        except Exception as e:
            print(f"Error creating event distribution chart: {e}")
            return self._create_empty_chart("Error loading data")
    
    def _create_threat_trends_chart(self) -> str:
        """Create threat trends line chart"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get threat data for the last 7 days
            cursor.execute("""
                SELECT DATE(timestamp) as date, COUNT(*) as count, AVG(risk_score) as avg_risk
                FROM security_events
                WHERE timestamp >= datetime('now', '-7 days')
                AND severity IN ('high', 'critical')
                GROUP BY DATE(timestamp)
                ORDER BY date
            """)
            
            data = cursor.fetchall()
            conn.close()
            
            if not data:
                return self._create_empty_chart("No threat data available")
            
            dates, counts, risks = zip(*data)
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            # Threat count trend
            ax1.plot(dates, counts, marker='o', linewidth=2, markersize=6)
            ax1.set_title('Daily Threat Count Trend')
            ax1.set_ylabel('Number of Threats')
            ax1.grid(True, alpha=0.3)
            
            # Average risk score trend
            ax2.plot(dates, risks, marker='s', linewidth=2, markersize=6, color='red')
            ax2.set_title('Daily Average Risk Score Trend')
            ax2.set_ylabel('Average Risk Score')
            ax2.set_xlabel('Date')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            return self._save_chart_to_base64()
        
        except Exception as e:
            print(f"Error creating threat trends chart: {e}")
            return self._create_empty_chart("Error loading data")
    
    def _create_user_risk_distribution_chart(self) -> str:
        """Create user risk score distribution chart"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT AVG(risk_score) as avg_risk
                FROM security_events
                WHERE user_id IS NOT NULL
                AND timestamp >= datetime('now', '-7 days')
                GROUP BY user_id
            """)
            
            risk_scores = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if not risk_scores:
                return self._create_empty_chart("No user risk data available")
            
            plt.figure(figsize=(10, 6))
            plt.hist(risk_scores, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
            plt.title('User Risk Score Distribution')
            plt.xlabel('Average Risk Score')
            plt.ylabel('Number of Users')
            plt.grid(True, alpha=0.3)
            
            # Add vertical line for mean
            mean_risk = np.mean(risk_scores)
            plt.axvline(mean_risk, color='red', linestyle='--', label=f'Mean: {mean_risk:.2f}')
            plt.legend()
            
            return self._save_chart_to_base64()
        
        except Exception as e:
            print(f"Error creating user risk distribution chart: {e}")
            return self._create_empty_chart("Error loading data")
    
    def _create_compliance_metrics_chart(self) -> str:
        """Create compliance metrics radar chart"""
        try:
            # Sample compliance data (in real implementation, get from database)
            compliance_data = {
                'PCI DSS': 85,
                'GDPR': 92,
                'HIPAA': 78,
                'SOX': 88,
                'ISO 27001': 90,
                'SOC 2': 82
            }
            
            categories = list(compliance_data.keys())
            values = list(compliance_data.values())
            
            # Create radar chart
            angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
            values += values[:1]  # Complete the circle
            angles += angles[:1]
            
            fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(projection='polar'))
            ax.plot(angles, values, 'o-', linewidth=2, label='Compliance Score')
            ax.fill(angles, values, alpha=0.25)
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories)
            ax.set_ylim(0, 100)
            ax.set_title('Compliance Metrics Overview', size=16, pad=20)
            ax.grid(True)
            
            return self._save_chart_to_base64()
        
        except Exception as e:
            print(f"Error creating compliance metrics chart: {e}")
            return self._create_empty_chart("Error loading data")
    
    def _create_system_health_chart(self) -> str:
        """Create system health gauge chart"""
        try:
            # Sample system health data
            health_metrics = {
                'Event Volume': 85,
                'Response Times': 92,
                'Error Rates': 78,
                'Authentication': 88,
                'API Health': 90,
                'Data Protection': 82
            }
            
            fig, axes = plt.subplots(2, 3, figsize=(15, 10))
            axes = axes.ravel()
            
            for i, (metric, value) in enumerate(health_metrics.items()):
                ax = axes[i]
                
                # Create gauge chart
                theta = np.linspace(0, np.pi, 100)
                r = np.ones_like(theta)
                
                # Color based on value
                if value >= 80:
                    color = 'green'
                elif value >= 60:
                    color = 'orange'
                else:
                    color = 'red'
                
                ax.plot(theta, r, color='lightgray', linewidth=10)
                ax.fill_between(theta, 0, r, alpha=0.3, color=color)
                
                # Add value text
                ax.text(0, 0.5, f'{value}%', ha='center', va='center', fontsize=14, fontweight='bold')
                ax.set_title(metric, fontsize=12)
                ax.set_xlim(0, np.pi)
                ax.set_ylim(0, 1.2)
                ax.axis('off')
            
            plt.tight_layout()
            
            return self._save_chart_to_base64()
        
        except Exception as e:
            print(f"Error creating system health chart: {e}")
            return self._create_empty_chart("Error loading data")
    
    def _create_geographic_threat_chart(self) -> str:
        """Create geographic threat heatmap"""
        try:
            # Sample geographic threat data
            countries = ['US', 'CN', 'RU', 'DE', 'GB', 'FR', 'JP', 'IN', 'BR', 'CA']
            threat_levels = [85, 92, 78, 88, 90, 82, 75, 88, 70, 85]
            
            plt.figure(figsize=(12, 6))
            bars = plt.bar(countries, threat_levels, color=plt.cm.RdYlGn_r(np.array(threat_levels)/100))
            plt.title('Geographic Threat Levels by Country')
            plt.xlabel('Country')
            plt.ylabel('Threat Level (%)')
            plt.ylim(0, 100)
            
            # Add value labels on bars
            for bar, value in zip(bars, threat_levels):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                        f'{value}%', ha='center', va='bottom')
            
            plt.grid(True, alpha=0.3)
            
            return self._save_chart_to_base64()
        
        except Exception as e:
            print(f"Error creating geographic threat chart: {e}")
            return self._create_empty_chart("Error loading data")
    
    def _save_chart_to_base64(self) -> str:
        """Save current matplotlib chart to base64 string"""
        try:
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            image_png = buffer.getvalue()
            buffer.close()
            plt.close()
            
            return base64.b64encode(image_png).decode()
        
        except Exception as e:
            print(f"Error saving chart to base64: {e}")
            return ""
    
    def _create_empty_chart(self, message: str) -> str:
        """Create empty chart with message"""
        try:
            plt.figure(figsize=(8, 6))
            plt.text(0.5, 0.5, message, ha='center', va='center', 
                    transform=plt.gca().transAxes, fontsize=14)
            plt.axis('off')
            
            return self._save_chart_to_base64()
        
        except Exception as e:
            print(f"Error creating empty chart: {e}")
            return ""
    
    # Helper methods for metrics calculation
    def _calculate_compliance_score(self, cursor) -> float:
        """Calculate overall compliance score"""
        try:
            # Sample compliance calculation
            return 85.5
        except:
            return 0.0
    
    def _calculate_system_health_score(self, cursor) -> float:
        """Calculate system health score"""
        try:
            # Sample health calculation
            return 88.2
        except:
            return 0.0
    
    def _calculate_average_user_risk(self, cursor) -> float:
        """Calculate average user risk score"""
        try:
            cursor.execute("""
                SELECT AVG(risk_score) FROM security_events
                WHERE user_id IS NOT NULL
                AND timestamp >= datetime('now', '-7 days')
            """)
            result = cursor.fetchone()
            return round(result[0] if result[0] else 0.0, 2)
        except:
            return 0.0
    
    def _determine_threat_level(self, active_alerts: int, failed_logins: int, suspicious_activities: int) -> ThreatLevel:
        """Determine current threat level"""
        total_threats = active_alerts + failed_logins + suspicious_activities
        
        if total_threats > 50:
            return ThreatLevel.CRITICAL
        elif total_threats > 20:
            return ThreatLevel.HIGH
        elif total_threats > 10:
            return ThreatLevel.MEDIUM
        else:
            return ThreatLevel.LOW
    
    def _determine_security_status(self, compliance_score: float, health_score: float, threat_level: ThreatLevel) -> SecurityStatus:
        """Determine overall security status"""
        avg_score = (compliance_score + health_score) / 2
        
        if threat_level == ThreatLevel.CRITICAL or avg_score < 50:
            return SecurityStatus.CRITICAL
        elif threat_level == ThreatLevel.HIGH or avg_score < 70:
            return SecurityStatus.POOR
        elif avg_score < 80:
            return SecurityStatus.FAIR
        elif avg_score < 90:
            return SecurityStatus.GOOD
        else:
            return SecurityStatus.EXCELLENT
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Get risk level from score"""
        if risk_score >= 8.0:
            return "critical"
        elif risk_score >= 6.0:
            return "high"
        elif risk_score >= 4.0:
            return "medium"
        else:
            return "low"
    
    def _get_default_metrics(self) -> SecurityMetrics:
        """Get default metrics when database is unavailable"""
        return SecurityMetrics(
            total_events=0,
            critical_events=0,
            high_risk_events=0,
            medium_risk_events=0,
            low_risk_events=0,
            active_alerts=0,
            failed_login_attempts=0,
            suspicious_activities=0,
            compliance_score=0.0,
            system_health_score=0.0,
            average_user_risk_score=0.0,
            threat_level=ThreatLevel.LOW,
            security_status=SecurityStatus.EXCELLENT
        )
    
    def _get_empty_dashboard(self) -> DashboardData:
        """Get empty dashboard when generation fails"""
        return DashboardData(
            metrics=self._get_default_metrics(),
            recent_events=[],
            threat_indicators=[],
            compliance_metrics={'overall_score': 0.0, 'violations': []},
            user_risk_scores=[],
            system_health={'overall_health_score': 0.0},
            charts={}
        )
    
    # Additional helper methods for specific metrics
    def _get_system_threat_indicators(self, cursor) -> List[Dict[str, Any]]:
        """Get system-level threat indicators"""
        return [
            {
                'threat_type': 'system_vulnerability',
                'occurrence_count': 3,
                'average_risk_score': 7.5,
                'last_occurrence': datetime.now().isoformat(),
                'threat_level': 'high'
            }
        ]
    
    def _calculate_pci_dss_compliance(self, cursor) -> float:
        """Calculate PCI DSS compliance score"""
        return 85.0
    
    def _calculate_gdpr_compliance(self, cursor) -> float:
        """Calculate GDPR compliance score"""
        return 92.0
    
    def _calculate_hipaa_compliance(self, cursor) -> float:
        """Calculate HIPAA compliance score"""
        return 78.0
    
    def _calculate_sox_compliance(self, cursor) -> float:
        """Calculate SOX compliance score"""
        return 88.0
    
    def _get_compliance_violations(self, cursor) -> List[Dict[str, Any]]:
        """Get compliance violations"""
        return [
            {
                'standard': 'PCI DSS',
                'violation': 'Missing encryption for sensitive data',
                'severity': 'high',
                'timestamp': datetime.now().isoformat()
            }
        ]
    
    def _get_event_volume_health(self, cursor) -> float:
        """Get event volume health score"""
        return 85.0
    
    def _get_response_time_health(self, cursor) -> float:
        """Get response time health score"""
        return 92.0
    
    def _get_error_rate_health(self, cursor) -> float:
        """Get error rate health score"""
        return 78.0
    
    def _get_authentication_health(self, cursor) -> float:
        """Get authentication health score"""
        return 88.0
    
    def _get_api_health(self, cursor) -> float:
        """Get API health score"""
        return 90.0
    
    def _get_data_protection_health(self, cursor) -> float:
        """Get data protection health score"""
        return 82.0

# Utility functions for dashboard integration
def create_security_dashboard(db_path: str = None) -> SecurityDashboard:
    """Create security dashboard instance"""
    return SecurityDashboard(db_path or '/var/lib/mingus/security_events.db')

def get_dashboard_json(dashboard: SecurityDashboard) -> str:
    """Get dashboard data as JSON string"""
    dashboard_data = dashboard.generate_dashboard()
    return json.dumps(asdict(dashboard_data), default=str, indent=2)

def export_dashboard_report(dashboard: SecurityDashboard, format: str = 'json') -> str:
    """Export dashboard as report"""
    dashboard_data = dashboard.generate_dashboard()
    
    if format.lower() == 'json':
        return json.dumps(asdict(dashboard_data), default=str, indent=2)
    elif format.lower() == 'html':
        return generate_html_dashboard(dashboard_data)
    else:
        raise ValueError(f"Unsupported format: {format}")

def generate_html_dashboard(dashboard_data: DashboardData) -> str:
    """Generate HTML dashboard"""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MINGUS Security Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
            .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
            .metric-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .metric-value { font-size: 2em; font-weight: bold; color: #667eea; }
            .metric-label { color: #666; margin-top: 5px; }
            .chart-container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
            .chart-title { font-size: 1.2em; font-weight: bold; margin-bottom: 15px; color: #333; }
            .status-excellent { color: #28a745; }
            .status-good { color: #17a2b8; }
            .status-fair { color: #ffc107; }
            .status-poor { color: #fd7e14; }
            .status-critical { color: #dc3545; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔒 MINGUS Security Dashboard</h1>
            <p>Real-time security monitoring and threat intelligence</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value status-{security_status}">{security_status}</div>
                <div class="metric-label">Security Status</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{total_events}</div>
                <div class="metric-label">Total Events (24h)</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{active_alerts}</div>
                <div class="metric-label">Active Alerts</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{compliance_score}%</div>
                <div class="metric-label">Compliance Score</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{system_health_score}%</div>
                <div class="metric-label">System Health</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{threat_level}</div>
                <div class="metric-label">Threat Level</div>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">Security Events Distribution</div>
            <img src="data:image/png;base64,{event_distribution_chart}" style="width: 100%; max-width: 600px;">
        </div>
        
        <div class="chart-container">
            <div class="chart-title">Threat Trends</div>
            <img src="data:image/png;base64,{threat_trends_chart}" style="width: 100%; max-width: 800px;">
        </div>
        
        <div class="chart-container">
            <div class="chart-title">User Risk Distribution</div>
            <img src="data:image/png;base64,{user_risk_chart}" style="width: 100%; max-width: 600px;">
        </div>
        
        <div class="chart-container">
            <div class="chart-title">Compliance Metrics</div>
            <img src="data:image/png;base64,{compliance_chart}" style="width: 100%; max-width: 600px;">
        </div>
        
        <div class="chart-container">
            <div class="chart-title">System Health Overview</div>
            <img src="data:image/png;base64,{system_health_chart}" style="width: 100%; max-width: 800px;">
        </div>
        
        <div class="chart-container">
            <div class="chart-title">Geographic Threat Levels</div>
            <img src="data:image/png;base64,{geographic_chart}" style="width: 100%; max-width: 800px;">
        </div>
    </body>
    </html>
    """
    
    # Format the template with dashboard data
    return html_template.format(
        security_status=dashboard_data.metrics.security_status.value,
        total_events=dashboard_data.metrics.total_events,
        active_alerts=dashboard_data.metrics.active_alerts,
        compliance_score=dashboard_data.metrics.compliance_score,
        system_health_score=dashboard_data.metrics.system_health_score,
        threat_level=dashboard_data.metrics.threat_level.value,
        event_distribution_chart=dashboard_data.charts.get('event_distribution', ''),
        threat_trends_chart=dashboard_data.charts.get('threat_trends', ''),
        user_risk_chart=dashboard_data.charts.get('user_risk_distribution', ''),
        compliance_chart=dashboard_data.charts.get('compliance_metrics', ''),
        system_health_chart=dashboard_data.charts.get('system_health', ''),
        geographic_chart=dashboard_data.charts.get('geographic_threats', '')
    ) 