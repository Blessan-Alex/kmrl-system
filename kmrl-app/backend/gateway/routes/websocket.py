"""
WebSocket API Routes
Handles real-time updates and notifications
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.monitoring.websocket_manager import websocket_manager
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/ws", tags=["websocket"])

@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
        logger.info("WebSocket disconnected")

@router.websocket("/documents/{document_id}")
async def document_websocket(websocket: WebSocket, document_id: int):
    """WebSocket endpoint for document-specific updates"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and send document updates
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
        logger.info(f"Document WebSocket disconnected for document {document_id}")
