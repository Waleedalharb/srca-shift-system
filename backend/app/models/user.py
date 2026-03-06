# backend/app/models/user.py
from sqlalchemy import Column, String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from ..core.database import Base
import uuid
import enum

class UserRole(str, enum.Enum):
    # ===== الإدارة العليا =====
    CHIEF_PARAMEDIC = "chief_paramedic"        # 👤 كبير المسعفين - كل الصلاحيات
    
    # ===== المشرفون =====
    FIELD_LEADER = "field_leader"              # 👥 مشرف مركز - يدير فريقه
    OPERATIONS_SUPERVISOR = "operations_supervisor"  # 🖥️ مشرف عمليات - يشرف على غرفة العمليات
    
    # ===== العمليات =====
    OPERATIONS_CONTROL = "operations_control"  # 🖥️ تحكم عملياتي
    RESPONSE_COORDINATOR = "response_coordinator"  # 📞 تنسيق استجابة
    
    # ===== الطواقم الإسعافية =====
    PARAMEDIC = "paramedic"                    # 👨‍⚕️ أخصائي إسعاف
    EMT = "emt"                                 # 🚑 مسعف
    ADMIN = "admin"                             # 📋 إداري

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(200))
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole))
    
    # ربط مع الموظف
    employee_id = Column(UUID, ForeignKey("employees.id"), nullable=True)
    
    # العلاقات
    employee = relationship("Employee", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.username} - {self.role.value}>"