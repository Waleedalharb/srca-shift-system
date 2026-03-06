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
    is_on_duty: Optional[bool] = None
    is_available: Optional[bool] = None

class Employee(EmployeeBase):
    id: UUID
    center_id: Optional[UUID]
    role_id: Optional[UUID]
    supervisor_id: Optional[UUID]
    is_on_duty: bool
    is_available: bool
    total_hours: int
    missions_count: int
    
    class Config:
        from_attributes = True  # تغيير من orm_mode إلى from_attributes

class EmployeeList(BaseModel):
    total: int
    items: List[Employee]
    
    class Config:
        from_attributes = True