# frontend/employee_app.py
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
import random
import requests
from config import config

# إعداد الصفحة
st.set_page_config(
    page_title="مناوباتي - منصة الموظفين",
    page_icon="👤",
    layout="wide"
)

# ===== التنسيقات =====
st.markdown("""
<style>
    /* إخفاء الشريط الجانبي */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stSidebarCollapsedControl"] { display: none !important; }
    .main > div { padding: 0.5rem 1rem !important; }
    
    /* تحسين للجوال */
    @media (max-width: 768px) {
        .main > div { padding: 0.5rem 0.75rem !important; }
        .greeting-card { padding: 1rem !important; }
        .greeting-card h2 { font-size: 1.2rem !important; }
        .stat-card { padding: 0.75rem !important; }
        .stat-value { font-size: 1.3rem !important; }
        .stat-label { font-size: 0.65rem !important; }
    }
    
    /* بطاقة الترحيب */
    .greeting-card {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 20px;
        margin-bottom: 1.5rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        border-top: 3px solid #d4af37;
    }
    .greeting-card h1 {
        margin: 0;
        font-size: 0.9rem;
        font-weight: 500;
        color: #6c757d;
    }
    .greeting-card h2 {
        margin: 0.5rem 0;
        font-size: 1.5rem;
        font-weight: 600;
        color: #1e2a3a;
    }
    .greeting-card p {
        margin: 0;
        font-size: 0.8rem;
        color: #6c757d;
    }
    
    /* بطاقات الإحصائيات */
    .stat-card {
        background: #ffffff;
        padding: 1rem;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        border: 1px solid #eef2f6;
    }
    .stat-value {
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0.3rem 0;
        color: #1e2a3a;
    }
    .stat-label {
        font-size: 0.7rem;
        color: #6c757d;
    }
    .stat-trend {
        font-size: 0.6rem;
        padding: 0.15rem 0.5rem;
        border-radius: 20px;
        display: inline-block;
        margin-top: 0.3rem;
    }
    .trend-up { background: #e6f7e6; color: #2e7d32; }
    .trend-neutral { background: #f5f5f5; color: #5d6b82; }
    
    /* بطاقات العبارات */
    .achievement-card {
        background: #f8fafc;
        padding: 0.8rem 1rem;
        border-radius: 16px;
        margin-bottom: 0.8rem;
        border-right: 3px solid;
        font-size: 0.85rem;
        color: #1e293b;
    }
    .quote-card {
        background: #eef2ff;
        padding: 0.8rem 1rem;
        border-radius: 16px;
        margin-bottom: 1rem;
        border-right: 3px solid #4f46e5;
        font-size: 0.85rem;
        color: #1e293b;
    }
    
    /* أيقونة الإشعارات */
    .notification-icon {
        position: relative;
        display: inline-block;
        cursor: pointer;
    }
    .notification-badge {
        position: absolute;
        top: -8px;
        right: -12px;
        background: #dc2626;
        color: white;
        border-radius: 50%;
        width: 20px;
        height: 20px;
        font-size: 0.7rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
    }
    
    /* جدول المناوبات */
    .shift-table-container {
        overflow-x: auto;
        margin: 1rem 0;
        border-radius: 16px;
        border: 1px solid #eef2f6;
        background: white;
    }
    .shift-table {
        width: 100%;
        border-collapse: collapse;
        min-width: 600px;
    }
    .shift-table th {
        background: #f8fafc;
        padding: 12px 8px;
        text-align: center;
        font-weight: 600;
        font-size: 0.85rem;
        color: #1e293b;
        border-bottom: 1px solid #e2e8f0;
    }
    .shift-table td {
        padding: 10px 4px;
        text-align: center;
        border: 1px solid #f0f2f5;
        vertical-align: middle;
    }
    .shift-day-number {
        font-size: 0.8rem;
        font-weight: 500;
        color: #64748b;
        margin-bottom: 6px;
    }
    .shift-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 24px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .shift-empty {
        color: #94a3b8;
        font-size: 0.75rem;
    }
    .today-cell { background: #eef2ff; }
    .weekend-cell { background: #fefce8; }
    .other-month-cell { background: #fafafa; color: #cbd5e1; }
    
    /* دليل الرموز */
    .legend-item {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.7rem;
    }
    
    /* زر تسجيل الخروج */
    .logout-btn { margin-top: 1rem; text-align: center; }
    hr { margin: 1rem 0; border: none; height: 1px; background: #eef2f6; }
</style>
""", unsafe_allow_html=True)

# ===== عبارات تشجيعية =====
MOTIVATIONAL_QUOTES = [
    "أنت تبذل جهداً رائعاً! استمر في التألق",
    "كل يوم عمل هو خطوة نحو النجاح. أنت مميز",
    "أداؤك المتميز يلهم الجميع. فخورون بك",
    "وجودك يجعل فريقنا أقوى. نحن نقدر تفانيك",
    "عملك الجليلي لا يمر دون تقدير. أنت نجمنا",
    "شكراً لالتزامك وإخلاصك في العمل",
    "كل صباح جديد معك هو بداية مميزة",
    "أنت قدوة حسنة لزملائك. فخورون بك",
    "تعاونك وروحك العالية تصنع الفرق",
    "إنجازاتك تتحدث عن نفسها. نحن نقدر جهودك",
    "نجم القطاع الجنوبي! أداؤك رائع دائماً"
]

# ===== رسالة حسب نسبة الإنجاز =====
def get_achievement_message(rate):
    if rate >= 90:
        return "🏆 متميز! أنت من أفضل الموظفين هذا الشهر"
    elif rate >= 70:
        return "🌟 أداء رائع! استمر بنفس الوتيرة الممتازة"
    elif rate >= 50:
        return "👍 أحسنت! مع القليل من الجهد ستصل للقمة"
    elif rate >= 30:
        return "💪 لا تستسلم! أنت قادر على تحقيق المزيد"
    else:
        return "🌱 بداية ممتازة! كل رحلة تبدأ بخطوة"

# تعريف ثوابت المناوبات
SHIFT_TYPES = {
    "D12": {"name": "صباحي 12", "hours": 12, "color": "#4CAF50", "bg": "#e8f5e9"},
    "N12": {"name": "ليلي 12", "hours": 12, "color": "#2196F3", "bg": "#e3f2fd"},
    "O12": {"name": "تداخلي 12", "hours": 12, "color": "#FF9800", "bg": "#fff3e0"},
    "V": {"name": "إجازة", "hours": 0, "color": "#F44336", "bg": "#ffebee"},
    "CP8": {"name": "تكميلية 8", "hours": 8, "color": "#9C27B0", "bg": "#f3e5f5"},
    "CP24": {"name": "تكميلية 24", "hours": 24, "color": "#3F51B5", "bg": "#e8eaf6"},
    "LN8": {"name": "ليلي تكميلي 8", "hours": 8, "color": "#009688", "bg": "#e0f2f1"},
}

# تهيئة الجلسة
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "token" not in st.session_state:
    st.session_state.token = None
if "employee_id" not in st.session_state:
    st.session_state.employee_id = None
if "full_name" not in st.session_state:
    st.session_state.full_name = None
if "username" not in st.session_state:
    st.session_state.username = None
if "daily_quote" not in st.session_state:
    st.session_state.daily_quote = random.choice(MOTIVATIONAL_QUOTES)
if "notifications" not in st.session_state:
    st.session_state.notifications = []
if "show_notifications" not in st.session_state:
    st.session_state.show_notifications = False
if "current_view" not in st.session_state:
    st.session_state.current_view = "shifts"  # shifts, settings

# ===== دالة جلب الإشعارات =====
def fetch_notifications():
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        response = requests.get(
            f"{config.API_URL}/api/notifications",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            st.session_state.notifications = response.json()
            return st.session_state.notifications
    except Exception as e:
        print(f"Error fetching notifications: {e}")
    return []

# ===== دالة تعيين إشعار كمقروء =====
def mark_notification_read(notification_id):
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        response = requests.put(
            f"{config.API_URL}/api/notifications/{notification_id}/read",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            fetch_notifications()
            return True
    except:
        pass
    return False

# ===== دالة تغيير كلمة المرور =====
def change_password(current_password, new_password, confirm_password):
    if new_password != confirm_password:
        return False, "كلمة المرور الجديدة غير متطابقة"
    
    if len(new_password) < 6:
        return False, "كلمة المرور يجب أن تكون 6 أحرف على الأقل"
    
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        response = requests.post(
            f"{config.API_URL}/api/auth/change-password",
            headers=headers,
            json={
                "current_password": current_password,
                "new_password": new_password
            },
            timeout=10
        )
        if response.status_code == 200:
            return True, "تم تغيير كلمة المرور بنجاح"
        elif response.status_code == 401:
            return False, "كلمة المرور الحالية غير صحيحة"
        else:
            return False, "حدث خطأ. حاول مرة أخرى"
    except Exception as e:
        return False, f"خطأ في الاتصال: {str(e)}"

# ===== دالة تحضير بيانات التقويم =====
def prepare_weekly_calendar(year, month, shifts_dict):
    first_day = date(year, month, 1)
    start_date = first_day - timedelta(days=first_day.weekday())
    
    weeks = []
    current = start_date
    
    while current.month <= month or (current.month == month + 1 and current.weekday() != 0):
        week = []
        for i in range(7):
            day_data = {
                "date": current,
                "day": current.day,
                "shift": shifts_dict.get(current.day, ""),
                "is_current_month": current.month == month,
                "is_today": current == date.today(),
                "is_weekend": current.weekday() >= 5
            }
            week.append(day_data)
            current += timedelta(days=1)
        weeks.append(week)
        if current.month > month + 1:
            break
    
    return weeks

# ===== صفحة تسجيل الدخول =====
def show_login():
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: #1e2a3a; font-size: 1.5rem;">منصة الموظفين</h1>
        <p style="color: #6c757d;">نظام إدارة المناوبات - قطاع الجنوب</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        username = st.text_input("الرقم الوظيفي", placeholder="أدخل الرقم الوظيفي")
        password = st.text_input("كلمة المرور", type="password", placeholder="أدخل كلمة المرور")
        
        if st.form_submit_button("دخول", use_container_width=True, type="primary"):
            if not username or not password:
                st.error("❌ الرجاء إدخال الرقم الوظيفي وكلمة المرور")
            else:
                with st.spinner("جاري تسجيل الدخول..."):
                    try:
                        response = requests.post(
                            f"{config.API_URL}/api/auth/login",
                            data={"username": username, "password": password},
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            token = data.get("access_token")
                            st.session_state.token = token
                            st.session_state.username = username
                            
                            headers = {"Authorization": f"Bearer {token}"}
                            user_response = requests.get(
                                f"{config.API_URL}/api/auth/me",
                                headers=headers,
                                timeout=10
                            )
                            
                            employee_id = None
                            full_name = username
                            
                            if user_response.status_code == 200:
                                user_data = user_response.json()
                                employee_id = user_data.get("employee_id")
                                
                                if employee_id:
                                    emp_response = requests.get(
                                        f"{config.API_URL}/api/employees/{employee_id}",
                                        headers=headers,
                                        timeout=10
                                    )
                                    if emp_response.status_code == 200:
                                        emp_data = emp_response.json()
                                        full_name = emp_data.get("full_name", username)
                            
                            st.session_state.employee_id = employee_id
                            st.session_state.full_name = full_name
                            st.session_state.authenticated = True
                            st.session_state.daily_quote = random.choice(MOTIVATIONAL_QUOTES)
                            st.session_state.current_view = "shifts"
                            
                            fetch_notifications()
                            
                            st.success(f"✅ مرحباً {full_name}")
                            st.rerun()
                        else:
                            st.error("❌ الرقم الوظيفي أو كلمة المرور غير صحيحة")
                    except Exception as e:
                        st.error(f"❌ فشل الاتصال بالخادم: {str(e)}")

# ===== صفحة الإعدادات =====
def show_settings():
    st.subheader("⚙️ الإعدادات الشخصية")
    st.markdown("---")
    
    # معلومات الموظف
    with st.container():
        st.markdown("### 👤 معلومات الحساب")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("الرقم الوظيفي", value=st.session_state.username, disabled=True)
        with col2:
            st.text_input("الاسم الكامل", value=st.session_state.full_name, disabled=True)
    
    st.markdown("---")
    
    # تغيير كلمة المرور
    with st.container():
        st.markdown("### 🔐 تغيير كلمة المرور")
        
        with st.form("change_password_form"):
            current_pwd = st.text_input("كلمة المرور الحالية", type="password")
            new_pwd = st.text_input("كلمة المرور الجديدة", type="password", placeholder="6 أحرف على الأقل")
            confirm_pwd = st.text_input("تأكيد كلمة المرور الجديدة", type="password")
            
            col1, col2, col3 = st.columns([2, 1, 2])
            with col2:
                submitted = st.form_submit_button("تحديث كلمة المرور", use_container_width=True, type="primary")
            
            if submitted:
                if not current_pwd or not new_pwd or not confirm_pwd:
                    st.error("❌ الرجاء تعبئة جميع الحقول")
                else:
                    success, message = change_password(current_pwd, new_pwd, confirm_pwd)
                    if success:
                        st.success(f"✅ {message}")
                        # مسح الحقول
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
    
    st.markdown("---")
    
    # إشعارات التطبيق
    with st.container():
        st.markdown("### 🔔 إشعارات التطبيق")
        notifications_enabled = st.toggle("تفعيل الإشعارات", value=True)
        if notifications_enabled:
            st.info("📬 سيتم إرسال إشعارات عند تعديل مناوباتك")
        else:
            st.warning("🔕 الإشعارات معطلة")
    
    st.markdown("---")
    
    # زر العودة
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("🔙 العودة للصفحة الرئيسية", use_container_width=True):
            st.session_state.current_view = "shifts"
            st.rerun()

# ===== صفحة عرض المناوبات =====
def show_shifts():
    full_name = st.session_state.get('full_name', st.session_state.username)
    hour = datetime.now().hour
    if 5 <= hour < 12:
        greeting = "صباح الخير"
    elif 12 <= hour < 16:
        greeting = "مساء الخير"
    elif 16 <= hour < 20:
        greeting = "مساء النور"
    else:
        greeting = "مساء الخير"
    
    # ===== رأس الصفحة =====
    col1, col2, col3, col4 = st.columns([1, 6, 1, 1])
    with col3:
        notifications = st.session_state.notifications
        unread_count = len([n for n in notifications if not n.get("is_read", False)])
        
        if unread_count > 0:
            if st.button(f"🔔 {unread_count}", key="notification_btn", use_container_width=True):
                st.session_state.show_notifications = not st.session_state.show_notifications
        else:
            if st.button("🔔", key="notification_btn", use_container_width=True):
                st.session_state.show_notifications = not st.session_state.show_notifications
    
    with col4:
        if st.button("⚙️", key="settings_btn", use_container_width=True):
            st.session_state.current_view = "settings"
            st.rerun()
    
    # ===== عرض الإشعارات =====
    if st.session_state.show_notifications:
        with st.expander("📋 الإشعارات", expanded=True):
            if not st.session_state.notifications:
                st.info("لا توجد إشعارات جديدة")
            else:
                for notif in st.session_state.notifications[:10]:
                    read_status = "✅" if notif.get("is_read") else "🔴"
                    col_a, col_b = st.columns([10, 1])
                    with col_a:
                        st.markdown(f"""
                        <div style="background: {'#f5f5f5' if notif.get('is_read') else '#fff3e0'}; 
                                    padding: 0.6rem; 
                                    border-radius: 12px; 
                                    margin-bottom: 0.5rem;
                                    border-right: 3px solid #d4af37;">
                            <div style="font-size: 0.75rem; color: #6c757d;">{notif.get('created_at', '').split('T')[0]}</div>
                            <div style="font-weight: 500; font-size: 0.85rem;">{notif.get('title', '')}</div>
                            <div style="font-size: 0.8rem; color: #4a5568;">{notif.get('message', '')}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_b:
                        if not notif.get("is_read"):
                            if st.button("📖", key=f"read_{notif.get('id')}"):
                                mark_notification_read(notif.get("id"))
                                st.rerun()
    
    # ===== بطاقة الترحيب =====
    st.markdown(f"""
    <div class="greeting-card">
        <h1>{greeting}</h1>
        <h2>{full_name}</h2>
        <p>يسعدنا وجودك معنا اليوم</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.employee_id:
        st.warning("⚠️ لم يتم العثور على بيانات الموظف")
        if st.button("تسجيل خروج"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        return
    
    # ===== اختيار الشهر والسنة =====
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        year = st.number_input("السنة", 2020, 2030, datetime.now().year, label_visibility="collapsed")
    with col2:
        month = st.number_input("الشهر", 1, 12, datetime.now().month, label_visibility="collapsed")
    with col3:
        if st.button("تحديث", use_container_width=True):
            st.rerun()
    
    # ===== جلب المناوبات =====
    with st.spinner("جاري تحميل مناوباتك..."):
        try:
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            start_date = f"{year}-{month:02d}-01"
            if month == 12:
                end_date = f"{year+1}-01-01"
            else:
                end_date = f"{year}-{month+1:02d}-01"
            
            response = requests.get(
                f"{config.API_URL}/api/shifts/by_employee",
                headers=headers,
                params={
                    "employee_id": st.session_state.employee_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "limit": 40
                },
                timeout=10
            )
            
            if response.status_code == 200:
                shifts = response.json().get("items", [])
            else:
                shifts = []
                st.error(f"فشل تحميل البيانات: {response.status_code}")
                return
        except Exception as e:
            st.error(f"خطأ في تحميل البيانات: {str(e)}")
            return
    
    # ===== تحليل البيانات =====
    days_in_month = calendar.monthrange(year, month)[1]
    shifts_dict = {}
    for shift in shifts:
        shift_date = shift.get("date", "").split("T")[0]
        try:
            day = int(shift_date.split("-")[2])
            shift_type = shift.get("shift_type")
            if shift_type and shift_type != "off":
                shifts_dict[day] = shift_type
        except:
            continue
    
    # ===== حساب الإحصائيات =====
    total_hours = 0
    work_days = 0
    vacation_days = 0
    
    for day in range(1, days_in_month + 1):
        shift_type = shifts_dict.get(day)
        if shift_type:
            if shift_type == 'V':
                vacation_days += 1
            else:
                work_days += 1
                if shift_type in SHIFT_TYPES:
                    total_hours += SHIFT_TYPES[shift_type]["hours"]
    
    required = 192
    rate = int((total_hours / required) * 100) if required > 0 else 0
    rate = min(rate, 100)
    
    # ===== عرض الإحصائيات =====
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">أيام العمل</div>
            <div class="stat-value">{work_days}</div>
            <div class="stat-trend trend-up">▲ مقابل الشهر الماضي</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">أيام إجازة</div>
            <div class="stat-value">{vacation_days}</div>
            <div class="stat-trend trend-neutral">—</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">إجمالي الساعات</div>
            <div class="stat-value">{total_hours} س</div>
            <div class="stat-trend trend-up">▲ مقابل الشهر الماضي</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">نسبة الإنجاز</div>
            <div class="stat-value">{rate}%</div>
            <div class="stat-trend trend-up">▲ مقابل الشهر الماضي</div>
        </div>
        """, unsafe_allow_html=True)
    
    # ===== عرض عبارة حسب الإنجاز =====
    achievement_msg = get_achievement_message(rate)
    st.markdown(f"""
    <div class="achievement-card" style="border-right-color: {'#4CAF50' if rate >= 70 else '#FF9800' if rate >= 50 else '#F44336'}">
        {achievement_msg}
    </div>
    """, unsafe_allow_html=True)
    
    # ===== عرض عبارة اليوم =====
    st.markdown(f"""
    <div class="quote-card">
        ✨ {st.session_state.daily_quote}
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # ===== جدول المناوبات =====
    st.subheader(f"📅 جدول مناوباتي - {calendar.month_name[month]} {year}")
    
    weeks = prepare_weekly_calendar(year, month, shifts_dict)
    weekdays_ar = ["الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]
    
    # بناء الجدول
    table_html = '<div class="shift-table-container"><table class="shift-table">'
    
    # رأس الجدول
    table_html += '<thead>资本'
    for day in weekdays_ar:
        table_html += f'<th>{day}</th>'
    table_html += '</tr></thead><tbody>'
    
    # صفوف الأسابيع
    for week in weeks:
        table_html += '<tr>'
        for day_data in week:
            day_num = day_data["day"]
            shift = day_data["shift"]
            is_today = day_data["is_today"]
            is_weekend = day_data["is_weekend"]
            is_current = day_data["is_current_month"]
            
            cell_class = ""
            if not is_current:
                cell_class = ' class="other-month-cell"'
            elif is_today:
                cell_class = ' class="today-cell"'
            elif is_weekend:
                cell_class = ' class="weekend-cell"'
            
            if shift and shift in SHIFT_TYPES:
                info = SHIFT_TYPES[shift]
                shift_display = f'<span class="shift-badge" style="background:{info["bg"]}; color:{info["color"]};">{shift}</span>'
            elif shift:
                shift_display = f'<span class="shift-badge" style="background:#f1f5f9; color:#475569;">{shift}</span>'
            else:
                shift_display = '<span class="shift-empty">—</span>'
            
            table_html += f'''
            <td{cell_class}>
                <div class="shift-day-number">{day_num}</div>
                <div>{shift_display}</div>
             </td>
            '''
        table_html += '</tr>'
    
    table_html += '</tbody></table></div>'
    st.markdown(table_html, unsafe_allow_html=True)
    
    # ملخص سريع
    st.caption(f"📌 أيام العمل: {work_days} | إجمالي الساعات: {total_hours} س | نسبة الإنجاز: {rate}%")
    
    # ===== دليل الرموز =====
    with st.expander("🔑 دليل الرموز"):
        cols = st.columns(4)
        codes = ["D12", "N12", "O12", "V", "CP8", "CP24", "LN8"]
        for i, code in enumerate(codes):
            if code in SHIFT_TYPES:
                info = SHIFT_TYPES[code]
                with cols[i % 4]:
                    st.markdown(f"<div class='legend-item' style='background:{info['bg']}; color:{info['color']};'><strong>{code}</strong> {info['name']}</div>", unsafe_allow_html=True)
    
    # ===== زر تسجيل الخروج =====
    st.divider()
    if st.button("تسجيل خروج", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ===== التشغيل الرئيسي =====
def main():
    if not st.session_state.authenticated:
        show_login()
    else:
        if st.session_state.token:
            fetch_notifications()
        
        if st.session_state.get("current_view") == "settings":
            show_settings()
        else:
            show_shifts()

if __name__ == "__main__":
    main()