import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.message import DirectMessage
from app.models.user import User
from app.schemas.message import DMCreate, DMOut
from app.services.connection_manager import manager

router = APIRouter()


@router.post("/dm", response_model=DMOut, status_code=201)
async def send_dm(
    body: DMCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    recipient = await db.get(User, body.recipient_id)
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    msg = DirectMessage(
        sender_id=current_user.id,
        recipient_id=body.recipient_id,
        content=body.content,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    payload = {
        "id": str(msg.id),
        "sender_id": str(msg.sender_id),
        "sender_username": current_user.username,
        "recipient_id": str(msg.recipient_id),
        "content": msg.content,
        "created_at": msg.created_at.isoformat(),
    }
    await manager.send_to_user(body.recipient_id, payload)

    return msg


@router.get("/dm/{other_user_id}", response_model=list[DMOut])
async def get_dm_history(
    other_user_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(DirectMessage)
        .where(
            or_(
                and_(
                    DirectMessage.sender_id == current_user.id,
                    DirectMessage.recipient_id == other_user_id,
                ),
                and_(
                    DirectMessage.sender_id == other_user_id,
                    DirectMessage.recipient_id == current_user.id,
                ),
            )
        )
        .order_by(desc(DirectMessage.created_at))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/conversations", response_model=list[dict])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the most recent message per conversation partner."""
    # Subquery: for each (sender, recipient) pair involving current user,
    # get the latest message id
    uid = current_user.id

    stmt = (
        select(DirectMessage)
        .where(
            or_(DirectMessage.sender_id == uid, DirectMessage.recipient_id == uid)
        )
        .order_by(desc(DirectMessage.created_at))
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()

    seen: set[uuid.UUID] = set()
    conversations = []
    for msg in messages:
        other_id = msg.recipient_id if msg.sender_id == uid else msg.sender_id
        if other_id in seen:
            continue
        seen.add(other_id)
        other = await db.get(User, other_id)
        conversations.append(
            {
                "user_id": str(other_id),
                "username": other.username if other else "unknown",
                "last_message": msg.content,
                "last_at": msg.created_at.isoformat(),
            }
        )
    return conversations
