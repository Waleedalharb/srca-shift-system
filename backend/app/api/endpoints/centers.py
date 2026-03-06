# backend/app/api/endpoints/centers.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api import deps
from app.models.center import EmergencyCenter
from app.models.user import User
from app.schemas.center import Center, CenterCreate, CenterUpdate, CenterList

router = APIRouter()

@router.get("/", response_model=CenterList)
def get_centers(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = Query(0, description="تخطي"),
    limit: int = Query(100, description="الحد الأقصى"),
    search: Optional[str] = Query(None, description="بحث بالاسم أو الرمز"),
) -> dict:
    """جلب قائمة المراكز"""
    query = db.query(EmergencyCenter)
    
    if search:
        query = query.filter(
            (EmergencyCenter.name.contains(search)) | 
            (EmergencyCenter.code.contains(search))
        )
    
    total = query.count()
    centers = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": centers
    }

@router.get("/{center_id}", response_model=Center)
def get_center(
    center_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> EmergencyCenter:
    """جلب بيانات مركز محدد"""
    center = db.query(EmergencyCenter).filter(EmergencyCenter.id == center_id).first()
    
    if not center:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المركز غير موجود"
        )
    
    return center

@router.post("/", response_model=Center, status_code=status.HTTP_201_CREATED)
def create_center(
    center_in: CenterCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> EmergencyCenter:
    """إنشاء مركز جديد (للمشرفين فقط)"""
    if current_user.role not in ["chief_paramedic", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="لا تملك صلاحية إنشاء مراكز"
        )
    
    # التحقق من عدم تكرار الرمز
    existing = db.query(EmergencyCenter).filter(
        EmergencyCenter.code == center_in.code
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="رمز المركز موجود مسبقاً"
        )
    
    center = EmergencyCenter(**center_in.dict())
    db.add(center)
    db.commit()
    db.refresh(center)
    
    return center

@router.put("/{center_id}", response_model=Center)
def update_center(
    center_id: UUID,
    center_in: CenterUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> EmergencyCenter:
    """تحديث بيانات مركز"""
    center = db.query(EmergencyCenter).filter(EmergencyCenter.id == center_id).first()
    
    if not center:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المركز غير موجود"
        )
    
    update_data = center_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(center, field, value)
    
    db.commit()
    db.refresh(center)
    
    return center

@router.get("/{center_id}/coverage")
def get_center_coverage(
    center_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> dict:
    """حساب نسبة تغطية المركز"""
    center = db.query(EmergencyCenter).filter(EmergencyCenter.id == center_id).first()
    
    if not center:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المركز غير موجود"
        )
    
    return {
        "center_id": center_id,
        "center_name": center.name,
        "coverage_percentage": center.coverage_percentage,
        "status": "جيد" if center.coverage_percentage >= 85 else "ضعيف"
    }