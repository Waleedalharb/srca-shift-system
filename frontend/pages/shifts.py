# frontend/pages/shifts.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
from utils.helpers import page_header, section_title
from components.cards import kpi_row
from components.charts import create_line_chart, display_chart

# ===== دوام رسمي =====
def show_official_schedule():
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 1.2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        color: white;
        direction: rtl;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border-right: 4px solid #FFD700;
    ">
        <div style="display: flex; align-items: center; justify-content: center; gap: 0.5rem; margin-bottom: 0.5rem;">
            <span style="font-size: 1.8rem;">⏰</span>
            <h4 style="margin: 0; font-size: 1.3rem;">الدوام الرسمي</h4>
        </div>
        <p style="margin: 0; font-size: 1.1rem; font-weight: 500;">
            🗓️ من الأحد إلى الخميس | 8 ساعات يومياً
        </p>
        <p style="margin: 0.3rem 0 0 0; font-size: 1rem; opacity: 0.9;">
            🚫 عطلة نهاية الأسبوع: الجمعة والسبت
        </p>
        <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem; opacity: 0.8; background: rgba(255,255,255,0.1); padding: 0.3rem; border-radius: 20px;">
            ⏱️ إجمالي ساعات العمل الأسبوعية: 40 ساعة
        </p>
    </div>
    """, unsafe_allow_html=True)

# ===== أنواع المناوبات كاملة =====
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
    cs = st.session_state.get("center_service")
    es = st.session_state.get("employee_service")
    ss = st.session_state.get("shift_service")
    
    if not cs:
        from services.center_service import CenterService
        cs = CenterService(auth)
        st.session_state.center_service = cs
    
    if not es:
        from services.employee_service import EmployeeService
        es = EmployeeService(auth)
        st.session_state.employee_service = es
    
    if not ss:
        from services.shift_service import ShiftService
        ss = ShiftService(auth)
        st.session_state.shift_service = ss
    
    return cs, es, ss

def show_shifts():
    """صفحة إدارة المناوبات - مع عرض وتعديل المناوبات المضافة"""
    
    page_header("📅 إدارة المناوبات", "عرض، إضافة، تعديل المناوبات", "⏰")
    
    # ===== عرض الدوام الرسمي =====
    show_official_schedule()
    
    # زر تحديث يدوي
    col1, col2 = st.columns([10, 1])
    with col2:
        if st.button("🔄 تحديث الجدول"):
            st.cache_data.clear()
            st.session_state.shift_service = None
            st.rerun()
    
    cs, es, ss = _get_services()
    centers = cs.get_centers() or []
    
    if not centers:
        st.warning("❌ لا توجد مراكز متاحة")
        return
    
    # ===== اختيار المركز والشهر =====
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        center_names = [c["name"] for c in centers]
        selected_center = st.selectbox("🏥 المركز", center_names)
        center_id = next(c["id"] for c in centers if c["name"] == selected_center)
    
    with col2:
        year = st.number_input("📅 السنة", 2020, 2030, datetime.now().year)
    
    with col3:
        month = st.number_input("📆 الشهر", 1, 12, datetime.now().month)
    
    with col4:
        view_mode = st.radio("عرض", ["📋 الجدول", "✏️ تعديل", "➕ إضافة"], horizontal=True)
    
    # جلب الموظفين
    employees = es.get_employees(center_id=center_id).get("items", [])
    
    if not employees:
        st.warning(f"⚠️ لا يوجد موظفون في {selected_center}")
        return
    
    # جلب المناوبات للشهر المحدد
    with st.spinner("جاري تحميل المناوبات..."):
        shifts = ss.get_shifts_by_month(center_id, year, month)
    
    # تحويل المناوبات إلى خريطة (employee_id -> day -> shift_type)
    shifts_map = {}
    for shift in shifts:
        shift_date = shift.get("date", "").split("T")[0]
        try:
            day = int(shift_date.split("-")[2])
            for assignment in shift.get("assignments", []):
                emp_id = assignment.get("employee_id")
                if emp_id:
                    if emp_id not in shifts_map:
                        shifts_map[emp_id] = {}
                    shifts_map[emp_id][day] = shift.get("shift_type", "off")
        except:
            continue
    
    days_in_month = calendar.monthrange(year, month)[1]
    
    # ===== عرض الجدول =====
    if view_mode == "📋 الجدول":
        st.subheader(f"📋 جدول مناوبات {selected_center} - {month}/{year}")
        
        # إنشاء الجدول مع إجمالي الساعات
        table_data = []
        total_hours_all = 0
        
        for emp in employees:
            emp_id = str(emp["id"])
            emp_shifts = shifts_map.get(emp_id, {})
            
            # حساب إجمالي ساعات الموظف
            total_hours = 0
            for day in range(1, days_in_month + 1):
                shift_type = emp_shifts.get(day, "off")
                total_hours += SHIFT_TYPES[shift_type]["hours"]
            
            total_hours_all += total_hours
            
            row = {
                "الموظف": emp['full_name'],
                "الرقم": emp.get('emp_no', ''),
                "إجمالي الساعات": f"{total_hours} س",
                "id": emp_id
            }
            
            for day in range(1, days_in_month + 1):
                shift_type = emp_shifts.get(day, "off")
                row[str(day)] = SHIFT_TYPES[shift_type]["icon"]
            
            table_data.append(row)
        
        if table_data:
            df = pd.DataFrame(table_data)
            display_cols = ["الموظف", "الرقم", "إجمالي الساعات"] + [str(d) for d in range(1, days_in_month + 1)]
            st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
            
            # عرض إجمالي ساعات الفريق
            st.info(f"⏱️ **إجمالي ساعات العمل للفريق:** {total_hours_all} ساعة في {selected_center}")
            
            # مفتاح الألوان
            st.markdown("### 🔑 دليل الرموز")
            cols = st.columns(5)
            for i, (key, value) in enumerate(list(SHIFT_TYPES.items())[:5]):
                with cols[i]:
                    st.markdown(f"<div style='background:{value['color']}; color:{value['text']}; padding:0.5rem; border-radius:8px; text-align:center;'>{value['icon']} {value['name']}</div>", unsafe_allow_html=True)
    
    # ===== وضع التعديل =====
    elif view_mode == "✏️ تعديل":
        st.subheader("✏️ تعديل المناوبات")
        
        # اختيار الموظف
        emp_names = [f"{e['full_name']} ({e.get('emp_no', '')})" for e in employees]
        selected_emp_name = st.selectbox("👤 اختر الموظف", emp_names)
        selected_emp = employees[emp_names.index(selected_emp_name)]
        emp_id = str(selected_emp["id"])
        
        st.markdown("---")
        st.markdown(f"**تعديل مناوبات:** {selected_emp['full_name']}")
        
        # عرض أيام الشهر للتعديل
        emp_shifts = shifts_map.get(emp_id, {})
        
        # اختيار نوع التعديل
        edit_type = st.radio("نوع التعديل", ["يومي", "نطاق أيام", "تطبيق نمط"], horizontal=True)
        
        if edit_type == "يومي":
            col1, col2 = st.columns([1, 3])
            with col1:
                day = st.number_input("اليوم", 1, days_in_month, 1)
            with col2:
                current_shift = emp_shifts.get(day, "off")
                current_index = list(SHIFT_TYPES.keys()).index(current_shift) if current_shift in SHIFT_TYPES else 0
                new_shift = st.selectbox(
                    "المناوبة",
                    options=list(SHIFT_TYPES.keys()),
                    format_func=lambda x: f"{SHIFT_TYPES[x]['icon']} {SHIFT_TYPES[x]['name']}",
                    index=current_index
                )
            
            if st.button("💾 تحديث", use_container_width=True, type="primary"):
                # تحضير التاريخ
                date_str = f"{year}-{month:02d}-{day:02d}"
                
                # إرسال التحديث إلى API
                success = ss.update_employee_shift(emp_id, date_str, new_shift)
                
                if success:
                    st.success(f"✅ تم تحديث يوم {day} إلى {SHIFT_TYPES[new_shift]['name']}")
                    # مسح الكاش وإعادة تعيين الخدمة
                    st.cache_data.clear()
                    st.session_state.shift_service = None
                    st.rerun()
                else:
                    st.error("❌ فشل في تحديث المناوبة")
        
        elif edit_type == "نطاق أيام":
            col1, col2 = st.columns(2)
            with col1:
                from_day = st.number_input("من يوم", 1, days_in_month, 1)
            with col2:
                to_day = st.number_input("إلى يوم", from_day, days_in_month, from_day)
            
            new_shift = st.selectbox(
                "المناوبة",
                options=list(SHIFT_TYPES.keys()),
                format_func=lambda x: f"{SHIFT_TYPES[x]['icon']} {SHIFT_TYPES[x]['name']}"
            )
            
            if st.button("💾 تحديث النطاق", use_container_width=True, type="primary"):
                success_count = 0
                for day in range(from_day, to_day + 1):
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    if ss.update_employee_shift(emp_id, date_str, new_shift):
                        success_count += 1
                
                if success_count > 0:
                    st.success(f"✅ تم تحديث {success_count} يوم إلى {SHIFT_TYPES[new_shift]['name']}")
                    st.cache_data.clear()
                    st.session_state.shift_service = None
                    st.rerun()
                else:
                    st.error("❌ فشل في تحديث المناوبات")
        
        else:  # تطبيق نمط
            st.markdown("#### أنماط التناوب")
            patterns = {
                "نظام 2+2+4": ["morning_12", "morning_12", "night_10", "night_10", "off", "off", "off", "off"],
                "نظام دوام رسمي": ["morning_8", "morning_8", "morning_8", "morning_8", "morning_8", "off", "off"],
                "نظام تداخلي": ["overlap_8", "overlap_8", "off"],
                "نظام 3+3+3": ["morning_12", "morning_12", "morning_12", "night_10", "night_10", "night_10", "off", "off", "off"],
                "نظام نهاية أسبوع": ["morning_8", "morning_8", "evening_8", "evening_8", "off", "off", "off"],
            }
            
            selected_pattern = st.selectbox("اختر النمط", list(patterns.keys()))
            pattern = patterns[selected_pattern]
            
            st.markdown("**نمط الدورة:**")
            cols = st.columns(len(pattern))
            for i, p in enumerate(pattern):
                with cols[i]:
                    st.markdown(f"<div style='background:{SHIFT_TYPES[p]['color']}; color:{SHIFT_TYPES[p]['text']}; padding:0.5rem; border-radius:8px; text-align:center;'>{SHIFT_TYPES[p]['icon']}</div>", unsafe_allow_html=True)
            
            start_day = st.number_input("بدءًا من يوم", 1, days_in_month, 1)
            
            if st.button("✅ تطبيق النمط", use_container_width=True, type="primary"):
                success_count = 0
                for i, day in enumerate(range(start_day, days_in_month + 1)):
                    pattern_idx = (i) % len(pattern)
                    shift_type = pattern[pattern_idx]
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    if ss.update_employee_shift(emp_id, date_str, shift_type):
                        success_count += 1
                
                st.success(f"✅ تم تطبيق نمط {selected_pattern} على {success_count} يوم")
                st.cache_data.clear()
                st.session_state.shift_service = None
                st.rerun()
    
    # ===== وضع الإضافة =====
    elif view_mode == "➕ إضافة":
        st.subheader("➕ إضافة مناوبة جديدة")
        
        with st.form("add_shift_form"):
            shift_date = st.date_input("📅 التاريخ", value=datetime(year, month, 1))
            shift_type = st.selectbox(
                "⏰ نوع المناوبة",
                options=list(SHIFT_TYPES.keys()),
                format_func=lambda x: f"{SHIFT_TYPES[x]['icon']} {SHIFT_TYPES[x]['name']} ({SHIFT_TYPES[x]['hours']} س)"
            )
            
            emp_options = {f"{e['full_name']} ({e.get('emp_no', '')})": e["id"] for e in employees}
            selected_emps = st.multiselect("👥 الموظفون", list(emp_options.keys()))
            employee_ids = [emp_options[name] for name in selected_emps]
            
            notes = st.text_area("📝 ملاحظات")
            
            if st.form_submit_button("✅ إضافة", use_container_width=True, type="primary"):
                if not employee_ids:
                    st.error("❌ اختر موظفًا واحدًا على الأقل")
                else:
                    # إنشاء مناوبة لكل موظف
                    success_count = 0
                    for emp_id in employee_ids:
                        date_str = shift_date.strftime("%Y-%m-%d")
                        if ss.save_shift(emp_id, date_str, shift_type):
                            success_count += 1
                    
                    st.success(f"✅ تم إضافة المناوبة لـ {success_count} موظف")
                    st.cache_data.clear()
                    st.session_state.shift_service = None
                    st.rerun()