# backend/app/models/center.py
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from ..core.database import Base
import uuid

class EmergencyCenter(Base):
    __tablename__ = "emergency_centers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(10), unique=True)  # HAER, DBA, SHF
    name = Column(String(100))  # مركز الحائر
    city = Column(String(50), default="الرياض")
    
    # القيادة الميدانية
    field_leader_id = Column(UUID, ForeignKey("employees.id"), nullable=True)
    
    # الموقع
    latitude = Column(String(20))
    longitude = Column(String(20))
    address = Column(String(200))
    coverage_area = Column(Float)  # مساحة التغطية كم²
    
    # التكوين المثالي
    ideal_crew = Column(JSON, default={
        "paramedics": 2,    # أخصائيين
        "emts": 2,          # مسعفين (عدلت من 4 إلى 2)
        "admins": 1,        # إداريين
        "ambulances": 2     # سيارات إسعاف
    })
    
    # الحالة
    is_active = Column(Boolean, default=True)
    
    # العلاقات - مع تحديد foreign_keys بشكل صريح
    field_leader = relationship("Employee", foreign_keys=[field_leader_id])
    employees = relationship("Employee", back_populates="center", foreign_keys="[Employee.center_id]")
    ambulances = relationship("Ambulance", back_populates="center", foreign_keys="[Ambulance.current_center_id]")
    shifts = relationship("Shift", back_populates="center", foreign_keys="[Shift.center_id]")
    
    @property
    def coverage_percentage(self) -> float:
        """حساب نسبة تغطية المركز للمنطقة المخصصة له"""
        
        # عدد الموظفين النشطين في المركز
        active_employees = [e for e in self.employees if e.is_active]
        
        # عدد الأخصائيين والمسعفين المتاحين
        available_paramedics = sum(1 for e in active_employees if e.employee_type == "paramedic")
        available_emts = sum(1 for e in active_employees if e.employee_type == "emt")
        
        # العدد المطلوب من التكوين المثالي
        required_paramedics = self.ideal_crew.get('paramedics', 2)
        required_emts = self.ideal_crew.get('emts', 2)
        
        # حساب نسبة التغطية
        if required_paramedics + required_emts == 0:
            return 0
            
        # وزن متساوي للأخصائيين والمسعفين
        paramedic_ratio = min(1.0, available_paramedics / required_paramedics) if required_paramedics > 0 else 1.0
        emt_ratio = min(1.0, available_emts / required_emts) if required_emts > 0 else 1.0
        
        # متوسط النسبتين
        coverage = (paramedic_ratio + emt_ratio) / 2 * 100
        
        return round(coverage, 1)
    
    @property
    def coverage_status(self) -> str:
        """حالة التغطية (ممتاز/جيد/ضعيف)"""
        coverage = self.coverage_percentage
        if coverage >= 90:
            return "ممتاز"
        elif coverage >= 70:
            return "جيد"
        elif coverage >= 50:
            return "متوسط"
        else:
            return "ضعيف"
    
    @property
    def coverage_color(self) -> str:
        """لون التغطية (أخضر/أصفر/أحمر)"""
        coverage = self.coverage_percentage
        if coverage >= 90:
            return "#42924B"  # أخضر
        elif coverage >= 70:
            return "#F1B944"  # أصفر
        elif coverage >= 50:
            return "#FF7C10"  # برتقالي
        else:
            return "#CE2E26"  # أحمر
    
    def get_stats(self) -> dict:
        """إحصائيات المركز"""
        active_employees = [e for e in self.employees if e.is_active]
        
        return {
            "total_employees": len(active_employees),
            "paramedics": sum(1 for e in active_employees if e.employee_type == "paramedic"),
            "emts": sum(1 for e in active_employees if e.employee_type == "emt"),
            "admins": sum(1 for e in active_employees if e.employee_type == "admin"),
            "on_duty": sum(1 for e in active_employees if e.is_on_duty),
            "available": sum(1 for e in active_employees if e.is_available and not e.is_on_duty),
            "coverage": self.coverage_percentage,
            "status": self.coverage_status
        }
    
    def __repr__(self):
        return f"<EmergencyCenter {self.code}: {self.name}>"