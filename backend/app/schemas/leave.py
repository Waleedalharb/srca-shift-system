# backend/app/schemas/leave.py
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class LeaveBase(BaseModel):
    employee_id: UUID
    leave_type: str
    start_date: datetime
    end_date: datetime
    days_count: int
    reason: Optional[str] = None

class LeaveCreate(LeaveBase):
    pass

class LeaveUpdate(BaseModel):
    status: Optional[str] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None

class Leave(LeaveBase):
    id: UUID
    status: str
    approved_by: Optional[UUID]
    approved_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class LeaveList(BaseModel):
    total: int
    items: List[Leave]
    
    class Config:
        from_attributes = True