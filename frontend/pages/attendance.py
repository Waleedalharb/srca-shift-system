# frontend/pages/attendance.py
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from utils.helpers import page_header, section_title

# ===== أنواع المناوبات حسب الطلب =====
SHIFT_TYPES = {
    # صباحية
    "morning_6":  {"name": "صباحية 6 ساعات", "icon": "🌅", "color": "#FFB74D", "text": "#7A5800", "hours": 6, "start": "08:00", "end": "14:00"},
    "morning_8":  {"name": "صباحية 8 ساعات", "icon": "🌅", "color": "#FFB74D", "text": "#7A5800", "hours": 8, "start": "08:00", "end": "16:00"},
    "morning_10": {"name": "صباحية 10 ساعات", "icon": "🌅", "color": "#FFB74D", "text": "#7A5800", "hours": 10, "start": "08:00", "end": "18:00"},
    "morning_11": {"name": "صباحية 11 ساعة", "icon": "🌅", "color": "#FFB74D", "text": "#7A5800", "hours": 11, "start": "08:00", "end": "19:00"},
    "morning_12": {"name": "صباحية 12 ساعة", "icon": "🌅", "color": "#FFB74D", "text": "#7A5800", "hours": 12, "start": "08:00", "end": "20:00"},
    
    # مسائية
    "evening_6":  {"name": "مسائية 6 ساعات", "icon": "🌆", "color": "#64B5F6", "text": "#1A3070", "hours": 6, "start": "16:00", "end": "22:00"},
    "evening_8":  {"name": "مسائية 8 ساعات", "icon": "🌆", "color": "#64B5F6", "text": "#1A3070", "hours": 8, "start": "16:00", "end": "00:00"},
    "evening_10": {"name": "مسائية 10 ساعات", "icon": "🌆", "color": "#64B5F6", "text": "#1A3070", "hours": 10, "start": "14:00", "end": "00:00"},
    "evening_11": {"name": "مسائية 11 ساعة", "icon": "🌆", "color": "#64B5F6", "text": "#1A3070", "hours": 11, "start": "13:00", "end": "00:00"},
    "evening_12": {"name": "مسائية 12 ساعة", "icon": "🌆", "color": "#64B5F6", "text": "#1A3070", "hours": 12, "start": "12:00", "end": "00:00"},
    
    # ليلية
    "night_8":    {"name": "ليلية 8 ساعات", "icon": "🌙", "color": "#4A6FA5", "text": "#FFFFFF", "hours": 8, "start": "00:00", "end": "08:00"},
    "night_10":   {"name": "ليلية 10 ساعات", "icon": "🌙", "color": "#4A6FA5", "text": "#FFFFFF", "hours": 10, "start": "22:00", "end": "08:00"},
    
    # تداخلية
    "overlap_6":  {"name": "تداخلية 6 ساعات", "icon": "🔄", "color": "#45CFEF", "text": "#1A1A2E", "hours": 6, "start": "10:00", "end": "16:00"},
    "overlap_8":  {"name": "تداخلية 8 ساعات", "icon": "🔄", "color": "#45CFEF", "text": "#1A1A2E", "hours": 8, "start": "10:00", "end": "18:00"},
    "overlap_10": {"name": "تداخلية 10 ساعات", "icon": "🔄", "color": "#45CFEF", "text": "#1A1A2E", "hours": 10, "start": "09:00", "end": "19:00"},
    "overlap_12": {"name": "تداخلية 12 ساعة", "icon": "🔄", "color": "#45CFEF", "text": "#1A1A2E", "hours": 12, "start": "08:00", "end": "20:00"},
    
    # 24 ساعة
    "fullday_24": {"name": "نوبة 24 ساعة", "icon": "🕐", "color": "#E57373", "text": "#7A1212", "hours": 24, "start": "08:00", "end": "08:00"},
}

def show_attendance():
    """صفحة التكميل اليومي"""
    
    page_header("📋 التكميل اليومي", "تسجيل المناوبات اليومية", "📝")
    
    auth = st.session_state.auth_service
    es = st.session_state.get("employee_service")
    cs = st.session_state.get("center_service")
    
    if not es:
        from services.employee_service import EmployeeService
        es = EmployeeService(auth)
        st.session_state.employee_service = es
    
    if not cs:
        from services.center_service import CenterService
        cs = CenterService(auth)
        st.session_state.center_service = cs
    
    # بيانات اليوم
    today = date.today()
    hijri_date = "1447/09/18"  # يمكن تحديثها لاحقًا
    
    # اختيار المركز
    centers = cs.get_centers()
    center_names = [c['name'] for c in centers]
    selected_center = st.selectbox("🏥 المركز", center_names)
    
    # ===== معلومات اليوم =====
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="background: #F8FAFC; padding: 1rem; border-radius: 12px; text-align: center;">
            <div style="color: #64748B; font-size: 0.8rem;">التاريخ الهجري</div>
            <div style="color: #CE2E26; font-size: 1.5rem; font-weight: 700;">{hijri_date}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: #F8FAFC; padding: 1rem; border-radius: 12px; text-align: center;">
            <div style="color: #64748B; font-size: 0.8rem;">التاريخ الميلادي</div>
            <div style="color: #3B4A82; font-size: 1.5rem; font-weight: 700;">{today.strftime('%Y/%m/%d')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        weekday = ['الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد'][today.weekday()]
        st.markdown(f"""
        <div style="background: #F8FAFC; padding: 1rem; border-radius: 12px; text-align: center;">
            <div style="color: #64748B; font-size: 0.8rem;">اليوم</div>
            <div style="color: #42924B; font-size: 1.5rem; font-weight: 700;">{weekday}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="background: #F8FAFC; padding: 1rem; border-radius: 12px; text-align: center;">
            <div style="color: #64748B; font-size: 0.8rem;">رقم الأسبوع</div>
            <div style="color: #F1B944; font-size: 1.5rem; font-weight: 700;">{today.isocalendar()[1]}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ===== نموذج التكميل =====
    st.subheader("📝 بيانات المناوبة")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # نوع المناوبة
        shift_options = {v["name"]: k for k, v in SHIFT_TYPES.items()}
        selected_shift_name = st.selectbox("⏰ نوع المناوبة", list(shift_options.keys()))
        selected_shift_key = shift_options[selected_shift_name]
        shift_info = SHIFT_TYPES[selected_shift_key]
        
        # وقت المناوبة (يظهر تلقائيًا)
        st.markdown(f"""
        <div style="background: #F1F5F9; padding: 0.5rem 1rem; border-radius: 8px; margin: 0.5rem 0;">
            <span style="color: #1E293B; font-weight: 600;">⏱️ وقت المناوبة:</span>
            <span style="color: #CE2E26; margin-right: 0.5rem;">{shift_info['start']} - {shift_info['end']}</span>
            <span style="color: #64748B; margin-right: 1rem;">({shift_info['hours']} ساعة)</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # الموقع ورقمه
        col2_1, col2_2 = st.columns(2)
        with col2_1:
            location_number = st.text_input("📍 رقم الموقع", placeholder="مثال: 101")
        with col2_2:
            location_name = st.text_input("🏷️ اسم الموقع", placeholder="مثال: طريق الملك")
    
    # الموظفين
    st.markdown("#### 👥 موظفي المركز")
    
    employees = es.get_employees(limit=100).get("items", [])
    
    if employees:
        # عرض الموظفين في جدول سريع
        emp_data = []
        for emp in employees[:10]:  # أول 10 موظفين
            emp_data.append({
                "الموظف": emp['full_name'],
                "الرقم": emp.get('emp_no', ''),
                "النوع": emp.get('employee_type', ''),
                "اختيار": False  # هذا راح يكون checkbox
            })
        
        df_emp = pd.DataFrame(emp_data)
        
        # تحويل العمود الاختيار إلى checkbox
        edited_df = st.data_editor(
            df_emp,
            use_container_width=True,
            hide_index=True,
            column_config={
                "اختيار": st.column_config.CheckboxColumn("✅", help="اختر الموظف")
            }
        )
        
        selected_emps = edited_df[edited_df["اختيار"]]["الموظف"].tolist()
        
        if selected_emps:
            st.success(f"✅ تم اختيار {len(selected_emps)} موظف")
    else:
        st.info("لا يوجد موظفون")
    
    # معلومات إضافية
    st.markdown("---")
    st.subheader("➕ معلومات إضافية")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        vehicle_name = st.text_input("🚑 اسم المركبة", placeholder="مثال: اسعاف 01")
    with col2:
        incident_number = st.text_input("🔢 رقم المناسبة", placeholder="مثال: 2026-001")
    with col3:
        shift_code = st.text_input("📋 كود المناوبة", value=selected_shift_key if selected_shift_key else "D12")
    
    # ملاحظات
    notes = st.text_area("📝 الملاحظات", placeholder="أي ملاحظات إضافية...")
    
    # أزرار التحكم
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("💾 حفظ", use_container_width=True, type="primary"):
            st.success("✅ تم حفظ التكميل بنجاح")
            st.balloons()
    with col2:
        if st.button("➕ إضافة", use_container_width=True):
            st.info("➕ إضافة سجل جديد")
    with col3:
        if st.button("✏️ تعديل", use_container_width=True):
            st.info("✏️ تعديل البيانات")
    with col4:
        if st.button("📄 تقرير", use_container_width=True):
            st.info("📄 جاري إنشاء التقرير")
    
    # عرض التكميلات السابقة
    st.markdown("---")
    st.subheader("📋 التكميلات السابقة")
    
    sample_data = pd.DataFrame({
        "التاريخ": ["2026/03/07", "2026/03/06", "2026/03/05"],
        "الموظف": ["مشعل الحجيلي", "سعد الحربي", "فهد القحطاني"],
        "المناوبة": ["صباحية 12 س", "مسائية 8 س", "ليلية 10 س"],
        "الموقع": ["101", "205", "303"],
        "المركبة": ["اسعاف 01", "اسعاف 03", "اسعاف 02"],
        "الحالة": ["مكتمل", "مكتمل", "مكتمل"]
    })
    
    st.dataframe(sample_data, use_container_width=True, hide_index=True)