# backend/app/models/leave.py
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from ..core.database import Base
import uuid
from datetime import datetime

class Leave(Base):
    __tablename__ = "leaves"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID, ForeignKey("employees.id"))
    
    leave_type = Column(String(20))  # annual, sick, emergency, etc
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    days_count = Column(Integer)
    
    reason = Column(Text)
    
    # الحالة
    status = Column(String(20), default="pending")  # pending, approved, rejected
    approved_by = Column(UUID, ForeignKey("employees.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # العلاقات - مع تحديد foreign_keys بشكل صريح
    employee = relationship("Employee", back_populates="leaves", foreign_keys=[employee_id])
    approver = relationship("Employee", foreign_keys=[approved_by])
    
    def __repr__(self):
        return f"<Leave {self.leave_type}>"