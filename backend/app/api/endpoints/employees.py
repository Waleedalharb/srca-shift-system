# backend/app/api/endpoints/employees.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from uuid import UUID, uuid4
from typing import Optional, List

from app.api import deps
from app.models.employee import Employee
from app.models.user import User
from app.schemas.employee import (
    EmployeeCreate, EmployeeUpdate, Employee as EmployeeSchema, EmployeeList
)
from app.core.security import require_permission, Permission

router = APIRouter()

@router.get("/", response_model=EmployeeList)
def get_employees(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = Query(0, description="تخطي"),
    limit: int = Query(100, description="الحد الأقصى"),
    center_id: Optional[str] = Query(None, description="تصفية حسب المركز"),
    search: Optional[str] = Query(None, description="بحث بالاسم أو الرقم الوظيفي"),
    employee_type: Optional[str] = Query(None, description="نوع الموظف"),
) -> dict:
    """جلب قائمة الموظفين حسب الصلاحية"""
    
    query = db.query(Employee)
    
    # ===== تصفية حسب صلاحية المستخدم =====
    if current_user.role.value == "field_leader":
        # مشرف مركز - يشوف موظفي مركزه فقط
        if current_user.employee and current_user.employee.center_id:
            query = query.filter(Employee.center_id == current_user.employee.center_id)
        else:
            return {"total": 0, "items": []}
    
    elif current_user.role.value in ["paramedic", "emt"]:
        # موظف عادي - يشوف نفسه فقط
        if current_user.employee:
            query = query.filter(Employee.id == current_user.employee.id)
        else:
            return {"total": 0, "items": []}
    
    # كبير المسعفين والمشرفين يشوفون الكل
    
    # تصفية حسب المركز (إذا أضيفت)
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
    """
    إحصائيات سريعة عن الموظفين
    """
    # بناء الاستعلام الأساسي
    query = db.query(Employee)
    
    # تصفية حسب صلاحية المستخدم
    if current_user.role.value == "field_leader":
        if current_user.employee and current_user.employee.center_id:
            query = query.filter(Employee.center_id == current_user.employee.center_id)
    elif current_user.role.value in ["paramedic", "emt"]:
        if current_user.employee:
            query = query.filter(Employee.id == current_user.employee.id)
        else:
            return {
                "total": 0,
                "by_type": {"paramedics": 0, "emts": 0, "admins": 0},
                "on_duty": 0,
                "available": 0,
                "top_centers": []
            }
    
    # إجمالي الموظفين
    total = query.count()
    
    # حسب النوع
    by_type = {
        "paramedics": query.filter(Employee.employee_type == "paramedic").count(),
        "emts": query.filter(Employee.employee_type == "emt").count(),
        "admins": query.filter(Employee.employee_type == "admin").count()
    }
    
    # إضافة أنواع العمليات إذا كانت موجودة
    if hasattr(Employee, 'employee_type'):
        by_type["operations"] = query.filter(Employee.employee_type == "operations").count()
        by_type["coordinator"] = query.filter(Employee.employee_type == "coordinator").count()
    
    # الحضور الآن
    on_duty = query.filter(Employee.is_on_duty == True).count()
    
    # الموظفين المتاحين
    available = query.filter(Employee.is_available == True).count()
    
    # حسب المراكز (للمديرين فقط)
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

@router.post("/", response_model=EmployeeSchema, status_code=status.HTTP_201_CREATED)
@require_permission(Permission.MANAGE_EMPLOYEES)
def create_employee(
    employee_in: EmployeeCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Employee:
    """إنشاء موظف جديد - يحتاج صلاحية إدارة الموظفين"""
    
    # التحقق من عدم تكرار الرقم الوظيفي
    existing = db.query(Employee).filter(Employee.emp_no == employee_in.emp_no).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="الرقم الوظيفي موجود مسبقاً"
        )
    
    # إذا كان مشرف مركز، يتأكد أن الموظف الجديد في مركزه
    if current_user.role.value == "field_leader":
        if current_user.employee and current_user.employee.center_id != employee_in.center_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="لا يمكنك إضافة موظف لمركز آخر"
            )
    
    employee = Employee(
        id=uuid4(),
        emp_no=employee_in.emp_no,
        full_name=employee_in.full_name,
        national_id=employee_in.national_id,
        phone=employee_in.phone,
        email=employee_in.email,
        hire_date=employee_in.hire_date,
        employee_type=employee_in.employee_type,
        center_id=employee_in.center_id,
        role_id=employee_in.role_id,
        is_active=True
    )
    
    db.add(employee)
    db.commit()
    db.refresh(employee)
    
    return employee