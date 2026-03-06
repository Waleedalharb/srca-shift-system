# backend/app/models/incident.py
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from ..core.database import Base
import uuid
from datetime import datetime

class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_number = Column(String(50), unique=True)
    
    # تفاصيل البلاغ
    location = Column(String(200))
    latitude = Column(String(20))
    longitude = Column(String(20))
    priority = Column(String(20))  # high, medium, low
    
    # التوقيتات
    call_time = Column(DateTime)
    dispatch_time = Column(DateTime)
    arrival_time = Column(DateTime)
    end_time = Column(DateTime)
    
    # المؤشرات
    response_time = Column(Integer)  # بالثواني
    
    # العلاقات
    shift_id = Column(UUID, ForeignKey("shifts.id"))
    assigned_crew = Column(UUID, ForeignKey("employees.id"))
    
    shift = relationship("Shift", foreign_keys=[shift_id])
    crew = relationship("Employee", foreign_keys=[assigned_crew])
    
    def __repr__(self):
        return f"<Incident {self.incident_number}>"