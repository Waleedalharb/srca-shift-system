# backend/app/api/endpoints/leaves.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.api import deps
from app.models.leave import Leave
from app.models.user import User
from app.models.employee import Employee
from app.schemas.leave import Leave as LeaveSchema, LeaveCreate, LeaveUpdate, LeaveList

router = APIRouter()

@router.get("/", response_model=LeaveList)
def get_leaves(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = Query(0, description="تخطي"),
    limit: int = Query(100, description="الحد الأقصى"),
    status_filter: Optional[str] = Query(None, description="تصفية حسب الحالة"),
) -> dict:
    """جلب قائمة الإجازات"""
    query = db.query(Leave)
    
    # قيادة ميدانية تشوف إجازات مركزها فقط
    if current_user.role == "field_leader":
        query = query.join(Employee).filter(Employee.center_id == current_user.employee.center_id)
    
    if status_filter:
        query = query.filter(Leave.status == status_filter)
    
    total = query.count()
    leaves = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": leaves
    }

@router.post("/", response_model=LeaveSchema, status_code=status.HTTP_201_CREATED)
def create_leave(
    leave_in: LeaveCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Leave:
    """تقديم طلب إجازة"""
    leave = Leave(**leave_in.dict())
    db.add(leave)
    db.commit()
    db.refresh(leave)
    
    return leave

@router.put("/{leave_id}/approve")
def approve_leave(
    leave_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> dict:
    """الموافقة على طلب إجازة"""
    if current_user.role not in ["chief_paramedic", "field_leader"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="لا تملك صلاحية الموافقة على الإجازات"
        )
    
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="طلب الإجازة غير موجود"
        )
    
    leave.status = "approved"
    leave.approved_by = current_user.employee_id
    leave.approved_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "تم الموافقة على طلب الإجازة"}