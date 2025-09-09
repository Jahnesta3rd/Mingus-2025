#!/usr/bin/env python3
"""
Meme Analytics System for Mingus Personal Finance App

This module provides comprehensive analytics tracking for the meme splash page feature,
including event tracking, dashboard queries, automated alerts, and data visualization.

Features:
- Event tracking for meme interactions
- User demographic analysis
- Performance metrics calculation
- Automated alert system
- CSV export functionality
- Simple admin dashboard with charts
"""

import sqlite3
import json
import csv
import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('meme_analytics.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class AnalyticsEvent:
    """Data class for analytics events"""
    user_id: int
    session_id: str
    meme_id: int
    event_type: str
    time_spent_seconds: int = 0
    user_agent: str = ""
    ip_address: str = ""
    referrer: str = ""
    device_type: str = ""
    browser: str = ""
    os: str = ""
    screen_resolution: str = ""
    additional_data: str = ""

@dataclass
class UserDemographics:
    """Data class for user demographics"""
    user_id: int
    age_range: str = ""
    gender: str = ""
    income_range: str = ""
    education_level: str = ""
    location_state: str = ""
    location_country: str = "US"

@dataclass
class PerformanceMetrics:
    """Data class for performance metrics"""
    meme_id: int
    date: date
    total_views: int = 0
    total_continues: int = 0
    total_skips: int = 0
    total_auto_advances: int = 0
    avg_time_spent_seconds: float = 0.0
    skip_rate: float = 0.0
    continue_rate: float = 0.0
    error_count: int = 0
    load_time_ms: float = 0.0

class MemeAnalyticsSystem:
    """Main analytics system class"""
    
    def __init__(self, db_path: str = "mingus_memes.db"):
        """Initialize the analytics system"""
        self.db_path = db_path
        self.ensure_database_exists()
        self.setup_matplotlib()
        
    def setup_matplotlib(self):
        """Configure matplotlib for better visualizations"""
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
    def ensure_database_exists(self):
        """Ensure the database and analytics tables exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Read and execute the analytics schema
                schema_path = Path(__file__).parent / "meme_analytics_schema.sql"
                if schema_path.exists():
                    with open(schema_path, 'r') as f:
                        schema_sql = f.read()
                    conn.executescript(schema_sql)
                    conn.commit()
                    logger.info("Analytics database schema initialized successfully")
                else:
                    logger.warning("Analytics schema file not found, creating basic tables")
                    self.create_basic_tables(conn)
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def create_basic_tables(self, conn: sqlite3.Connection):
        """Create basic analytics tables if schema file is not available"""
        basic_schema = """
        CREATE TABLE IF NOT EXISTS meme_analytics_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            meme_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            event_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            time_spent_seconds INTEGER DEFAULT 0,
            device_type TEXT,
            browser TEXT,
            additional_data TEXT
        );
        
        CREATE TABLE IF NOT EXISTS user_demographics (
            user_id INTEGER PRIMARY KEY,
            age_range TEXT,
            gender TEXT,
            income_range TEXT,
            education_level TEXT,
            location_state TEXT,
            location_country TEXT DEFAULT 'US',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS meme_performance_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meme_id INTEGER NOT NULL,
            date DATE NOT NULL,
            total_views INTEGER DEFAULT 0,
            total_continues INTEGER DEFAULT 0,
            total_skips INTEGER DEFAULT 0,
            avg_time_spent_seconds REAL DEFAULT 0,
            skip_rate REAL DEFAULT 0,
            continue_rate REAL DEFAULT 0,
            UNIQUE(meme_id, date)
        );
        """
        conn.executescript(basic_schema)
        conn.commit()
    
    def track_event(self, event: AnalyticsEvent) -> bool:
        """Track an analytics event"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO meme_analytics_events 
                    (user_id, session_id, meme_id, event_type, time_spent_seconds,
                     user_agent, ip_address, referrer, device_type, browser, os,
                     screen_resolution, additional_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.user_id, event.session_id, event.meme_id, event.event_type,
                    event.time_spent_seconds, event.user_agent, event.ip_address,
                    event.referrer, event.device_type, event.browser, event.os,
                    event.screen_resolution, event.additional_data
                ))
                conn.commit()
                logger.info(f"Tracked event: {event.event_type} for user {event.user_id}, meme {event.meme_id}")
                return True
        except Exception as e:
            logger.error(f"Error tracking event: {e}")
            return False
    
    def add_user_demographics(self, demographics: UserDemographics) -> bool:
        """Add or update user demographics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO user_demographics 
                    (user_id, age_range, gender, income_range, education_level, 
                     location_state, location_country)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    demographics.user_id, demographics.age_range, demographics.gender,
                    demographics.income_range, demographics.education_level,
                    demographics.location_state, demographics.location_country
                ))
                conn.commit()
                logger.info(f"Updated demographics for user {demographics.user_id}")
                return True
        except Exception as e:
            logger.error(f"Error updating demographics: {e}")
            return False
    
    def get_daily_engagement_rates(self, days: int = 30) -> pd.DataFrame:
        """Get daily engagement rates for the specified number of days"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                SELECT 
                    DATE(event_timestamp) as date,
                    COUNT(CASE WHEN event_type = 'view' THEN 1 END) as total_views,
                    COUNT(CASE WHEN event_type = 'continue' THEN 1 END) as total_continues,
                    COUNT(CASE WHEN event_type = 'skip' THEN 1 END) as total_skips,
                    COUNT(CASE WHEN event_type = 'auto_advance' THEN 1 END) as total_auto_advances,
                    COUNT(DISTINCT user_id) as unique_users,
                    AVG(CASE WHEN time_spent_seconds > 0 THEN time_spent_seconds END) as avg_time_spent
                FROM meme_analytics_events 
                WHERE event_timestamp >= date('now', '-{} days')
                GROUP BY DATE(event_timestamp)
                ORDER BY date DESC
                """.format(days)
                
                df = pd.read_sql_query(query, conn)
                if not df.empty:
                    df['skip_rate'] = (df['total_skips'] / (df['total_views'] + 1e-6)) * 100
                    df['continue_rate'] = (df['total_continues'] / (df['total_views'] + 1e-6)) * 100
                    df['engagement_rate'] = ((df['total_continues'] + df['total_auto_advances']) / (df['total_views'] + 1e-6)) * 100
                
                return df
        except Exception as e:
            logger.error(f"Error getting daily engagement rates: {e}")
            return pd.DataFrame()
    
    def get_category_performance(self, days: int = 30) -> pd.DataFrame:
        """Get performance metrics by category"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                SELECT 
                    m.category,
                    COUNT(CASE WHEN mae.event_type = 'view' THEN 1 END) as total_views,
                    COUNT(CASE WHEN mae.event_type = 'continue' THEN 1 END) as total_continues,
                    COUNT(CASE WHEN mae.event_type = 'skip' THEN 1 END) as total_skips,
                    COUNT(DISTINCT mae.user_id) as unique_users,
                    AVG(CASE WHEN mae.time_spent_seconds > 0 THEN mae.time_spent_seconds END) as avg_time_spent
                FROM meme_analytics_events mae
                JOIN memes m ON mae.meme_id = m.id
                WHERE mae.event_timestamp >= date('now', '-{} days')
                GROUP BY m.category
                ORDER BY total_views DESC
                """.format(days)
                
                df = pd.read_sql_query(query, conn)
                if not df.empty:
                    df['skip_rate'] = (df['total_skips'] / (df['total_views'] + 1e-6)) * 100
                    df['continue_rate'] = (df['total_continues'] / (df['total_views'] + 1e-6)) * 100
                    df['popularity_score'] = df['total_views'] * df['continue_rate'] / 100
                
                return df
        except Exception as e:
            logger.error(f"Error getting category performance: {e}")
            return pd.DataFrame()
    
    def get_user_retention_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Analyze user retention correlation with meme usage"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get users who used memes vs those who didn't
                query = """
                WITH meme_users AS (
                    SELECT DISTINCT user_id, MIN(event_timestamp) as first_meme_date
                    FROM meme_analytics_events
                    WHERE event_timestamp >= date('now', '-{} days')
                    GROUP BY user_id
                ),
                user_activity AS (
                    SELECT 
                        mu.user_id,
                        mu.first_meme_date,
                        COUNT(mae.id) as total_meme_interactions,
                        COUNT(DISTINCT DATE(mae.event_timestamp)) as active_days,
                        MAX(mae.event_timestamp) as last_activity
                    FROM meme_users mu
                    LEFT JOIN meme_analytics_events mae ON mu.user_id = mae.user_id
                    WHERE mae.event_timestamp >= date('now', '-{} days')
                    GROUP BY mu.user_id, mu.first_meme_date
                )
                SELECT 
                    AVG(total_meme_interactions) as avg_interactions,
                    AVG(active_days) as avg_active_days,
                    COUNT(*) as total_meme_users,
                    AVG(julianday('now') - julianday(first_meme_date)) as avg_days_since_first_use
                FROM user_activity
                """.format(days, days)
                
                result = conn.execute(query).fetchone()
                return {
                    'avg_interactions': result[0] or 0,
                    'avg_active_days': result[1] or 0,
                    'total_meme_users': result[2] or 0,
                    'avg_days_since_first_use': result[3] or 0
                }
        except Exception as e:
            logger.error(f"Error getting user retention analysis: {e}")
            return {}
    
    def get_performance_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get overall performance metrics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                SELECT 
                    COUNT(CASE WHEN event_type = 'view' THEN 1 END) as total_views,
                    COUNT(CASE WHEN event_type = 'continue' THEN 1 END) as total_continues,
                    COUNT(CASE WHEN event_type = 'skip' THEN 1 END) as total_skips,
                    COUNT(CASE WHEN event_type = 'error' THEN 1 END) as total_errors,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(DISTINCT session_id) as total_sessions,
                    AVG(CASE WHEN time_spent_seconds > 0 THEN time_spent_seconds END) as avg_time_spent,
                    MIN(event_timestamp) as first_event,
                    MAX(event_timestamp) as last_event
                FROM meme_analytics_events 
                WHERE event_timestamp >= date('now', '-{} days')
                """.format(days)
                
                result = conn.execute(query).fetchone()
                if result:
                    total_views = result[0] or 0
                    total_continues = result[1] or 0
                    total_skips = result[2] or 0
                    total_errors = result[3] or 0
                    
                    return {
                        'total_views': total_views,
                        'total_continues': total_continues,
                        'total_skips': total_skips,
                        'total_errors': total_errors,
                        'unique_users': result[4] or 0,
                        'total_sessions': result[5] or 0,
                        'avg_time_spent': result[6] or 0,
                        'skip_rate': (total_skips / (total_views + 1e-6)) * 100,
                        'continue_rate': (total_continues / (total_views + 1e-6)) * 100,
                        'error_rate': (total_errors / (total_views + 1e-6)) * 100,
                        'first_event': result[7],
                        'last_event': result[8]
                    }
                return {}
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {}
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check for conditions that should trigger alerts"""
        alerts = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check for high skip rates (>70%)
                skip_rate_query = """
                SELECT 
                    m.category,
                    COUNT(CASE WHEN mae.event_type = 'skip' THEN 1 END) as skips,
                    COUNT(CASE WHEN mae.event_type IN ('view', 'continue', 'skip', 'auto_advance') THEN 1 END) as total_actions,
                    (COUNT(CASE WHEN mae.event_type = 'skip' THEN 1 END) * 100.0) / 
                    NULLIF(COUNT(CASE WHEN mae.event_type IN ('view', 'continue', 'skip', 'auto_advance') THEN 1 END), 0) as skip_rate
                FROM meme_analytics_events mae
                JOIN memes m ON mae.meme_id = m.id
                WHERE mae.event_timestamp >= date('now', '-7 days')
                GROUP BY m.category
                HAVING skip_rate > 70
                """
                
                for row in conn.execute(skip_rate_query).fetchall():
                    alerts.append({
                        'type': 'high_skip_rate',
                        'severity': 'high' if row[3] > 80 else 'medium',
                        'title': f'High Skip Rate in {row[0].title()} Category',
                        'description': f'Skip rate is {row[3]:.1f}% for {row[0]} category',
                        'affected_metric': 'skip_rate',
                        'threshold_value': 70.0,
                        'actual_value': row[3],
                        'affected_category': row[0]
                    })
                
                # Check for technical errors
                error_query = """
                SELECT 
                    COUNT(CASE WHEN event_type = 'error' THEN 1 END) as error_count,
                    COUNT(*) as total_events,
                    (COUNT(CASE WHEN event_type = 'error' THEN 1 END) * 100.0) / COUNT(*) as error_rate
                FROM meme_analytics_events 
                WHERE event_timestamp >= date('now', '-1 day')
                """
                
                error_result = conn.execute(error_query).fetchone()
                if error_result and error_result[2] > 5:  # More than 5% error rate
                    alerts.append({
                        'type': 'technical_error',
                        'severity': 'high' if error_result[2] > 10 else 'medium',
                        'title': 'High Error Rate Detected',
                        'description': f'Error rate is {error_result[2]:.1f}% ({error_result[0]} errors out of {error_result[1]} events)',
                        'affected_metric': 'error_rate',
                        'threshold_value': 5.0,
                        'actual_value': error_result[2]
                    })
                
                # Check for unusual usage patterns (sudden drop in activity)
                usage_query = """
                SELECT 
                    DATE(event_timestamp) as date,
                    COUNT(*) as daily_events
                FROM meme_analytics_events 
                WHERE event_timestamp >= date('now', '-7 days')
                GROUP BY DATE(event_timestamp)
                ORDER BY date DESC
                LIMIT 2
                """
                
                usage_results = conn.execute(usage_query).fetchall()
                if len(usage_results) == 2:
                    today_events = usage_results[0][1]
                    yesterday_events = usage_results[1][1]
                    if yesterday_events > 0 and today_events < (yesterday_events * 0.5):  # 50% drop
                        alerts.append({
                            'type': 'unusual_usage_pattern',
                            'severity': 'medium',
                            'title': 'Unusual Drop in Activity',
                            'description': f'Activity dropped from {yesterday_events} to {today_events} events',
                            'affected_metric': 'daily_events',
                            'threshold_value': yesterday_events * 0.5,
                            'actual_value': today_events
                        })
                
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
        
        return alerts
    
    def create_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Create an alert in the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO analytics_alerts 
                    (alert_type, severity, title, description, affected_metric,
                     threshold_value, actual_value, affected_category, affected_meme_id,
                     date_range_start, date_range_end)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert_data.get('type'),
                    alert_data.get('severity'),
                    alert_data.get('title'),
                    alert_data.get('description'),
                    alert_data.get('affected_metric'),
                    alert_data.get('threshold_value'),
                    alert_data.get('actual_value'),
                    alert_data.get('affected_category'),
                    alert_data.get('affected_meme_id'),
                    date.today() - timedelta(days=7),
                    date.today()
                ))
                conn.commit()
                logger.info(f"Created alert: {alert_data.get('title')}")
                return True
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return False
    
    def export_to_csv(self, data: pd.DataFrame, filename: str) -> bool:
        """Export data to CSV file"""
        try:
            data.to_csv(filename, index=False)
            logger.info(f"Exported data to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False
    
    def create_dashboard_charts(self, output_dir: str = "analytics_charts") -> bool:
        """Create dashboard charts and save them as images"""
        try:
            Path(output_dir).mkdir(exist_ok=True)
            
            # Daily engagement rates chart
            daily_data = self.get_daily_engagement_rates(30)
            if not daily_data.empty:
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
                
                # Engagement rates over time
                daily_data['date'] = pd.to_datetime(daily_data['date'])
                ax1.plot(daily_data['date'], daily_data['skip_rate'], label='Skip Rate', marker='o')
                ax1.plot(daily_data['date'], daily_data['continue_rate'], label='Continue Rate', marker='s')
                ax1.plot(daily_data['date'], daily_data['engagement_rate'], label='Engagement Rate', marker='^')
                ax1.set_title('Daily Engagement Rates (30 Days)')
                ax1.set_ylabel('Rate (%)')
                ax1.legend()
                ax1.grid(True, alpha=0.3)
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                
                # Daily views and users
                ax2.bar(daily_data['date'], daily_data['total_views'], alpha=0.7, label='Total Views')
                ax2_twin = ax2.twinx()
                ax2_twin.plot(daily_data['date'], daily_data['unique_users'], color='red', marker='o', label='Unique Users')
                ax2.set_title('Daily Views and Users')
                ax2.set_ylabel('Views')
                ax2_twin.set_ylabel('Users')
                ax2.legend(loc='upper left')
                ax2_twin.legend(loc='upper right')
                ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                
                plt.tight_layout()
                plt.savefig(f"{output_dir}/daily_engagement.png", dpi=300, bbox_inches='tight')
                plt.close()
            
            # Category performance chart
            category_data = self.get_category_performance(30)
            if not category_data.empty:
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
                
                # Category views
                category_data_sorted = category_data.sort_values('total_views', ascending=True)
                ax1.barh(category_data_sorted['category'], category_data_sorted['total_views'])
                ax1.set_title('Total Views by Category (30 Days)')
                ax1.set_xlabel('Views')
                
                # Category skip rates
                ax2.bar(category_data['category'], category_data['skip_rate'])
                ax2.set_title('Skip Rate by Category (30 Days)')
                ax2.set_ylabel('Skip Rate (%)')
                ax2.tick_params(axis='x', rotation=45)
                
                plt.tight_layout()
                plt.savefig(f"{output_dir}/category_performance.png", dpi=300, bbox_inches='tight')
                plt.close()
            
            # Performance metrics summary
            metrics = self.get_performance_metrics(30)
            if metrics:
                fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
                
                # Key metrics pie chart
                labels = ['Continues', 'Skips', 'Auto Advances']
                sizes = [metrics['total_continues'], metrics['total_skips'], 
                        metrics.get('total_auto_advances', 0)]
                colors = ['#2ecc71', '#e74c3c', '#f39c12']
                ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
                ax1.set_title('User Actions Distribution')
                
                # Engagement metrics
                engagement_data = [metrics['continue_rate'], metrics['skip_rate'], 
                                 metrics.get('error_rate', 0)]
                engagement_labels = ['Continue Rate', 'Skip Rate', 'Error Rate']
                ax2.bar(engagement_labels, engagement_data, color=['#2ecc71', '#e74c3c', '#e67e22'])
                ax2.set_title('Engagement Metrics (%)')
                ax2.set_ylabel('Rate (%)')
                ax2.tick_params(axis='x', rotation=45)
                
                # Time spent distribution
                ax3.hist([metrics['avg_time_spent']], bins=10, alpha=0.7, color='#3498db')
                ax3.set_title('Average Time Spent (seconds)')
                ax3.set_xlabel('Seconds')
                ax3.set_ylabel('Frequency')
                
                # User activity
                activity_data = [metrics['unique_users'], metrics['total_sessions']]
                activity_labels = ['Unique Users', 'Total Sessions']
                ax4.bar(activity_labels, activity_data, color=['#9b59b6', '#1abc9c'])
                ax4.set_title('User Activity (30 Days)')
                ax4.set_ylabel('Count')
                
                plt.tight_layout()
                plt.savefig(f"{output_dir}/performance_summary.png", dpi=300, bbox_inches='tight')
                plt.close()
            
            logger.info(f"Dashboard charts created in {output_dir}/")
            return True
            
        except Exception as e:
            logger.error(f"Error creating dashboard charts: {e}")
            return False
    
    def generate_report(self, days: int = 30) -> str:
        """Generate a comprehensive analytics report"""
        try:
            metrics = self.get_performance_metrics(days)
            category_data = self.get_category_performance(days)
            retention_data = self.get_user_retention_analysis(days)
            alerts = self.check_alerts()
            
            report = f"""
# Meme Analytics Report - {days} Days

## Executive Summary
- **Total Views**: {metrics.get('total_views', 0):,}
- **Unique Users**: {metrics.get('unique_users', 0):,}
- **Total Sessions**: {metrics.get('total_sessions', 0):,}
- **Overall Skip Rate**: {metrics.get('skip_rate', 0):.1f}%
- **Overall Continue Rate**: {metrics.get('continue_rate', 0):.1f}%
- **Average Time Spent**: {metrics.get('avg_time_spent', 0):.1f} seconds

## Category Performance
"""
            
            if not category_data.empty:
                for _, row in category_data.iterrows():
                    report += f"""
### {row['category'].title()}
- **Views**: {row['total_views']:,}
- **Skip Rate**: {row['skip_rate']:.1f}%
- **Continue Rate**: {row['continue_rate']:.1f}%
- **Unique Users**: {row['unique_users']:,}
- **Avg Time Spent**: {row['avg_time_spent']:.1f}s
"""
            
            report += f"""
## User Retention Analysis
- **Average Interactions per User**: {retention_data.get('avg_interactions', 0):.1f}
- **Average Active Days**: {retention_data.get('avg_active_days', 0):.1f}
- **Total Meme Users**: {retention_data.get('total_meme_users', 0):,}
- **Average Days Since First Use**: {retention_data.get('avg_days_since_first_use', 0):.1f}

## Alerts ({len(alerts)} active)
"""
            
            for alert in alerts:
                report += f"""
### {alert['title']} ({alert['severity'].upper()})
- **Type**: {alert['type']}
- **Description**: {alert['description']}
- **Threshold**: {alert['threshold_value']}
- **Actual Value**: {alert['actual_value']}
"""
            
            report += f"""
## Recommendations
"""
            
            # Generate recommendations based on data
            if metrics.get('skip_rate', 0) > 60:
                report += "- **High Skip Rate**: Consider improving meme relevance or reducing frequency\n"
            
            if metrics.get('avg_time_spent', 0) < 5:
                report += "- **Low Engagement Time**: Memes may not be engaging enough\n"
            
            if not category_data.empty:
                worst_category = category_data.loc[category_data['skip_rate'].idxmax()]
                if worst_category['skip_rate'] > 70:
                    report += f"- **Category Issue**: {worst_category['category'].title()} has high skip rate ({worst_category['skip_rate']:.1f}%)\n"
            
            if len(alerts) > 0:
                report += "- **Active Alerts**: Address the alerts above to improve user experience\n"
            
            report += f"""
---
*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return f"Error generating report: {e}"

def main():
    """Main function for testing the analytics system"""
    # Initialize the analytics system
    analytics = MemeAnalyticsSystem()
    
    # Create some sample events for testing
    sample_events = [
        AnalyticsEvent(
            user_id=1, session_id="test_session_1", meme_id=1, 
            event_type="view", time_spent_seconds=8, device_type="mobile"
        ),
        AnalyticsEvent(
            user_id=1, session_id="test_session_1", meme_id=1, 
            event_type="continue", time_spent_seconds=8, device_type="mobile"
        ),
        AnalyticsEvent(
            user_id=2, session_id="test_session_2", meme_id=2, 
            event_type="view", time_spent_seconds=12, device_type="desktop"
        ),
        AnalyticsEvent(
            user_id=2, session_id="test_session_2", meme_id=2, 
            event_type="skip", time_spent_seconds=12, device_type="desktop"
        ),
    ]
    
    # Track sample events
    for event in sample_events:
        analytics.track_event(event)
    
    # Add sample demographics
    sample_demographics = [
        UserDemographics(user_id=1, age_range="25-34", gender="female", income_range="50k-75k"),
        UserDemographics(user_id=2, age_range="35-44", gender="male", income_range="75k-100k"),
    ]
    
    for demo in sample_demographics:
        analytics.add_user_demographics(demo)
    
    # Generate report
    report = analytics.generate_report(30)
    print(report)
    
    # Create dashboard charts
    analytics.create_dashboard_charts()
    
    # Export data to CSV
    daily_data = analytics.get_daily_engagement_rates(30)
    if not daily_data.empty:
        analytics.export_to_csv(daily_data, "daily_engagement_data.csv")
    
    category_data = analytics.get_category_performance(30)
    if not category_data.empty:
        analytics.export_to_csv(category_data, "category_performance_data.csv")
    
    print("\nAnalytics system test completed successfully!")
    print("Check the following files:")
    print("- meme_analytics.log (log file)")
    print("- analytics_charts/ (dashboard charts)")
    print("- daily_engagement_data.csv")
    print("- category_performance_data.csv")

if __name__ == "__main__":
    main()
