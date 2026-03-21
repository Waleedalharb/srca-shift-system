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
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stSidebarCollapsedControl"] { display: none !important; }
    .main > div { padding: 0.5rem 1rem !important; }
    
    @media (max-width: 768px) {
        .main > div { padding: 0.5rem 0.75rem !important; }
        .greeting-card { padding: 1rem !important; }
        .greeting-card h2 { font-size: 1.2rem !important; }
        .stat-card { padding: 0.75rem !important; }
        .stat-value { font-size: 1.3rem !important; }
        .shift-table th { padding: 8px 2px; font-size: 0.7rem; }
        .shift-table td { min-width: 45px; padding: 4px 1px; }
        .shift-badge { padding: 2px 4px; font-size: 0.6rem; }
        .shift-day-number { font-size: 0.65rem; }
    }
    
    .greeting-card {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 20px;
        margin-bottom: 1.5rem;
        text-align: center;
        border-top: 3px solid #d4af37;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
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
    
    .stat-card {
        background: #ffffff;
        padding: 1rem;
        border-radius: 16px;
        text-align: center;
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
    
    .achievement-card {
        background: #f8fafc;
        padding: 0.8rem 1rem;
        border-radius: 16px;
        margin-bottom: 0.8rem;
        border-right: 3px solid;
        font-size: 0.85rem;
    }
    .quote-card {
        background: #eef2ff;
        padding: 0.8rem 1rem;
        border-radius: 16px;
        margin-bottom: 1rem;
        border-right: 3px solid #4f46e5;
        font-size: 0.85rem;
    }
    
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
        min-width: 560px;
    }
    .shift-table th {
        background: #f8fafc;
        padding: 10px 4px;
        text-align: center;
        font-weight: 600;
        font-size: 0.8rem;
        border-bottom: 1px solid #e2e8f0;
    }
    .shift-table td {
        padding: 8px 2px;
        text-align: center;
        border: 1px solid #f0f2f5;
        vertical-align: middle;
    }
    .shift-day-number {
        font-size: 0.75rem;
        font-weight: 500;
        color: #64748b;
        margin-bottom: 4px;
    }
    .shift-badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    .shift-empty {
        color: #cbd5e1;
        font-size: 0.7rem;
    }
    .today-cell { background: #eef2ff; }
    .weekend-cell { background: #fef9e6; }
    .other-month-cell { background: #fafafa; opacity: 0.6; }
    
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
]

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
if "show_settings" not in st.session_state:
    st.session_state.show_settings = False

# ===== دوال API =====
def refresh_notifications():
    try:
        if not st.session_state.token:
            return []
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        response = requests.get(
            f"{config.API_URL}/api/notifications",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            st.session_state.notifications = response.json()
            return st.session_state.notifications
        else:
            st.session_state.notifications = []
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []

def mark_notification_read(notification_id):
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        response = requests.put(
            f"{config.API_URL}/api/notifications/{notification_id}/read",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            refresh_notifications()
            return True
    except:
        pass
    return False

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
            json={"current_password": current_password, "new_password": new_password},
            timeout=10
        )
        if response.status_code == 200:
            return True, "تم تغيير كلمة المرور بنجاح"
        elif response.status_code == 401:
            return False, "كلمة المرور الحالية غير صحيحة"
        else:
            return False, "حدث خطأ"
    except Exception as e:
        return False, f"خطأ: {str(e)}"

def build_calendar_rows(year, month, shifts_dict):
    """بناء صفوف الجدول (كل صف = أسبوع)"""
    import calendar as cal
    
    first_day = date(year, month, 1)
    days_in_month = cal.monthrange(year, month)[1]
    
    # يوم الأسبوع لليوم الأول (0=الإثنين, 6=الأحد)
    first_weekday = first_day.weekday()
    # تحويل بحيث الأحد = 0
    start_offset = (first_weekday + 1) % 7
    
    # إنشاء مصفوفة 6x7
    rows = []
    current_row = []
    
    # إضافة فراغات قبل بداية الشهر
    for _ in range(start_offset):
        current_row.append(None)
    
    # إضافة أيام الشهر
    for day in range(1, days_in_month + 1):
        current_date = date(year, month, day)
        current_row.append({
            "day": day,
            "shift": shifts_dict.get(day, ""),
            "is_today": current_date == date.today(),
            "is_weekend": current_date.weekday() >= 5
        })
        
        if len(current_row) == 7:
            rows.append(current_row)
            current_row = []
    
    # إضافة فراغات بعد نهاية الشهر
    if current_row:
        while len(current_row) < 7:
            current_row.append(None)
        rows.append(current_row)
    
    return rows

# ===== صفحة تسجيل الدخول =====
def show_login():
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: #1e2a3a;">منصة الموظفين</h1>
        <p style="color: #6c757d;">نظام إدارة المناوبات - قطاع الجنوب</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        username = st.text_input("الرقم الوظيفي")
        password = st.text_input("كلمة المرور", type="password")
        
        if st.form_submit_button("دخول", use_container_width=True, type="primary"):
            if not username or not password:
                st.error("❌ الرجاء إدخال جميع البيانات")
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
                            refresh_notifications()
                            
                            st.success(f"✅ مرحباً {full_name}")
                            st.rerun()
                        else:
                            st.error("❌ الرقم الوظيفي أو كلمة المرور غير صحيحة")
                    except Exception as e:
                        st.error(f"❌ فشل الاتصال: {str(e)}")

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
    
    # الشريط العلوي
    col1, col2, col3, col4 = st.columns([6, 1, 1, 1])
    with col2:
        unread = len([n for n in st.session_state.notifications if not n.get("is_read")])
        if st.button(f"🔔 {unread}" if unread > 0 else "🔔", key="notif_btn"):
            st.session_state.show_notifications = not st.session_state.show_notifications
    with col3:
        if st.button("🔄", key="refresh_btn", help="تحديث الإشعارات"):
            refresh_notifications()
            st.success("✅ تم تحديث الإشعارات")
            st.rerun()
    with col4:
        if st.button("⚙️", key="settings_btn"):
            st.session_state.show_settings = not st.session_state.show_settings
    
    # الإشعارات
    if st.session_state.show_notifications:
        with st.expander("📋 الإشعارات", expanded=True):
            if not st.session_state.notifications:
                st.info("لا توجد إشعارات")
            else:
                for n in st.session_state.notifications[:10]:
                    col_a, col_b = st.columns([10, 1])
                    with col_a:
                        st.markdown(f"""
                        <div style="background: {'#fff3e0' if not n.get('is_read') else '#f5f5f5'}; 
                                    padding: 0.6rem; border-radius: 12px; margin-bottom: 0.5rem;">
                            <div style="font-size: 0.7rem; color: #888;">{n.get('created_at', '').split('T')[0]}</div>
                            <div><strong>{n.get('title', '')}</strong></div>
                            <div>{n.get('message', '')}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_b:
                        if not n.get("is_read"):
                            if st.button("📖", key=f"read_{n.get('id')}"):
                                mark_notification_read(n.get("id"))
                                st.rerun()
    
    # الإعدادات
    if st.session_state.show_settings:
        with st.expander("⚙️ الإعدادات", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("الرقم الوظيفي", value=st.session_state.username, disabled=True)
            with col2:
                st.text_input("الاسم", value=st.session_state.full_name, disabled=True)
            
            st.markdown("---")
            with st.form("change_pwd"):
                current = st.text_input("كلمة المرور الحالية", type="password")
                new = st.text_input("كلمة المرور الجديدة", type="password")
                confirm = st.text_input("تأكيد", type="password")
                if st.form_submit_button("تغيير كلمة المرور"):
                    if not current or not new or not confirm:
                        st.error("❌ تعبئة جميع الحقول")
                    else:
                        ok, msg = change_password(current, new, confirm)
                        if ok:
                            st.success(f"✅ {msg}")
                        else:
                            st.error(f"❌ {msg}")
    
    # الترحيب
    st.markdown(f"""
    <div class="greeting-card">
        <h1>{greeting}</h1>
        <h2>{full_name}</h2>
        <p>يسعدنا وجودك معنا اليوم</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.employee_id:
        st.warning("⚠️ لا توجد بيانات موظف")
        return
    
    # اختيار الشهر
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        year = st.number_input("السنة", 2020, 2030, datetime.now().year, label_visibility="collapsed")
    with col2:
        month = st.number_input("الشهر", 1, 12, datetime.now().month, label_visibility="collapsed")
    with col3:
        if st.button("تحديث"):
            st.rerun()
    
    # جلب المناوبات
    with st.spinner("جاري التحميل..."):
        try:
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            start = f"{year}-{month:02d}-01"
            if month == 12:
                end = f"{year+1}-01-01"
            else:
                end = f"{year}-{month+1:02d}-01"
            
            resp = requests.get(
                f"{config.API_URL}/api/shifts/by_employee",
                headers=headers,
                params={"employee_id": st.session_state.employee_id, "start_date": start, "end_date": end},
                timeout=10
            )
            shifts = resp.json().get("items", []) if resp.status_code == 200 else []
        except Exception as e:
            st.error(f"خطأ: {e}")
            return
    
    # تحليل المناوبات
    shifts_dict = {}
    for s in shifts:
        d = s.get("date", "").split("T")[0]
        try:
            day = int(d.split("-")[2])
            t = s.get("shift_type")
            if t and t != "off":
                shifts_dict[day] = t
        except:
            pass
    
    # إحصائيات
    days_in_month = calendar.monthrange(year, month)[1]
    work = 0
    vacation = 0
    hours = 0
    for day in range(1, days_in_month + 1):
        t = shifts_dict.get(day)
        if t:
            if t == 'V':
                vacation += 1
            else:
                work += 1
                hours += SHIFT_TYPES.get(t, {}).get("hours", 0)
    
    rate = min(int((hours / 192) * 100), 100)
    
    # عرض الإحصائيات
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="stat-card"><div class="stat-label">أيام العمل</div><div class="stat-value">{work}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-card"><div class="stat-label">إجازات</div><div class="stat-value">{vacation}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="stat-card"><div class="stat-label">الساعات</div><div class="stat-value">{hours}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="stat-card"><div class="stat-label">الإنجاز</div><div class="stat-value">{rate}%</div></div>', unsafe_allow_html=True)
    
    # عبارات
    st.markdown(f'<div class="achievement-card" style="border-right-color: {"#4CAF50" if rate>=70 else "#FF9800"}">{get_achievement_message(rate)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="quote-card">✨ {st.session_state.daily_quote}</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # ===== جدول المناوبات (شهر كامل) =====
    st.subheader(f"📅 جدول مناوباتي - {calendar.month_name[month]} {year}")
    
    rows = build_calendar_rows(year, month, shifts_dict)
    weekdays_ar = ["الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]
    
    # بناء جدول HTML بشكل صحيح
    html = '<div class="shift-table-container"><table class="shift-table">'
    html += '<thead>资本'
    for wd in weekdays_ar:
        html += f'<th>{wd}</th>'
    html += '</thead><tbody>'
    
    for row in rows:
        html += ' tr'
        for cell in row:
            if cell is None:
                html += '<td class="other-month-cell"><div class="shift-day-number"> </div><div> </div>'
            else:
                day_num = cell["day"]
                shift = cell["shift"]
                is_today = cell["is_today"]
                is_weekend = cell["is_weekend"]
                
                cell_class = ""
                if is_today:
                    cell_class = ' class="today-cell"'
                elif is_weekend:
                    cell_class = ' class="weekend-cell"'
                
                if shift and shift in SHIFT_TYPES:
                    info = SHIFT_TYPES[shift]
                    shift_html = f'<span class="shift-badge" style="background:{info["bg"]}; color:{info["color"]};">{shift}</span>'
                elif shift:
                    shift_html = f'<span class="shift-badge" style="background:#f1f5f9;">{shift}</span>'
                else:
                    shift_html = '<span class="shift-empty">—</span>'
                
                html += f'<td{cell_class}><div class="shift-day-number">{day_num}</div><div>{shift_html}</div>'
        html += '   '
    
    html += '</tbody>   </div>'
    st.markdown(html, unsafe_allow_html=True)
    
    st.caption(f"📌 {work} يوم عمل | {hours} ساعة | {rate}% إنجاز")
    
    # دليل الرموز
    with st.expander("🔑 دليل الرموز"):
        cols = st.columns(4)
        for i, (code, info) in enumerate(SHIFT_TYPES.items()):
            with cols[i % 4]:
                st.markdown(f'<div style="background:{info["bg"]}; padding:0.3rem; border-radius:12px; text-align:center;"><strong>{code}</strong><br>{info["name"]}</div>', unsafe_allow_html=True)
    
    # تسجيل الخروج
    st.divider()
    if st.button("تسجيل خروج", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

def main():
    if not st.session_state.authenticated:
        show_login()
    else:
        if st.session_state.token:
            refresh_notifications()
        show_shifts()

if __name__ == "__main__":
    main()