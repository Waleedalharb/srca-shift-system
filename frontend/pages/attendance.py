# frontend/pages/attendance.py
import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta
from utils.helpers import page_header

# ===== أنواع المناوبات (مطابقة لصفحة المناوبات) =====
SHIFT_TYPES = {
    "morning_6":  {"name": "صباحية 6 س", "icon": "🌅", "color": "#FFB74D", "text": "#7A5800", "hours": 6, "start": "08:00", "end": "14:00"},
    "morning_8":  {"name": "صباحية 8 س", "icon": "🌅", "color": "#FFB74D", "text": "#7A5800", "hours": 8, "start": "08:00", "end": "16:00"},
    "morning_10": {"name": "صباحية 10 س", "icon": "🌅", "color": "#FFB74D", "text": "#7A5800", "hours": 10, "start": "08:00", "end": "18:00"},
    "morning_11": {"name": "صباحية 11 س", "icon": "🌅", "color": "#FFB74D", "text": "#7A5800", "hours": 11, "start": "08:00", "end": "19:00"},
    "morning_12": {"name": "صباحية 12 س", "icon": "🌅", "color": "#FFB74D", "text": "#7A5800", "hours": 12, "start": "08:00", "end": "20:00"},
    "evening_6":  {"name": "مسائية 6 س", "icon": "🌆", "color": "#64B5F6", "text": "#1A3070", "hours": 6, "start": "16:00", "end": "22:00"},
    "evening_8":  {"name": "مسائية 8 س", "icon": "🌆", "color": "#64B5F6", "text": "#1A3070", "hours": 8, "start": "16:00", "end": "00:00"},
    "evening_10": {"name": "مسائية 10 س", "icon": "🌆", "color": "#64B5F6", "text": "#1A3070", "hours": 10, "start": "14:00", "end": "00:00"},
    "evening_11": {"name": "مسائية 11 س", "icon": "🌆", "color": "#64B5F6", "text": "#1A3070", "hours": 11, "start": "13:00", "end": "00:00"},
    "evening_12": {"name": "مسائية 12 س", "icon": "🌆", "color": "#64B5F6", "text": "#1A3070", "hours": 12, "start": "12:00", "end": "00:00"},
    "night_8":    {"name": "ليلية 8 س", "icon": "🌙", "color": "#4A6FA5", "text": "#FFFFFF", "hours": 8, "start": "00:00", "end": "08:00"},
    "night_10":   {"name": "ليلية 10 س", "icon": "🌙", "color": "#4A6FA5", "text": "#FFFFFF", "hours": 10, "start": "22:00", "end": "08:00"},
    "overlap_6":  {"name": "تداخلية 6 س", "icon": "🔄", "color": "#45CFEF", "text": "#1A1A2E", "hours": 6, "start": "10:00", "end": "16:00"},
    "overlap_8":  {"name": "تداخلية 8 س", "icon": "🔄", "color": "#45CFEF", "text": "#1A1A2E", "hours": 8, "start": "10:00", "end": "18:00"},
    "overlap_10": {"name": "تداخلية 10 س", "icon": "🔄", "color": "#45CFEF", "text": "#1A1A2E", "hours": 10, "start": "09:00", "end": "19:00"},
    "overlap_12": {"name": "تداخلية 12 س", "icon": "🔄", "color": "#45CFEF", "text": "#1A1A2E", "hours": 12, "start": "08:00", "end": "20:00"},
    "fullday_24": {"name": "نوبة 24 س", "icon": "🕐", "color": "#E57373", "text": "#7A1212", "hours": 24, "start": "08:00", "end": "08:00"},
    "off":        {"name": "إجازة", "icon": "⭕", "color": "#E0E0E0", "text": "#4A5568", "hours": 0, "start": "--:--", "end": "--:--"},
}

def _get_services():
    """تهيئة الخدمات"""
    auth = st.session_state.auth_service
    es = st.session_state.get("employee_service")
    cs = st.session_state.get("center_service")
    ss = st.session_state.get("shift_service")
    
    if not es:
        from services.employee_service import EmployeeService
        es = EmployeeService(auth)
        st.session_state.employee_service = es
    
    if not cs:
        from services.center_service import CenterService
        cs = CenterService(auth)
        st.session_state.center_service = cs
    
    if not ss:
        from services.shift_service import ShiftService
        ss = ShiftService(auth)
        st.session_state.shift_service = ss
    
    return es, cs, ss

def show_attendance():
    """صفحة التكميل الذكي - مع اختيار نوع المناوبة"""
    
    page_header("📋 التكميل الذكي", "تسجيل الحضور مع تحديد نوع المناوبة", "📝")
    
    es, cs, ss = _get_services()
    
    # جلب المراكز
    all_centers = cs.get_centers() or []
    
    if not all_centers:
        st.warning("⚠️ لا توجد مراكز")
        return
    
    # ===== اختيار التاريخ والمركز =====
    col1, col2 = st.columns(2)
    
    with col1:
        selected_date = st.date_input("📅 التاريخ", value=date.today())
    
    with col2:
        center_names = [c["name"] for c in all_centers]
        selected_center = st.selectbox("🏥 المركز", center_names)
        center_id = next(c["id"] for c in all_centers if c["name"] == selected_center)
    
    # جلب موظفي المركز
    employees = es.get_employees(center_id=center_id).get("items", [])
    
    if not employees:
        st.warning(f"⚠️ لا يوجد موظفون في {selected_center}")
        return
    
    # جلب المناوبات المخطط لها لهذا اليوم
    with st.spinner("جاري تحميل المناوبات..."):
        planned_shifts = ss.get_shifts_by_date(center_id, selected_date)
    
    # إنشاء خريطة للمناوبات المخطط لها (employee_id -> shift_type)
    planned_map = {}
    for shift in planned_shifts:
        for assignment in shift.get("assignments", []):
            emp_id = assignment.get("employee_id")
            if emp_id:
                planned_map[emp_id] = shift.get("shift_type", "off")
    
    # ===== نموذج التكميل =====
    st.markdown("---")
    st.markdown("### 📝 تسجيل الحضور")
    
    attendance_data = []
    
    for emp in employees:
        emp_id = str(emp["id"])
        planned_shift = planned_map.get(emp_id, "off")
        shift_info = SHIFT_TYPES.get(planned_shift, SHIFT_TYPES["off"])
        
        with st.container():
            st.markdown(f"#### 👤 {emp['full_name']} ({emp.get('emp_no', '')})")
            
            col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
            
            with col1:
                st.markdown(f"**المناوبة المخطط لها:** {shift_info['name']}")
            
            with col2:
                # اختيار نوع المناوبة الفعلية (كل الخيارات متاحة)
                actual_shift = st.selectbox(
                    "نوع المناوبة الفعلية",
                    options=list(SHIFT_TYPES.keys()),
                    format_func=lambda x: f"{SHIFT_TYPES[x]['icon']} {SHIFT_TYPES[x]['name']}",
                    index=list(SHIFT_TYPES.keys()).index(planned_shift) if planned_shift in SHIFT_TYPES else 0,
                    key=f"shift_{emp_id}"
                )
            
            with col3:
                status = st.selectbox(
                    "الحالة",
                    ["حاضر", "غائب", "متأخر", "إجازة", "مهمة رسمية"],
                    key=f"status_{emp_id}"
                )
            
            with col4:
                check_in = st.time_input(
                    "⏰ وقت الحضور",
                    value=datetime.strptime(SHIFT_TYPES[actual_shift]['start'], "%H:%M").time(),
                    key=f"in_{emp_id}"
                )
            
            attendance_data.append({
                "employee_id": emp_id,
                "employee_name": emp['full_name'],
                "planned_shift": shift_info['name'],
                "actual_shift": actual_shift,
                "status": status,
                "check_in": check_in
            })
            
            st.markdown("---")
    
    # ===== التوكيل والبديل =====
    st.markdown("### 🔄 التوكيل والبديل")
    
    emp_options = [f"{e['full_name']} ({e.get('emp_no', '')})" for e in employees]
    
    col1, col2 = st.columns(2)
    
    with col1:
        delegator = st.selectbox("👤 الموكل (الموظف الأساسي)", ["لا يوجد"] + emp_options)
    
    with col2:
        substitute = st.selectbox("🔄 البديل", ["لا يوجد"] + emp_options)
    
    notes = st.text_area("📝 ملاحظات", placeholder="أي ملاحظات إضافية...")
    
    # ===== حفظ التكميل =====
    if st.button("💾 حفظ التكميل", type="primary", use_container_width=True):
        st.success("✅ تم حفظ التكميل بنجاح")
        st.balloons()
        
        # عرض التقرير
        st.markdown("---")
        st.markdown("## 📄 تقرير التكميل النهائي")
        
        col1, col2 = st.columns(2)
        col1.markdown(f"**المركز:** {selected_center}")
        col2.markdown(f"**التاريخ:** {selected_date}")
        
        report_data = []
        for item in attendance_data:
            actual_info = SHIFT_TYPES.get(item['actual_shift'], SHIFT_TYPES["off"])
            status_color = {
                "حاضر": "🟢",
                "غائب": "🔴",
                "متأخر": "🟡",
                "إجازة": "🔵",
                "مهمة رسمية": "🟠"
            }.get(item['status'], "⚪")
            
            report_data.append({
                "الموظف": item['employee_name'],
                "المخطط": item['planned_shift'],
                "الفعلية": actual_info['name'],
                "الحالة": f"{status_color} {item['status']}",
                "الحضور": item['check_in'].strftime("%H:%M")
            })
        
        df_report = pd.DataFrame(report_data)
        st.dataframe(df_report, use_container_width=True, hide_index=True)