# backend/app/schemas/center.py
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class CenterBase(BaseModel):
    code: str
    name: str
    city: str = "الرياض"
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    address: Optional[str] = None
    coverage_area: Optional[float] = None
    is_active: bool = True

class CenterCreate(CenterBase):
    pass

class CenterUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    address: Optional[str] = None
    coverage_area: Optional[float] = None
    is_active: Optional[bool] = None
    field_leader_id: Optional[UUID] = None

class Center(CenterBase):
    id: UUID
    field_leader_id: Optional[UUID]
    
    class Config:
        from_attributes = True

class CenterList(BaseModel):
    total: int
    items: List[Center]
    
    class Config:
        from_attributes = True