# backend/app/schemas/incident.py
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class IncidentBase(BaseModel):
    incident_number: str
    location: str
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    priority: str = "medium"
    call_time: datetime
    dispatch_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    shift_id: Optional[UUID] = None
    assigned_crew: Optional[UUID] = None

class IncidentCreate(IncidentBase):
    pass

class IncidentUpdate(BaseModel):
    dispatch_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    response_time: Optional[int] = None
    assigned_crew: Optional[UUID] = None

class Incident(IncidentBase):
    id: UUID
    response_time: Optional[int]
    
    class Config:
        from_attributes = True

class IncidentList(BaseModel):
    total: int
    items: List[Incident]
    
    class Config:
        from_attributes = True