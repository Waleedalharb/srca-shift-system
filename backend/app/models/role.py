# backend/app/models/role.py
from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import UUID
from ..core.database import Base
import uuid

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(20), unique=True, nullable=False)  # CHIEF_PARAMEDIC, FIELD_LEADER, etc
    name = Column(String(50), nullable=False)  # كبير المسعفين, قيادة ميدانية, etc
    level = Column(Integer, default=4)  # 1 أعلى صلاحية, 4 أقل صلاحية
    description = Column(String(200), nullable=True)
    
    def __repr__(self):
        return f"<Role {self.code}: {self.name}>"