# backend/app/models/employee.py
from sqlalchemy import Column, String, Integer, ForeignKey, Date, Boolean, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from ..core.database import Base
import uuid

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    emp_no = Column(String(10), unique=True, nullable=False, index=True)
    emp_code = Column(String(20), nullable=True)  # ✅ رمز الموظف (A1, B7, O12, ...)
    full_name = Column(String(100), nullable=False)
    national_id = Column(String(20), unique=True)
    phone = Column(String(20))
    email = Column(String(100))
    hire_date = Column(Date)
    
    # نوع الموظف (أخصائي/مسعف/إداري)
    employee_type = Column(String(20))  # paramedic, emt, admin
    
    # المركز التابع له
    center_id = Column(UUID, ForeignKey("emergency_centers.id"))
    role_id = Column(UUID, ForeignKey("roles.id"))
    supervisor_id = Column(UUID, ForeignKey("employees.id"), nullable=True)
    
    # الحالة الحالية
    is_active = Column(Boolean, default=True)  # ✅ حالة النشاط
    is_on_duty = Column(Boolean, default=False)
    is_available = Column(Boolean, default=True)
    current_shift_id = Column(UUID, ForeignKey("shifts.id"), nullable=True)
    
    # الشهادات والمؤهلات
    certifications = Column(JSON, default=list)
    
    # الإحصائيات التراكمية
    total_hours = Column(Integer, default=0)
    missions_count = Column(Integer, default=0)
    avg_response_time = Column(Float, default=0)
    
    # العلاقات - مع تحديد foreign_keys بشكل صريح
    center = relationship("EmergencyCenter", back_populates="employees", foreign_keys=[center_id])
    role = relationship("Role", foreign_keys=[role_id])
    supervisor = relationship("Employee", remote_side=[id], foreign_keys=[supervisor_id])
    user = relationship("User", back_populates="employee", uselist=False, foreign_keys="[User.employee_id]")
    shifts = relationship("ShiftAssignment", back_populates="employee", foreign_keys="[ShiftAssignment.employee_id]")
    leaves = relationship("Leave", back_populates="employee", foreign_keys="[Leave.employee_id]")
    
    def __repr__(self):
        # عرض حالة النشاط في التمثيل النصي
        active_status = "نشط" if self.is_active else "غير نشط"
        return f"<Employee {self.emp_no}: {self.full_name} ({active_status})>"