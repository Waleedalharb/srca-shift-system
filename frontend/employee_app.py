# frontend/employee_app.py
import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
import requests
from config import config

# إعداد الصفحة
st.set_page_config(
    page_title="مناوباتي - منصة الموظفين",
    page_icon="👤",
    layout="wide"
)

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

# ===== صفحة تسجيل الدخول =====
def show_login():
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1>👤 منصة الموظفين</h1>
        <p>نظام إدارة المناوبات - قطاع الجنوب</p>
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
                            
                            # 2. جلب بيانات المستخدم (بما فيها employee_id)
                            headers = {"Authorization": f"Bearer {token}"}
                            user_response = requests.get(
                                f"{config.API_URL}/api/auth/me",
                                headers=headers,
                                timeout=10
                            )
                            
                            if user_response.status_code == 200:
                                user_data = user_response.json()
                                st.session_state.employee_id = user_data.get("employee_id")
                                st.session_state.full_name = user_data.get("full_name", username)
                                st.session_state.authenticated = True
                                st.success(f"✅ مرحباً {st.session_state.full_name}")
                                st.rerun()
                            else:
                                # إذا فشل جلب البيانات، استخدم بيانات افتراضية
                                st.session_state.employee_id = None
                                st.session_state.full_name = username
                                st.session_state.authenticated = True
                                st.warning("تم تسجيل الدخول ولكن لم نتمكن من جلب بياناتك بالكامل")
                                st.rerun()
                        else:
                            st.error("❌ الرقم الوظيفي أو كلمة المرور غير صحيحة")
                    except Exception as e:
                        st.error(f"❌ فشل الاتصال بالخادم: {str(e)}")

# ===== صفحة عرض المناوبات =====
def show_shifts():
    st.title(f"📅 مناوباتي")
    st.caption(f"مرحباً {st.session_state.get('full_name', st.session_state.username)}")
    
    if not st.session_state.employee_id:
        st.error("❌ لم يتم العثور على بيانات الموظف")
        if st.button("تسجيل خروج"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        return
    
    # اختيار الشهر والسنة
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        year = st.number_input("📅 السنة", 2020, 2030, datetime.now().year)
    with col2:
        month = st.number_input("📆 الشهر", 1, 12, datetime.now().month)
    with col3:
        if st.button("🔄 تحديث", use_container_width=True):
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
                    "employee_id": st.session_state.employee_id,  # 👈 المعرف الصحيح
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
    
    if not shifts:
        st.info(f"📭 لا توجد مناوبات مسجلة لك في {calendar.month_name[month]} {year}")
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
    
    # عرض الإحصائيات
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📅 أيام العمل", work_days)
    with col2:
        st.metric("🏖️ أيام إجازة", vacation_days)
    with col3:
        st.metric("⏱️ إجمالي الساعات", f"{total_hours} س")
    with col4:
        required = 192
        rate = int((total_hours / required) * 100) if required > 0 else 0
        st.metric("📊 نسبة الإنجاز", f"{min(rate, 100)}%")
    
    st.divider()
    
    # عرض جدول المناوبات
    st.subheader(f"📋 جدول مناوباتي - {calendar.month_name[month]} {year}")
    
    # عرض الجدول
    table_data = []
    for day in range(1, days_in_month + 1):
        shift_type = shifts_dict.get(day, "")
        shift_display = shift_type if shift_type else "-"
        table_data.append({"اليوم": day, "نوع المناوبة": shift_display})
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # دليل الرموز
    with st.expander("🔑 دليل الرموز"):
        cols = st.columns(4)
        codes = ["D12", "N12", "O12", "V", "CP8", "CP24", "LN8"]
        for i, code in enumerate(codes):
            if code in SHIFT_TYPES:
                info = SHIFT_TYPES[code]
                with cols[i % 4]:
                    st.markdown(f"<div style='background:{info['color']}; padding:0.5rem; border-radius:8px; text-align:center; color:white;'><strong>{code}</strong><br>{info['name']}</div>", unsafe_allow_html=True)
    
    # زر تسجيل الخروج
    st.divider()
    if st.button("🚪 تسجيل خروج", use_container_width=True):
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