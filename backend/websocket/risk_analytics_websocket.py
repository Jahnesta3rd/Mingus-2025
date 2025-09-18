#!/usr/bin/env python3
"""
WebSocket Integration for Real-Time Risk Analytics Updates

This module provides WebSocket functionality for real-time risk analytics updates,
including risk score changes, recommendation notifications, and performance alerts.

Features:
- Real-time risk score updates
- Live recommendation notifications
- Performance monitoring alerts
- Success outcome notifications
- Risk trend updates
- A/B test notifications
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import current_user

# Import risk analytics components
from ..analytics.risk_analytics_integration import RiskAnalyticsIntegration
from ..analytics.risk_predictive_analytics import RiskPredictiveAnalytics
from ..analytics.risk_performance_monitor import RiskPerformanceMonitor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskAnalyticsWebSocket:
    """
    WebSocket handler for real-time risk analytics updates.
    
    Manages WebSocket connections, room management, and real-time data broadcasting
    for risk analytics components.
    """
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.risk_analytics = RiskAnalyticsIntegration()
        self.predictive_analytics = RiskPredictiveAnalytics()
        self.performance_monitor = RiskPerformanceMonitor()
        
        # Track active connections
        self.active_connections: Dict[str, Set[str]] = {}  # user_id -> set of session_ids
        self.user_rooms: Dict[str, str] = {}  # session_id -> user_id
        
        # Register event handlers
        self._register_handlers()
        
        logger.info("RiskAnalyticsWebSocket initialized successfully")
    
    def _register_handlers(self):
        """Register WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            logger.info(f"Client connected: {request.sid}")
            
            # Check authentication
            if not current_user.is_authenticated:
                emit('error', {'message': 'Authentication required'})
                return False
            
            # Add to active connections
            user_id = str(current_user.id)
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            
            self.active_connections[user_id].add(request.sid)
            self.user_rooms[request.sid] = user_id
            
            # Join user-specific room
            join_room(f"user_{user_id}")
            
            # Send initial data
            self._send_initial_data(user_id)
            
            emit('connected', {
                'message': 'Connected to risk analytics updates',
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            logger.info(f"Client disconnected: {request.sid}")
            
            if request.sid in self.user_rooms:
                user_id = self.user_rooms[request.sid]
                
                # Remove from active connections
                if user_id in self.active_connections:
                    self.active_connections[user_id].discard(request.sid)
                    if not self.active_connections[user_id]:
                        del self.active_connections[user_id]
                
                # Leave user room
                leave_room(f"user_{user_id}")
                
                del self.user_rooms[request.sid]
        
        @self.socketio.on('subscribe_risk_updates')
        def handle_subscribe_risk_updates(data):
            """Handle subscription to risk updates"""
            if not current_user.is_authenticated:
                emit('error', {'message': 'Authentication required'})
                return
            
            user_id = str(current_user.id)
            update_types = data.get('update_types', ['risk_scores', 'recommendations', 'alerts'])
            
            # Join specific update rooms
            for update_type in update_types:
                join_room(f"user_{user_id}_{update_type}")
            
            emit('subscribed', {
                'message': 'Subscribed to risk updates',
                'update_types': update_types,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        @self.socketio.on('unsubscribe_risk_updates')
        def handle_unsubscribe_risk_updates(data):
            """Handle unsubscription from risk updates"""
            if not current_user.is_authenticated:
                emit('error', {'message': 'Authentication required'})
                return
            
            user_id = str(current_user.id)
            update_types = data.get('update_types', ['risk_scores', 'recommendations', 'alerts'])
            
            # Leave specific update rooms
            for update_type in update_types:
                leave_room(f"user_{user_id}_{update_type}")
            
            emit('unsubscribed', {
                'message': 'Unsubscribed from risk updates',
                'update_types': update_types,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        @self.socketio.on('request_risk_dashboard')
        def handle_request_risk_dashboard():
            """Handle request for risk dashboard data"""
            if not current_user.is_authenticated:
                emit('error', {'message': 'Authentication required'})
                return
            
            user_id = str(current_user.id)
            
            # Send dashboard data
            asyncio.create_task(self._send_risk_dashboard_data(user_id))
        
        @self.socketio.on('acknowledge_alert')
        def handle_acknowledge_alert(data):
            """Handle alert acknowledgment"""
            if not current_user.is_authenticated:
                emit('error', {'message': 'Authentication required'})
                return
            
            alert_id = data.get('alert_id')
            if not alert_id:
                emit('error', {'message': 'Alert ID required'})
                return
            
            # Acknowledge alert in database
            asyncio.create_task(self._acknowledge_alert(alert_id, current_user.id))
    
    async def _send_initial_data(self, user_id: str):
        """Send initial data to newly connected client"""
        try:
            # Get current risk status
            risk_status = await self.risk_analytics.get_user_current_risk_status(user_id)
            
            # Get active alerts
            active_alerts = await self.risk_analytics.get_user_active_alerts(user_id)
            
            # Get recent recommendations
            recent_recommendations = await self.risk_analytics.get_user_recent_recommendations(user_id)
            
            # Send initial data
            self.socketio.emit('initial_data', {
                'risk_status': risk_status,
                'active_alerts': active_alerts,
                'recent_recommendations': recent_recommendations,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"user_{user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send initial data to user {user_id}: {e}")
    
    async def _send_risk_dashboard_data(self, user_id: str):
        """Send risk dashboard data to client"""
        try:
            # Get dashboard data
            dashboard_data = await self.risk_analytics.get_user_risk_dashboard(user_id)
            
            # Send dashboard data
            self.socketio.emit('risk_dashboard_data', {
                'dashboard_data': dashboard_data,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"user_{user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send dashboard data to user {user_id}: {e}")
    
    async def _acknowledge_alert(self, alert_id: str, user_id: str):
        """Acknowledge alert in database"""
        try:
            # Update alert in database
            await self.risk_analytics.acknowledge_alert(alert_id, user_id)
            
            # Send acknowledgment confirmation
            self.socketio.emit('alert_acknowledged', {
                'alert_id': alert_id,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"user_{user_id}")
            
        except Exception as e:
            logger.error(f"Failed to acknowledge alert {alert_id} for user {user_id}: {e}")
    
    # =====================================================
    # REAL-TIME UPDATE BROADCASTING METHODS
    # =====================================================
    
    async def broadcast_risk_score_update(self, user_id: str, risk_data: Dict):
        """Broadcast risk score update to user"""
        try:
            self.socketio.emit('risk_score_updated', {
                'risk_data': risk_data,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"user_{user_id}_risk_scores")
            
        except Exception as e:
            logger.error(f"Failed to broadcast risk score update to user {user_id}: {e}")
    
    async def broadcast_recommendation_notification(self, user_id: str, recommendation_data: Dict):
        """Broadcast recommendation notification to user"""
        try:
            self.socketio.emit('recommendation_notification', {
                'recommendation_data': recommendation_data,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"user_{user_id}_recommendations")
            
        except Exception as e:
            logger.error(f"Failed to broadcast recommendation notification to user {user_id}: {e}")
    
    async def broadcast_performance_alert(self, user_id: str, alert_data: Dict):
        """Broadcast performance alert to user"""
        try:
            self.socketio.emit('performance_alert', {
                'alert_data': alert_data,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"user_{user_id}_alerts")
            
        except Exception as e:
            logger.error(f"Failed to broadcast performance alert to user {user_id}: {e}")
    
    async def broadcast_success_outcome(self, user_id: str, outcome_data: Dict):
        """Broadcast success outcome notification to user"""
        try:
            self.socketio.emit('success_outcome', {
                'outcome_data': outcome_data,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"user_{user_id}")
            
        except Exception as e:
            logger.error(f"Failed to broadcast success outcome to user {user_id}: {e}")
    
    async def broadcast_risk_trend_update(self, user_id: str, trend_data: Dict):
        """Broadcast risk trend update to user"""
        try:
            self.socketio.emit('risk_trend_updated', {
                'trend_data': trend_data,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"user_{user_id}_trends")
            
        except Exception as e:
            logger.error(f"Failed to broadcast risk trend update to user {user_id}: {e}")
    
    async def broadcast_ab_test_notification(self, user_id: str, test_data: Dict):
        """Broadcast A/B test notification to user"""
        try:
            self.socketio.emit('ab_test_notification', {
                'test_data': test_data,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"user_{user_id}_experiments")
            
        except Exception as e:
            logger.error(f"Failed to broadcast A/B test notification to user {user_id}: {e}")
    
    # =====================================================
    # SYSTEM-WIDE BROADCASTING METHODS
    # =====================================================
    
    async def broadcast_system_health_update(self, health_data: Dict):
        """Broadcast system health update to all connected users"""
        try:
            self.socketio.emit('system_health_update', {
                'health_data': health_data,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to broadcast system health update: {e}")
    
    async def broadcast_global_risk_trends(self, trends_data: Dict):
        """Broadcast global risk trends to all connected users"""
        try:
            self.socketio.emit('global_risk_trends', {
                'trends_data': trends_data,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to broadcast global risk trends: {e}")
    
    # =====================================================
    # MONITORING AND MAINTENANCE
    # =====================================================
    
    def get_connection_stats(self) -> Dict:
        """Get WebSocket connection statistics"""
        return {
            'total_connections': sum(len(sessions) for sessions in self.active_connections.values()),
            'unique_users': len(self.active_connections),
            'active_connections': dict(self.active_connections),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def cleanup_inactive_connections(self):
        """Clean up inactive connections"""
        try:
            # This would typically check for stale connections
            # and remove them from tracking
            pass
        except Exception as e:
            logger.error(f"Failed to cleanup inactive connections: {e}")

# =====================================================
# WEBSOCKET EVENT HANDLERS FOR RISK ANALYTICS
# =====================================================

def register_risk_analytics_websocket_handlers(socketio: SocketIO):
    """Register WebSocket handlers for risk analytics"""
    
    # Initialize WebSocket handler
    risk_ws = RiskAnalyticsWebSocket(socketio)
    
    # Register additional event handlers
    @socketio.on('get_risk_analytics_status')
    def handle_get_risk_analytics_status():
        """Handle request for risk analytics status"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return
        
        # Get risk analytics status
        status = risk_ws.get_connection_stats()
        emit('risk_analytics_status', status)
    
    @socketio.on('ping_risk_analytics')
    def handle_ping_risk_analytics():
        """Handle ping for risk analytics connection"""
        emit('pong_risk_analytics', {
            'message': 'Risk analytics connection active',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    return risk_ws
