# backend/app/api/endpoints/shifts.py
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
import uuid

from app.api import deps
from app.models.shift import Shift, ShiftAssignment
from app.models.user import User
from app.models.employee import Employee
from app.schemas.shift import Shift as ShiftSchema, ShiftCreate, ShiftUpdate, ShiftList
from app.schemas.shift import ShiftAssignment as ShiftAssignmentSchema, ShiftAssignmentCreate

router = APIRouter()

@router.get("/", response_model=ShiftList)
def get_shifts(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = Query(0, description="تخطي"),
    limit: int = Query(100, description="الحد الأقصى"),
    center_id: Optional[UUID] = Query(None, description="تصفية حسب المركز"),
    shift_date: Optional[date] = Query(None, description="تصفية حسب التاريخ"),
) -> dict:
    """جلب قائمة المناوبات"""
    query = db.query(Shift)
    
    if center_id:
        query = query.filter(Shift.center_id == center_id)
    
    if shift_date:
        query = query.filter(Shift.date >= shift_date)
    
    total = query.count()
    shifts = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": shifts
    }

@router.get("/by_month")
def get_shifts_by_month(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    center_id: Optional[UUID] = Query(None, description="معرف المركز"),
    start_date: Optional[date] = Query(None, description="تاريخ البداية (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="تاريخ النهاية (YYYY-MM-DD)"),
    limit: int = Query(500, description="الحد الأقصى للنتائج"),
) -> dict:
    """جلب المناوبات لشهر محدد"""
    query = db.query(Shift)
    
    if center_id:
        query = query.filter(Shift.center_id == center_id)
    
    if start_date:
        query = query.filter(Shift.date >= start_date)
    
    if end_date:
        query = query.filter(Shift.date < end_date)
    
    # 👈 ترتيب تنازلي (الأحدث أولاً)
    shifts = query.order_by(Shift.date.desc()).limit(limit).all()
    
    # تحويل النتيجة إلى الشكل المطلوب مع إضافة الموظفين
    result = []
    for shift in shifts:
        shift_data = {
            "id": str(shift.id),
            "date": shift.date.isoformat(),
            "shift_type": shift.shift_type,
            "center_id": str(shift.center_id) if shift.center_id else None,
            "assignments": []
        }
        
        # إضافة تعيينات الموظفين
        for assignment in shift.assignments:
            employee = db.query(Employee).filter(Employee.id == assignment.employee_id).first()
            shift_data["assignments"].append({
                "employee_id": str(assignment.employee_id) if assignment.employee_id else None,
                "employee_name": employee.full_name if employee else "غير معروف"
            })
        
        result.append(shift_data)
    
    return {"items": result}

@router.post("/", response_model=ShiftSchema, status_code=status.HTTP_201_CREATED)
def create_shift(
    shift_in: ShiftCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Shift:
    """إنشاء مناوبة جديدة"""
    if current_user.role not in ["chief_paramedic", "field_leader", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="لا تملك صلاحية إنشاء مناوبات"
        )
    
    shift = Shift(**shift_in.dict())
    db.add(shift)
    db.commit()
    db.refresh(shift)
    
    return shift

@router.get("/{shift_id}", response_model=ShiftSchema)
def get_shift(
    shift_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Shift:
    """جلب بيانات مناوبة محددة"""
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    
    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المناوبة غير موجودة"
        )
    
    return shift

@router.post("/{shift_id}/assign")
def assign_employee(
    shift_id: UUID,
    assignment: ShiftAssignmentCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> dict:
    """تعيين موظف لمناوبة"""
    if current_user.role not in ["chief_paramedic", "field_leader"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="لا تملك صلاحية تعيين موظفين"
        )
    
    shift_assignment = ShiftAssignment(**assignment.dict())
    db.add(shift_assignment)
    db.commit()
    
    return {"message": "تم تعيين الموظف بنجاح"}

# ===== دالة تحديث مناوبة موظف =====
@router.put("/update")
def update_employee_shift(
    data: dict = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """تحديث مناوبة موظف ليوم محدد"""
    employee_id = data.get("employee_id")
    date_str = data.get("date")
    shift_type = data.get("shift_type")
    
    if not employee_id or not date_str or not shift_type:
        raise HTTPException(status_code=400, detail="بيانات ناقصة")
    
    # تحويل النص إلى UUID
    try:
        emp_uuid = UUID(employee_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"معرف موظف غير صالح: {employee_id}, خطأ: {str(e)}")
    
    # تحويل التاريخ
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"صيغة تاريخ غير صالحة: {date_str}, خطأ: {str(e)}")
    
    # التحقق من وجود الموظف في قاعدة البيانات
    employee = db.query(Employee).filter(Employee.id == emp_uuid).first()
    if not employee:
        raise HTTPException(status_code=404, detail="الموظف غير موجود")
    
    # الحصول على مركز الموظف
    center_id = employee.center_id
    if not center_id:
        raise HTTPException(status_code=400, detail="الموظف غير مرتبط بمركز")
    
    # البحث عن المناوبة في ذلك اليوم للمركز
    shift = db.query(Shift).filter(
        Shift.center_id == center_id,
        Shift.date == target_date
    ).first()
    
    if not shift:
        # إذا ما في مناوبة، ننشئ واحدة جديدة
        shift = Shift(
            id=uuid.uuid4(),
            date=target_date,
            shift_type=shift_type,
            center_id=center_id
        )
        db.add(shift)
        db.commit()
        db.refresh(shift)
    else:
        # تحديث نوع المناوبة في جدول Shift نفسه
        shift.shift_type = shift_type
    
    # البحث عن تعيين الموظف
    assignment = db.query(ShiftAssignment).filter(
        ShiftAssignment.shift_id == shift.id,
        ShiftAssignment.employee_id == emp_uuid
    ).first()
    
    if not assignment:
        # إضافة تعيين جديد
        assignment = ShiftAssignment(
            id=uuid.uuid4(),
            shift_id=shift.id,
            employee_id=emp_uuid
        )
        db.add(assignment)
    else:
        # تحديث الموظف في التعيين الموجود
        assignment.employee_id = emp_uuid
    
    # تأكيد التغييرات
    db.commit()
    db.refresh(assignment)
    
    # تأكد من أن employee_id محفوظ بشكل صحيح
    print(f"✅ تم حفظ تعيين: {assignment.id}, موظف: {assignment.employee_id}")
    
    return {"message": "تم التحديث بنجاح", "saved_id": str(assignment.id)}