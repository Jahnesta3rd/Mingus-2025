"""
WebSocket Service

This module provides WebSocket functionality for real-time communication
including dashboard updates, alerts, and notifications.
"""

import logging
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import websockets
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types"""
    BALANCE_UPDATE = "balance_update"
    TRANSACTION_NOTIFICATION = "transaction_notification"
    GOAL_PROGRESS_UPDATE = "goal_progress_update"
    ALERT = "alert"
    PERFORMANCE_METRICS_UPDATE = "performance_metrics_update"
    DASHBOARD_REFRESH = "dashboard_refresh"
    PING = "ping"
    PONG = "pong"


@dataclass
class WebSocketMessage:
    """WebSocket message structure"""
    type: MessageType
    user_id: str
    data: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            'type': self.type.value,
            'user_id': self.user_id,
            'data': self.data,
            'timestamp': self.timestamp.isoformat()
        }
    
    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps(self.to_dict())


class WebSocketService:
    """Service for managing WebSocket connections and real-time updates"""
    
    def __init__(self, db_session, config: Dict[str, Any]):
        self.db = db_session
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Active connections
        self.connections: Dict[str, WebSocketServerProtocol] = {}
        self.user_connections: Dict[str, Set[str]] = {}
        
        # Message queue for broadcasting
        self.message_queue = asyncio.Queue()
        
        # Heartbeat interval
        self.heartbeat_interval = 30  # seconds
        
    async def handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new WebSocket connection"""
        connection_id = id(websocket)
        
        try:
            # Wait for authentication message
            auth_message = await websocket.recv()
            auth_data = json.loads(auth_message)
            
            user_id = auth_data.get('user_id')
            if not user_id:
                await websocket.close(1008, "User ID required")
                return
            
            # Store connection
            self.connections[connection_id] = websocket
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
            
            self.logger.info(f"WebSocket connected: user_id={user_id}, connection_id={connection_id}")
            
            # Send welcome message
            welcome_message = WebSocketMessage(
                type=MessageType.DASHBOARD_REFRESH,
                user_id=user_id,
                data={'message': 'Connected to MINGUS real-time updates'}
            )
            await websocket.send(welcome_message.to_json())
            
            # Start heartbeat
            asyncio.create_task(self._heartbeat(websocket, connection_id))
            
            # Handle incoming messages
            async for message in websocket:
                await self._handle_message(websocket, connection_id, user_id, message)
                
        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"WebSocket connection closed: connection_id={connection_id}")
        except Exception as e:
            self.logger.error(f"Error handling WebSocket connection: {e}")
        finally:
            # Clean up connection
            await self._cleanup_connection(connection_id, user_id)
    
    async def _handle_message(self, websocket: WebSocketServerProtocol, connection_id: str, user_id: str, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'ping':
                # Respond to ping
                pong_message = WebSocketMessage(
                    type=MessageType.PONG,
                    user_id=user_id,
                    data={'timestamp': datetime.utcnow().isoformat()}
                )
                await websocket.send(pong_message.to_json())
                
            elif message_type == 'dashboard_refresh':
                # Handle dashboard refresh request
                await self._handle_dashboard_refresh(user_id)
                
            elif message_type == 'alert_read':
                # Handle alert read acknowledgment
                alert_id = data.get('alert_id')
                if alert_id:
                    await self._handle_alert_read(user_id, alert_id)
                    
        except json.JSONDecodeError:
            self.logger.warning(f"Invalid JSON message from connection {connection_id}")
        except Exception as e:
            self.logger.error(f"Error handling message from connection {connection_id}: {e}")
    
    async def _heartbeat(self, websocket: WebSocketServerProtocol, connection_id: str):
        """Send periodic heartbeat to keep connection alive"""
        try:
            while connection_id in self.connections:
                await asyncio.sleep(self.heartbeat_interval)
                
                if connection_id in self.connections:
                    ping_message = WebSocketMessage(
                        type=MessageType.PING,
                        user_id="system",
                        data={'timestamp': datetime.utcnow().isoformat()}
                    )
                    await websocket.send(ping_message.to_json())
                    
        except Exception as e:
            self.logger.error(f"Error in heartbeat for connection {connection_id}: {e}")
    
    async def _cleanup_connection(self, connection_id: str, user_id: str):
        """Clean up connection when it's closed"""
        try:
            # Remove from connections
            if connection_id in self.connections:
                del self.connections[connection_id]
            
            # Remove from user connections
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up connection {connection_id}: {e}")
    
    async def send_alert(self, user_id: str, alert_data: Dict[str, Any]):
        """Send alert to a specific user"""
        try:
            message = WebSocketMessage(
                type=MessageType.ALERT,
                user_id=user_id,
                data=alert_data
            )
            
            await self._send_to_user(user_id, message)
            
        except Exception as e:
            self.logger.error(f"Error sending alert to user {user_id}: {e}")
    
    async def send_balance_update(self, user_id: str, balance_data: Dict[str, Any]):
        """Send balance update to a specific user"""
        try:
            message = WebSocketMessage(
                type=MessageType.BALANCE_UPDATE,
                user_id=user_id,
                data=balance_data
            )
            
            await self._send_to_user(user_id, message)
            
        except Exception as e:
            self.logger.error(f"Error sending balance update to user {user_id}: {e}")
    
    async def send_transaction_notification(self, user_id: str, transaction_data: Dict[str, Any]):
        """Send transaction notification to a specific user"""
        try:
            message = WebSocketMessage(
                type=MessageType.TRANSACTION_NOTIFICATION,
                user_id=user_id,
                data=transaction_data
            )
            
            await self._send_to_user(user_id, message)
            
        except Exception as e:
            self.logger.error(f"Error sending transaction notification to user {user_id}: {e}")
    
    async def send_goal_progress_update(self, user_id: str, goal_data: Dict[str, Any]):
        """Send goal progress update to a specific user"""
        try:
            message = WebSocketMessage(
                type=MessageType.GOAL_PROGRESS_UPDATE,
                user_id=user_id,
                data=goal_data
            )
            
            await self._send_to_user(user_id, message)
            
        except Exception as e:
            self.logger.error(f"Error sending goal progress update to user {user_id}: {e}")
    
    async def send_metrics_update(self, user_id: str, metrics_data: Dict[str, Any]):
        """Send performance metrics update to a specific user"""
        try:
            message = WebSocketMessage(
                type=MessageType.PERFORMANCE_METRICS_UPDATE,
                user_id=user_id,
                data=metrics_data
            )
            
            await self._send_to_user(user_id, message)
            
        except Exception as e:
            self.logger.error(f"Error sending metrics update to user {user_id}: {e}")
    
    async def send_dashboard_refresh(self, user_id: str, refresh_data: Dict[str, Any] = None):
        """Send dashboard refresh notification to a specific user"""
        try:
            message = WebSocketMessage(
                type=MessageType.DASHBOARD_REFRESH,
                user_id=user_id,
                data=refresh_data or {'message': 'Dashboard data updated'}
            )
            
            await self._send_to_user(user_id, message)
            
        except Exception as e:
            self.logger.error(f"Error sending dashboard refresh to user {user_id}: {e}")
    
    async def _send_to_user(self, user_id: str, message: WebSocketMessage):
        """Send message to all connections for a specific user"""
        try:
            if user_id not in self.user_connections:
                return
            
            # Get all connections for the user
            user_connections = self.user_connections[user_id].copy()
            
            # Send message to each connection
            for connection_id in user_connections:
                if connection_id in self.connections:
                    try:
                        websocket = self.connections[connection_id]
                        await websocket.send(message.to_json())
                    except Exception as e:
                        self.logger.error(f"Error sending message to connection {connection_id}: {e}")
                        # Remove failed connection
                        await self._cleanup_connection(connection_id, user_id)
                        
        except Exception as e:
            self.logger.error(f"Error sending message to user {user_id}: {e}")
    
    async def broadcast_message(self, message: WebSocketMessage):
        """Broadcast message to all connected users"""
        try:
            # Send to all users
            for user_id in self.user_connections.keys():
                await self._send_to_user(user_id, message)
                
        except Exception as e:
            self.logger.error(f"Error broadcasting message: {e}")
    
    async def _handle_dashboard_refresh(self, user_id: str):
        """Handle dashboard refresh request"""
        try:
            # This would trigger a dashboard refresh for the user
            # For now, just log the request
            self.logger.info(f"Dashboard refresh requested for user {user_id}")
            
        except Exception as e:
            self.logger.error(f"Error handling dashboard refresh for user {user_id}: {e}")
    
    async def _handle_alert_read(self, user_id: str, alert_id: str):
        """Handle alert read acknowledgment"""
        try:
            # This would mark the alert as read in the database
            # For now, just log the acknowledgment
            self.logger.info(f"Alert {alert_id} marked as read by user {user_id}")
            
        except Exception as e:
            self.logger.error(f"Error handling alert read for user {user_id}, alert {alert_id}: {e}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        try:
            total_connections = len(self.connections)
            total_users = len(self.user_connections)
            
            user_connection_counts = {}
            for user_id, connections in self.user_connections.items():
                user_connection_counts[user_id] = len(connections)
            
            return {
                'total_connections': total_connections,
                'total_users': total_users,
                'user_connection_counts': user_connection_counts,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting connection stats: {e}")
            return {}
    
    def is_user_connected(self, user_id: str) -> bool:
        """Check if a user has active WebSocket connections"""
        return user_id in self.user_connections and len(self.user_connections[user_id]) > 0
    
    def get_user_connection_count(self, user_id: str) -> int:
        """Get number of active connections for a user"""
        if user_id in self.user_connections:
            return len(self.user_connections[user_id])
        return 0 