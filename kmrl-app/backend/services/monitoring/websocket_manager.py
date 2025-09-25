"""
WebSocket Manager for KMRL Gateway
Real-time updates and progress tracking for document processing
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Set
import json
import asyncio
from datetime import datetime
import structlog

logger = structlog.get_logger()

class WebSocketManager:
    """Manages WebSocket connections and real-time broadcasting"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, List[WebSocket]] = {}
        self.document_subscriptions: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(websocket)
        
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket, user_id: str = None):
        """Handle WebSocket disconnection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if user_id and user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Remove from document subscriptions
        for doc_id, connections in self.document_subscriptions.items():
            if websocket in connections:
                connections.remove(websocket)
        
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def subscribe_to_document(self, websocket: WebSocket, document_id: int):
        """Subscribe a connection to updates for a specific document"""
        if document_id not in self.document_subscriptions:
            self.document_subscriptions[document_id] = set()
        self.document_subscriptions[document_id].add(websocket)
        logger.info(f"Subscribed to document {document_id} updates")
    
    async def unsubscribe_from_document(self, websocket: WebSocket, document_id: int):
        """Unsubscribe a connection from document updates"""
        if document_id in self.document_subscriptions:
            self.document_subscriptions[document_id].discard(websocket)
            if not self.document_subscriptions[document_id]:
                del self.document_subscriptions[document_id]
        logger.info(f"Unsubscribed from document {document_id} updates")
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to send message to connection: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            await self.disconnect(connection)
    
    async def broadcast_to_user(self, user_id: str, message: dict):
        """Broadcast message to specific user"""
        if user_id not in self.user_connections:
            return
        
        disconnected = []
        for connection in self.user_connections[user_id]:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to send message to user {user_id}: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            await self.disconnect(connection, user_id)
    
    async def broadcast_to_document_subscribers(self, document_id: int, message: dict):
        """Broadcast message to subscribers of a specific document"""
        if document_id not in self.document_subscriptions:
            return
        
        disconnected = []
        for connection in self.document_subscriptions[document_id]:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to send message to document {document_id} subscriber: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            await self.disconnect(connection)
    
    async def broadcast_document_update(self, document_id: int, status: str, progress: int = None, message: str = None):
        """Broadcast document processing update"""
        update_message = {
            "type": "document_update",
            "document_id": document_id,
            "status": status,
            "progress": progress,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        # Broadcast to document subscribers
        await self.broadcast_to_document_subscribers(document_id, update_message)
        
        # Also broadcast to all connections for system-wide updates
        await self.broadcast_to_all(update_message)
        
        logger.info(f"Broadcasted document {document_id} update: {status}")
    
    async def broadcast_system_status(self, status: str, message: str = None):
        """Broadcast system-wide status update"""
        status_message = {
            "type": "system_status",
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_all(status_message)
        logger.info(f"Broadcasted system status: {status}")
    
    async def broadcast_processing_stats(self, stats: dict):
        """Broadcast processing statistics"""
        stats_message = {
            "type": "processing_stats",
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_all(stats_message)
        logger.info("Broadcasted processing statistics")
    
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return len(self.active_connections)
    
    def get_user_connection_count(self, user_id: str) -> int:
        """Get number of connections for a specific user"""
        return len(self.user_connections.get(user_id, []))
    
    def get_document_subscriber_count(self, document_id: int) -> int:
        """Get number of subscribers for a specific document"""
        return len(self.document_subscriptions.get(document_id, set()))

# Global WebSocket manager instance
websocket_manager = WebSocketManager()
