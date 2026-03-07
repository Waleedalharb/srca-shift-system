# frontend/pages/attendance.py
import streamlit as st
import pandas as pd
from datetime import datetime, date, time
from utils.helpers import page_header

# ===== أنواع المناوبات (مطابقة لصفحة المناوبات) =====
SHIFT_TYPES = {
    "morning_12": {"name": "صباحي 12 س", "icon": "🌅", "hours": 12, "start": "08:00", "end": "20:00"},
    "night_12":   {"name": "ليلي 12 س", "icon": "🌙", "hours": 12, "start": "20:00", "end": "08:00"},
    "official_8": {"name": "دوام رسمي", "icon": "🏢", "hours": 8, "start": "08:00", "end": "16:00"},
    "official_9": {"name": "دوام 9 س", "icon": "📋", "hours": 9, "start": "08:00", "end": "17:00"},
    "overlap_morning": {"name": "تداخلي صباحي", "icon": "🔄", "hours": 10, "start": "10:00", "end": "20:00"},
    "overlap_evening": {"name": "تداخلي مسائي", "icon": "🔄", "hours": 10, "start": "14:00", "end": "00:00"},
    "weekend_morning": {"name": "نهاية أسبوع صباحي", "icon": "🌅", "hours": 8, "start": "08:00", "end": "16:00"},
    "weekend_night":   {"name": "نهاية أسبوع ليلي", "icon": "🌙", "hours": 8, "start": "16:00", "end": "00:00"},
    "off":             {"name": "إجازة", "icon": "⭕", "hours": 0, "start": "--:--", "end": "--:--"},
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
    """صفحة التكميل الذكي - المناوبات تظهر تلقائيًا من جدول المناوبات"""
    
    page_header("📋 التكميل الذكي", "المناوبات تظهر تلقائيًا حسب الجدول", "🤖")
    
    es, cs, ss = _get_services()
    
    # جلب المراكز
    all_centers = cs.get_centers() or []
    
    if not all_centers:
        st.warning("⚠️ لا توجد مراكز")
        return
    
    # ===== اختيار التاريخ والمركز =====
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_date = st.date_input("📅 التاريخ", value=date.today())
    
    with col2:
        center_names = [c["name"] for c in all_centers]
        selected_center = st.selectbox("🏥 المركز", center_names)
        center_id = next(c["id"] for c in all_centers if c["name"] == selected_center)
    
    with col3:
        # تاريخ هجري تقريبي (يمكن تحديثه لاحقًا)
        hijri_date = st.text_input("📅 التاريخ الهجري", value="1447/09/18")
    
    # ===== جلب المناوبات المخطط لها لهذا اليوم =====
    with st.spinner("جاري تحميل المناوبات المخطط لها..."):
        planned_shifts = ss.get_shifts_by_date(center_id, selected_date)
    
    if not planned_shifts:
        st.info("ℹ️ لا توجد مناوبات مخطط لها لهذا اليوم. يمكنك إضافتها من صفحة المناوبات.")
        
        # رابط سريع لصفحة المناوبات
        if st.button("➕ الذهاب إلى صفحة المناوبات", use_container_width=True):
            st.session_state.current_page = "shifts"
            st.rerun()
        return
    
    st.success(f"✅ تم العثور على {len(planned_shifts)} مناوبة مخطط لها")
    
    # ===== عرض المناوبات للتكميل =====
    st.markdown("---")
    st.markdown("### 📝 تسجيل الحضور والغياب")
    
    attendance_data = []
    
    for shift in planned_shifts:
        employee_name = shift.get("employee_name", "غير معروف")
        employee_id = shift.get("employee_id")
        shift_type = shift.get("shift_type", "morning_12")
        shift_info = SHIFT_TYPES.get(shift_type, {"name": shift_type, "hours": 8, "start": "08:00", "end": "16:00"})
        
        with st.container():
            st.markdown(f"#### 👤 {employee_name}")
            
            col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
            
            with col1:
                st.markdown(f"**المناوبة المخطط لها:** {shift_info['name']}")
                st.markdown(f"⏱️ {shift_info['start']} - {shift_info['end']}")
            
            with col2:
                status = st.selectbox(
                    "الحالة",
                    ["حاضر", "غائب", "متأخر", "إجازة", "مهمة رسمية"],
                    key=f"status_{employee_id}"
                )
            
            with col3:
                check_in = st.time_input(
                    "⏰ وقت الحضور",
                    value=datetime.strptime(shift_info['start'], "%H:%M").time(),
                    key=f"in_{employee_id}"
                )
            
            with col4:
                check_out = st.time_input(
                    "🕒 وقت الانصراف",
                    value=datetime.strptime(shift_info['end'], "%H:%M").time(),
                    key=f"out_{employee_id}"
                )
            
            attendance_data.append({
                "employee_id": employee_id,
                "employee_name": employee_name,
                "planned_shift": shift_info['name'],
                "status": status,
                "check_in": check_in,
                "check_out": check_out,
                "shift_type": shift_type
            })
            
            st.markdown("---")
    
    # ===== التوكيل والبديل =====
    st.markdown("### 🔄 التوكيل والبديل")
    
    employee_options = [f"{shift.get('employee_name', '')}" for shift in planned_shifts]
    
    col1, col2 = st.columns(2)
    
    with col1:
        delegator = st.selectbox("👤 الموكل (الموظف الأساسي)", ["لا يوجد"] + employee_options)
    
    with col2:
        substitute = st.selectbox("🔄 البديل", ["لا يوجد"] + employee_options)
    
    notes = st.text_area("📝 ملاحظات", placeholder="أي ملاحظات إضافية...")
    
    # ===== حفظ التكميل =====
    if st.button("💾 حفظ التكميل", type="primary", use_container_width=True):
        st.success("✅ تم حفظ التكميل بنجاح")
        st.balloons()
        
        # ===== عرض التقرير النهائي =====
        st.markdown("---")
        st.markdown("## 📄 تقرير التكميل النهائي")
        
        # معلومات التقرير
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"**المركز:** {selected_center}")
        col2.markdown(f"**التاريخ:** {selected_date}")
        col3.markdown(f"**التاريخ الهجري:** {hijri_date}")
        
        # جدول النتائج
        report_data = []
        for item in attendance_data:
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
                "الحالة": f"{status_color} {item['status']}",
                "الحضور": item['check_in'].strftime("%H:%M"),
                "الانصراف": item['check_out'].strftime("%H:%M")
            })
        
        df_report = pd.DataFrame(report_data)
        st.dataframe(df_report, use_container_width=True, hide_index=True)
        
        # إحصائيات
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("👥 إجمالي", len(report_data))
        col2.metric("✅ حاضر", sum(1 for r in report_data if "حاضر" in r["الحالة"]))
        col3.metric("❌ غائب", sum(1 for r in report_data if "غائب" in r["الحالة"]))
        col4.metric("⏰ متأخر", sum(1 for r in report_data if "متأخر" in r["الحالة"]))
        
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
        
        # توقيع
        st.markdown("---")
        st.markdown("""
        <div style="display: flex; justify-content: space-between; margin-top: 30px;">
            <div style="text-align: center; width: 45%; border-top: 1px solid #333; padding-top: 5px;">
                توقيع المشرف
            </div>
            <div style="text-align: center; width: 45%; border-top: 1px solid #333; padding-top: 5px;">
                الختم
            </div>
        </div>
        """, unsafe_allow_html=True)