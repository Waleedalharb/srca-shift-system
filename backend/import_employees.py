# backend/import_employees.py
import pandas as pd
import uuid
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys

# إضافة المسار للمشروع
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Employee, Role, EmergencyCenter
from app.core.database import engine

# إعداد الاتصال بقاعدة البيانات
Session = sessionmaker(bind=engine)
session = Session()

# ==================== المراكز ====================
MAIN_CENTER = "مركز المنصورة"           # 🏛️ المركز الرئيسي (إداري + إسعافي)
OPS_CENTER = "مركز العمليات"            # 🖥️ مركز العمليات (منفصل)

# باقي المراكز الإسعافية
FIELD_CENTERS = {
    'A': 'مركز الحائر',
    'B': 'مركز الدار البيضاء',
    'C': 'مركز الشفاء',
    'D': 'مركز عكاظ',
    'X': 'مركز منفوحة',
    'O': 'مركز الخالدية',
    'AA': 'مركز الإسكان',
    'CC': 'مركز ديراب',
    'DD': 'مركز طريق الخرج',
}

def get_center(job_title, code_prefix):
    """
    تحديد المركز المناسب حسب المسمى الوظيفي والكود
    """
    job = str(job_title).strip()
    
    # ===== 1. مركز العمليات (منفصل) =====
    if 'تحكم عملياتي' in job or 'تنسيق استجابة' in job:
        return OPS_CENTER
    
    # ===== 2. المركز الرئيسي - المنصورة =====
    if any(x in job for x in ['كبير مسعفين', 'مساعد كبير مسعفين', 'دعم لوجستي']):
        return MAIN_CENTER
    
    # ===== 3. إذا كان الكود BB = المنصورة (فيه مسعفين تابعين للمركز الرئيسي) =====
    if str(code_prefix).startswith('BB'):
        return MAIN_CENTER
    
    # ===== 4. باقي المراكز الإسعافية =====
    code = str(code_prefix)
    for key, center_name in FIELD_CENTERS.items():
        if code.startswith(key):
            return center_name
    
    # افتراضي
    return MAIN_CENTER

def get_employee_type_and_role(job_title):
    """تحديد نوع الموظف والدور"""
    job = str(job_title).strip()
    
    # قيادات وإدارة
    if 'كبير مسعفين' in job:
        return 'admin', 'chief'
    elif 'مساعد كبير مسعفين' in job:
        return 'admin', 'field_leader'
    elif 'دعم لوجستي' in job:
        return 'admin', 'admin'
    
    # العمليات
    elif 'تحكم عملياتي' in job:
        return 'operations', 'operations_control'
    elif 'تنسيق استجابة' in job:
        return 'coordinator', 'response_coordinator'
    
    # الطواقم الإسعافية
    elif 'أخصائي اسعاف' in job:
        return 'paramedic', 'paramedic'
    elif 'فني اسعاف' in job:
        return 'emt', 'emt'
    
    # افتراضي
    return 'emt', 'emt'

def import_employees():
    """استيراد الموظفين من ملف Excel"""
    
    print("=" * 70)
    print("🚑 استيراد موظفي قطاع الجنوب - هيئة الهلال الأحمر")
    print("=" * 70)
    print(f"🏛️ المركز الرئيسي: {MAIN_CENTER}")
    print(f"🖥️ مركز العمليات: {OPS_CENTER}")
    print(f"🚚 {len(FIELD_CENTERS)} مركز إسعافي ميداني")
    print("=" * 70)
    
    # قراءة ملف Excel
    file_path = 'القطاع الجنوبي.xlsx'
    
    if not os.path.exists(file_path):
        print(f"❌ الملف غير موجود: {file_path}")
        return
    
    try:
        df = pd.read_excel(file_path)
        print(f"📊 تم قراءة {len(df)} سجل من الملف")
    except Exception as e:
        print(f"❌ خطأ في قراءة الملف: {e}")
        return
    
    # الحصول على الأدوار
    roles = {
        'chief': session.query(Role).filter(Role.code == "CHIEF_PARAMEDIC").first(),
        'field_leader': session.query(Role).filter(Role.code == "FIELD_LEADER").first(),
        'operations_control': session.query(Role).filter(Role.code == "OPERATIONS_CONTROL").first(),
        'response_coordinator': session.query(Role).filter(Role.code == "RESPONSE_COORDINATOR").first(),
        'paramedic': session.query(Role).filter(Role.code == "PARAMEDIC").first(),
        'emt': session.query(Role).filter(Role.code == "EMT").first(),
        'admin': session.query(Role).filter(Role.code == "ADMIN").first(),
    }
    
    # التحقق من وجود مركز العمليات
    ops_center = session.query(EmergencyCenter).filter(EmergencyCenter.name == OPS_CENTER).first()
    if not ops_center:
        print(f"⚠️ مركز العمليات '{OPS_CENTER}' غير موجود - سيتم إنشاؤه")
        ops_center = EmergencyCenter(
            id=uuid.uuid4(),
            code="OPS",
            name=OPS_CENTER,
            city="الرياض",
            is_active=True
        )
        session.add(ops_center)
        session.commit()
    
    # إحصائيات
    stats = {
        'added': 0,
        'skipped': 0,
        'centers': {},
        'types': {
            'admin': 0,        # إداريين
            'operations': 0,    # تحكم عملياتي
            'coordinator': 0,   # تنسيق استجابة
            'paramedic': 0,     # أخصائيين
            'emt': 0            # مسعفين
        }
    }
    
    print("\n🔄 جاري استيراد الموظفين...\n")
    
    for index, row in df.iterrows():
        try:
            emp_no = str(row['الكود']).strip()
            full_name = str(row['الاسم']).strip()
            job_title = str(row['طبيعة العمل']).strip()
            code_prefix = str(row['رمز']).strip() if pd.notna(row['رمز']) else ''
            
            # التحقق من التكرار
            if session.query(Employee).filter(Employee.emp_no == emp_no).first():
                print(f"⏭️ {index+1}: {full_name[:20]} - موجود مسبقاً")
                stats['skipped'] += 1
                continue
            
            # تحديد المركز
            center_name = get_center(job_title, code_prefix)
            center = session.query(EmergencyCenter).filter(EmergencyCenter.name == center_name).first()
            
            if not center:
                print(f"⚠️ {index+1}: {full_name} - مركز '{center_name}' غير موجود")
                continue
            
            # تحديد النوع والدور
            emp_type, role_key = get_employee_type_and_role(job_title)
            role = roles.get(role_key)
            
            # إنشاء الموظف
            employee = Employee(
                id=uuid.uuid4(),
                emp_no=emp_no,
                full_name=full_name,
                employee_type=emp_type,
                center_id=center.id,
                role_id=role.id if role else None,
                hire_date=date(2020, 1, 1)
            )
            
            session.add(employee)
            stats['added'] += 1
            stats['types'][emp_type] = stats['types'].get(emp_type, 0) + 1
            stats['centers'][center_name] = stats['centers'].get(center_name, 0) + 1
            
            # عرض النتيجة
            center_display = f"{center_name}"
            if center_name == MAIN_CENTER:
                center_display += " (🏛️ رئيسي + إسعافي)"
            elif center_name == OPS_CENTER:
                center_display += " (🖥️ عمليات)"
            
            print(f"✅ {index+1}: {full_name[:20]:20} - {center_display:30} - {job_title[:20]}")
            
        except Exception as e:
            print(f"❌ {index+1}: خطأ في استيراد {row.get('الاسم', 'غير معروف')}: {e}")
            stats['skipped'] += 1
    
    # حفظ التغييرات
    session.commit()
    
    # عرض الإحصائيات
    print("\n" + "=" * 70)
    print("📊 تقرير الاستيراد")
    print("=" * 70)
    print(f"✅ تم إضافة: {stats['added']} موظف")
    print(f"⏭️ تم تخطي: {stats['skipped']} موظف")
    
    print("\n👥 توزيع الموظفين حسب النوع:")
    type_names = {
        'admin': '👨‍💼 إداريين',
        'operations': '🖥️ تحكم عملياتي',
        'coordinator': '📞 تنسيق استجابة',
        'paramedic': '👨‍⚕️ أخصائيين',
        'emt': '🚑 مسعفين'
    }
    for emp_type, count in stats['types'].items():
        if count > 0:
            print(f"  {type_names.get(emp_type, emp_type)}: {count}")
    
    print("\n🏥 توزيع الموظفين حسب المركز:")
    for center, count in sorted(stats['centers'].items()):
        if center == MAIN_CENTER:
            print(f"  🏛️ {center}: {count} (رئيسي + إسعافي)")
        elif center == OPS_CENTER:
            print(f"  🖥️ {center}: {count} (عمليات)")
        else:
            print(f"  🚑 {center}: {count}")
    
    print("\n" + "=" * 70)
    print("🎉 تم الانتهاء بنجاح!")
    
    session.close()

if __name__ == "__main__":
    import_employees()