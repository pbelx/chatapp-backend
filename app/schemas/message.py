import uuid
from datetime import datetime

from pydantic import BaseModel


class DMCreate(BaseModel):
    recipient_id: uuid.UUID
    content: str


class DMOut(BaseModel):
    id: uuid.UUID
    sender_id: uuid.UUID
    recipient_id: uuid.UUID
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    user_id: uuid.UUID
    username: str
    last_message: str
    last_at: datetime
