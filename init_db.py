# backend/init_db.py
from app.core.database import engine, SessionLocal
from app.models import Base, User, Employee, EmergencyCenter, Role
from app.core.security import get_password_hash
import uuid
from datetime import date

def init_database():
    """تهيئة قاعدة البيانات بالبيانات الأساسية"""
    
    # إنشاء الجداول
    Base.metadata.create_all(bind=engine)
    print("✅ تم إنشاء الجداول")
    
    db = SessionLocal()
    
    # إضافة الأدوار الأساسية
    roles = [
        {"code": "CHIEF_PARAMEDIC", "name": "كبير المسعفين", "level": 1},
        {"code": "FIELD_LEADER", "name": "قيادة ميدانية", "level": 2},
        {"code": "OPERATIONS_CONTROL", "name": "تحكم عملياتي", "level": 3},
        {"code": "PARAMEDIC", "name": "أخصائي إسعاف", "level": 4},
        {"code": "EMT", "name": "مسعف", "level": 4},
        {"code": "ADMIN", "name": "إداري", "level": 4},
    ]
    
    for role_data in roles:
        role = db.query(Role).filter(Role.code == role_data["code"]).first()
        if not role:
            role = Role(**role_data)
            db.add(role)
    
    db.commit()
    print("✅ تم إضافة الأدوار")
    
    # إضافة كبير المسعفين الافتراضي
    chief_role = db.query(Role).filter(Role.code == "CHIEF_PARAMEDIC").first()
    
    # التحقق من وجود كبير المسعفين
    chief = db.query(Employee).filter(Employee.emp_no == "1001").first()
    if not chief:
        chief = Employee(
            id=uuid.uuid4(),
            emp_no="1001",
            full_name="عبدالله السعدون",
            national_id="1000000001",
            phone="0500000001",
            email="chief@srca.gov.sa",
            hire_date=date(2020, 1, 1),
            employee_type="admin",
            role_id=chief_role.id
        )
        db.add(chief)
        db.commit()
        print("✅ تم إضافة كبير المسعفين")
    
    # إنشاء حساب مستخدم لكبير المسعفين
    chief_user = db.query(User).filter(User.username == "chief").first()
    if not chief_user:
        chief_user = User(
            username="chief",
            email="chief@srca.gov.sa",
            hashed_password=get_password_hash("admin123"),
            role=User.UserRole.CHIEF_PARAMEDIC,
            employee_id=chief.id
        )
        db.add(chief_user)
        db.commit()
        print("✅ تم إنشاء حساب كبير المسعفين (admin123)")
    
    # إضافة المراكز الأساسية
    centers = [
        {"code": "HAER", "name": "مركز الحائر", "lat": "24.5667", "lng": "46.7333"},
        {"code": "DBA", "name": "مركز الدار البيضاء", "lat": "24.7000", "lng": "46.7167"},
        {"code": "SHF", "name": "مركز الشفاء", "lat": "24.6333", "lng": "46.7167"},
        {"code": "AKAZ", "name": "مركز عكاظ", "lat": "24.6833", "lng": "46.6833"},
        {"code": "MNF", "name": "مركز منفوحة", "lat": "24.6167", "lng": "46.7333"},
        {"code": "KLD", "name": "مركز الخالدية", "lat": "24.6500", "lng": "46.7000"},
        {"code": "ESKAN", "name": "مركز الإسكان", "lat": "24.6833", "lng": "46.7500"},
        {"code": "MNS", "name": "مركز المنصورة", "lat": "24.6333", "lng": "46.7000"},
        {"code": "DIRAB", "name": "مركز ديراب", "lat": "24.5833", "lng": "46.6667"},
        {"code": "KHARJRD", "name": "مركز طريق الخرج", "lat": "24.6000", "lng": "46.7833"},
    ]
    
    for center_data in centers:
        center = db.query(EmergencyCenter).filter(EmergencyCenter.code == center_data["code"]).first()
        if not center:
            center = EmergencyCenter(
                code=center_data["code"],
                name=center_data["name"],
                latitude=center_data["lat"],
                longitude=center_data["lng"],
                coverage_area=50,  # افتراضي 50 كم²
                is_active=True
            )
            db.add(center)
    
    db.commit()
    print("✅ تم إضافة المراكز الإسعافية")
    
    db.close()
    print("🎯 تهيئة قاعدة البيانات اكتملت بنجاح")

if __name__ == "__main__":
    init_database()