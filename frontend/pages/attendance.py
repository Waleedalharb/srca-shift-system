# frontend/pages/attendance.py
import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta
from utils.helpers import page_header

# دالة مساعدة للوقت الآمن
def safe_time(time_str, default="08:00"):
    """تحويل النص إلى وقت بأمان"""
    if time_str == "--:--" or not time_str:
        return datetime.strptime(default, "%H:%M").time()
    try:
        return datetime.strptime(time_str, "%H:%M").time()
    except:
        return datetime.strptime(default, "%H:%M").time()

# ===== أنواع المناوبات =====
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
    """صفحة التكميل الذكي - مع التواقيت الكاملة"""
    
    page_header("📋 التكميل الذكي", "تسجيل الحضور مع أوقات المناوبة الكاملة", "📝")
    
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
        planned_info = SHIFT_TYPES.get(planned_shift, SHIFT_TYPES["off"])
        
        with st.container():
            st.markdown(f"#### 👤 {emp['full_name']} ({emp.get('emp_no', '')})")
            
            # معلومات المناوبة المخطط لها
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**المخطط:** {planned_info['name']}")
            with col2:
                st.markdown(f"**من:** {planned_info['start']}")
            with col3:
                st.markdown(f"**إلى:** {planned_info['end']}")
            
            # بيانات الحضور الفعلية
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                # نوع المناوبة الفعلية
                actual_shift = st.selectbox(
                    "المناوبة الفعلية",
                    options=list(SHIFT_TYPES.keys()),
                    format_func=lambda x: f"{SHIFT_TYPES[x]['icon']} {SHIFT_TYPES[x]['name']}",
                    index=list(SHIFT_TYPES.keys()).index(planned_shift) if planned_shift in SHIFT_TYPES else 0,
                    key=f"shift_{emp_id}"
                )
            
            with col2:
                # الحالة
                status = st.selectbox(
                    "الحالة",
                    ["حاضر", "غائب", "متأخر", "إجازة", "مهمة رسمية"],
                    key=f"status_{emp_id}"
                )
            
            with col3:
                # وقت الحضور الفعلي
                actual_start = st.time_input(
                    "⏰ وقت الحضور",
                    value=safe_time(planned_info['start']),
                    key=f"start_{emp_id}"
                )
            
            with col4:
                # وقت الانصراف الفعلي
                actual_end = st.time_input(
                    "🕒 وقت الانصراف",
                    value=safe_time(planned_info['end']),
                    key=f"end_{emp_id}"
                )
            
            with col5:
                # وقت التأخير (يظهر فقط إذا كان متأخر)
                if status == "متأخر":
                    late_time = st.time_input(
                        "⏱️ وقت التأخير",
                        value=time(8, 15),
                        key=f"late_{emp_id}"
                    )
                else:
                    late_time = None
                    st.markdown("—")
            
            attendance_data.append({
                "employee_id": emp_id,
                "employee_name": emp['full_name'],
                "planned_shift": planned_info['name'],
                "planned_start": planned_info['start'],
                "planned_end": planned_info['end'],
                "actual_shift": actual_shift,
                "status": status,
                "actual_start": actual_start,
                "actual_end": actual_end,
                "late_time": late_time
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
        
        # ===== عرض التقرير النهائي =====
        st.markdown("---")
        st.markdown("## 📄 تقرير التكميل النهائي")
        
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"**المركز:** {selected_center}")
        col2.markdown(f"**التاريخ:** {selected_date}")
        col3.markdown(f"**إجمالي الموظفين:** {len(attendance_data)}")
        
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
            
            # حساب التأخير
            late_info = ""
            if item['status'] == "متأخر" and item['late_time']:
                late_info = f"⏱️ {item['late_time'].strftime('%H:%M')}"
            
            report_data.append({
                "الموظف": item['employee_name'],
                "المخطط": item['planned_shift'],
                "الفعلية": actual_info['name'],
                "الحالة": f"{status_color} {item['status']}",
                "الحضور": item['actual_start'].strftime("%H:%M"),
                "الانصراف": item['actual_end'].strftime("%H:%M"),
                "التأخير": late_info
            })
        
        df_report = pd.DataFrame(report_data)
        st.dataframe(df_report, use_container_width=True, hide_index=True)
        
        # إحصائيات
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("👥 إجمالي", len(attendance_data))
        col2.metric("✅ حاضر", sum(1 for r in attendance_data if r['status'] == "حاضر"))
        col3.metric("❌ غائب", sum(1 for r in attendance_data if r['status'] == "غائب"))
        col4.metric("⏰ متأخر", sum(1 for r in attendance_data if r['status'] == "متأخر"))
        
        # التوكيل
        if delegator != "لا يوجد" and substitute != "لا يوجد":
            st.markdown("---")
            st.markdown("### 🔄 تفاصيل التوكيل")
            st.markdown(f"""
            <div style="background: #F0F9FF; padding: 1rem; border-radius: 8px; border-right: 4px solid #3B4A82;">
                <p><strong>👤 الموكل:</strong> {delegator}</p>
                <p><strong>🔄 البديل:</strong> {substitute}</p>
                <p><strong>📝 ملاحظات:</strong> {notes if notes else "لا توجد"}</p>
            </div>
            """, unsafe_allow_html=True)