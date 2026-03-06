# backend/app/api/endpoints/incidents.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.api import deps
from app.models.incident import Incident
from app.models.user import User
from app.schemas.incident import Incident as IncidentSchema, IncidentCreate, IncidentUpdate, IncidentList

router = APIRouter()

@router.get("/", response_model=IncidentList)
def get_incidents(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = Query(0, description="تخطي"),
    limit: int = Query(100, description="الحد الأقصى"),
) -> dict:
    """جلب قائمة البلاغات"""
    query = db.query(Incident)
    
    total = query.count()
    incidents = query.order_by(Incident.call_time.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": incidents
    }

@router.post("/", response_model=IncidentSchema, status_code=status.HTTP_201_CREATED)
def create_incident(
    incident_in: IncidentCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Incident:
    """تسجيل بلاغ جديد"""
    incident = Incident(**incident_in.dict())
    db.add(incident)
    db.commit()
    db.refresh(incident)
    
    return incident

@router.put("/{incident_id}/response")
def update_response_time(
    incident_id: UUID,
    arrival_time: datetime,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> dict:
    """تحديث وقت الاستجابة للبلاغ"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="البلاغ غير موجود"
        )
    
    incident.arrival_time = arrival_time
    # حساب وقت الاستجابة بالثواني
    if incident.call_time:
        response_time = (arrival_time - incident.call_time).total_seconds()
        incident.response_time = int(response_time)
    
    db.commit()
    
    return {
        "message": "تم تحديث وقت الاستجابة",
        "response_time_seconds": incident.response_time
    }