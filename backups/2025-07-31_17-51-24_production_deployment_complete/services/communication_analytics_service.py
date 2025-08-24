"""
Communication Analytics Service
Handles real-time metrics tracking, user engagement analysis, and financial impact measurement
"""

import uuid
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, extract
import json
import statistics
from decimal import Decimal

from ..models.communication_analytics import (
    CommunicationMetrics, UserEngagementAnalytics, FinancialImpactMetrics,
    ABTestResults, CommunicationQueueStatus, AnalyticsAlert, AnalyticsReport,
    UserSegmentPerformance, MetricType, ChannelType, UserSegment, FinancialOutcome
)
from ..models.communication_preferences import (
    CommunicationDeliveryLog, AlertType, CommunicationChannel
)
from ..models.user import User
from ..database import get_db_session

logger = logging.getLogger(__name__)


class CommunicationAnalyticsService:
    """Service for communication analytics and effectiveness tracking"""
    
    def __init__(self):
        self.db: Session = get_db_session()
    
    def track_delivery_metrics(self, delivery_log: CommunicationDeliveryLog) -> None:
        """
        Track delivery metrics for a communication
        
        Args:
            delivery_log: Communication delivery log entry
        """
        try:
            # Get user segment
            user_segment = self._get_user_segment(delivery_log.user_id)
            
            # Get time dimensions
            sent_time = delivery_log.sent_at or datetime.utcnow()
            time_dims = self._get_time_dimensions(sent_time)
            
            # Calculate cost (simplified - would integrate with actual cost data)
            cost = self._calculate_message_cost(delivery_log.channel, delivery_log.alert_type)
            
            # Update or create metrics record
            metrics = self._get_or_create_metrics_record(
                delivery_log.channel,
                delivery_log.alert_type,
                user_segment,
                time_dims
            )
            
            # Update metrics
            metrics.total_sent += 1
            if delivery_log.status == 'delivered':
                metrics.total_delivered += 1
            if delivery_log.opened_at:
                metrics.total_opened += 1
            if delivery_log.clicked_at:
                metrics.total_clicked += 1
            if delivery_log.responded_at:
                metrics.total_responded += 1
            
            # Recalculate rates
            self._recalculate_metrics_rates(metrics)
            
            # Update cost metrics
            metrics.total_cost += cost
            metrics.cost_per_message = metrics.total_cost / metrics.total_sent if metrics.total_sent > 0 else 0
            
            self.db.commit()
            
            logger.info(f"Tracked delivery metrics for message {delivery_log.id}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error tracking delivery metrics: {e}")
            raise
    
    def update_user_engagement(self, user_id: str, delivery_log: CommunicationDeliveryLog) -> None:
        """
        Update user engagement analytics
        
        Args:
            user_id: User ID
            delivery_log: Communication delivery log entry
        """
        try:
            # Get or create user engagement analytics
            analytics = self.db.query(UserEngagementAnalytics).filter(
                UserEngagementAnalytics.user_id == user_id
            ).first()
            
            if not analytics:
                analytics = UserEngagementAnalytics(
                    id=str(uuid.uuid4()),
                    user_id=user_id
                )
                self.db.add(analytics)
            
            # Update engagement counts
            analytics.total_messages_received += 1
            
            # Check if user engaged
            engaged = False
            if delivery_log.opened_at or delivery_log.clicked_at or delivery_log.responded_at:
                analytics.total_messages_engaged += 1
                engaged = True
            else:
                analytics.total_messages_ignored += 1
            
            # Update channel-specific engagement
            if engaged:
                if delivery_log.channel == CommunicationChannel.SMS:
                    analytics.sms_engagement_count += 1
                elif delivery_log.channel == CommunicationChannel.EMAIL:
                    analytics.email_engagement_count += 1
                elif delivery_log.channel == CommunicationChannel.PUSH:
                    analytics.push_engagement_count += 1
                elif delivery_log.channel == CommunicationChannel.IN_APP:
                    analytics.in_app_engagement_count += 1
            
            # Update time-based engagement patterns
            if engaged:
                self._update_time_based_engagement(analytics, delivery_log.sent_at)
            
            # Update alert type engagement
            self._update_alert_type_engagement(analytics, delivery_log.alert_type, engaged)
            
            # Update response time analysis
            if delivery_log.responded_at and delivery_log.sent_at:
                response_time = (delivery_log.responded_at - delivery_log.sent_at).total_seconds() / 60
                self._update_response_time_analysis(analytics, response_time)
            
            # Update engagement trends
            self._update_engagement_trends(analytics)
            
            # Update engagement score
            analytics.engagement_score = self._calculate_engagement_score(analytics)
            
            analytics.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Updated engagement analytics for user {user_id}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user engagement: {e}")
            raise
    
    def track_financial_impact(self, user_id: str, outcome_type: FinancialOutcome, 
                             outcome_value: float = None, message_id: str = None) -> None:
        """
        Track financial impact correlation with communication
        
        Args:
            user_id: User ID
            outcome_type: Type of financial outcome
            outcome_value: Dollar value of the outcome
            message_id: Related message ID if applicable
        """
        try:
            # Get user's recent communication history
            recent_communication = self.db.query(CommunicationDeliveryLog).filter(
                and_(
                    CommunicationDeliveryLog.user_id == user_id,
                    CommunicationDeliveryLog.sent_at >= datetime.utcnow() - timedelta(days=30)
                )
            ).order_by(desc(CommunicationDeliveryLog.sent_at)).first()
            
            # Determine attribution
            attributed_to_communication = False
            attribution_confidence = 0.0
            attribution_reason = None
            
            if recent_communication:
                days_since_communication = (datetime.utcnow() - recent_communication.sent_at).days
                
                # Simple attribution logic (would be more sophisticated in production)
                if days_since_communication <= 7:
                    attributed_to_communication = True
                    attribution_confidence = max(0, 100 - (days_since_communication * 10))
                    attribution_reason = f"Outcome occurred {days_since_communication} days after communication"
            
            # Create financial impact record
            impact = FinancialImpactMetrics(
                id=str(uuid.uuid4()),
                user_id=user_id,
                outcome_type=outcome_type,
                outcome_value=Decimal(str(outcome_value)) if outcome_value else None,
                outcome_date=datetime.utcnow(),
                communication_channel=recent_communication.channel if recent_communication else None,
                alert_type=recent_communication.alert_type.value if recent_communication else None,
                message_id=message_id or (recent_communication.message_id if recent_communication else None),
                days_since_last_communication=days_since_communication if recent_communication else None,
                user_engaged_with_communication=recent_communication.opened_at is not None if recent_communication else False,
                attributed_to_communication=attributed_to_communication,
                attribution_confidence=attribution_confidence,
                attribution_reason=attribution_reason
            )
            
            self.db.add(impact)
            self.db.commit()
            
            logger.info(f"Tracked financial impact for user {user_id}: {outcome_type.value}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error tracking financial impact: {e}")
            raise
    
    def get_real_time_metrics(self, channel: ChannelType = None, 
                            alert_type: str = None, time_period: str = "24h") -> Dict[str, Any]:
        """
        Get real-time communication metrics
        
        Args:
            channel: Filter by channel
            alert_type: Filter by alert type
            time_period: Time period (1h, 24h, 7d, 30d)
            
        Returns:
            Real-time metrics dictionary
        """
        try:
            # Calculate time range
            end_time = datetime.utcnow()
            if time_period == "1h":
                start_time = end_time - timedelta(hours=1)
            elif time_period == "24h":
                start_time = end_time - timedelta(days=1)
            elif time_period == "7d":
                start_time = end_time - timedelta(days=7)
            elif time_period == "30d":
                start_time = end_time - timedelta(days=30)
            else:
                start_time = end_time - timedelta(days=1)
            
            # Build query
            query = self.db.query(CommunicationMetrics).filter(
                and_(
                    CommunicationMetrics.date >= start_time,
                    CommunicationMetrics.date <= end_time
                )
            )
            
            if channel:
                query = query.filter(CommunicationMetrics.channel == channel)
            if alert_type:
                query = query.filter(CommunicationMetrics.alert_type == alert_type)
            
            metrics = query.all()
            
            # Aggregate metrics
            total_sent = sum(m.total_sent for m in metrics)
            total_delivered = sum(m.total_delivered for m in metrics)
            total_opened = sum(m.total_opened for m in metrics)
            total_clicked = sum(m.total_clicked for m in metrics)
            total_responded = sum(m.total_responded for m in metrics)
            total_cost = sum(float(m.total_cost) for m in metrics)
            
            # Calculate rates
            delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
            open_rate = (total_opened / total_delivered * 100) if total_delivered > 0 else 0
            click_rate = (total_clicked / total_opened * 100) if total_opened > 0 else 0
            response_rate = (total_responded / total_delivered * 100) if total_delivered > 0 else 0
            cost_per_message = total_cost / total_sent if total_sent > 0 else 0
            
            return {
                'time_period': time_period,
                'total_sent': total_sent,
                'total_delivered': total_delivered,
                'total_opened': total_opened,
                'total_clicked': total_clicked,
                'total_responded': total_responded,
                'delivery_rate': round(delivery_rate, 2),
                'open_rate': round(open_rate, 2),
                'click_rate': round(click_rate, 2),
                'response_rate': round(response_rate, 2),
                'total_cost': round(total_cost, 4),
                'cost_per_message': round(cost_per_message, 4),
                'channel_breakdown': self._get_channel_breakdown(metrics),
                'alert_type_breakdown': self._get_alert_type_breakdown(metrics)
            }
            
        except Exception as e:
            logger.error(f"Error getting real-time metrics: {e}")
            raise
    
    def get_user_engagement_analysis(self, user_id: str = None, 
                                   segment: UserSegment = None) -> Dict[str, Any]:
        """
        Get user engagement analysis
        
        Args:
            user_id: Specific user ID (optional)
            segment: User segment filter (optional)
            
        Returns:
            User engagement analysis dictionary
        """
        try:
            query = self.db.query(UserEngagementAnalytics)
            
            if user_id:
                query = query.filter(UserEngagementAnalytics.user_id == user_id)
            
            analytics = query.all()
            
            if not analytics:
                return {
                    'total_users': 0,
                    'avg_engagement_score': 0,
                    'engagement_distribution': {},
                    'channel_preferences': {},
                    'time_patterns': {},
                    'frequency_analysis': {}
                }
            
            # Calculate aggregate metrics
            total_users = len(analytics)
            avg_engagement_score = sum(a.engagement_score for a in analytics) / total_users
            
            # Engagement distribution
            engagement_distribution = {
                'high': len([a for a in analytics if a.engagement_score >= 80]),
                'medium': len([a for a in analytics if 40 <= a.engagement_score < 80]),
                'low': len([a for a in analytics if a.engagement_score < 40])
            }
            
            # Channel preferences
            total_sms = sum(a.sms_engagement_count for a in analytics)
            total_email = sum(a.email_engagement_count for a in analytics)
            total_push = sum(a.push_engagement_count for a in analytics)
            total_in_app = sum(a.in_app_engagement_count for a in analytics)
            
            channel_preferences = {
                'sms': total_sms,
                'email': total_email,
                'push': total_push,
                'in_app': total_in_app
            }
            
            # Time patterns (aggregate from all users)
            time_patterns = self._aggregate_time_patterns(analytics)
            
            # Frequency analysis
            frequency_analysis = {
                'optimal_frequency': self._get_most_common_frequency(analytics),
                'frequency_effectiveness': sum(a.frequency_effectiveness for a in analytics) / total_users
            }
            
            return {
                'total_users': total_users,
                'avg_engagement_score': round(avg_engagement_score, 2),
                'engagement_distribution': engagement_distribution,
                'channel_preferences': channel_preferences,
                'time_patterns': time_patterns,
                'frequency_analysis': frequency_analysis,
                'engagement_trends': self._get_engagement_trends_summary(analytics)
            }
            
        except Exception as e:
            logger.error(f"Error getting user engagement analysis: {e}")
            raise
    
    def get_financial_impact_analysis(self, outcome_type: FinancialOutcome = None,
                                    time_period: str = "30d") -> Dict[str, Any]:
        """
        Get financial impact analysis
        
        Args:
            outcome_type: Filter by outcome type
            time_period: Time period for analysis
            
        Returns:
            Financial impact analysis dictionary
        """
        try:
            # Calculate time range
            end_time = datetime.utcnow()
            if time_period == "7d":
                start_time = end_time - timedelta(days=7)
            elif time_period == "30d":
                start_time = end_time - timedelta(days=30)
            elif time_period == "90d":
                start_time = end_time - timedelta(days=90)
            else:
                start_time = end_time - timedelta(days=30)
            
            # Build query
            query = self.db.query(FinancialImpactMetrics).filter(
                and_(
                    FinancialImpactMetrics.outcome_date >= start_time,
                    FinancialImpactMetrics.outcome_date <= end_time
                )
            )
            
            if outcome_type:
                query = query.filter(FinancialImpactMetrics.outcome_type == outcome_type)
            
            impacts = query.all()
            
            if not impacts:
                return {
                    'total_outcomes': 0,
                    'total_value': 0,
                    'attribution_rate': 0,
                    'outcome_breakdown': {},
                    'channel_effectiveness': {},
                    'engagement_correlation': {}
                }
            
            # Calculate metrics
            total_outcomes = len(impacts)
            total_value = sum(float(i.outcome_value or 0) for i in impacts)
            attributed_outcomes = len([i for i in impacts if i.attributed_to_communication])
            attribution_rate = (attributed_outcomes / total_outcomes * 100) if total_outcomes > 0 else 0
            
            # Outcome breakdown
            outcome_breakdown = {}
            for impact in impacts:
                outcome_type_str = impact.outcome_type.value
                if outcome_type_str not in outcome_breakdown:
                    outcome_breakdown[outcome_type_str] = {
                        'count': 0,
                        'total_value': 0,
                        'attributed_count': 0
                    }
                outcome_breakdown[outcome_type_str]['count'] += 1
                outcome_breakdown[outcome_type_str]['total_value'] += float(impact.outcome_value or 0)
                if impact.attributed_to_communication:
                    outcome_breakdown[outcome_type_str]['attributed_count'] += 1
            
            # Channel effectiveness
            channel_effectiveness = {}
            for impact in impacts:
                if impact.communication_channel:
                    channel = impact.communication_channel.value
                    if channel not in channel_effectiveness:
                        channel_effectiveness[channel] = {
                            'total_outcomes': 0,
                            'attributed_outcomes': 0,
                            'total_value': 0
                        }
                    channel_effectiveness[channel]['total_outcomes'] += 1
                    channel_effectiveness[channel]['total_value'] += float(impact.outcome_value or 0)
                    if impact.attributed_to_communication:
                        channel_effectiveness[channel]['attributed_outcomes'] += 1
            
            # Engagement correlation
            engaged_outcomes = len([i for i in impacts if i.user_engaged_with_communication])
            engagement_correlation = {
                'engaged_outcomes': engaged_outcomes,
                'engagement_rate': (engaged_outcomes / total_outcomes * 100) if total_outcomes > 0 else 0
            }
            
            return {
                'total_outcomes': total_outcomes,
                'total_value': round(total_value, 2),
                'attribution_rate': round(attribution_rate, 2),
                'outcome_breakdown': outcome_breakdown,
                'channel_effectiveness': channel_effectiveness,
                'engagement_correlation': engagement_correlation,
                'avg_attribution_confidence': sum(i.attribution_confidence for i in impacts) / total_outcomes if total_outcomes > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting financial impact analysis: {e}")
            raise
    
    def update_queue_status(self, queue_name: str, channel: ChannelType, 
                          queue_depth: int, messages_processed: int = 0,
                          messages_failed: int = 0, error_rate: float = 0.0) -> None:
        """
        Update communication queue status
        
        Args:
            queue_name: Name of the queue
            channel: Communication channel
            queue_depth: Current queue depth
            messages_processed: Messages processed since last update
            messages_failed: Messages failed since last update
            error_rate: Current error rate
        """
        try:
            # Get or create queue status
            queue_status = self.db.query(CommunicationQueueStatus).filter(
                CommunicationQueueStatus.queue_name == queue_name
            ).first()
            
            if not queue_status:
                queue_status = CommunicationQueueStatus(
                    id=str(uuid.uuid4()),
                    queue_name=queue_name,
                    channel=channel
                )
                self.db.add(queue_status)
            
            # Update metrics
            queue_status.queue_depth = queue_depth
            queue_status.messages_processed += messages_processed
            queue_status.messages_failed += messages_failed
            queue_status.error_rate = error_rate
            queue_status.last_health_check = datetime.utcnow()
            
            # Update health status
            queue_status.is_healthy = error_rate < 10.0 and queue_depth < 1000
            queue_status.health_score = max(0, 100 - error_rate - (queue_depth / 10))
            
            queue_status.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Updated queue status for {queue_name}: depth={queue_depth}, health={queue_status.health_score}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating queue status: {e}")
            raise
    
    def check_analytics_alerts(self) -> List[AnalyticsAlert]:
        """
        Check for analytics alerts based on current metrics
        
        Returns:
            List of active alerts
        """
        try:
            alerts = []
            
            # Get current metrics
            current_metrics = self.get_real_time_metrics(time_period="24h")
            
            # Check delivery rate alert
            if current_metrics['delivery_rate'] < 85.0:
                alert = self._create_alert(
                    'low_delivery_rate',
                    'high',
                    'delivery_rate',
                    85.0,
                    current_metrics['delivery_rate'],
                    '<',
                    f"Low delivery rate: {current_metrics['delivery_rate']}%",
                    "Delivery rate has fallen below 85% threshold"
                )
                alerts.append(alert)
            
            # Check cost threshold alert
            if current_metrics['cost_per_message'] > 2.0:
                alert = self._create_alert(
                    'cost_threshold_breach',
                    'critical',
                    'cost_per_message',
                    2.0,
                    current_metrics['cost_per_message'],
                    '>',
                    f"Cost threshold breached: ${current_metrics['cost_per_message']}",
                    "Cost per message has exceeded $2.00 threshold"
                )
                alerts.append(alert)
            
            # Check queue depth alerts
            queue_statuses = self.db.query(CommunicationQueueStatus).all()
            for queue in queue_statuses:
                if queue.queue_depth > 1000:
                    alert = self._create_alert(
                        'queue_depth_alert',
                        'medium',
                        'queue_depth',
                        1000,
                        queue.queue_depth,
                        '>',
                        f"High queue depth: {queue.queue_name} has {queue.queue_depth} messages",
                        f"Queue {queue.queue_name} depth has exceeded 1000 messages"
                    )
                    alerts.append(alert)
                
                if queue.error_rate > 10.0:
                    alert = self._create_alert(
                        'error_rate_alert',
                        'high',
                        'error_rate',
                        10.0,
                        queue.error_rate,
                        '>',
                        f"High error rate: {queue.queue_name} has {queue.error_rate}% errors",
                        f"Queue {queue.queue_name} error rate has exceeded 10%"
                    )
                    alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking analytics alerts: {e}")
            raise
    
    def generate_weekly_report(self) -> AnalyticsReport:
        """
        Generate weekly communication performance report
        
        Returns:
            AnalyticsReport object
        """
        try:
            # Get metrics for the past week
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=7)
            
            # Get real-time metrics
            metrics = self.get_real_time_metrics(time_period="7d")
            
            # Get user engagement analysis
            engagement = self.get_user_engagement_analysis()
            
            # Get financial impact analysis
            financial_impact = self.get_financial_impact_analysis(time_period="7d")
            
            # Generate insights
            insights = self._generate_insights(metrics, engagement, financial_impact)
            
            # Create report
            report = AnalyticsReport(
                id=str(uuid.uuid4()),
                report_type='weekly_performance',
                report_period='weekly',
                report_date=end_date,
                channels_included=['sms', 'email', 'push', 'in_app'],
                total_messages_sent=metrics['total_sent'],
                total_engagements=metrics['total_opened'] + metrics['total_clicked'],
                total_conversions=metrics['total_responded'],
                total_revenue_impact=Decimal(str(financial_impact['total_value'])),
                total_cost=Decimal(str(metrics['total_cost'])),
                avg_delivery_rate=metrics['delivery_rate'],
                avg_engagement_rate=engagement['avg_engagement_score'],
                avg_conversion_rate=metrics['response_rate'],
                avg_cost_per_engagement=Decimal(str(metrics['cost_per_message'])),
                overall_roi=financial_impact['total_value'] / float(metrics['total_cost']) if metrics['total_cost'] > 0 else 0,
                top_performing_channel=self._get_top_performing_channel(metrics['channel_breakdown']),
                top_performing_alert_type=self._get_top_performing_alert_type(metrics['alert_type_breakdown']),
                most_engaged_segment='engaged',  # Would calculate from segment data
                key_insights=insights,
                report_data={
                    'metrics': metrics,
                    'engagement': engagement,
                    'financial_impact': financial_impact
                }
            )
            
            self.db.add(report)
            self.db.commit()
            
            logger.info(f"Generated weekly report: {report.id}")
            return report
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error generating weekly report: {e}")
            raise
    
    # Helper methods
    def _get_user_segment(self, user_id: str) -> UserSegment:
        """Get user segment based on user behavior"""
        # Simplified logic - would be more sophisticated in production
        return UserSegment.ENGAGED
    
    def _get_time_dimensions(self, timestamp: datetime) -> Dict[str, int]:
        """Get time dimensions from timestamp"""
        return {
            'date': timestamp.date(),
            'hour': timestamp.hour,
            'day_of_week': timestamp.weekday(),
            'week_of_year': timestamp.isocalendar()[1],
            'month': timestamp.month,
            'quarter': (timestamp.month - 1) // 3 + 1,
            'year': timestamp.year
        }
    
    def _calculate_message_cost(self, channel: CommunicationChannel, alert_type: AlertType) -> float:
        """Calculate message cost (simplified)"""
        base_costs = {
            CommunicationChannel.SMS: 0.05,
            CommunicationChannel.EMAIL: 0.01,
            CommunicationChannel.PUSH: 0.001,
            CommunicationChannel.IN_APP: 0.0001
        }
        return base_costs.get(channel, 0.01)
    
    def _get_or_create_metrics_record(self, channel: CommunicationChannel, alert_type: AlertType,
                                    user_segment: UserSegment, time_dims: Dict[str, Any]) -> CommunicationMetrics:
        """Get or create metrics record"""
        metrics = self.db.query(CommunicationMetrics).filter(
            and_(
                CommunicationMetrics.channel == ChannelType(channel.value),
                CommunicationMetrics.alert_type == alert_type.value,
                CommunicationMetrics.user_segment == user_segment,
                CommunicationMetrics.date == time_dims['date'],
                CommunicationMetrics.hour == time_dims['hour']
            )
        ).first()
        
        if not metrics:
            metrics = CommunicationMetrics(
                id=str(uuid.uuid4()),
                metric_type=MetricType.DELIVERY_RATE,
                channel=ChannelType(channel.value),
                alert_type=alert_type.value,
                user_segment=user_segment,
                date=time_dims['date'],
                hour=time_dims['hour'],
                day_of_week=time_dims['day_of_week'],
                week_of_year=time_dims['week_of_year'],
                month=time_dims['month'],
                quarter=time_dims['quarter'],
                year=time_dims['year']
            )
            self.db.add(metrics)
        
        return metrics
    
    def _recalculate_metrics_rates(self, metrics: CommunicationMetrics) -> None:
        """Recalculate metrics rates"""
        if metrics.total_sent > 0:
            metrics.delivery_rate = (metrics.total_delivered / metrics.total_sent) * 100
        if metrics.total_delivered > 0:
            metrics.open_rate = (metrics.total_opened / metrics.total_delivered) * 100
            metrics.response_rate = (metrics.total_responded / metrics.total_delivered) * 100
        if metrics.total_opened > 0:
            metrics.click_rate = (metrics.total_clicked / metrics.total_opened) * 100
        if metrics.total_delivered > 0:
            metrics.engagement_rate = ((metrics.total_opened + metrics.total_clicked) / metrics.total_delivered) * 100
    
    def _update_time_based_engagement(self, analytics: UserEngagementAnalytics, sent_time: datetime) -> None:
        """Update time-based engagement patterns"""
        hour = sent_time.hour
        day = sent_time.weekday()
        month = sent_time.month
        
        # Update hour-based engagement
        if not analytics.engagement_by_hour:
            analytics.engagement_by_hour = {}
        analytics.engagement_by_hour[str(hour)] = analytics.engagement_by_hour.get(str(hour), 0) + 1
        
        # Update day-based engagement
        if not analytics.engagement_by_day:
            analytics.engagement_by_day = {}
        analytics.engagement_by_day[str(day)] = analytics.engagement_by_day.get(str(day), 0) + 1
        
        # Update month-based engagement
        if not analytics.engagement_by_month:
            analytics.engagement_by_month = {}
        analytics.engagement_by_month[str(month)] = analytics.engagement_by_month.get(str(month), 0) + 1
    
    def _update_alert_type_engagement(self, analytics: UserEngagementAnalytics, alert_type: AlertType, engaged: bool) -> None:
        """Update alert type engagement"""
        if not analytics.alert_type_engagement:
            analytics.alert_type_engagement = {}
        
        alert_type_str = alert_type.value
        if alert_type_str not in analytics.alert_type_engagement:
            analytics.alert_type_engagement[alert_type_str] = {'engaged': 0, 'total': 0, 'rate': 0}
        
        analytics.alert_type_engagement[alert_type_str]['total'] += 1
        if engaged:
            analytics.alert_type_engagement[alert_type_str]['engaged'] += 1
        
        # Calculate rate
        total = analytics.alert_type_engagement[alert_type_str]['total']
        engaged_count = analytics.alert_type_engagement[alert_type_str]['engaged']
        analytics.alert_type_engagement[alert_type_str]['rate'] = (engaged_count / total * 100) if total > 0 else 0
    
    def _update_response_time_analysis(self, analytics: UserEngagementAnalytics, response_time: float) -> None:
        """Update response time analysis"""
        if analytics.avg_response_time_minutes == 0:
            analytics.avg_response_time_minutes = response_time
        else:
            # Simple moving average
            analytics.avg_response_time_minutes = (analytics.avg_response_time_minutes + response_time) / 2
        
        # Update distribution
        if not analytics.response_time_distribution:
            analytics.response_time_distribution = {}
        
        if response_time <= 5:
            time_range = "0-5min"
        elif response_time <= 30:
            time_range = "5-30min"
        elif response_time <= 60:
            time_range = "30-60min"
        else:
            time_range = "60min+"
        
        analytics.response_time_distribution[time_range] = analytics.response_time_distribution.get(time_range, 0) + 1
    
    def _update_engagement_trends(self, analytics: UserEngagementAnalytics) -> None:
        """Update engagement trends"""
        # Simplified trend calculation
        if analytics.engagement_score > 80:
            analytics.engagement_trend = "increasing"
        elif analytics.engagement_score < 40:
            analytics.engagement_trend = "decreasing"
        else:
            analytics.engagement_trend = "stable"
    
    def _calculate_engagement_score(self, analytics: UserEngagementAnalytics) -> float:
        """Calculate engagement score (0-100)"""
        if analytics.total_messages_received == 0:
            return 0.0
        
        engagement_rate = (analytics.total_messages_engaged / analytics.total_messages_received) * 100
        
        # Factor in response time (faster responses = higher score)
        time_factor = max(0, 100 - analytics.avg_response_time_minutes)
        
        # Factor in channel diversity (more channels = higher score)
        channels_used = sum([
            1 if analytics.sms_engagement_count > 0 else 0,
            1 if analytics.email_engagement_count > 0 else 0,
            1 if analytics.push_engagement_count > 0 else 0,
            1 if analytics.in_app_engagement_count > 0 else 0
        ])
        channel_factor = channels_used * 10
        
        return min(100, (engagement_rate * 0.6) + (time_factor * 0.2) + (channel_factor * 0.2))
    
    def _get_channel_breakdown(self, metrics: List[CommunicationMetrics]) -> Dict[str, Any]:
        """Get channel breakdown from metrics"""
        breakdown = {}
        for metric in metrics:
            channel = metric.channel.value
            if channel not in breakdown:
                breakdown[channel] = {
                    'sent': 0,
                    'delivered': 0,
                    'opened': 0,
                    'clicked': 0,
                    'delivery_rate': 0,
                    'open_rate': 0
                }
            
            breakdown[channel]['sent'] += metric.total_sent
            breakdown[channel]['delivered'] += metric.total_delivered
            breakdown[channel]['opened'] += metric.total_opened
            breakdown[channel]['clicked'] += metric.total_clicked
        
        # Calculate rates
        for channel in breakdown:
            if breakdown[channel]['sent'] > 0:
                breakdown[channel]['delivery_rate'] = (breakdown[channel]['delivered'] / breakdown[channel]['sent']) * 100
            if breakdown[channel]['delivered'] > 0:
                breakdown[channel]['open_rate'] = (breakdown[channel]['opened'] / breakdown[channel]['delivered']) * 100
        
        return breakdown
    
    def _get_alert_type_breakdown(self, metrics: List[CommunicationMetrics]) -> Dict[str, Any]:
        """Get alert type breakdown from metrics"""
        breakdown = {}
        for metric in metrics:
            if metric.alert_type:
                alert_type = metric.alert_type
                if alert_type not in breakdown:
                    breakdown[alert_type] = {
                        'sent': 0,
                        'delivered': 0,
                        'opened': 0,
                        'delivery_rate': 0,
                        'open_rate': 0
                    }
                
                breakdown[alert_type]['sent'] += metric.total_sent
                breakdown[alert_type]['delivered'] += metric.total_delivered
                breakdown[alert_type]['opened'] += metric.total_opened
        
        # Calculate rates
        for alert_type in breakdown:
            if breakdown[alert_type]['sent'] > 0:
                breakdown[alert_type]['delivery_rate'] = (breakdown[alert_type]['delivered'] / breakdown[alert_type]['sent']) * 100
            if breakdown[alert_type]['delivered'] > 0:
                breakdown[alert_type]['open_rate'] = (breakdown[alert_type]['opened'] / breakdown[alert_type]['delivered']) * 100
        
        return breakdown
    
    def _aggregate_time_patterns(self, analytics: List[UserEngagementAnalytics]) -> Dict[str, Any]:
        """Aggregate time patterns from user analytics"""
        hour_patterns = {}
        day_patterns = {}
        
        for analytic in analytics:
            if analytic.engagement_by_hour:
                for hour, count in analytic.engagement_by_hour.items():
                    hour_patterns[hour] = hour_patterns.get(hour, 0) + count
            
            if analytic.engagement_by_day:
                for day, count in analytic.engagement_by_day.items():
                    day_patterns[day] = day_patterns.get(day, 0) + count
        
        return {
            'hour_patterns': hour_patterns,
            'day_patterns': day_patterns
        }
    
    def _get_most_common_frequency(self, analytics: List[UserEngagementAnalytics]) -> str:
        """Get most common optimal frequency"""
        frequencies = [a.optimal_frequency for a in analytics if a.optimal_frequency]
        if not frequencies:
            return "weekly"
        
        from collections import Counter
        return Counter(frequencies).most_common(1)[0][0]
    
    def _get_engagement_trends_summary(self, analytics: List[UserEngagementAnalytics]) -> Dict[str, int]:
        """Get engagement trends summary"""
        trends = [a.engagement_trend for a in analytics]
        return {
            'increasing': trends.count('increasing'),
            'decreasing': trends.count('decreasing'),
            'stable': trends.count('stable')
        }
    
    def _create_alert(self, alert_type: str, severity: str, metric_name: str,
                     threshold: float, current_value: float, operator: str,
                     message: str, description: str) -> AnalyticsAlert:
        """Create analytics alert"""
        alert = AnalyticsAlert(
            id=str(uuid.uuid4()),
            alert_type=alert_type,
            alert_severity=severity,
            metric_name=metric_name,
            threshold_value=threshold,
            current_value=current_value,
            comparison_operator=operator,
            alert_message=message,
            alert_description=description
        )
        
        self.db.add(alert)
        self.db.commit()
        
        return alert
    
    def _generate_insights(self, metrics: Dict[str, Any], engagement: Dict[str, Any], 
                          financial_impact: Dict[str, Any]) -> List[str]:
        """Generate insights from analytics data"""
        insights = []
        
        # Delivery rate insights
        if metrics['delivery_rate'] < 90:
            insights.append(f"Delivery rate of {metrics['delivery_rate']}% is below target. Consider reviewing message content and timing.")
        
        # Engagement insights
        if engagement['avg_engagement_score'] < 50:
            insights.append(f"Average engagement score of {engagement['avg_engagement_score']} indicates room for improvement in message relevance.")
        
        # Financial impact insights
        if financial_impact['attribution_rate'] > 50:
            insights.append(f"Strong communication attribution: {financial_impact['attribution_rate']}% of outcomes linked to communications.")
        
        # Channel insights
        channel_breakdown = metrics.get('channel_breakdown', {})
        if channel_breakdown:
            best_channel = max(channel_breakdown.items(), key=lambda x: x[1]['delivery_rate'])
            insights.append(f"{best_channel[0].title()} shows highest delivery rate at {best_channel[1]['delivery_rate']}%.")
        
        return insights
    
    def _get_top_performing_channel(self, channel_breakdown: Dict[str, Any]) -> str:
        """Get top performing channel"""
        if not channel_breakdown:
            return "email"
        
        return max(channel_breakdown.items(), key=lambda x: x[1]['delivery_rate'])[0]
    
    def _get_top_performing_alert_type(self, alert_breakdown: Dict[str, Any]) -> str:
        """Get top performing alert type"""
        if not alert_breakdown:
            return "critical_financial"
        
        return max(alert_breakdown.items(), key=lambda x: x[1]['delivery_rate'])[0]


# Global service instance
communication_analytics_service = CommunicationAnalyticsService() 