# frontend/pages/my_shifts.py
import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
from utils.constants import SHIFT_TYPES
from services.shift_service import ShiftService
import time

# محاولة تعيين إعدادات الصفحة، مع تجاهل الخطأ إذا كانت مضبوطة مسبقاً
try:
    st.set_page_config(page_title="مناوباتي", layout="wide")
except Exception:
    pass

def calculate_employee_hours(emp_shifts, days_in_month):
    """حساب إجمالي ساعات الموظف"""
    total = 0
    for day in range(1, days_in_month + 1):
        shift_type = emp_shifts.get(day)
        if shift_type and shift_type in SHIFT_TYPES:
            if shift_type in ['D12', 'N12', 'O12']:
                total += 12
            elif shift_type == 'V':
                total += 0
            else:
                total += SHIFT_TYPES[shift_type].get("hours", 0)
    return total

def show_my_shifts():
    """عرض مناوبات الموظف الحالي فقط"""
    
    # التحقق من وجود المستخدم
    if 'user' not in st.session_state:
        st.switch_page("pages/login.py")
        return
    
    user = st.session_state.user
    employee_id = user.get("employee_id")
    employee_name = user.get("full_name", user.get("username", "الموظف"))
    
    st.title(f"📅 مناوباتي")
    st.caption(f"مرحباً {employee_name}")
    
    if not employee_id:
        st.error("❌ لا يوجد موظف مرتبط بهذا الحساب")
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
    
    # جلب مناوبات الموظف
    ss = ShiftService(st.session_state.auth_service)
    
    with st.spinner("جاري تحميل مناوباتك..."):
        shifts = ss.get_employee_shifts_by_month(employee_id, year, month)
    
    if not shifts:
        st.info(f"📭 لا توجد مناوبات مسجلة لك في {calendar.month_name[month]} {year}")
        return
    
    # تحويل البيانات إلى جدول
    days_in_month = calendar.monthrange(year, month)[1]
    
    # بناء قاموس المناوبات
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
    
    # عرض إحصائيات سريعة
    total_hours = calculate_employee_hours(shifts_dict, days_in_month)
    required_hours = 192
    completion_rate = int((total_hours / required_hours) * 100) if required_hours > 0 else 0
    completion_rate = min(completion_rate, 100)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📅 أيام العمل", len([d for d in shifts_dict.values() if d not in ['V', 'off']]))
    with col2:
        st.metric("🏖️ أيام إجازة", len([d for d in shifts_dict.values() if d == 'V']))
    with col3:
        st.metric("⏱️ إجمالي الساعات", f"{total_hours} س")
    with col4:
        st.metric("📊 نسبة الإنجاز", f"{completion_rate}%")
    
    st.divider()
    
    # عرض جدول المناوبات
    st.subheader(f"📋 جدول مناوباتي - {calendar.month_name[month]} {year}")
    
    # إنشاء صفوف الجدول (عرض أفقي)
    table_data = []
    
    # نعرض جدول بصف واحد للموظف
    row = {
        "الموظف": employee_name,
        "الرقم الوظيفي": user.get("username", ""),
        "إجمالي الساعات": f"{total_hours} س",
        "نسبة الإنجاز": f"{completion_rate}%"
    }
    
    for day in range(1, days_in_month + 1):
        shift_type = shifts_dict.get(day)
        shift_display = shift_type if shift_type else ""
        row[f"يوم {day}"] = shift_display
    
    table_data.append(row)
    
    df = pd.DataFrame(table_data)
    
    # إعداد الأعمدة
    display_cols = ["الموظف", "الرقم الوظيفي", "إجمالي الساعات", "نسبة الإنجاز"] + [f"يوم {d}" for d in range(1, days_in_month + 1)]
    
    column_config = {}
    for day in range(1, days_in_month + 1):
        column_config[f"يوم {day}"] = st.column_config.TextColumn(
            str(day),
            width="small",
            help=f"يوم {day}"
        )
    
    st.dataframe(df[display_cols], use_container_width=True, hide_index=True, column_config=column_config)
    
    # دليل الرموز
    with st.expander("🔑 دليل الرموز"):
        cols = st.columns(5)
        codes_to_show = ["D12", "N12", "O12", "V", "CP8", "CP24", "LN8"]
        for i, code in enumerate(codes_to_show):
            if code in SHIFT_TYPES:
                info = SHIFT_TYPES[code]
                with cols[i % 5]:
                    st.markdown(f"""
                    <div style='background:{info["color"]}; color:{info["text_color"]}; padding:0.5rem; border-radius:8px; text-align:center;'>
                        <strong>{code}</strong> - {info["name"]}
                    </div>
                    """, unsafe_allow_html=True)
    
    # ملاحظة للموظف
    st.info("📌 **ملاحظة:** هذا الجدول يعرض مناوباتك فقط. أي تغيير من قبل المشرف سيظهر لك إشعار.")

if __name__ == "__main__":
    show_my_shifts()