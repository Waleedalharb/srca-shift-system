# backend/app/models/station.py
from sqlalchemy import Column, String, Integer, ForeignKey, JSONB, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

class EmergencyCenter(Base):
    __tablename__ = "emergency_centers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(10), unique=True)  # HAER, DBA, SHF, إلخ
    name = Column(String(100))  # مركز الحائر, مركز الدار البيضاء, إلخ
    city = Column(String(50), default="الرياض")
    
    # القيادة الميدانية للمركز
    field_leader_id = Column(UUID, ForeignKey("employees.id"))
    
    # معلومات الموقع
    latitude = Column(String(20))
    longitude = Column(String(20))
    address = Column(String(200))
    
    # نطاق التغطية (كم²)
    coverage_area = Column(Integer)  # مساحة التغطية بالكيلومتر المربع
    
    # تكوين الفريق المثالي للمركز
    ideal_crew = Column(JSONB, default={
        "paramedics": 2,  # أخصائيين
        "emts": 4,  # مسعفين
        "admins": 1,  # إداريين
        "ambulances": 2  # عدد سيارات الإسعاف
    })
    
    # مؤشرات الأداء الحالية للمركز
    current_kpi = Column(JSONB, default={})
    
    # حالة المركز
    is_active = Column(Boolean, default=True)
    
    field_leader = relationship("Employee", foreign_keys=[field_leader_id])
    employees = relationship("Employee", back_populates="center", foreign_keys="[Employee.center_id]")
    
    @property
    def coverage_percentage(self) -> float:
        """حساب نسبة تغطية المركز للمنطقة المخصصة له"""
        # هذه تحسب بناءً على عدد الفرق المتاحة مقابل المساحة
        available_crews = len([e for e in self.employees if e.is_available])
        required_crews = self.ideal_crew.get('paramedics', 0) + self.ideal_crew.get('emts', 0)
        
        if required_crews == 0:
            return 0
            
        return min(100, (available_crews / required_crews) * 100)