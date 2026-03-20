# backend/app/models/notification.py
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship  
from ..core.database import Base
import uuid
import enum

class NotificationType(str, enum.Enum):
    SHIFT_CHANGE = "shift_change"
    NEW_SHIFT = "new_shift"
    SHIFT_DELETED = "shift_deleted"
    SYSTEM = "system"
    ALERT = "alert"

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(SQLEnum(NotificationType), default=NotificationType.SYSTEM)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # العلاقات - استخدم back_populates لتتناسب مع user.py
    user = relationship("User", back_populates="notifications")
    
    def __repr__(self):
        return f"<Notification {self.title} - {self.is_read}>"