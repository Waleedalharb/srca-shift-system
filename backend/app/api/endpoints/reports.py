# backend/app/api/endpoints/reports.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from uuid import UUID
from datetime import date, timedelta

from app.api import deps
from app.models.user import User
from app.models.employee import Employee
from app.models.center import EmergencyCenter
from app.models.incident import Incident
from app.models.shift import Shift

router = APIRouter()

@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> dict:
    """لوحة المعلومات الرئيسية"""
    
    # إحصائيات سريعة
    total_employees = db.query(Employee).count()
    total_centers = db.query(EmergencyCenter).count()
    
    # البلاغات اليوم
    today = date.today()
    today_incidents = db.query(Incident).filter(
        func.date(Incident.call_time) == today
    ).count()
    
    # الموظفين الحاليين
    on_duty = db.query(Employee).filter(Employee.is_on_duty == True).count()
    
    return {
        "total_employees": total_employees,
        "total_centers": total_centers,
        "today_incidents": today_incidents,
        "on_duty": on_duty,
        "message": "مرحباً بك في نظام إدارة المراكز الإسعافية"
    }