# backend/app/schemas/shift.py
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date

class ShiftBase(BaseModel):
    date: datetime
    shift_type: str
    center_id: UUID

class ShiftCreate(ShiftBase):
    pass

class ShiftUpdate(BaseModel):
    shift_type: Optional[str] = None
    total_incidents: Optional[int] = None
    avg_response_time: Optional[int] = None

class Shift(ShiftBase):
    id: UUID
    total_incidents: int
    avg_response_time: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ShiftList(BaseModel):
    total: int
    items: List[Shift]
    
    class Config:
        from_attributes = True

class ShiftAssignmentBase(BaseModel):
    shift_id: UUID
    employee_id: UUID
    status: str = "scheduled"
    actual_hours: int = 0

class ShiftAssignmentCreate(ShiftAssignmentBase):
    pass

class ShiftAssignment(ShiftAssignmentBase):
    id: UUID
    
    class Config:
        from_attributes = True