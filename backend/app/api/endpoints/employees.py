from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from uuid import UUID, uuid4
from typing import Optional, List

from app.api import deps
from app.models.employee import Employee
from app.models.center import EmergencyCenter
from app.models.user import User
from app.schemas.employee import (
    EmployeeCreate, EmployeeUpdate, Employee as EmployeeSchema, EmployeeList
)

router = APIRouter()

def get_center_from_code(db: Session, emp_code: str) -> Optional[UUID]:
    """تحديد المركز المناسب بناءً على كود الموظف"""
    if not emp_code:
        return None
    
    # 1. مدير القطاع والقيادات (0, A0, B0, C0, D0) -> المركز الرئيسي (HQ)
    if emp_code == '0' or (emp_code.endswith('0') and len(emp_code) <= 3 and emp_code[0] in 'ABCD'):
        center = db.query(EmergencyCenter).filter(EmergencyCenter.code == 'HQ').first()
        if not center:
            # إنشاء مركز HQ إذا لم يكن موجوداً
            center = EmergencyCenter(
                id=uuid4(),
                name="المركز الرئيسي للقطاع",
                code="HQ",
                city="الرياض",
                is_active=True
            )
            db.add(center)
            db.commit()
            db.refresh(center)
        return center.id
    
    # 2. التداخلية والتدخل السريع -> التمركز (12)
    if emp_code.startswith('O') or emp_code.startswith('RR'):
        center = db.query(EmergencyCenter).filter(EmergencyCenter.code == '12').first()
        return center.id if center else None
    
    # 3. أعضاء الفرق (A1, A2, A10, B1, B2, B10, C3, ...) -> المراكز 1-10
    if emp_code and emp_code[0] in 'ABCD' and len(emp_code) > 1 and emp_code[1:].isdigit():
        center_num = int(emp_code[1:])
        if 1 <= center_num <= 10:
            center = db.query(EmergencyCenter).filter(EmergencyCenter.code == str(center_num)).first()
            return center.id if center else None
    
    # 4. العمليات (XW) -> المركز الرئيسي (HQ)
    if emp_code.startswith('XW'):
        center = db.query(EmergencyCenter).filter(EmergencyCenter.code == 'HQ').first()
        return center.id if center else None
    
    # 5. الوحدات الخاصة والدعم (ST, TT, Y, YY, Z, AZ, BZ, CZ, DZ) -> المركز الرئيسي (HQ)
    special_codes = ['ST', 'TT', 'Y', 'YY', 'YYY', 'YYYY', 'Z', 'AZ', 'BZ', 'CZ', 'DZ']
    if emp_code in special_codes:
        center = db.query(EmergencyCenter).filter(EmergencyCenter.code == 'HQ').first()
        return center.id if center else None
    
    return None

@router.get("/", response_model=EmployeeList)
def get_employees(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = Query(0, description="تخطي"),
    limit: int = Query(100, description="الحد الأقصى"),
    center_id: Optional[str] = Query(None, description="تصفية حسب المركز"),
    search: Optional[str] = Query(None, description="بحث بالاسم أو الرقم الوظيفي"),
    employee_type: Optional[str] = Query(None, description="نوع الموظف"),
    _cache_buster: Optional[int] = Query(None, description="لكسر Cache"),
) -> dict:
    """جلب قائمة الموظفين حسب الصلاحية"""
    
    query = db.query(Employee)
    
    # ===== تصفية حسب صلاحية المستخدم =====
    if current_user.role.value == "field_leader":
        if current_user.employee and current_user.employee.center_id:
            query = query.filter(Employee.center_id == current_user.employee.center_id)
        else:
            return {"total": 0, "items": []}
    
    elif current_user.role.value in ["paramedic", "emt"]:
        if current_user.employee:
            query = query.filter(Employee.id == current_user.employee.id)
        else:
            return {"total": 0, "items": []}
    
    # تصفية حسب المركز
    if center_id:
        try:
            center_uuid = UUID(center_id)
            query = query.filter(Employee.center_id == center_uuid)
        except ValueError:
            return {"total": 0, "items": []}
    
    # تصفية حسب النوع
    if employee_type:
        query = query.filter(Employee.employee_type == employee_type)
    
    # بحث
    if search:
        query = query.filter(
            or_(
                Employee.full_name.contains(search),
                Employee.emp_no.contains(search)
            )
        )
    
    total = query.count()
    employees = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": employees
    }

@router.get("/stats/overview")
def get_employees_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> dict:
    """إحصائيات سريعة عن الموظفين"""
    query = db.query(Employee)
    
    if current_user.role.value == "field_leader":
        if current_user.employee and current_user.employee.center_id:
            query = query.filter(Employee.center_id == current_user.employee.center_id)
    elif current_user.role.value in ["paramedic", "emt"]:
        if current_user.employee:
            query = query.filter(Employee.id == current_user.employee.id)
        else:
            return {"total": 0, "by_type": {}, "on_duty": 0, "available": 0, "top_centers": []}
    
    total = query.count()
    
    by_type = {
        "paramedics": query.filter(Employee.employee_type == "paramedic").count(),
        "emts": query.filter(Employee.employee_type == "emt").count(),
        "admins": query.filter(Employee.employee_type == "admin").count()
    }
    
    on_duty = query.filter(Employee.is_on_duty == True).count()
    available = query.filter(Employee.is_available == True).count()
    
    top_centers = []
    if current_user.role.value in ["chief_paramedic", "operations_supervisor", "admin"]:
        from app.models.center import EmergencyCenter
        centers = db.query(EmergencyCenter).limit(5).all()
        for center in centers:
            count = query.filter(Employee.center_id == center.id).count()
            top_centers.append({
                "center": center.name,
                "count": count
            })
    
    return {
        "total": total,
        "by_type": by_type,
        "on_duty": on_duty,
        "available": available,
        "top_centers": top_centers
    }

@router.get("/{employee_id}", response_model=EmployeeSchema)
def get_employee(
    employee_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Employee:
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الموظف غير موجود")
    return employee

@router.post("/", response_model=EmployeeSchema, status_code=status.HTTP_201_CREATED)
def create_employee(
    employee_in: EmployeeCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Employee:
    # التحقق من عدم تكرار الرقم الوظيفي
    existing = db.query(Employee).filter(Employee.emp_no == employee_in.emp_no).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="الرقم الوظيفي موجود مسبقاً")
    
    # استخدام center_id المرسل من الفرونتند أولاً
    center_id = employee_in.center_id
    
    # إذا لم يكن موجود، نحسب من الكود
    if not center_id and employee_in.emp_code:
        auto_center_id = get_center_from_code(db, employee_in.emp_code)
        if auto_center_id:
            center_id = auto_center_id
    
    # التحقق من صلاحية مشرف المركز
    if current_user.role.value == "field_leader":
        if current_user.employee and current_user.employee.center_id != center_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="لا يمكنك إضافة موظف لمركز آخر")
    
    employee = Employee(
        id=uuid4(),
        emp_no=employee_in.emp_no,
        full_name=employee_in.full_name,
        national_id=employee_in.national_id,
        phone=employee_in.phone,
        email=employee_in.email,
        hire_date=employee_in.hire_date,
        employee_type=employee_in.employee_type,
        center_id=center_id,
        role_id=employee_in.role_id,
        emp_code=employee_in.emp_code,
        is_active=True
    )
    
    db.add(employee)
    db.commit()
    db.refresh(employee)
    
    return employee

@router.put("/{employee_id}", response_model=EmployeeSchema)
def update_employee(
    employee_id: UUID,
    employee_in: EmployeeUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Employee:
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الموظف غير موجود")
    
    if current_user.role.value == "field_leader":
        if current_user.employee and employee.center_id != current_user.employee.center_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="لا يمكنك تعديل موظف من مركز آخر")
    
    update_data = employee_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(employee, field, value)
    
    db.commit()
    db.refresh(employee)
    
    return employee

@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(
    employee_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> None:
    if current_user.role.value != "chief_paramedic":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="فقط كبير المسعفين يمكنه حذف الموظفين")
    
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الموظف غير موجود")
    
    db.delete(employee)
    db.commit()