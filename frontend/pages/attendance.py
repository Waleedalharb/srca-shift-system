# frontend/pages/attendance.py
import streamlit as st
import pandas as pd
from datetime import datetime, date
from utils.helpers import page_header

# ===== أنواع المناوبات =====
SHIFT_TYPES = {
    "morning_6":  {"name": "صباحية 6 س", "icon": "🌅", "hours": 6, "start": "08:00", "end": "14:00"},
    "morning_8":  {"name": "صباحية 8 س", "icon": "🌅", "hours": 8, "start": "08:00", "end": "16:00"},
    "morning_10": {"name": "صباحية 10 س", "icon": "🌅", "hours": 10, "start": "08:00", "end": "18:00"},
    "morning_12": {"name": "صباحية 12 س", "icon": "🌅", "hours": 12, "start": "08:00", "end": "20:00"},
    "evening_6":  {"name": "مسائية 6 س", "icon": "🌆", "hours": 6, "start": "16:00", "end": "22:00"},
    "evening_8":  {"name": "مسائية 8 س", "icon": "🌆", "hours": 8, "start": "16:00", "end": "00:00"},
    "evening_10": {"name": "مسائية 10 س", "icon": "🌆", "hours": 10, "start": "14:00", "end": "00:00"},
    "evening_12": {"name": "مسائية 12 س", "icon": "🌆", "hours": 12, "start": "12:00", "end": "00:00"},
    "night_8":    {"name": "ليلية 8 س", "icon": "🌙", "hours": 8, "start": "00:00", "end": "08:00"},
    "night_10":   {"name": "ليلية 10 س", "icon": "🌙", "hours": 10, "start": "22:00", "end": "08:00"},
    "overlap_6":  {"name": "تداخلية 6 س", "icon": "🔄", "hours": 6, "start": "10:00", "end": "16:00"},
    "overlap_8":  {"name": "تداخلية 8 س", "icon": "🔄", "hours": 8, "start": "10:00", "end": "18:00"},
    "overlap_10": {"name": "تداخلية 10 س", "icon": "🔄", "hours": 10, "start": "09:00", "end": "19:00"},
    "overlap_12": {"name": "تداخلية 12 س", "icon": "🔄", "hours": 12, "start": "08:00", "end": "20:00"},
    "fullday_24": {"name": "نوبة 24 س", "icon": "🕐", "hours": 24, "start": "08:00", "end": "08:00"},
}

def show_attendance():
    """صفحة التكميل اليومي"""
    
    page_header("📋 التكميل اليومي", "تسجيل المناوبات والحضور", "📝")
    
    # ===== نموذج الإدخال (بسيط مثل القديم) =====
    with st.form("attendance_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📅 معلومات اليوم")
            hijri_date = st.text_input("التاريخ الهجري", value="1447/09/18")
            gregorian_date = st.date_input("التاريخ الميلادي", value=date.today())
        
        with col2:
            st.markdown("### 📍 معلومات الموقع")
            center = st.selectbox("الفرع", ["منطقة الرياض", "منطقة مكة", "منطقة المدينة"])
            location = st.text_input("اسم الموقع", value="موقع 1")
        
        st.markdown("---")
        st.markdown("### 👥 بيانات الموظفين")
        
        # جدول سريع للإدخال (مثل Excel)
        employees_data = []
        
        for i in range(5):  # 5 موظفين كبداية
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])
            
            with col1:
                name = st.text_input(f"الاسم {i+1}", key=f"name_{i}")
            with col2:
                emp_type = st.selectbox(f"النوع", ["مسعف", "فني", "سائق"], key=f"type_{i}")
            with col3:
                shift = st.selectbox(f"المناوبة", list(SHIFT_TYPES.keys()), format_func=lambda x: SHIFT_TYPES[x]["name"], key=f"shift_{i}")
            with col4:
                status = st.selectbox(f"الحالة", ["حاضر", "غائب", "متأخر"], key=f"status_{i}")
            with col5:
                vehicle = st.text_input(f"المركبة", key=f"vehicle_{i}")
            
            employees_data.append({
                "name": name,
                "type": emp_type,
                "shift": shift,
                "status": status,
                "vehicle": vehicle
            })
        
        submitted = st.form_submit_button("💾 حفظ التكميل", use_container_width=True, type="primary")
    
    # ===== عند الحفظ: عرض التقرير النهائي =====
    if submitted:
        st.success("✅ تم حفظ التكميل بنجاح")
        st.balloons()
        
        # ===== عرض التقرير النهائي =====
        st.markdown("---")
        st.markdown("## 📄 تقرير التكميل النهائي")
        
        # معلومات التقرير
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"**التاريخ الهجري:** {hijri_date}")
        col2.markdown(f"**التاريخ الميلادي:** {gregorian_date}")
        col3.markdown(f"**الفرع:** {center}")
        
        st.markdown("---")
        
        # جدول التقرير النهائي
        report_data = []
        for emp in employees_data:
            if emp["name"]:  # فقط الموظفين المدخلين
                shift_info = SHIFT_TYPES.get(emp["shift"], {"name": emp["shift"], "hours": 0, "start": "--:--", "end": "--:--"})
                
                # تحديد لون الحالة
                if emp["status"] == "غائب":
                    status_color = "🔴"
                elif emp["status"] == "متأخر":
                    status_color = "🟡"
                else:
                    status_color = "🟢"
                
                report_data.append({
                    "م": len(report_data) + 1,
                    "الاسم": emp["name"],
                    "الوظيفة": emp["type"],
                    "المناوبة": shift_info["name"],
                    "من": shift_info["start"],
                    "إلى": shift_info["end"],
                    "الساعات": shift_info["hours"],
                    "الحالة": f"{status_color} {emp['status']}",
                    "المركبة": emp["vehicle"] if emp["vehicle"] else "—",
                })
        
        if report_data:
            df_report = pd.DataFrame(report_data)
            st.dataframe(df_report, use_container_width=True, hide_index=True)
            
            # إحصائيات سريعة
            total = len(report_data)
            present = sum(1 for e in report_data if e["الحالة"].endswith("حاضر"))
            absent = sum(1 for e in report_data if e["الحالة"].endswith("غائب"))
            late = sum(1 for e in report_data if e["الحالة"].endswith("متأخر"))
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("👥 إجمالي الموظفين", total)
            col2.metric("✅ حاضر", present)
            col3.metric("❌ غائب", absent)
            col4.metric("⏰ متأخر", late)
            
            # تذييل التقرير
            st.markdown("---")
            st.markdown(f"""
            <div style="text-align: center; color: #666; padding: 20px; border-top: 2px solid #CE2E26;">
                <p>هيئة الهلال الأحمر السعودي - قطاع الجنوب</p>
                <p>توقيع المشرف: _________________</p>
                <p>الختم: _________________</p>
            </div>
            """, unsafe_allow_html=True)
            
            # أزرار إضافية
            col1, col2, col3 = st.columns(3)
            with col1:
                st.button("🖨️ طباعة", use_container_width=True)
            with col2:
                st.button("📥 تصدير PDF", use_container_width=True)
            with col3:
                st.button("✏️ تعديل", use_container_width=True)