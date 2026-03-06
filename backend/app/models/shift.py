# backend/app/models/shift.py
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from ..core.database import Base
import uuid
from datetime import datetime

class Shift(Base):
    __tablename__ = "shifts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(DateTime, nullable=False)
    shift_type = Column(String(20))
    center_id = Column(UUID, ForeignKey("emergency_centers.id"))
    
    total_incidents = Column(Integer, default=0)
    avg_response_time = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # العلاقات
    center = relationship("EmergencyCenter", back_populates="shifts", foreign_keys=[center_id])
    assignments = relationship("ShiftAssignment", back_populates="shift", foreign_keys="[ShiftAssignment.shift_id]")
    
    def __repr__(self):
        return f"<Shift {self.date}>"

class ShiftAssignment(Base):
    __tablename__ = "shift_assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shift_id = Column(UUID, ForeignKey("shifts.id"))
    employee_id = Column(UUID, ForeignKey("employees.id"))
    
    status = Column(String(20), default="scheduled")
    actual_hours = Column(Integer, default=0)
    
    # العلاقات
    shift = relationship("Shift", back_populates="assignments", foreign_keys=[shift_id])
    employee = relationship("Employee", back_populates="shifts", foreign_keys=[employee_id])
    
    def __repr__(self):
        return f"<ShiftAssignment>"