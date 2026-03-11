# backend/app/schemas/employee.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID

class EmployeeBase(BaseModel):
    emp_no: str = Field(..., description="الرقم الوظيفي")
    full_name: str = Field(..., description="الاسم الكامل")
    national_id: Optional[str] = Field(None, description="رقم الهوية")
    phone: Optional[str] = Field(None, description="رقم الجوال")
    email: Optional[str] = Field(None, description="البريد الإلكتروني")
    hire_date: Optional[date] = Field(None, description="تاريخ التعيين")
    employee_type: str = Field(..., description="نوع الموظف")

class EmployeeCreate(EmployeeBase):
    center_id: Optional[UUID] = Field(None, description="معرف المركز")
    role_id: Optional[UUID] = Field(None, description="معرف الدور")

class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    center_id: Optional[UUID] = None
    role_id: Optional[UUID] = None
    employee_type: Optional[str] = None        # ✅ أضف هذا السطر
    is_on_duty: Optional[bool] = None
    is_available: Optional[bool] = None
    is_active: Optional[bool] = None           # ✅ أضف هذا السطر
    certifications: Optional[List[str]] = None  # ✅ أضف هذا السطر (اختياري)
    notes: Optional[str] = None                  # ✅ أضف هذا السطر (اختياري)

class Employee(EmployeeBase):
    id: UUID
    center_id: Optional[UUID]
    role_id: Optional[UUID]
    supervisor_id: Optional[UUID]
    is_on_duty: bool
    is_available: bool
    is_active: bool                              # ✅ أضف هذا السطر
    total_hours: int
    missions_count: int
    certifications: Optional[List[str]] = Field(default_factory=list)  # ✅ أضف
    notes: Optional[str] = None                   # ✅ أضف
    
    class Config:
        from_attributes = True

class EmployeeList(BaseModel):
    total: int
    items: List[Employee]
    
    class Config:
        from_attributes = True