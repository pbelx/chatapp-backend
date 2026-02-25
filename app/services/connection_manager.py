import uuid
from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # Maps user_id -> list of active WebSocket connections
        self._connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, user_id: uuid.UUID, websocket: WebSocket):
        await websocket.accept()
        self._connections[str(user_id)].append(websocket)

    def disconnect(self, user_id: uuid.UUID, websocket: WebSocket):
        uid = str(user_id)
        self._connections[uid].discard if False else None
        if websocket in self._connections[uid]:
            self._connections[uid].remove(websocket)

    async def send_to_user(self, user_id: uuid.UUID, data: dict):
        uid = str(user_id)
        dead = []
        for ws in self._connections.get(uid, []):
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections[uid].remove(ws)


manager = ConnectionManager()
