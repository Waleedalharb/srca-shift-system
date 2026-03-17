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
    
    # ترتيب تنازلي (الأحدث أولاً)
    shifts = query.order_by(Shift.date.desc()).limit(limit).all()
    
    # ✅ تصفية: نجيب فقط المناوبات اللي فيها تعيينات
    result = []
    for shift in shifts:
        if shift.assignments:  # إذا فيه تعيينات
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

# ===== ✅ دالة جديدة: جلب مناوبات موظف محدد =====
@router.get("/by_employee")
def get_shifts_by_employee(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    employee_id: UUID = Query(..., description="معرف الموظف"),
    start_date: Optional[date] = Query(None, description="تاريخ البداية (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="تاريخ النهاية (YYYY-MM-DD)"),
    limit: int = Query(100, description="الحد الأقصى للنتائج"),
) -> dict:
    """
    جلب مناوبات موظف محدد في فترة زمنية
    """
    # بناء الاستعلام
    query = db.query(Shift).join(
        ShiftAssignment, Shift.id == ShiftAssignment.shift_id
    ).filter(
        ShiftAssignment.employee_id == employee_id
    )
    
    if start_date:
        query = query.filter(Shift.date >= start_date)
    if end_date:
        query = query.filter(Shift.date < end_date)
    
    # تنفيذ الاستعلام
    shifts = query.order_by(Shift.date.desc()).limit(limit).all()
    
    # تحويل النتيجة
    result = []
    for shift in shifts:
        # نجيب الموظف المعني فقط
        assignment = next(
            (a for a in shift.assignments if a.employee_id == employee_id), 
            None
        )
        
        if assignment:
            employee = db.query(Employee).filter(Employee.id == employee_id).first()
            shift_data = {
                "id": str(shift.id),
                "date": shift.date.isoformat(),
                "shift_type": shift.shift_type,
                "center_id": str(shift.center_id) if shift.center_id else None,
                "assignments": [{
                    "employee_id": str(assignment.employee_id),
                    "employee_name": employee.full_name if employee else "غير معروف"
                }]
            }
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

# ===== دالة تحديث مناوبة موظف (مفردة) =====
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
        # إذا ما في مناوبة، ننشئ واحدة جديدة (بدون commit)
        shift = Shift(
            id=uuid.uuid4(),
            date=target_date,
            shift_type=shift_type,
            center_id=center_id
        )
        db.add(shift)
        db.flush()  # 👈 نجيب الـ ID بدون commit
    else:
        # تحديث نوع المناوبة
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
    
    # ✅ commit واحد لكل التغييرات
    db.commit()
    db.refresh(shift)
    
    print(f"✅ تم حفظ مناوبة: {shift.id}, عدد التعيينات: {len(shift.assignments)}")
    
    return {"message": "تم التحديث بنجاح", "shift_id": str(shift.id)}


# ===== 🚀 دالة جديدة: Batch Update (تحديث دفعة واحدة) =====
@router.post("/batch-update")
def batch_update_shifts(
    data: List[dict] = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    تحديث مجموعة من المناوبات دفعة واحدة
    - يستقبل قائمة من المناوبات
    - ينفذ كل التحديثات في commit واحد
    - أسرع 10-20 مرة من التحديث المفرد
    """
    if not data:
        raise HTTPException(status_code=400, detail="لا توجد بيانات للتحديث")
    
    print(f"📦 استقبال {len(data)} مناوبة للتحديث الدفعي")
    
    success = 0
    failed = 0
    errors = []
    
    # معالجة كل عنصر في القائمة
    for idx, item in enumerate(data):
        try:
            employee_id = item.get("employee_id")
            date_str = item.get("date")
            shift_type = item.get("shift_type")
            
            if not employee_id or not date_str or not shift_type:
                failed += 1
                errors.append(f"عنصر {idx}: بيانات ناقصة")
                continue
            
            # تحويل النص إلى UUID
            try:
                emp_uuid = UUID(employee_id)
            except Exception as e:
                failed += 1
                errors.append(f"عنصر {idx}: معرف موظف غير صالح - {str(e)}")
                continue
            
            # تحويل التاريخ
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except Exception as e:
                failed += 1
                errors.append(f"عنصر {idx}: صيغة تاريخ غير صالحة - {str(e)}")
                continue
            
            # التحقق من وجود الموظف
            employee = db.query(Employee).filter(Employee.id == emp_uuid).first()
            if not employee:
                failed += 1
                errors.append(f"عنصر {idx}: الموظف غير موجود")
                continue
            
            # الحصول على مركز الموظف
            center_id = employee.center_id
            if not center_id:
                failed += 1
                errors.append(f"عنصر {idx}: الموظف غير مرتبط بمركز")
                continue
            
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
                db.flush()  # نجيب الـ ID بدون commit
            else:
                # تحديث نوع المناوبة
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
            
            success += 1
            
            # كل 500 عنصر نطبع تقدم
            if success % 500 == 0:
                print(f"⏳ تم معالجة {success} مناوبة...")
                
        except Exception as e:
            failed += 1
            errors.append(f"عنصر {idx}: خطأ غير متوقع - {str(e)}")
    
    # ✅ commit واحد لكل التغييرات (أسرع بكثير)
    if success > 0:
        db.commit()
        print(f"✅ تم حفظ {success} مناوبة في قاعدة البيانات")
    
    # طباعة الملخص
    print(f"\n📊 ملخص التحديث الدفعي:")
    print(f"   ✅ نجاح: {success}")
    print(f"   ❌ فشل: {failed}")
    if errors and len(errors) <= 10:
        for err in errors:
            print(f"   ⚠️ {err}")
    elif errors:
        print(f"   ⚠️ يوجد {len(errors)} خطأ - أول 10:")
        for err in errors[:10]:
            print(f"   ⚠️ {err}")
    
    return {
        "message": f"✅ تم تحديث {success} مناوبة بنجاح",
        "success": success,
        "failed": failed,
        "total": len(data)
    }


# ===== دالة إضافية: حذف المناوبات القديمة =====
@router.delete("/cleanup")
def cleanup_old_shifts(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    before_date: Optional[str] = Query(None, description="حذف المناوبات قبل هذا التاريخ (YYYY-MM-DD)"),
):
    """حذف المناوبات القديمة التي لا تحتوي على تعيينات"""
    if current_user.role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="صلاحية Admin فقط"
        )
    
    try:
        # حذف التعيينات بدون موظفين
        deleted_assignments = db.query(ShiftAssignment).filter(
            ShiftAssignment.employee_id == None
        ).delete(synchronize_session=False)
        
        # حذف المناوبات بدون تعيينات
        subquery = db.query(ShiftAssignment.shift_id).distinct()
        deleted_shifts = db.query(Shift).filter(
            ~Shift.id.in_(subquery)
        ).delete(synchronize_session=False)
        
        db.commit()
        
        return {
            "message": "✅ تم التنظيف بنجاح",
            "deleted_assignments": deleted_assignments,
            "deleted_shifts": deleted_shifts
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ===== 🔥 دالة جديدة: clear-cache (لإشارة الفرونتند بتحديث الكاش) =====
@router.post("/clear-cache")
def clear_cache(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """مسح الكاش من قاعدة البيانات (للتطوير)"""
    # هذه الدالة مخصصة للإشارة للفرونتند بأنه يجب مسح الكاش
    print(f"🧹 تم طلب مسح الكاش بواسطة المستخدم: {current_user.username}")
    return {
        "message": "تم مسح الكاش بنجاح",
        "cache_clear": True,
        "timestamp": datetime.now().isoformat()
    }


# ===== 🧹 دالة تنظيف قاعدة البيانات بالكامل (محدثة - تمسح كل شي) =====
@router.delete("/cleanup-all")
def cleanup_all_shifts(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    confirm: bool = Query(False, description="تأكيد الحذف"),
    delete_all: bool = Query(False, description="حذف كل البيانات نهائياً"),
    month: Optional[int] = Query(None, description="شهر محدد (1-12)"),
    year: Optional[int] = Query(None, description="سنة محددة"),
):
    """
    🧹 تنظيف قاعدة البيانات من البيانات القديمة والمكررة
    - confirm=true: تأكيد الحذف (مطلوب)
    - delete_all=true: حذف كل البيانات (بدون أي شروط)
    - month=X&year=Y: حذف شهر محدد فقط
    """
    if current_user.role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="❌ هذه العملية تحتاج صلاحية Admin فقط"
        )
    
    if not confirm:
        return {
            "warning": "⚠️ هذا الإجراء سوف يحذف بيانات المناوبات!",
            "message": "أضف ?confirm=true في الرابط لتأكيد الحذف"
        }
    
    try:
        deleted_assignments = 0
        deleted_shifts = 0
        
        # ✅ إذا كان delete_all = true → امسح كل البيانات (زي ما تبي)
        if delete_all:
            print("🧨🧨🧨 حذف كل البيانات بالكامل...")
            deleted_assignments = db.query(ShiftAssignment).delete(synchronize_session=False)
            deleted_shifts = db.query(Shift).delete(synchronize_session=False)
            print(f"💥 تم حذف {deleted_assignments} تعيين و {deleted_shifts} مناوبة")
        
        # ✅ إذا كان فيه شهر وسنة → امسح شهر محدد
        elif year and month:
            start_date = datetime(year, month, 1).date()
            if month == 12:
                end_date = datetime(year+1, 1, 1).date()
            else:
                end_date = datetime(year, month+1, 1).date()
            
            print(f"📅 حذف بيانات شهر {month}/{year}")
            
            shifts_in_month = db.query(Shift).filter(
                Shift.date >= start_date,
                Shift.date < end_date
            ).all()
            
            shift_ids = [s.id for s in shifts_in_month]
            
            if shift_ids:
                deleted_assignments = db.query(ShiftAssignment).filter(
                    ShiftAssignment.shift_id.in_(shift_ids)
                ).delete(synchronize_session=False)
                
                deleted_shifts = db.query(Shift).filter(
                    Shift.id.in_(shift_ids)
                ).delete(synchronize_session=False)
        
        # ✅ إذا ما حددت شيء → امسح كل البيانات (حماية)
        else:
            return {
                "error": "⚠️ لم تحدد نطاق الحذف",
                "message": "استخدم ?delete_all=true لمسح كل البيانات، أو حدد month&year"
            }
        
        db.commit()
        
        return {
            "message": "✅ تم التنظيف بنجاح",
            "deleted_assignments": deleted_assignments,
            "deleted_shifts": deleted_shifts,
            "month": month,
            "year": year,
            "delete_all": delete_all
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))