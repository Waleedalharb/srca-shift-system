# backend/app/models/ambulance.py
from sqlalchemy import Column, String, ForeignKey, Boolean, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from ..core.database import Base
import uuid

class Ambulance(Base):
    __tablename__ = "ambulances"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plate_number = Column(String(20), unique=True)
    model = Column(String(50))
    year = Column(Integer)
    
    # الحالة
    is_operational = Column(Boolean, default=True)
    current_center_id = Column(UUID, ForeignKey("emergency_centers.id"))
    
    # العلاقات
    center = relationship("EmergencyCenter", back_populates="ambulances", foreign_keys=[current_center_id])
    
    def __repr__(self):
        return f"<Ambulance {self.plate_number}>"