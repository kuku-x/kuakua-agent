import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    _instance: "WebSocketManager | None" = None

    def __new__(cls) -> "WebSocketManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._connections: list[WebSocket] = []
            cls._instance._lock = asyncio.Lock()
        return cls._instance

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self._connections)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            if websocket in self._connections:
                self._connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self._connections)}")

    async def broadcast(self, message: dict[str, Any]) -> None:
        payload = json.dumps(message, ensure_ascii=False)
        dead: list[WebSocket] = []
        async with self._lock:
            conns = list(self._connections)
        for ws in conns:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        async with self._lock:
            for ws in dead:
                if ws in self._connections:
                    self._connections.remove(ws)

    async def send_praise(self, content: str, trigger: str) -> None:
        await self.broadcast({
            "type": "praise_push",
            "data": {
                "content": content,
                "trigger": trigger,
            }
        })

    async def send_summary_progress(self, date: str, progress: str) -> None:
        await self.broadcast({
            "type": "summary_progress",
            "data": {
                "date": date,
                "progress": progress,
            }
        })

    async def send_chat_stream(self, chat_id: str, chunk: str, done: bool) -> None:
        await self.broadcast({
            "type": "chat_stream",
            "data": {
                "chat_id": chat_id,
                "chunk": chunk,
                "done": done,
            }
        })

    @property
    def connection_count(self) -> int:
        return len(self._connections)


ws_manager = WebSocketManager()