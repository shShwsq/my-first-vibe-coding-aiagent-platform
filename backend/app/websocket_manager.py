import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        async with self._lock:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected for user {user_id}")
    
    async def disconnect(self, websocket: WebSocket, user_id: int):
        async with self._lock:
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_to_user(self, user_id: int, message: dict):
        async with self._lock:
            connections = self.active_connections.get(user_id, set()).copy()
        
        message_str = json.dumps(message, ensure_ascii=False)
        
        if not connections:
            logger.warning(f"No active WebSocket connection for user {user_id}")
            return
        
        disconnected = []
        
        for connection in connections:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                disconnected.append(connection)
        
        for conn in disconnected:
            async with self._lock:
                if user_id in self.active_connections:
                    self.active_connections[user_id].discard(conn)
    
    async def broadcast(self, message: dict):
        message_str = json.dumps(message, ensure_ascii=False)
        async with self._lock:
            connections = [
                conn
                for conns in self.active_connections.values()
                for conn in conns
            ]
        
        for connection in connections:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.error(f"Failed to broadcast message: {e}")


manager = ConnectionManager()
