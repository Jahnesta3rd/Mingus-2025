#!/usr/bin/env python3
"""
Risk Success Dashboard for Career Protection System

This module provides comprehensive success tracking and dashboard generation
for risk-based career protection interventions.

Features:
- Career protection effectiveness metrics
- User success story tracking
- ROI analysis for risk interventions
- Success rate calculations
- Dashboard data generation
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SuccessType(Enum):
    """Types of success outcomes"""
    JOB_SAVED = "job_saved"
    PROACTIVE_SWITCH = "proactive_switch"
    PROMOTION_RECEIVED = "promotion_received"
    SKILLS_UPGRADED = "skills_upgraded"
    NETWORK_EXPANDED = "network_expanded"
    INCOME_INCREASED = "income_increased"

@dataclass
class SuccessStory:
    """Data class for user success stories"""
    user_id: str
    success_type: str
    outcome_data: Dict[str, Any]
    original_risk_score: float
    intervention_date: datetime
    success_date: datetime
    impact_score: float
    story_text: str

class RiskSuccessDashboard:
    """
    Success dashboard for risk-based career protection.
    
    Tracks and analyzes the effectiveness of risk interventions
    and generates comprehensive success metrics.
    """
    
    def __init__(self, db_path: str = "backend/analytics/risk_success.db"):
        """Initialize the risk success dashboard"""
        self.db_path = db_path
        self._init_database()
        logger.info("RiskSuccessDashboard initialized successfully")
    
    def _init_database(self):
        """Initialize success tracking database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Success stories table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS success_stories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    success_type TEXT NOT NULL,
                    outcome_data TEXT NOT NULL, -- JSON
                    original_risk_score REAL NOT NULL,
                    intervention_date TIMESTAMP NOT NULL,
                    success_date TIMESTAMP NOT NULL,
                    impact_score REAL DEFAULT 0.0,
                    story_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Career protection metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS career_protection_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    calculation_date TIMESTAMP NOT NULL,
                    period_days INTEGER NOT NULL,
                    metadata TEXT -- JSON
                )
            ''')
            
            # ROI analysis table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS roi_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_date TIMESTAMP NOT NULL,
                    total_interventions INTEGER NOT NULL,
                    successful_interventions INTEGER NOT NULL,
                    total_cost REAL NOT NULL,
                    total_benefit REAL NOT NULL,
                    roi_percentage REAL NOT NULL,
                    period_days INTEGER NOT NULL
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to initialize success dashboard database: {e}")
            raise
    
    async def generate_career_protection_report(self) -> Dict:
        """Generate comprehensive career protection effectiveness report"""
        try:
            # Get success metrics
            success_metrics = await self._calculate_success_metrics()
            
            # Get intervention effectiveness
            intervention_effectiveness = await self._calculate_intervention_effectiveness()
            
            # Get user engagement metrics
            engagement_metrics = await self._calculate_engagement_metrics()
            
            # Get risk reduction metrics
            risk_reduction_metrics = await self._calculate_risk_reduction_metrics()
            
            return {
                'success_metrics': success_metrics,
                'intervention_effectiveness': intervention_effectiveness,
                'engagement_metrics': engagement_metrics,
                'risk_reduction_metrics': risk_reduction_metrics,
                'report_generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate career protection report: {e}")
            return {'error': str(e)}
    
    async def track_user_success_story(self, user_id: str, success_type: str, outcome_data: Dict) -> Dict:
        """Track user success story"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate impact score
            impact_score = self._calculate_impact_score(success_type, outcome_data)
            
            # Generate story text
            story_text = self._generate_story_text(success_type, outcome_data)
            
            cursor.execute('''
                INSERT INTO success_stories 
                (user_id, success_type, outcome_data, original_risk_score, 
                 intervention_date, success_date, impact_score, story_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                success_type,
                json.dumps(outcome_data),
                outcome_data.get('original_risk_score', 0.0),
                outcome_data.get('intervention_date', datetime.utcnow().isoformat()),
                datetime.utcnow().isoformat(),
                impact_score,
                story_text
            ))
            
            story_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                'id': story_id,
                'user_id': user_id,
                'success_type': success_type,
                'impact_score': impact_score,
                'story_text': story_text
            }
            
        except Exception as e:
            logger.error(f"Failed to track success story: {e}")
            return {'error': str(e)}
    
    async def generate_roi_analysis(self) -> Dict:
        """Generate ROI analysis for risk interventions"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get intervention data
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_interventions,
                    SUM(CASE WHEN impact_score > 0.5 THEN 1 ELSE 0 END) as successful_interventions,
                    AVG(impact_score) as avg_impact_score
                FROM success_stories 
                WHERE created_at > datetime('now', '-30 days')
            ''')
            
            row = cursor.fetchone()
            total_interventions = row[0] or 0
            successful_interventions = row[1] or 0
            avg_impact_score = row[2] or 0.0
            
            # Calculate ROI (simplified calculation)
            success_rate = (successful_interventions / total_interventions * 100) if total_interventions > 0 else 0
            estimated_cost_per_intervention = 50.0  # Estimated cost
            estimated_benefit_per_success = 5000.0  # Estimated benefit
            
            total_cost = total_interventions * estimated_cost_per_intervention
            total_benefit = successful_interventions * estimated_benefit_per_success
            roi_percentage = ((total_benefit - total_cost) / total_cost * 100) if total_cost > 0 else 0
            
            # Store ROI analysis
            cursor.execute('''
                INSERT INTO roi_analysis 
                (analysis_date, total_interventions, successful_interventions, 
                 total_cost, total_benefit, roi_percentage, period_days)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.utcnow().isoformat(),
                total_interventions,
                successful_interventions,
                total_cost,
                total_benefit,
                roi_percentage,
                30
            ))
            
            conn.commit()
            conn.close()
            
            return {
                'total_interventions': total_interventions,
                'successful_interventions': successful_interventions,
                'success_rate': round(success_rate, 2),
                'total_cost': round(total_cost, 2),
                'total_benefit': round(total_benefit, 2),
                'roi_percentage': round(roi_percentage, 2),
                'avg_impact_score': round(avg_impact_score, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate ROI analysis: {e}")
            return {'error': str(e)}
    
    async def get_recent_success_stories(self, limit: int = 10) -> List[Dict]:
        """Get recent success stories"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, success_type, outcome_data, impact_score, 
                       story_text, created_at
                FROM success_stories 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            stories = []
            for row in cursor.fetchall():
                stories.append({
                    'user_id': row[0],
                    'success_type': row[1],
                    'outcome_data': json.loads(row[2]),
                    'impact_score': row[3],
                    'story_text': row[4],
                    'created_at': row[5]
                })
            
            conn.close()
            return stories
            
        except Exception as e:
            logger.error(f"Failed to get recent success stories: {e}")
            return []
    
    async def _calculate_success_metrics(self) -> Dict:
        """Calculate success metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get overall success rate
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_stories,
                    AVG(impact_score) as avg_impact,
                    COUNT(DISTINCT user_id) as unique_users
                FROM success_stories 
                WHERE created_at > datetime('now', '-30 days')
            ''')
            
            row = cursor.fetchone()
            total_stories = row[0] or 0
            avg_impact = row[1] or 0.0
            unique_users = row[2] or 0
            
            # Get success by type
            cursor.execute('''
                SELECT success_type, COUNT(*) as count, AVG(impact_score) as avg_impact
                FROM success_stories 
                WHERE created_at > datetime('now', '-30 days')
                GROUP BY success_type
            ''')
            
            success_by_type = {}
            for row in cursor.fetchall():
                success_by_type[row[0]] = {
                    'count': row[1],
                    'avg_impact': round(row[2], 2)
                }
            
            conn.close()
            
            return {
                'total_success_stories': total_stories,
                'avg_impact_score': round(avg_impact, 2),
                'unique_users_with_success': unique_users,
                'success_by_type': success_by_type
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate success metrics: {e}")
            return {}
    
    async def _calculate_intervention_effectiveness(self) -> Dict:
        """Calculate intervention effectiveness metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get intervention effectiveness over time
            cursor.execute('''
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as interventions,
                    AVG(impact_score) as avg_impact
                FROM success_stories 
                WHERE created_at > datetime('now', '-30 days')
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            ''')
            
            daily_effectiveness = []
            for row in cursor.fetchall():
                daily_effectiveness.append({
                    'date': row[0],
                    'interventions': row[1],
                    'avg_impact': round(row[2], 2)
                })
            
            conn.close()
            
            return {
                'daily_effectiveness': daily_effectiveness,
                'trend_direction': 'improving' if len(daily_effectiveness) > 1 and 
                                 daily_effectiveness[0]['avg_impact'] > daily_effectiveness[-1]['avg_impact'] 
                                 else 'stable'
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate intervention effectiveness: {e}")
            return {}
    
    async def _calculate_engagement_metrics(self) -> Dict:
        """Calculate user engagement metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get engagement metrics
            cursor.execute('''
                SELECT 
                    COUNT(DISTINCT user_id) as active_users,
                    COUNT(*) as total_activities,
                    AVG(impact_score) as avg_engagement
                FROM success_stories 
                WHERE created_at > datetime('now', '-7 days')
            ''')
            
            row = cursor.fetchone()
            active_users = row[0] or 0
            total_activities = row[1] or 0
            avg_engagement = row[2] or 0.0
            
            conn.close()
            
            return {
                'active_users_7d': active_users,
                'total_activities_7d': total_activities,
                'avg_engagement_score': round(avg_engagement, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate engagement metrics: {e}")
            return {}
    
    async def _calculate_risk_reduction_metrics(self) -> Dict:
        """Calculate risk reduction metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get risk reduction data
            cursor.execute('''
                SELECT 
                    AVG(original_risk_score) as avg_original_risk,
                    AVG(impact_score) as avg_risk_reduction,
                    COUNT(*) as interventions_count
                FROM success_stories 
                WHERE created_at > datetime('now', '-30 days')
            ''')
            
            row = cursor.fetchone()
            avg_original_risk = row[0] or 0.0
            avg_risk_reduction = row[1] or 0.0
            interventions_count = row[2] or 0
            
            conn.close()
            
            return {
                'avg_original_risk_score': round(avg_original_risk, 2),
                'avg_risk_reduction': round(avg_risk_reduction, 2),
                'total_risk_interventions': interventions_count
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate risk reduction metrics: {e}")
            return {}
    
    def _calculate_impact_score(self, success_type: str, outcome_data: Dict) -> float:
        """Calculate impact score for success story"""
        base_scores = {
            'job_saved': 0.9,
            'proactive_switch': 0.8,
            'promotion_received': 0.7,
            'skills_upgraded': 0.6,
            'network_expanded': 0.5,
            'income_increased': 0.8
        }
        
        base_score = base_scores.get(success_type, 0.5)
        
        # Adjust based on outcome data
        if 'income_increase_percentage' in outcome_data:
            income_increase = outcome_data['income_increase_percentage']
            if income_increase > 20:
                base_score += 0.2
            elif income_increase > 10:
                base_score += 0.1
        
        if 'time_to_success_days' in outcome_data:
            time_to_success = outcome_data['time_to_success_days']
            if time_to_success < 30:
                base_score += 0.1
            elif time_to_success > 180:
                base_score -= 0.1
        
        return min(max(base_score, 0.0), 1.0)
    
    def _generate_story_text(self, success_type: str, outcome_data: Dict) -> str:
        """Generate story text for success story"""
        templates = {
            'job_saved': "Successfully protected job through proactive risk management and skill development.",
            'proactive_switch': "Made strategic career move before risk materialized, securing better position.",
            'promotion_received': "Received promotion after implementing risk mitigation strategies.",
            'skills_upgraded': "Enhanced skills and marketability through targeted learning and development.",
            'network_expanded': "Built valuable professional network to increase career resilience.",
            'income_increased': "Achieved income growth through strategic career moves and skill development."
        }
        
        base_story = templates.get(success_type, "Achieved positive career outcome through risk management.")
        
        # Add specific details if available
        if 'income_increase_percentage' in outcome_data:
            base_story += f" Income increased by {outcome_data['income_increase_percentage']}%."
        
        if 'time_to_success_days' in outcome_data:
            days = outcome_data['time_to_success_days']
            base_story += f" Success achieved in {days} days."
        
        return base_story