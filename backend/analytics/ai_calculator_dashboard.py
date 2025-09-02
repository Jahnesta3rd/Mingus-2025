"""
AI Calculator Analytics Dashboard Service
Custom dashboard for tracking calculator performance, funnel analysis, and business metrics.
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging

from sqlalchemy import text, func, and_, or_, desc, asc
from sqlalchemy.orm import Session
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from backend.database import get_db_session
from backend.models.analytics import AnalyticsEvent, ConversionEvent
from backend.models.assessment import Assessment
from backend.models.user import User
from backend.analytics.ai_calculator_analytics import EventType, RiskLevel

logger = logging.getLogger(__name__)

@dataclass
class FunnelMetrics:
    """Funnel analysis metrics"""
    step_number: int
    step_name: str
    total_visitors: int
    step_completions: int
    conversion_rate: float
    dropoff_rate: float
    avg_time_on_step: float

@dataclass
class ConversionMetrics:
    """Conversion analysis metrics"""
    risk_level: str
    total_assessments: int
    conversion_offers_viewed: int
    paid_upgrades_clicked: int
    conversion_rate: float
    avg_revenue_per_user: float
    total_revenue: float

@dataclass
class GeographicMetrics:
    """Geographic distribution metrics"""
    country: str
    state: Optional[str]
    city: Optional[str]
    total_assessments: int
    avg_risk_level: float
    conversion_rate: float

class AICalculatorDashboard:
    """Dashboard service for AI calculator analytics"""
    
    def __init__(self):
        self.db_session = get_db_session()
    
    def get_calculator_funnel(self, start_date: datetime, end_date: datetime) -> List[FunnelMetrics]:
        """Get calculator completion funnel by step"""
        try:
            # Get total calculator opens
            total_opens = self.db_session.query(AnalyticsEvent).filter(
                and_(
                    AnalyticsEvent.event_type == EventType.CALCULATOR_OPENED.value,
                    AnalyticsEvent.timestamp >= start_date,
                    AnalyticsEvent.timestamp <= end_date
                )
            ).count()
            
            # Get step completions
            step_completions = self.db_session.query(
                AnalyticsEvent.event_data['step_number'].astext.cast(int).label('step_number'),
                func.count(AnalyticsEvent.id).label('completions'),
                func.avg(AnalyticsEvent.event_data['time_on_step'].astext.cast(float)).label('avg_time')
            ).filter(
                and_(
                    AnalyticsEvent.event_type == EventType.STEP_COMPLETED.value,
                    AnalyticsEvent.timestamp >= start_date,
                    AnalyticsEvent.timestamp <= end_date
                )
            ).group_by(text('step_number')).all()
            
            # Build funnel metrics
            funnel = []
            previous_completions = total_opens
            
            for step in step_completions:
                conversion_rate = (step.completions / previous_completions * 100) if previous_completions > 0 else 0
                dropoff_rate = ((previous_completions - step.completions) / previous_completions * 100) if previous_completions > 0 else 0
                
                funnel.append(FunnelMetrics(
                    step_number=step.step_number,
                    step_name=f"Step {step.step_number}",
                    total_visitors=previous_completions,
                    step_completions=step.completions,
                    conversion_rate=conversion_rate,
                    dropoff_rate=dropoff_rate,
                    avg_time_on_step=step.avg_time or 0
                ))
                
                previous_completions = step.completions
            
            return funnel
            
        except Exception as e:
            logger.error(f"Error getting calculator funnel: {e}")
            return []
    
    def get_conversion_rates_by_risk_level(self, start_date: datetime, end_date: datetime) -> List[ConversionMetrics]:
        """Get conversion rates by risk level and demographic"""
        try:
            # Get assessments by risk level
            assessments = self.db_session.query(
                Assessment.risk_level,
                func.count(Assessment.id).label('total_assessments'),
                func.avg(Assessment.completion_time).label('avg_completion_time')
            ).filter(
                and_(
                    Assessment.created_at >= start_date,
                    Assessment.created_at <= end_date
                )
            ).group_by(Assessment.risk_level).all()
            
            # Get conversion events by risk level
            conversion_events = self.db_session.query(
                AnalyticsEvent.event_data['risk_level'].astext.label('risk_level'),
                AnalyticsEvent.event_type,
                func.count(AnalyticsEvent.id).label('event_count')
            ).filter(
                and_(
                    AnalyticsEvent.event_type.in_([
                        EventType.CONVERSION_OFFER_VIEWED.value,
                        EventType.PAID_UPGRADE_CLICKED.value
                    ]),
                    AnalyticsEvent.timestamp >= start_date,
                    AnalyticsEvent.timestamp <= end_date
                )
            ).group_by(
                text('risk_level'),
                AnalyticsEvent.event_type
            ).all()
            
            # Build conversion metrics
            conversion_metrics = []
            
            for assessment in assessments:
                offers_viewed = 0
                upgrades_clicked = 0
                
                for event in conversion_events:
                    if event.risk_level == assessment.risk_level:
                        if event.event_type == EventType.CONVERSION_OFFER_VIEWED.value:
                            offers_viewed = event.event_count
                        elif event.event_type == EventType.PAID_UPGRADE_CLICKED.value:
                            upgrades_clicked = event.event_count
                
                conversion_rate = (upgrades_clicked / assessment.total_assessments * 100) if assessment.total_assessments > 0 else 0
                
                # Estimate revenue (this would need to be connected to actual payment data)
                avg_revenue = self._estimate_revenue_by_risk_level(assessment.risk_level)
                total_revenue = avg_revenue * upgrades_clicked
                
                conversion_metrics.append(ConversionMetrics(
                    risk_level=assessment.risk_level,
                    total_assessments=assessment.total_assessments,
                    conversion_offers_viewed=offers_viewed,
                    paid_upgrades_clicked=upgrades_clicked,
                    conversion_rate=conversion_rate,
                    avg_revenue_per_user=avg_revenue,
                    total_revenue=total_revenue
                ))
            
            return conversion_metrics
            
        except Exception as e:
            logger.error(f"Error getting conversion rates: {e}")
            return []
    
    def get_popular_job_titles_and_industries(self, start_date: datetime, end_date: datetime, limit: int = 20) -> Dict[str, List[Dict]]:
        """Get popular job titles and industries assessed"""
        try:
            # Get popular job titles
            job_titles = self.db_session.query(
                Assessment.job_title,
                func.count(Assessment.id).label('count'),
                func.avg(Assessment.completion_time).label('avg_completion_time')
            ).filter(
                and_(
                    Assessment.created_at >= start_date,
                    Assessment.created_at <= end_date,
                    Assessment.job_title.isnot(None)
                )
            ).group_by(Assessment.job_title).order_by(desc('count')).limit(limit).all()
            
            # Get popular industries
            industries = self.db_session.query(
                Assessment.industry,
                func.count(Assessment.id).label('count'),
                func.avg(Assessment.completion_time).label('avg_completion_time')
            ).filter(
                and_(
                    Assessment.created_at >= start_date,
                    Assessment.created_at <= end_date,
                    Assessment.industry.isnot(None)
                )
            ).group_by(Assessment.industry).order_by(desc('count')).limit(limit).all()
            
            return {
                'job_titles': [
                    {
                        'title': job.job_title,
                        'count': job.count,
                        'avg_completion_time': job.avg_completion_time or 0
                    } for job in job_titles
                ],
                'industries': [
                    {
                        'industry': industry.industry,
                        'count': industry.count,
                        'avg_completion_time': industry.avg_completion_time or 0
                    } for industry in industries
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting popular jobs/industries: {e}")
            return {'job_titles': [], 'industries': []}
    
    def get_geographic_distribution(self, start_date: datetime, end_date: datetime) -> List[GeographicMetrics]:
        """Get geographic distribution of assessments"""
        try:
            # This would need to be connected to IP geolocation data
            # For now, return mock data structure
            return []
            
        except Exception as e:
            logger.error(f"Error getting geographic distribution: {e}")
            return []
    
    def get_revenue_attribution(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get revenue attribution to calculator traffic"""
        try:
            # Get calculator traffic sources
            traffic_sources = self.db_session.query(
                AnalyticsEvent.event_data['source'].astext.label('source'),
                AnalyticsEvent.event_data['medium'].astext.label('medium'),
                AnalyticsEvent.event_data['campaign'].astext.label('campaign'),
                func.count(AnalyticsEvent.id).label('sessions'),
                func.count(func.distinct(AnalyticsEvent.session_id)).label('unique_sessions')
            ).filter(
                and_(
                    AnalyticsEvent.event_type == EventType.CALCULATOR_OPENED.value,
                    AnalyticsEvent.timestamp >= start_date,
                    AnalyticsEvent.timestamp <= end_date
                )
            ).group_by(
                text('source'),
                text('medium'),
                text('campaign')
            ).all()
            
            # Get conversions by source
            conversions_by_source = self.db_session.query(
                AnalyticsEvent.event_data['source'].astext.label('source'),
                func.count(AnalyticsEvent.id).label('conversions')
            ).filter(
                and_(
                    AnalyticsEvent.event_type == EventType.PAID_UPGRADE_CLICKED.value,
                    AnalyticsEvent.timestamp >= start_date,
                    AnalyticsEvent.timestamp <= end_date
                )
            ).group_by(text('source')).all()
            
            # Calculate attribution metrics
            attribution_data = []
            total_revenue = 0
            
            for source in traffic_sources:
                conversions = next((c.conversions for c in conversions_by_source if c.source == source.source), 0)
                conversion_rate = (conversions / source.unique_sessions * 100) if source.unique_sessions > 0 else 0
                
                # Estimate revenue (would need actual payment data)
                estimated_revenue = conversions * self._estimate_avg_revenue()
                total_revenue += estimated_revenue
                
                attribution_data.append({
                    'source': source.source or 'direct',
                    'medium': source.medium or 'none',
                    'campaign': source.campaign or 'none',
                    'sessions': source.sessions,
                    'unique_sessions': source.unique_sessions,
                    'conversions': conversions,
                    'conversion_rate': conversion_rate,
                    'estimated_revenue': estimated_revenue
                })
            
            return {
                'attribution_data': attribution_data,
                'total_revenue': total_revenue,
                'total_sessions': sum(s.unique_sessions for s in traffic_sources),
                'total_conversions': sum(c.conversions for c in conversions_by_source)
            }
            
        except Exception as e:
            logger.error(f"Error getting revenue attribution: {e}")
            return {}
    
    def generate_funnel_chart(self, funnel_data: List[FunnelMetrics]) -> go.Figure:
        """Generate funnel chart visualization"""
        try:
            fig = go.Figure(go.Funnel(
                y=[step.step_name for step in funnel_data],
                x=[step.step_completions for step in funnel_data],
                textinfo="value+percent initial",
                textposition="inside",
                marker={"color": ["#10b981", "#8A31FF", "#f97316", "#dc2626"]},
                connector={"line": {"color": "royalblue", "width": 3}}
            ))
            
            fig.update_layout(
                title="AI Calculator Completion Funnel",
                font=dict(size=12),
                showlegend=False,
                height=500
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error generating funnel chart: {e}")
            return go.Figure()
    
    def generate_conversion_chart(self, conversion_data: List[ConversionMetrics]) -> go.Figure:
        """Generate conversion rate chart"""
        try:
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Conversion Rates by Risk Level', 'Revenue by Risk Level'),
                vertical_spacing=0.1
            )
            
            # Conversion rate bar chart
            fig.add_trace(
                go.Bar(
                    x=[c.risk_level for c in conversion_data],
                    y=[c.conversion_rate for c in conversion_data],
                    name='Conversion Rate (%)',
                    marker_color='#10b981'
                ),
                row=1, col=1
            )
            
            # Revenue bar chart
            fig.add_trace(
                go.Bar(
                    x=[c.risk_level for c in conversion_data],
                    y=[c.total_revenue for c in conversion_data],
                    name='Total Revenue ($)',
                    marker_color='#8A31FF'
                ),
                row=2, col=1
            )
            
            fig.update_layout(
                title="Conversion Performance by Risk Level",
                height=600,
                showlegend=False
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error generating conversion chart: {e}")
            return go.Figure()
    
    def generate_weekly_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate weekly performance report"""
        try:
            funnel = self.get_calculator_funnel(start_date, end_date)
            conversions = self.get_conversion_rates_by_risk_level(start_date, end_date)
            popular_data = self.get_popular_job_titles_and_industries(start_date, end_date)
            attribution = self.get_revenue_attribution(start_date, end_date)
            
            # Calculate key metrics
            total_assessments = sum(c.total_assessments for c in conversions)
            total_conversions = sum(c.paid_upgrades_clicked for c in conversions)
            overall_conversion_rate = (total_conversions / total_assessments * 100) if total_assessments > 0 else 0
            
            # Get top performing sources
            top_sources = sorted(
                attribution.get('attribution_data', []),
                key=lambda x: x['estimated_revenue'],
                reverse=True
            )[:5]
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'key_metrics': {
                    'total_assessments': total_assessments,
                    'total_conversions': total_conversions,
                    'overall_conversion_rate': overall_conversion_rate,
                    'total_revenue': attribution.get('total_revenue', 0),
                    'total_sessions': attribution.get('total_sessions', 0)
                },
                'funnel_performance': [
                    {
                        'step': step.step_name,
                        'completions': step.step_completions,
                        'conversion_rate': step.conversion_rate,
                        'avg_time': step.avg_time_on_step
                    } for step in funnel
                ],
                'conversion_by_risk': [
                    {
                        'risk_level': c.risk_level,
                        'assessments': c.total_assessments,
                        'conversion_rate': c.conversion_rate,
                        'revenue': c.total_revenue
                    } for c in conversions
                ],
                'top_job_titles': popular_data['job_titles'][:10],
                'top_industries': popular_data['industries'][:10],
                'top_traffic_sources': top_sources
            }
            
        except Exception as e:
            logger.error(f"Error generating weekly report: {e}")
            return {}
    
    def _estimate_revenue_by_risk_level(self, risk_level: str) -> float:
        """Estimate average revenue by risk level"""
        # This would be connected to actual pricing data
        revenue_map = {
            'low': 29.99,
            'medium': 49.99,
            'high': 79.99,
            'critical': 99.99
        }
        return revenue_map.get(risk_level.lower(), 49.99)
    
    def _estimate_avg_revenue(self) -> float:
        """Estimate average revenue per conversion"""
        return 59.99  # Average across all tiers

# Global dashboard instance
ai_calculator_dashboard = AICalculatorDashboard()
