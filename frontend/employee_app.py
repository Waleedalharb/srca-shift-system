# frontend/employee_app.py
import streamlit as st
import pandas as pd
from datetime import datetime
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

# ✅ إخفاء الشريط الجانبي بالكامل
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        display: none !important;
    }
    [data-testid="stSidebarCollapsedControl"] {
        display: none !important;
    }
    .main > div {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    .greeting-card {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 1.8rem;
        border-radius: 24px;
        margin-bottom: 1.8rem;
        color: white;
        text-align: center;
        box-shadow: 0 8px 20px rgba(0,0,0,0.08);
        border-bottom: 3px solid #ffd700;
    }
    .greeting-card h1 {
        margin: 0;
        font-size: 1.4rem;
        font-weight: 500;
        letter-spacing: 1px;
        opacity: 0.9;
    }
    .greeting-card h2 {
        margin: 0.6rem 0;
        font-size: 1.8rem;
        font-weight: 600;
    }
    .greeting-card p {
        margin: 0;
        font-size: 0.9rem;
        opacity: 0.8;
    }
    .motivation-card {
        background: #f8fafc;
        padding: 1rem 1.2rem;
        border-radius: 16px;
        margin-bottom: 1rem;
        border-right: 4px solid #2a5298;
        font-size: 1rem;
        color: #1e293b;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# ===== عبارات تشجيعية =====
MOTIVATIONAL_QUOTES = [
    "أنت تبذل جهداً رائعاً! استمر في التألق",
    "كل يوم عمل هو خطوة نحو النجاح. أنت مميز",
    "أداؤك المتميز يلهم الجميع. فخورون بك",
    "حتى في الليالي الطويلة، نورك يضيء القسم. شكراً لك",
    "وجودك يجعل فريقنا أقوى. نحن نقدر تفانيك",
    "عملك الجليل لا يمر دون تقدير. أنت نجمنا",
    "شكراً لالتزامك وإخلاصك في العمل",
    "كل صباح جديد معك هو بداية مميزة. استمر",
    "أنت قدوة حسنة لزملائك. فخورون بك",
    "تعاونك وروحك العالية تصنع الفرق",
    "إنجازاتك تتحدث عن نفسها. نحن نقدر جهودك",
    "نجم القطاع الجنوبي! أداؤك رائع دائماً"
]

# ===== تحية =====
def get_time_greeting():
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "صباح الخير"
    elif 12 <= hour < 16:
        return "مساء الخير"
    elif 16 <= hour < 20:
        return "مساء النور"
    else:
        return "مساء الخير"

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
        return "🌱 بداية ممتازة! كل رحلة تبدأ بخطوة، ونحن ندعمك"

# تعريف ثوابت المناوبات
SHIFT_TYPES = {
    "D12": {"name": "صباحي 12 س", "hours": 12, "color": "#4CAF50"},
    "N12": {"name": "ليلي 12 س", "hours": 12, "color": "#2196F3"},
    "O12": {"name": "تداخلي 12 س", "hours": 12, "color": "#FF9800"},
    "V": {"name": "إجازة", "hours": 0, "color": "#F44336"},
    "CP8": {"name": "تكميلية 8 س", "hours": 8, "color": "#9C27B0"},
    "CP24": {"name": "تكميلية 24 س", "hours": 24, "color": "#3F51B5"},
    "LN8": {"name": "ليلي تكميلي 8 س", "hours": 8, "color": "#009688"},
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

# ===== صفحة تسجيل الدخول =====
def show_login():
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: #1e3c72;">منصة الموظفين</h1>
        <p style="color: #64748b;">نظام إدارة المناوبات - قطاع الجنوب</p>
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
                        # 1. تسجيل الدخول
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
                            
                            # 2. جلب بيانات المستخدم (user)
                            user_response = requests.get(
                                f"{config.API_URL}/api/auth/me",
                                headers=headers,
                                timeout=10
                            )
                            
                            employee_id = None
                            full_name = username  # افتراضي
        
                            if user_response.status_code == 200:
                                user_data = user_response.json()
                                employee_id = user_data.get("employee_id")
                                
                                # 3. إذا كان لدينا employee_id، نجلب اسم الموظف
                                if employee_id:
                                    emp_response = requests.get(
                                        f"{config.API_URL}/api/employees/{employee_id}",
                                        headers=headers,
                                        timeout=10
                                    )
                                    if emp_response.status_code == 200:
                                        emp_data = emp_response.json()
                                        full_name = emp_data.get("full_name", username)
                            
                            # حفظ البيانات
                            st.session_state.employee_id = employee_id
                            st.session_state.full_name = full_name
                            st.session_state.authenticated = True
                            st.session_state.daily_quote = random.choice(MOTIVATIONAL_QUOTES)
                            
                            st.success(f"✅ مرحباً {full_name}")
                            st.rerun()
                        else:
                            st.error("❌ الرقم الوظيفي أو كلمة المرور غير صحيحة")
                    except Exception as e:
                        st.error(f"❌ فشل الاتصال بالخادم: {str(e)}")

# ===== صفحة عرض المناوبات =====
def show_shifts():
    full_name = st.session_state.get('full_name', st.session_state.username)
    greeting = get_time_greeting()
    
    # ✅ بطاقة ترحيبية
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
    
    # اختيار الشهر والسنة
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        year = st.number_input("السنة", 2020, 2030, datetime.now().year)
    with col2:
        month = st.number_input("الشهر", 1, 12, datetime.now().month)
    with col3:
        if st.button("تحديث", use_container_width=True):
            st.rerun()
    
    # جلب المناوبات
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
    
    # تحليل البيانات
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
    
    # حساب الإحصائيات
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
    
    # عرض الإحصائيات
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("أيام العمل", work_days)
    with col2:
        st.metric("أيام إجازة", vacation_days)
    with col3:
        st.metric("إجمالي الساعات", f"{total_hours} س")
    with col4:
        st.metric("نسبة الإنجاز", f"{rate}%")
    
    # عرض عبارة حسب الإنجاز
    achievement_msg = get_achievement_message(rate)
    st.markdown(f"""
    <div class="motivation-card">
        <span>{achievement_msg}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # عرض عبارة اليوم
    st.markdown(f"""
    <div class="motivation-card" style="background: #eef2ff; border-right-color: #4f46e5;">
        <span>✨ {st.session_state.daily_quote}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # عرض جدول المناوبات
    st.subheader(f"جدول مناوباتي - {calendar.month_name[month]} {year}")
    
    table_data = []
    for day in range(1, days_in_month + 1):
        shift_type = shifts_dict.get(day, "")
        shift_display = shift_type if shift_type else "—"
        table_data.append({"اليوم": day, "نوع المناوبة": shift_display})
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # دليل الرموز
    with st.expander("دليل الرموز"):
        cols = st.columns(4)
        codes = ["D12", "N12", "O12", "V", "CP8", "CP24", "LN8"]
        for i, code in enumerate(codes):
            if code in SHIFT_TYPES:
                info = SHIFT_TYPES[code]
                with cols[i % 4]:
                    st.markdown(f"<div style='background:{info['color']}; padding:0.5rem; border-radius:8px; text-align:center; color:white;'><strong>{code}</strong><br>{info['name']}</div>", unsafe_allow_html=True)
    
    # زر تسجيل الخروج
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
        show_shifts()

if __name__ == "__main__":
    main()