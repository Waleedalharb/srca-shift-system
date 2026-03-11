# backend/app/models/center.py
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from ..core.database import Base
import uuid

class EmergencyCenter(Base):
    __tablename__ = "emergency_centers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(10), unique=True)  # HQ, C001, DEP1
    name = Column(String(100))  # المركز الرئيسي للقطاع, مركز الحائر, التمركز الأول
    center_type = Column(String(20), default="مركز ثابت")  # قيادة, مركز ثابت, تمركز
    city = Column(String(50), default="الرياض")
    
    # للتمركزات (مواقع الدعم)
    is_virtual = Column(Boolean, default=False)  # True للتمركزات
    is_hq = Column(Boolean, default=False)  # True للمركز الرئيسي
    
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
        "emts": 2,          # مسعفين
        "admins": 1,        # إداريين
        "ambulances": 2     # سيارات إسعاف
    })
    
    # الحالة
    is_active = Column(Boolean, default=True)
    
    # العلاقات
    field_leader = relationship("Employee", foreign_keys=[field_leader_id])
    employees = relationship("Employee", back_populates="center", foreign_keys="[Employee.center_id]")
    ambulances = relationship("Ambulance", back_populates="center", foreign_keys="[Ambulance.current_center_id]")
    shifts = relationship("Shift", back_populates="center", foreign_keys="[Shift.center_id]")
    
    @property
    def coverage_percentage(self) -> float:
        """حساب نسبة تغطية المركز للمنطقة المخصصة له"""
        if self.is_virtual:
            return 100.0  # التمركزات متنقلة، تغطيتها كاملة افتراضياً
        
        active_employees = [e for e in self.employees if e.is_active]
        
        available_paramedics = sum(1 for e in active_employees if e.employee_type == "paramedic")
        available_emts = sum(1 for e in active_employees if e.employee_type == "emt")
        
        required_paramedics = self.ideal_crew.get('paramedics', 2)
        required_emts = self.ideal_crew.get('emts', 2)
        
        if required_paramedics + required_emts == 0:
            return 0
            
        paramedic_ratio = min(1.0, available_paramedics / required_paramedics) if required_paramedics > 0 else 1.0
        emt_ratio = min(1.0, available_emts / required_emts) if required_emts > 0 else 1.0
        
        coverage = (paramedic_ratio + emt_ratio) / 2 * 100
        return round(coverage, 1)
    
    @property
    def coverage_status(self) -> str:
        """حالة التغطية"""
        if self.is_virtual:
            return "متنقل"
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
        """لون التغطية"""
        if self.is_virtual:
            return "#45CFEF"  # أزرق للتمركزات
        coverage = self.coverage_percentage
        if coverage >= 90:
            return "#42924B"
        elif coverage >= 70:
            return "#F1B944"
        elif coverage >= 50:
            return "#FF7C10"
        else:
            return "#CE2E26"
    
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