# backend/app/models/notification.py
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship  
from ..core.database import Base
import uuid
import enum

class NotificationType(str, enum.Enum):
    SHIFT_CHANGE = "shift_change"      # تغيير في المناوبة
    NEW_SHIFT = "new_shift"            # إضافة مناوبة جديدة
    SHIFT_DELETED = "shift_deleted"    # حذف مناوبة
    SYSTEM = "system"                  # إشعار نظام
    ALERT = "alert"                    # تنبيه مهم

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(SQLEnum(NotificationType), default=NotificationType.SYSTEM)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # العلاقات
    user = relationship("User", backref="notifications")
    
    def __repr__(self):
        return f"<Notification {self.title} - {self.is_read}>"