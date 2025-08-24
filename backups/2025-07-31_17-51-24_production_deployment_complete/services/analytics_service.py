"""
Comprehensive Analytics Service for MINGUS
Integrates with Flask app factory pattern and provides analytics functionality
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
from sqlalchemy.exc import SQLAlchemyError
import logging
from decimal import Decimal

from ..models.communication_analytics import (
    CommunicationMetrics, UserEngagementMetrics, FinancialImpactMetrics,
    ChannelEffectiveness, CostTracking, ABTestResults, CommunicationQueueStatus,
    AnalyticsAlert, AnalyticsReport, UserSegmentPerformance,
    MetricType, ChannelType, UserSegment, FinancialOutcome
)
from ..models.communication_preferences import (
    CommunicationPreferences, DeliveryLog, OptOutHistory
)
from ..models.user import User
from ..database import get_db_session

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Comprehensive analytics service for MINGUS communication tracking
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize analytics service
        
        Args:
            db_session: Database session (optional, will use Flask context if not provided)
        """
        self.db: Session = db_session or get_db_session()
    
    def track_communication_metrics(self, 
                                  user_id: int,
                                  message_type: str,
                                  channel: str,
                                  status: str = "sent",
                                  cost: float = 0.0,
                                  delivered_at: Optional[datetime] = None,
                                  opened_at: Optional[datetime] = None,
                                  clicked_at: Optional[datetime] = None,
                                  action_taken: Optional[str] = None) -> CommunicationMetrics:
        """
        Track communication metrics for real-time analytics
        
        Args:
            user_id: User ID
            message_type: Type of message (e.g., "low_balance", "weekly_checkin")
            channel: Communication channel ("sms" or "email")
            status: Message status ("sent", "delivered", "failed")
            cost: Cost in dollars
            delivered_at: When message was delivered
            opened_at: When message was opened
            clicked_at: When message was clicked
            action_taken: Action taken by user (e.g., "viewed_forecast", "updated_budget")
            
        Returns:
            CommunicationMetrics object
        """
        try:
            # Create communication metrics record
            metrics = CommunicationMetrics(
                user_id=user_id,
                message_type=message_type,
                channel=channel,
                status=status,
                cost=cost,
                sent_at=datetime.utcnow(),
                delivered_at=delivered_at,
                opened_at=opened_at,
                clicked_at=clicked_at,
                action_taken=action_taken
            )
            
            self.db.add(metrics)
            self.db.commit()
            
            logger.info(f"Tracked communication metrics for user {user_id} - {message_type} via {channel}")
            return metrics
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to track communication metrics: {e}")
            raise
    
    def update_message_status(self, 
                            message_id: int,
                            status: str,
                            timestamp: Optional[datetime] = None) -> CommunicationMetrics:
        """
        Update message status (delivered, opened, clicked)
        
        Args:
            message_id: Message ID
            status: New status
            timestamp: When the status change occurred
            
        Returns:
            Updated CommunicationMetrics object
        """
        try:
            metrics = self.db.query(CommunicationMetrics).filter(
                CommunicationMetrics.id == message_id
            ).first()
            
            if not metrics:
                raise ValueError(f"Message with ID {message_id} not found")
            
            metrics.status = status
            timestamp = timestamp or datetime.utcnow()
            
            if status == "delivered":
                metrics.delivered_at = timestamp
            elif status == "opened":
                metrics.opened_at = timestamp
            elif status == "clicked":
                metrics.clicked_at = timestamp
            
            self.db.commit()
            
            logger.info(f"Updated message {message_id} status to {status}")
            return metrics
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to update message status: {e}")
            raise
    
    def record_user_action(self, 
                          message_id: int,
                          action_taken: str) -> CommunicationMetrics:
        """
        Record user action taken in response to a message
        
        Args:
            message_id: Message ID
            action_taken: Action taken by user
            
        Returns:
            Updated CommunicationMetrics object
        """
        try:
            metrics = self.db.query(CommunicationMetrics).filter(
                CommunicationMetrics.id == message_id
            ).first()
            
            if not metrics:
                raise ValueError(f"Message with ID {message_id} not found")
            
            metrics.action_taken = action_taken
            self.db.commit()
            
            logger.info(f"Recorded user action {action_taken} for message {message_id}")
            return metrics
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to record user action: {e}")
            raise
    
    def get_user_communication_history(self, 
                                     user_id: int,
                                     limit: int = 100) -> List[CommunicationMetrics]:
        """
        Get communication history for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of records to return
            
        Returns:
            List of CommunicationMetrics objects
        """
        try:
            metrics = self.db.query(CommunicationMetrics).filter(
                CommunicationMetrics.user_id == user_id
            ).order_by(desc(CommunicationMetrics.sent_at)).limit(limit).all()
            
            return metrics
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get user communication history: {e}")
            raise
    
    def get_communication_stats(self, 
                              user_id: Optional[int] = None,
                              message_type: Optional[str] = None,
                              channel: Optional[str] = None,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get communication statistics
        
        Args:
            user_id: Filter by user ID (optional)
            message_type: Filter by message type (optional)
            channel: Filter by channel (optional)
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
            
        Returns:
            Dictionary with communication statistics
        """
        try:
            query = self.db.query(CommunicationMetrics)
            
            if user_id:
                query = query.filter(CommunicationMetrics.user_id == user_id)
            if message_type:
                query = query.filter(CommunicationMetrics.message_type == message_type)
            if channel:
                query = query.filter(CommunicationMetrics.channel == channel)
            if start_date:
                query = query.filter(CommunicationMetrics.sent_at >= start_date)
            if end_date:
                query = query.filter(CommunicationMetrics.sent_at <= end_date)
            
            metrics = query.all()
            
            # Calculate statistics
            total_messages = len(metrics)
            total_cost = sum(m.cost for m in metrics)
            
            # Status breakdown
            status_counts = {}
            for metric in metrics:
                status = metric.status
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Channel breakdown
            channel_counts = {}
            for metric in metrics:
                channel = metric.channel
                channel_counts[channel] = channel_counts.get(channel, 0) + 1
            
            # Message type breakdown
            message_type_counts = {}
            for metric in metrics:
                msg_type = metric.message_type
                message_type_counts[msg_type] = message_type_counts.get(msg_type, 0) + 1
            
            # Engagement metrics
            delivered_count = status_counts.get("delivered", 0)
            opened_count = len([m for m in metrics if m.opened_at])
            clicked_count = len([m for m in metrics if m.clicked_at])
            action_count = len([m for m in metrics if m.action_taken])
            
            delivery_rate = (delivered_count / total_messages * 100) if total_messages > 0 else 0.0
            open_rate = (opened_count / delivered_count * 100) if delivered_count > 0 else 0.0
            click_rate = (clicked_count / opened_count * 100) if opened_count > 0 else 0.0
            action_rate = (action_count / delivered_count * 100) if delivered_count > 0 else 0.0
            
            return {
                "total_messages": total_messages,
                "total_cost": total_cost,
                "avg_cost_per_message": total_cost / total_messages if total_messages > 0 else 0.0,
                "status_breakdown": status_counts,
                "channel_breakdown": channel_counts,
                "message_type_breakdown": message_type_counts,
                "delivery_rate": delivery_rate,
                "open_rate": open_rate,
                "click_rate": click_rate,
                "action_rate": action_rate,
                "delivered_count": delivered_count,
                "opened_count": opened_count,
                "clicked_count": clicked_count,
                "action_count": action_count
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get communication stats: {e}")
            raise
    
    def update_user_engagement(self, 
                             user_id: int,
                             channel: ChannelType,
                             alert_type: str,
                             engaged: bool = True,
                             response_time_minutes: Optional[float] = None) -> UserEngagementMetrics:
        """
        Update user engagement metrics
        
        Args:
            user_id: User ID
            channel: Communication channel
            alert_type: Type of alert/message
            engaged: Whether user engaged with the message
            response_time_minutes: Response time in minutes
            
        Returns:
            UserEngagementMetrics object
        """
        try:
            # Get or create user engagement metrics
            engagement = self.db.query(UserEngagementMetrics).filter(
                UserEngagementMetrics.user_id == user_id
            ).first()
            
            if not engagement:
                engagement = UserEngagementMetrics(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    total_messages_received=0,
                    total_messages_engaged=0,
                    total_messages_ignored=0,
                    sms_engagement_count=0,
                    email_engagement_count=0,
                    push_engagement_count=0,
                    in_app_engagement_count=0,
                    engagement_by_hour={},
                    engagement_by_day={},
                    engagement_by_month={},
                    alert_type_engagement={},
                    response_time_distribution={},
                    engagement_score=0.0
                )
                self.db.add(engagement)
            
            # Update metrics
            engagement.total_messages_received += 1
            
            if engaged:
                engagement.total_messages_engaged += 1
                
                # Update channel-specific engagement
                if channel == ChannelType.SMS:
                    engagement.sms_engagement_count += 1
                elif channel == ChannelType.EMAIL:
                    engagement.email_engagement_count += 1
                elif channel == ChannelType.PUSH:
                    engagement.push_engagement_count += 1
                elif channel == ChannelType.IN_APP:
                    engagement.in_app_engagement_count += 1
                
                # Update time-based patterns
                now = datetime.utcnow()
                hour = now.hour
                day = now.weekday()
                month = now.month
                
                # Update engagement by hour
                engagement.engagement_by_hour = engagement.engagement_by_hour or {}
                engagement.engagement_by_hour[str(hour)] = engagement.engagement_by_hour.get(str(hour), 0) + 1
                
                # Update engagement by day
                engagement.engagement_by_day = engagement.engagement_by_day or {}
                engagement.engagement_by_day[str(day)] = engagement.engagement_by_day.get(str(day), 0) + 1
                
                # Update engagement by month
                engagement.engagement_by_month = engagement.engagement_by_month or {}
                engagement.engagement_by_month[str(month)] = engagement.engagement_by_month.get(str(month), 0) + 1
                
                # Update alert type engagement
                engagement.alert_type_engagement = engagement.alert_type_engagement or {}
                if alert_type not in engagement.alert_type_engagement:
                    engagement.alert_type_engagement[alert_type] = {'engaged': 0, 'total': 0, 'rate': 0.0}
                
                engagement.alert_type_engagement[alert_type]['engaged'] += 1
                engagement.alert_type_engagement[alert_type]['total'] += 1
                engagement.alert_type_engagement[alert_type]['rate'] = (
                    engagement.alert_type_engagement[alert_type]['engaged'] / 
                    engagement.alert_type_engagement[alert_type]['total'] * 100
                )
                
                # Update response time
                if response_time_minutes:
                    if engagement.avg_response_time_minutes == 0:
                        engagement.avg_response_time_minutes = response_time_minutes
                    else:
                        engagement.avg_response_time_minutes = (
                            (engagement.avg_response_time_minutes + response_time_minutes) / 2
                        )
                    
                    # Update response time distribution
                    engagement.response_time_distribution = engagement.response_time_distribution or {}
                    time_range = self._get_response_time_range(response_time_minutes)
                    engagement.response_time_distribution[time_range] = (
                        engagement.response_time_distribution.get(time_range, 0) + 1
                    )
            else:
                engagement.total_messages_ignored += 1
            
            # Calculate engagement score
            engagement.engagement_score = (
                engagement.total_messages_engaged / engagement.total_messages_received * 100
            ) if engagement.total_messages_received > 0 else 0.0
            
            # Determine engagement trend
            engagement.engagement_trend = self._calculate_engagement_trend(engagement)
            
            self.db.commit()
            
            logger.info(f"Updated user engagement for user {user_id}")
            return engagement
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to update user engagement: {e}")
            raise
    
    def track_channel_effectiveness(self,
                                  channel: ChannelType,
                                  alert_type: str,
                                  user_segment: Optional[UserSegment] = None,
                                  period_type: str = "daily") -> ChannelEffectiveness:
        """
        Track channel effectiveness for SMS vs Email comparison
        
        Args:
            channel: Communication channel
            alert_type: Type of alert/message
            user_segment: User segment (optional)
            period_type: Time period type (daily, weekly, monthly)
            
        Returns:
            ChannelEffectiveness object
        """
        try:
            now = datetime.utcnow()
            
            # Get metrics for this channel/period from CommunicationMetrics
            channel_str = channel.value
            metrics = self.db.query(CommunicationMetrics).filter(
                CommunicationMetrics.channel == channel_str,
                CommunicationMetrics.message_type == alert_type,
                CommunicationMetrics.sent_at >= now - timedelta(days=1)
            ).all()
            
            # Aggregate metrics
            total_sent = len(metrics)
            total_delivered = len([m for m in metrics if m.status == "delivered"])
            total_opened = len([m for m in metrics if m.opened_at])
            total_clicked = len([m for m in metrics if m.clicked_at])
            total_responded = len([m for m in metrics if m.action_taken])
            total_converted = len([m for m in metrics if m.action_taken and "upgrade" in m.action_taken.lower()])
            total_cost = sum(m.cost for m in metrics)
            
            # Calculate rates
            delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0.0
            open_rate = (total_opened / total_delivered * 100) if total_delivered > 0 else 0.0
            click_rate = (total_clicked / total_opened * 100) if total_opened > 0 else 0.0
            response_rate = (total_responded / total_delivered * 100) if total_delivered > 0 else 0.0
            conversion_rate = (total_converted / total_delivered * 100) if total_delivered > 0 else 0.0
            engagement_rate = (total_responded / total_delivered * 100) if total_delivered > 0 else 0.0
            
            # Calculate cost metrics
            cost_per_message = total_cost / total_sent if total_sent > 0 else 0.0
            cost_per_engagement = total_cost / total_responded if total_responded > 0 else 0.0
            cost_per_conversion = total_cost / total_converted if total_converted > 0 else 0.0
            
            # Calculate performance score (weighted average of key metrics)
            performance_score = (
                delivery_rate * 0.2 +
                open_rate * 0.2 +
                engagement_rate * 0.3 +
                conversion_rate * 0.3
            )
            
            # Create or update channel effectiveness
            effectiveness = ChannelEffectiveness(
                id=str(uuid.uuid4()),
                channel=channel,
                alert_type=alert_type,
                user_segment=user_segment,
                date=now.date(),
                period_type=period_type,
                messages_sent=total_sent,
                messages_delivered=total_delivered,
                messages_opened=total_opened,
                messages_clicked=total_clicked,
                messages_responded=total_responded,
                messages_converted=total_converted,
                delivery_rate=delivery_rate,
                open_rate=open_rate,
                click_rate=click_rate,
                response_rate=response_rate,
                conversion_rate=conversion_rate,
                engagement_rate=engagement_rate,
                total_cost=total_cost,
                cost_per_message=cost_per_message,
                cost_per_engagement=cost_per_engagement,
                cost_per_conversion=cost_per_conversion,
                performance_score=performance_score
            )
            
            self.db.add(effectiveness)
            self.db.commit()
            
            logger.info(f"Tracked channel effectiveness for {channel}")
            return effectiveness
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to track channel effectiveness: {e}")
            raise
    
    def track_financial_impact(self,
                             user_id: int,
                             outcome_type: FinancialOutcome,
                             outcome_value: Decimal,
                             communication_channel: Optional[ChannelType] = None,
                             alert_type: Optional[str] = None,
                             message_id: Optional[str] = None,
                             attributed_to_communication: bool = False) -> FinancialImpactMetrics:
        """
        Track financial impact correlation with communication engagement
        
        Args:
            user_id: User ID
            outcome_type: Type of financial outcome
            outcome_value: Dollar amount of the outcome
            communication_channel: Communication channel (optional)
            alert_type: Type of alert (optional)
            message_id: Message ID (optional)
            attributed_to_communication: Whether outcome is attributed to communication
            
        Returns:
            FinancialImpactMetrics object
        """
        try:
            # Get user's recent communication activity
            recent_delivery = None
            if message_id:
                recent_delivery = self.db.query(DeliveryLog).filter(
                    DeliveryLog.message_id == message_id,
                    DeliveryLog.user_id == user_id
                ).first()
            
            # Calculate days since last communication
            days_since_last_communication = None
            if recent_delivery:
                days_since_last_communication = (datetime.utcnow() - recent_delivery.sent_at).days
            
            # Determine engagement level
            engagement_level = "low"
            if attributed_to_communication:
                engagement_level = "high"
            elif recent_delivery and recent_delivery.delivered:
                engagement_level = "medium"
            
            # Calculate attribution confidence
            attribution_confidence = 0.0
            if attributed_to_communication:
                attribution_confidence = 85.0  # Base confidence
                if recent_delivery and recent_delivery.opened:
                    attribution_confidence += 10.0
                if recent_delivery and recent_delivery.clicked:
                    attribution_confidence += 5.0
            
            # Create financial impact record
            impact = FinancialImpactMetrics(
                id=str(uuid.uuid4()),
                user_id=user_id,
                outcome_type=outcome_type,
                outcome_value=outcome_value,
                outcome_date=datetime.utcnow(),
                communication_channel=communication_channel,
                alert_type=alert_type,
                message_id=message_id,
                days_since_last_communication=days_since_last_communication,
                user_engaged_with_communication=attributed_to_communication,
                engagement_level=engagement_level,
                attributed_to_communication=attributed_to_communication,
                attribution_confidence=attribution_confidence
            )
            
            self.db.add(impact)
            self.db.commit()
            
            logger.info(f"Tracked financial impact for user {user_id}: {outcome_type}")
            return impact
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to track financial impact: {e}")
            raise
    
    def track_costs(self,
                   channel: ChannelType,
                   alert_type: str,
                   user_segment: Optional[UserSegment] = None,
                   period_type: str = "daily",
                   sms_cost: Decimal = Decimal('0.00'),
                   email_cost: Decimal = Decimal('0.00'),
                   push_cost: Decimal = Decimal('0.00'),
                   in_app_cost: Decimal = Decimal('0.00'),
                   twilio_cost: Decimal = Decimal('0.00'),
                   resend_cost: Decimal = Decimal('0.00'),
                   total_messages: int = 0) -> CostTracking:
        """
        Track communication costs for budget monitoring
        
        Args:
            channel: Communication channel
            alert_type: Type of alert/message
            user_segment: User segment (optional)
            period_type: Time period type
            sms_cost: SMS costs
            email_cost: Email costs
            push_cost: Push notification costs
            in_app_cost: In-app message costs
            twilio_cost: Twilio service costs
            resend_cost: Resend service costs
            total_messages: Total messages sent
            
        Returns:
            CostTracking object
        """
        try:
            now = datetime.utcnow()
            
            # Calculate total cost
            total_cost = sms_cost + email_cost + push_cost + in_app_cost + twilio_cost + resend_cost
            
            # Calculate cost per message
            cost_per_message = total_cost / total_messages if total_messages > 0 else Decimal('0.00')
            
            # Get budget allocation (this would come from configuration)
            budget_allocation = Decimal('1000.00')  # Example budget
            
            # Calculate budget utilization
            budget_utilization = (total_cost / budget_allocation * 100) if budget_allocation > 0 else 0.0
            
            # Calculate budget variance
            budget_variance = total_cost - budget_allocation
            
            # Calculate cost efficiency score (inverse of cost per message, normalized)
            cost_efficiency_score = max(0, 100 - (float(cost_per_message) * 1000))  # Simple scoring
            
            # Determine cost trend
            cost_trend = "stable"  # This would be calculated based on historical data
            
            # Check for cost threshold alerts
            cost_threshold_exceeded = total_cost > budget_allocation
            budget_alert_triggered = budget_utilization > 90.0
            
            # Create cost tracking record
            cost_tracking = CostTracking(
                id=str(uuid.uuid4()),
                channel=channel,
                alert_type=alert_type,
                user_segment=user_segment,
                date=now.date(),
                period_type=period_type,
                sms_cost=sms_cost,
                email_cost=email_cost,
                push_cost=push_cost,
                in_app_cost=in_app_cost,
                twilio_cost=twilio_cost,
                resend_cost=resend_cost,
                total_cost=total_cost,
                total_messages=total_messages,
                cost_per_message=cost_per_message,
                budget_allocation=budget_allocation,
                budget_utilization=budget_utilization,
                budget_variance=budget_variance,
                cost_efficiency_score=cost_efficiency_score,
                cost_trend=cost_trend,
                cost_threshold_exceeded=cost_threshold_exceeded,
                budget_alert_triggered=budget_alert_triggered
            )
            
            self.db.add(cost_tracking)
            self.db.commit()
            
            logger.info(f"Tracked costs for {channel}: ${total_cost}")
            return cost_tracking
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to track costs: {e}")
            raise
    
    def get_real_time_metrics(self, 
                            channel: Optional[ChannelType] = None,
                            alert_type: Optional[str] = None,
                            time_period: str = "last_24_hours") -> Dict[str, Any]:
        """
        Get real-time communication metrics
        
        Args:
            channel: Filter by channel (optional)
            alert_type: Filter by alert type (optional)
            time_period: Time period for metrics
            
        Returns:
            Dictionary with real-time metrics
        """
        try:
            # Calculate time range
            now = datetime.utcnow()
            if time_period == "last_24_hours":
                start_time = now - timedelta(hours=24)
            elif time_period == "last_7_days":
                start_time = now - timedelta(days=7)
            elif time_period == "last_30_days":
                start_time = now - timedelta(days=30)
            else:
                start_time = now - timedelta(hours=24)
            
            # Build query using CommunicationMetrics
            query = self.db.query(CommunicationMetrics).filter(
                CommunicationMetrics.sent_at >= start_time
            )
            
            if channel:
                query = query.filter(CommunicationMetrics.channel == channel.value)
            if alert_type:
                query = query.filter(CommunicationMetrics.message_type == alert_type)
            
            metrics = query.all()
            
            # Aggregate metrics
            total_sent = len(metrics)
            total_delivered = len([m for m in metrics if m.status == "delivered"])
            total_opened = len([m for m in metrics if m.opened_at])
            total_clicked = len([m for m in metrics if m.clicked_at])
            total_responded = len([m for m in metrics if m.action_taken])
            total_converted = len([m for m in metrics if m.action_taken and "upgrade" in m.action_taken.lower()])
            total_cost = sum(m.cost for m in metrics)
            
            # Calculate rates
            delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0.0
            open_rate = (total_opened / total_delivered * 100) if total_delivered > 0 else 0.0
            click_rate = (total_clicked / total_opened * 100) if total_opened > 0 else 0.0
            response_rate = (total_responded / total_delivered * 100) if total_delivered > 0 else 0.0
            conversion_rate = (total_converted / total_delivered * 100) if total_delivered > 0 else 0.0
            
            return {
                "time_period": time_period,
                "total_sent": total_sent,
                "total_delivered": total_delivered,
                "total_opened": total_opened,
                "total_clicked": total_clicked,
                "total_responded": total_responded,
                "total_converted": total_converted,
                "total_cost": float(total_cost),
                "delivery_rate": delivery_rate,
                "open_rate": open_rate,
                "click_rate": click_rate,
                "response_rate": response_rate,
                "conversion_rate": conversion_rate,
                "cost_per_message": float(total_cost / total_sent) if total_sent > 0 else 0.0,
                "cost_per_engagement": float(total_cost / total_responded) if total_responded > 0 else 0.0
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get real-time metrics: {e}")
            raise
    
    def get_channel_comparison(self, 
                             alert_type: Optional[str] = None,
                             user_segment: Optional[UserSegment] = None,
                             time_period: str = "last_7_days") -> Dict[str, Any]:
        """
        Compare SMS vs Email performance
        
        Args:
            alert_type: Filter by alert type (optional)
            user_segment: Filter by user segment (optional)
            time_period: Time period for comparison
            
        Returns:
            Dictionary with channel comparison data
        """
        try:
            # Calculate time range
            now = datetime.utcnow()
            if time_period == "last_7_days":
                start_date = now.date() - timedelta(days=7)
            elif time_period == "last_30_days":
                start_date = now.date() - timedelta(days=30)
            else:
                start_date = now.date() - timedelta(days=7)
            
            # Get channel effectiveness data
            query = self.db.query(ChannelEffectiveness).filter(
                ChannelEffectiveness.date >= start_date
            )
            
            if alert_type:
                query = query.filter(ChannelEffectiveness.alert_type == alert_type)
            if user_segment:
                query = query.filter(ChannelEffectiveness.user_segment == user_segment)
            
            effectiveness_data = query.all()
            
            # Group by channel
            channel_data = {}
            for data in effectiveness_data:
                if data.channel not in channel_data:
                    channel_data[data.channel] = {
                        "total_sent": 0,
                        "total_delivered": 0,
                        "total_opened": 0,
                        "total_responded": 0,
                        "total_converted": 0,
                        "total_cost": Decimal('0.00'),
                        "performance_score": 0.0
                    }
                
                channel_data[data.channel]["total_sent"] += data.messages_sent
                channel_data[data.channel]["total_delivered"] += data.messages_delivered
                channel_data[data.channel]["total_opened"] += data.messages_opened
                channel_data[data.channel]["total_responded"] += data.messages_responded
                channel_data[data.channel]["total_converted"] += data.messages_converted
                channel_data[data.channel]["total_cost"] += data.total_cost
                channel_data[data.channel]["performance_score"] = data.performance_score
            
            # Calculate rates for each channel
            comparison = {}
            for channel, data in channel_data.items():
                delivery_rate = (data["total_delivered"] / data["total_sent"] * 100) if data["total_sent"] > 0 else 0.0
                open_rate = (data["total_opened"] / data["total_delivered"] * 100) if data["total_delivered"] > 0 else 0.0
                response_rate = (data["total_responded"] / data["total_delivered"] * 100) if data["total_delivered"] > 0 else 0.0
                conversion_rate = (data["total_converted"] / data["total_delivered"] * 100) if data["total_delivered"] > 0 else 0.0
                
                comparison[channel.value] = {
                    "total_sent": data["total_sent"],
                    "total_delivered": data["total_delivered"],
                    "total_opened": data["total_opened"],
                    "total_responded": data["total_responded"],
                    "total_converted": data["total_converted"],
                    "total_cost": float(data["total_cost"]),
                    "delivery_rate": delivery_rate,
                    "open_rate": open_rate,
                    "response_rate": response_rate,
                    "conversion_rate": conversion_rate,
                    "performance_score": data["performance_score"],
                    "cost_per_message": float(data["total_cost"] / data["total_sent"]) if data["total_sent"] > 0 else 0.0,
                    "cost_per_engagement": float(data["total_cost"] / data["total_responded"]) if data["total_responded"] > 0 else 0.0
                }
            
            return {
                "time_period": time_period,
                "channels": comparison,
                "winner": max(comparison.keys(), key=lambda k: comparison[k]["performance_score"]) if comparison else None
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get channel comparison: {e}")
            raise
    
    def get_cost_analysis(self,
                         channel: Optional[ChannelType] = None,
                         time_period: str = "last_30_days") -> Dict[str, Any]:
        """
        Get cost analysis for budget monitoring
        
        Args:
            channel: Filter by channel (optional)
            time_period: Time period for analysis
            
        Returns:
            Dictionary with cost analysis data
        """
        try:
            # Calculate time range
            now = datetime.utcnow()
            if time_period == "last_30_days":
                start_date = now.date() - timedelta(days=30)
            elif time_period == "last_90_days":
                start_date = now.date() - timedelta(days=90)
            else:
                start_date = now.date() - timedelta(days=30)
            
            # Get cost tracking data
            query = self.db.query(CostTracking).filter(
                CostTracking.date >= start_date
            )
            
            if channel:
                query = query.filter(CostTracking.channel == channel)
            
            cost_data = query.all()
            
            # Aggregate costs
            total_sms_cost = sum(c.sms_cost for c in cost_data)
            total_email_cost = sum(c.email_cost for c in cost_data)
            total_twilio_cost = sum(c.twilio_cost for c in cost_data)
            total_resend_cost = sum(c.resend_cost for c in cost_data)
            total_cost = sum(c.total_cost for c in cost_data)
            total_messages = sum(c.total_messages for c in cost_data)
            
            # Calculate averages
            avg_cost_per_message = total_cost / total_messages if total_messages > 0 else Decimal('0.00')
            avg_budget_utilization = sum(c.budget_utilization for c in cost_data) / len(cost_data) if cost_data else 0.0
            
            # Get cost trends
            cost_trends = {}
            for c in cost_data:
                if c.channel not in cost_trends:
                    cost_trends[c.channel] = []
                cost_trends[c.channel].append({
                    "date": c.date.isoformat(),
                    "total_cost": float(c.total_cost),
                    "cost_per_message": float(c.cost_per_message)
                })
            
            return {
                "time_period": time_period,
                "total_sms_cost": float(total_sms_cost),
                "total_email_cost": float(total_email_cost),
                "total_twilio_cost": float(total_twilio_cost),
                "total_resend_cost": float(total_resend_cost),
                "total_cost": float(total_cost),
                "total_messages": total_messages,
                "avg_cost_per_message": float(avg_cost_per_message),
                "avg_budget_utilization": avg_budget_utilization,
                "cost_trends": cost_trends,
                "cost_breakdown": {
                    "sms": float(total_sms_cost),
                    "email": float(total_email_cost),
                    "twilio": float(total_twilio_cost),
                    "resend": float(total_resend_cost)
                }
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get cost analysis: {e}")
            raise
    
    def _get_response_time_range(self, response_time_minutes: float) -> str:
        """Helper method to categorize response time ranges"""
        if response_time_minutes < 5:
            return "0-5 minutes"
        elif response_time_minutes < 15:
            return "5-15 minutes"
        elif response_time_minutes < 60:
            return "15-60 minutes"
        elif response_time_minutes < 1440:  # 24 hours
            return "1-24 hours"
        else:
            return "24+ hours"
    
    def _calculate_engagement_trend(self, engagement: UserEngagementMetrics) -> str:
        """Helper method to calculate engagement trend"""
        # This is a simplified calculation - in production, you'd compare with historical data
        if engagement.engagement_score > 70:
            return "increasing"
        elif engagement.engagement_score < 30:
            return "decreasing"
        else:
            return "stable"
    
    def close(self):
        """Close the database session"""
        if self.db:
            self.db.close() 

    def track_message_sent(self, user_id: int, channel: str, message_type: str, cost: float) -> CommunicationMetrics:
        """
        Track when a message is sent
        
        Args:
            user_id: User ID
            channel: Communication channel ("sms" or "email")
            message_type: Type of message (e.g., "low_balance", "weekly_checkin")
            cost: Cost in dollars
            
        Returns:
            CommunicationMetrics object with the sent message record
        """
        try:
            # Create communication metrics record for sent message
            metrics = CommunicationMetrics(
                user_id=user_id,
                message_type=message_type,
                channel=channel,
                status="sent",
                cost=cost,
                sent_at=datetime.utcnow()
            )
            
            self.db.add(metrics)
            self.db.commit()
            
            logger.info(f"Tracked message sent for user {user_id} - {message_type} via {channel}")
            return metrics
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to track message sent: {e}")
            raise
    
    def track_message_delivered(self, message_id: int, delivery_time: Optional[datetime] = None) -> CommunicationMetrics:
        """
        Track when a message is delivered
        
        Args:
            message_id: Message ID
            delivery_time: When message was delivered (defaults to current time)
            
        Returns:
            Updated CommunicationMetrics object
        """
        try:
            metrics = self.db.query(CommunicationMetrics).filter(
                CommunicationMetrics.id == message_id
            ).first()
            
            if not metrics:
                raise ValueError(f"Message with ID {message_id} not found")
            
            # Update status and delivery time
            metrics.status = "delivered"
            metrics.delivered_at = delivery_time or datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Tracked message {message_id} delivered at {metrics.delivered_at}")
            return metrics
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to track message delivered: {e}")
            raise
    
    def track_message_opened(self, message_id: int, open_time: Optional[datetime] = None) -> CommunicationMetrics:
        """
        Track when a message is opened
        
        Args:
            message_id: Message ID
            open_time: When message was opened (defaults to current time)
            
        Returns:
            Updated CommunicationMetrics object
        """
        try:
            metrics = self.db.query(CommunicationMetrics).filter(
                CommunicationMetrics.id == message_id
            ).first()
            
            if not metrics:
                raise ValueError(f"Message with ID {message_id} not found")
            
            # Update opened time
            metrics.opened_at = open_time or datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Tracked message {message_id} opened at {metrics.opened_at}")
            return metrics
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to track message opened: {e}")
            raise
    
    def track_user_action(self, message_id: int, action_type: str, timestamp: Optional[datetime] = None) -> CommunicationMetrics:
        """
        Track user action taken in response to a message
        
        Args:
            message_id: Message ID
            action_type: Type of action taken (e.g., "viewed_forecast", "updated_budget")
            timestamp: When action was taken (defaults to current time)
            
        Returns:
            Updated CommunicationMetrics object
        """
        try:
            metrics = self.db.query(CommunicationMetrics).filter(
                CommunicationMetrics.id == message_id
            ).first()
            
            if not metrics:
                raise ValueError(f"Message with ID {message_id} not found")
            
            # Update action taken and timestamp
            metrics.action_taken = action_type
            
            # If this is a click action, also update clicked_at
            if "click" in action_type.lower():
                metrics.clicked_at = timestamp or datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Tracked user action {action_type} for message {message_id}")
            return metrics
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to track user action: {e}")
            raise
    
    def track_financial_outcome(self, user_id: int, action: str, impact_amount: float) -> FinancialImpactMetrics:
        """
        Track financial outcome resulting from user actions
        
        Args:
            user_id: User ID
            action: Action that led to financial outcome (e.g., "bill_paid_on_time", "savings_goal_achieved")
            impact_amount: Dollar amount of the financial impact
            
        Returns:
            FinancialImpactMetrics object
        """
        try:
            # Map action to FinancialOutcome enum
            outcome_mapping = {
                "bill_paid_on_time": FinancialOutcome.BILL_PAID_ON_TIME,
                "late_fee_avoided": FinancialOutcome.LATE_FEE_AVOIDED,
                "savings_goal_achieved": FinancialOutcome.SAVINGS_GOAL_ACHIEVED,
                "subscription_upgraded": FinancialOutcome.SUBSCRIPTION_UPGRADED,
                "career_advancement": FinancialOutcome.CAREER_ADVANCEMENT,
                "budget_improved": FinancialOutcome.BUDGET_IMPROVED,
                "emergency_fund_built": FinancialOutcome.EMERGENCY_FUND_BUILT
            }
            
            outcome_type = outcome_mapping.get(action, FinancialOutcome.BUDGET_IMPROVED)
            
            # Create financial impact record
            impact = FinancialImpactMetrics(
                id=str(uuid.uuid4()),
                user_id=user_id,
                outcome_type=outcome_type,
                outcome_value=Decimal(str(impact_amount)),
                outcome_date=datetime.utcnow(),
                attributed_to_communication=True,  # Assume communication contributed
                attribution_confidence=75.0  # Default confidence
            )
            
            self.db.add(impact)
            self.db.commit()
            
            logger.info(f"Tracked financial outcome for user {user_id}: {action} - ${impact_amount}")
            return impact
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to track financial outcome: {e}")
            raise 