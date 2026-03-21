# frontend/employee_app.py
import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
import requests
from config import config

# إعداد الصفحة
st.set_page_config(
    page_title="مناوباتي",
    page_icon="👤",
    layout="wide"
)

# تعريف ثوابت المناوبات (إذا لم تكن موجودة في utils.constants)
SHIFT_TYPES = {
    "D12": {"name": "صباحي 12 س", "hours": 12, "color": "#4CAF50", "text_color": "white"},
    "N12": {"name": "ليلي 12 س", "hours": 12, "color": "#2196F3", "text_color": "white"},
    "O12": {"name": "تداخلي 12 س", "hours": 12, "color": "#FF9800", "text_color": "white"},
    "V": {"name": "إجازة", "hours": 0, "color": "#F44336", "text_color": "white"},
    "CP8": {"name": "تكميلية 8 س", "hours": 8, "color": "#9C27B0", "text_color": "white"},
    "CP24": {"name": "تكميلية 24 س", "hours": 24, "color": "#3F51B5", "text_color": "white"},
    "LN8": {"name": "ليلي تكميلي 8 س", "hours": 8, "color": "#009688", "text_color": "white"},
}

# خدمات API
class AuthService:
    def __init__(self):
        self.base_url = config.API_URL
        self.token = None
    
    def login(self, username, password):
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={"username": username, "password": password},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                st.session_state.token = self.token
                return True
            return False
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def get_headers(self):
        token = st.session_state.get("token", self.token)
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

class ShiftService:
    def __init__(self, auth):
        self.auth = auth
        self.base_url = f"{config.API_URL}/shifts"
    
    def get_employee_shifts_by_month(self, employee_id, year, month):
        try:
            start_date = f"{year}-{month:02d}-01"
            if month == 12:
                end_date = f"{year+1}-01-01"
            else:
                end_date = f"{year}-{month+1:02d}-01"
            
            response = requests.get(
                f"{self.base_url}/by_employee",
                headers=self.auth.get_headers(),
                params={
                    "employee_id": employee_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "limit": 40
                },
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("items", [])
            return []
        except Exception as e:
            print(f"Error getting shifts: {e}")
            return []

# ===== صفحة تسجيل الدخول =====
def show_employee_login():
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1>👤 منصة الموظفين</h1>
        <p>نظام إدارة المناوبات - قطاع الجنوب</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("employee_login"):
        username = st.text_input("الرقم الوظيفي", placeholder="أدخل الرقم الوظيفي")
        password = st.text_input("كلمة المرور", type="password", placeholder="أدخل كلمة المرور")
        
        if st.form_submit_button("دخول", use_container_width=True, type="primary"):
            if not username or not password:
                st.error("❌ الرجاء إدخال الرقم الوظيفي وكلمة المرور")
            else:
                with st.spinner("جاري تسجيل الدخول..."):
                    auth = AuthService()
                    if auth.login(username, password):
                        # جلب بيانات المستخدم
                        token = st.session_state.get("token")
                        headers = {"Authorization": f"Bearer {token}"}
                        try:
                            response = requests.get(
                                f"{config.API_URL}/users/me",
                                headers=headers,
                                timeout=5
                            )
                            if response.status_code == 200:
                                user_data = response.json()
                                st.session_state.user = user_data
                                st.session_state.user_role = user_data.get("role", "").upper()
                                st.session_state.user_employee_id = user_data.get("employee_id")
                                st.session_state.user_full_name = user_data.get("full_name", username)
                                st.session_state.username = username
                                st.session_state.authenticated = True
                                st.session_state.auth_service = auth
                                st.rerun()
                            else:
                                st.error("❌ فشل في جلب بيانات المستخدم")
                        except Exception as e:
                            st.error(f"❌ خطأ: {str(e)}")
                    else:
                        st.error("❌ الرقم الوظيفي أو كلمة المرور غير صحيحة")

# ===== صفحة عرض المناوبات =====
def show_employee_shifts():
    user = st.session_state.get("user", {})
    employee_id = user.get("employee_id")
    employee_name = st.session_state.get("user_full_name", "الموظف")
    auth = st.session_state.get("auth_service")
    
    st.title(f"📅 مناوباتي")
    st.caption(f"مرحباً {employee_name}")
    
    if not employee_id:
        st.error("❌ لا يوجد موظف مرتبط بهذا الحساب")
        if st.button("تسجيل خروج"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        return
    
    if not auth:
        st.error("❌ خطأ في المصادقة")
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
    ss = ShiftService(auth)
    
    with st.spinner("جاري تحميل مناوباتك..."):
        shifts = ss.get_employee_shifts_by_month(employee_id, year, month)
    
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
    for day in range(1, days_in_month + 1):
        shift_type = shifts_dict.get(day)
        if shift_type in SHIFT_TYPES:
            total_hours += SHIFT_TYPES[shift_type].get("hours", 0)
    
    # عرض الإحصائيات
    work_days = len([d for d in shifts_dict.values() if d != 'V'])
    vacation_days = len([d for d in shifts_dict.values() if d == 'V'])
    required = 192
    rate = int((total_hours / required) * 100) if required > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📅 أيام العمل", work_days)
    with col2:
        st.metric("🏖️ أيام إجازة", vacation_days)
    with col3:
        st.metric("⏱️ إجمالي الساعات", f"{total_hours} س")
    with col4:
        st.metric("📊 نسبة الإنجاز", f"{min(rate, 100)}%")
    
    st.divider()
    
    # عرض جدول المناوبات
    st.subheader(f"📋 جدول مناوباتي - {calendar.month_name[month]} {year}")
    
    # بناء الجدول
    row = {
        "الموظف": employee_name,
        "الرقم الوظيفي": st.session_state.get("username", ""),
        "إجمالي الساعات": f"{total_hours} س"
    }
    
    for day in range(1, days_in_month + 1):
        shift_type = shifts_dict.get(day)
        row[f"يوم {day}"] = shift_type if shift_type else ""
    
    df = pd.DataFrame([row])
    display_cols = ["الموظف", "الرقم الوظيفي", "إجمالي الساعات"] + [f"يوم {d}" for d in range(1, days_in_month + 1)]
    
    column_config = {}
    for day in range(1, days_in_month + 1):
        column_config[f"يوم {day}"] = st.column_config.TextColumn(str(day), width="small")
    
    st.dataframe(df[display_cols], use_container_width=True, hide_index=True, column_config=column_config)
    
    # دليل الرموز
    with st.expander("🔑 دليل الرموز"):
        cols = st.columns(4)
        codes = ["D12", "N12", "O12", "V", "CP8", "CP24", "LN8"]
        for i, code in enumerate(codes):
            if code in SHIFT_TYPES:
                info = SHIFT_TYPES[code]
                with cols[i % 4]:
                    st.markdown(f"<div style='background:{info['color']}; padding:0.5rem; border-radius:8px; text-align:center;'><strong>{code}</strong><br>{info['name']}</div>", unsafe_allow_html=True)
    
    # زر تسجيل الخروج
    st.divider()
    if st.button("🚪 تسجيل خروج", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ===== التشغيل الرئيسي =====
def main():
    if not st.session_state.get("authenticated", False):
        show_employee_login()
    else:
        show_employee_shifts()

if __name__ == "__main__":
    main()