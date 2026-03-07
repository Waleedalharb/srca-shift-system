# frontend/pages/attendance.py
import streamlit as st
import pandas as pd
from datetime import datetime, date, time
from utils.helpers import page_header

# ===== أنواع المناوبات =====
SHIFT_TYPES = {
    "morning_6":  {"name": "صباحية 6 س", "icon": "🌅", "hours": 6, "start": "08:00", "end": "14:00"},
    "morning_8":  {"name": "صباحية 8 س", "icon": "🌅", "hours": 8, "start": "08:00", "end": "16:00"},
    "morning_10": {"name": "صباحية 10 س", "icon": "🌅", "hours": 10, "start": "08:00", "end": "18:00"},
    "morning_11": {"name": "صباحية 11 س", "icon": "🌅", "hours": 11, "start": "08:00", "end": "19:00"},
    "morning_12": {"name": "صباحية 12 س", "icon": "🌅", "hours": 12, "start": "08:00", "end": "20:00"},
    "evening_6":  {"name": "مسائية 6 س", "icon": "🌆", "hours": 6, "start": "16:00", "end": "22:00"},
    "evening_8":  {"name": "مسائية 8 س", "icon": "🌆", "hours": 8, "start": "16:00", "end": "00:00"},
    "evening_10": {"name": "مسائية 10 س", "icon": "🌆", "hours": 10, "start": "14:00", "end": "00:00"},
    "evening_11": {"name": "مسائية 11 س", "icon": "🌆", "hours": 11, "start": "13:00", "end": "00:00"},
    "evening_12": {"name": "مسائية 12 س", "icon": "🌆", "hours": 12, "start": "12:00", "end": "00:00"},
    "night_8":    {"name": "ليلية 8 س", "icon": "🌙", "hours": 8, "start": "00:00", "end": "08:00"},
    "night_10":   {"name": "ليلية 10 س", "icon": "🌙", "hours": 10, "start": "22:00", "end": "08:00"},
    "overlap_6":  {"name": "تداخلية 6 س", "icon": "🔄", "hours": 6, "start": "10:00", "end": "16:00"},
    "overlap_8":  {"name": "تداخلية 8 س", "icon": "🔄", "hours": 8, "start": "10:00", "end": "18:00"},
    "overlap_10": {"name": "تداخلية 10 س", "icon": "🔄", "hours": 10, "start": "09:00", "end": "19:00"},
    "overlap_12": {"name": "تداخلية 12 س", "icon": "🔄", "hours": 12, "start": "08:00", "end": "20:00"},
    "fullday_24": {"name": "نوبة 24 س", "icon": "🕐", "hours": 24, "start": "08:00", "end": "08:00"},
}

def _get_services():
    """تهيئة الخدمات"""
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
    
    return es, cs

def show_attendance():
    """صفحة التكميل اليومي - مع التوكيل والبديل"""
    
    page_header("📋 التكميل اليومي", "تسجيل المناوبات والحضور مع التوكيل", "📝")
    
    es, cs = _get_services()
    
    # جلب المراكز (قطاع الجنوب فقط)
    all_centers = cs.get_centers() or []
    
    if not all_centers:
        st.warning("⚠️ لا توجد مراكز في قطاع الجنوب")
        return
    
    # ===== اختيار المركز =====
    center_names = [c["name"] for c in all_centers]
    selected_center = st.selectbox("🏥 اختر المركز", center_names)
    
    # جلب موظفي المركز المختار
    with st.spinner("جاري تحميل الموظفين..."):
        center_id = next(c["id"] for c in all_centers if c["name"] == selected_center)
        employees = es.get_employees(center_id=center_id, limit=100).get("items", [])
    
    if not employees:
        st.warning(f"⚠️ لا يوجد موظفون في {selected_center}")
        return
    
    # ===== نموذج التكميل =====
    with st.form("attendance_form"):
        # معلومات اليوم
        col1, col2, col3 = st.columns(3)
        with col1:
            hijri_date = st.text_input("📅 التاريخ الهجري", value="1447/09/18")
        with col2:
            gregorian_date = st.date_input("📆 التاريخ الميلادي", value=date.today())
        with col3:
            shift_date = st.selectbox("⏰ المناوبة", ["صباحية", "مسائية", "ليلية"])
        
        st.markdown("---")
        st.markdown("### 👥 تسجيل حضور الموظفين")
        
        # تجهيز بيانات الموظفين
        employee_options = {f"{e['full_name']} ({e.get('emp_no', '')})": e['id'] for e in employees}
        
        # جدول الحضور
        attendance_data = []
        selected_employees = st.multiselect("اختر الموظفين", list(employee_options.keys()))
        
        if selected_employees:
            st.markdown("#### ⏱️ تسجيل الأوقات والحالات")
            
            for emp_name in selected_employees:
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])
                    
                    with col1:
                        st.write(f"**{emp_name}**")
                    
                    with col2:
                        status = st.selectbox(
                            "الحالة",
                            ["حاضر", "غائب", "متأخر", "إجازة", "مهمة رسمية"],
                            key=f"status_{emp_name}"
                        )
                    
                    with col3:
                        check_in = st.time_input("وقت الحضور", value=time(8, 0), key=f"in_{emp_name}")
                    
                    with col4:
                        check_out = st.time_input("وقت الانصراف", value=time(16, 0), key=f"out_{emp_name}")
                    
                    with col5:
                        shift_type = st.selectbox(
                            "المناوبة",
                            list(SHIFT_TYPES.keys()),
                            format_func=lambda x: SHIFT_TYPES[x]["name"],
                            key=f"shift_{emp_name}"
                        )
                    
                    attendance_data.append({
                        "employee_id": employee_options[emp_name],
                        "employee_name": emp_name,
                        "status": status,
                        "check_in": check_in,
                        "check_out": check_out,
                        "shift_type": shift_type
                    })
                    
                    st.markdown("---")
        
        st.markdown("### 🔄 التوكيل والبديل")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # الموكل (الموظف الأساسي)
            delegator = st.selectbox("👤 الموكل (الموظف الأساسي)", ["لا يوجد"] + list(employee_options.keys()))
        
        with col2:
            # البديل
            substitute = st.selectbox("🔄 البديل", ["لا يوجد"] + list(employee_options.keys()))
        
        # ملاحظات
        notes = st.text_area("📝 ملاحظات", placeholder="أي ملاحظات إضافية...")
        
        submitted = st.form_submit_button("💾 حفظ التكميل", use_container_width=True, type="primary")
    
    # ===== بعد الحفظ - عرض التقرير النهائي =====
    if submitted:
        st.success("✅ تم حفظ التكميل بنجاح")
        st.balloons()
        
        # ===== تقرير التكميل النهائي =====
        st.markdown("---")
        st.markdown("## 📄 تقرير التكميل اليومي")
        
        # معلومات التقرير
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"**المركز:** {selected_center}")
        col2.markdown(f"**التاريخ:** {gregorian_date} / {hijri_date}")
        col3.markdown(f"**المناوبة:** {shift_date}")
        
        st.markdown("---")
        
        # جدول الحضور
        report_data = []
        for item in attendance_data:
            shift_info = SHIFT_TYPES.get(item["shift_type"], {"name": item["shift_type"], "hours": 0})
            
            # تحديد لون الحالة
            status_colors = {
                "حاضر": "🟢",
                "غائب": "🔴",
                "متأخر": "🟡",
                "إجازة": "🔵",
                "مهمة رسمية": "🟠"
            }
            
            report_data.append({
                "م": len(report_data) + 1,
                "الموظف": item["employee_name"],
                "الحالة": f"{status_colors.get(item['status'], '⚪')} {item['status']}",
                "وقت الحضور": item["check_in"].strftime("%H:%M"),
                "وقت الانصراف": item["check_out"].strftime("%H:%M"),
                "المناوبة": shift_info["name"],
                "الساعات": shift_info["hours"]
            })
        
        if report_data:
            df_report = pd.DataFrame(report_data)
            st.dataframe(df_report, use_container_width=True, hide_index=True)
            
            # إحصائيات
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("👥 إجمالي", len(report_data))
            col2.metric("✅ حاضر", sum(1 for r in report_data if "حاضر" in r["الحالة"]))
            col3.metric("❌ غائب", sum(1 for r in report_data if "غائب" in r["الحالة"]))
            col4.metric("⏰ متأخر", sum(1 for r in report_data if "متأخر" in r["الحالة"]))
            
            # التوكيل والبديل
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