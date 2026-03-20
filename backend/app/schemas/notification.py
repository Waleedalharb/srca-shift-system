# backend/app/schemas/notification.py
from pydantic import BaseModel
from datetime import datetime
import uuid
from app.models.notification import NotificationType

class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    message: str
    type: NotificationType
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True