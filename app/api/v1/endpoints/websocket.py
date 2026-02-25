import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import AsyncSessionLocal
from app.models.message import DirectMessage
from app.models.user import User
from app.services.connection_manager import manager

router = APIRouter()


async def _get_user_from_token(token: str, db: AsyncSession):
    user_id = decode_token(token)
    if not user_id:
        return None
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    return result.scalar_one_or_none()


@router.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket, token: str):
    async with AsyncSessionLocal() as db:
        user = await _get_user_from_token(token, db)
        if not user:
            await websocket.close(code=4001)
            return

        await manager.connect(user.id, websocket)
        try:
            while True:
                data = await websocket.receive_json()

                recipient_id_str = data.get("recipient_id")
                content = data.get("content", "").strip()

                if not recipient_id_str or not content:
                    await websocket.send_json({"error": "recipient_id and content are required"})
                    continue

                try:
                    recipient_id = uuid.UUID(recipient_id_str)
                except ValueError:
                    await websocket.send_json({"error": "Invalid recipient_id"})
                    continue

                # Persist message
                msg = DirectMessage(
                    sender_id=user.id,
                    recipient_id=recipient_id,
                    content=content,
                )
                db.add(msg)
                await db.commit()
                await db.refresh(msg)

                payload = {
                    "id": str(msg.id),
                    "sender_id": str(msg.sender_id),
                    "sender_username": user.username,
                    "recipient_id": str(msg.recipient_id),
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                }

                # Deliver to recipient (if online) and echo back to sender
                await manager.send_to_user(recipient_id, payload)
                await manager.send_to_user(user.id, payload)

        except WebSocketDisconnect:
            manager.disconnect(user.id, websocket)
