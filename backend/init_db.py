# backend/init_db.py - إضافة بعد إنشاء الموظفين

def create_test_users(db):
    """إنشاء مستخدمين تجريبيين بصلاحيات مختلفة"""
    
    from app.models.user import User, UserRole
    from app.core.security import get_password_hash
    
    # مستخدمين تجريبيين
    test_users = [
        {
            "username": "chief",
            "password": "admin123",
            "role": UserRole.CHIEF_PARAMEDIC,
            "emp_no": "1001",
            "name": "عبدالله السعدون"
        },
        {
            "username": "leader_haer",
            "password": "leader123",
            "role": UserRole.FIELD_LEADER,
            "emp_no": "1002",
            "name": "أحمد محمد العلي",
            "center": "مركز الحائر"
        },
        {
            "username": "leader_dba",
            "password": "leader123",
            "role": UserRole.FIELD_LEADER,
            "emp_no": "2001",
            "name": "خالد إبراهيم القحطاني",
            "center": "مركز الدار البيضاء"
        },
        {
            "username": "ops_supervisor",
            "password": "ops123",
            "role": UserRole.OPERATIONS_SUPERVISOR,
            "emp_no": "8323",
            "name": "تركي عتيق الله المطيري"
        },
        {
            "username": "paramedic1",
            "password": "emp123",
            "role": UserRole.PARAMEDIC,
            "emp_no": "3001",
            "name": "محمد عبدالله الغامدي"
        },
        {
            "username": "emt1",
            "password": "emp123",
            "role": UserRole.EMT,
            "emp_no": "3002",
            "name": "عمر حسن الزهراني"
        }
    ]
    
    for user_data in test_users:
        # البحث عن الموظف
        employee = db.query(Employee).filter(Employee.emp_no == user_data["emp_no"]).first()
        
        if employee:
            # التحقق من وجود المستخدم
            existing = db.query(User).filter(User.username == user_data["username"]).first()
            if not existing:
                user = User(
                    id=uuid.uuid4(),
                    username=user_data["username"],
                    email=f"{user_data['username']}@srca.gov.sa",
                    hashed_password=get_password_hash(user_data["password"]),
                    role=user_data["role"],
                    employee_id=employee.id,
                    is_active=True
                )
                db.add(user)
                print(f"✅ مستخدم: {user_data['username']} - {user_data['role'].value}")
    
    db.commit()