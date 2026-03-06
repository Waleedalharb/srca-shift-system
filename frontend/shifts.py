# frontend/pages/shifts.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
from utils.helpers import page_header, section_title
from components.cards import kpi_row

# أسماء الأشهر
MONTHS_AR = {
    1:"يناير",2:"فبراير",3:"مارس",4:"أبريل",5:"مايو",6:"يونيو",
    7:"يوليو",8:"أغسطس",9:"سبتمبر",10:"أكتوبر",11:"نوفمبر",12:"ديسمبر",
}

# أيام الأسبوع
WEEKDAYS_AR = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]

# أنواع المناوبات مع ألوانها
SHIFT_TYPES = {
    "morning":  {"name": "صباحية", "icon": "🌅", "color": "#FFB74D", "text": "#7A5800"},
    "evening":  {"name": "مسائية", "icon": "🌆", "color": "#64B5F6", "text": "#1A3070"},
    "night":    {"name": "ليلية", "icon": "🌙", "color": "#4A6FA5", "text": "#FFFFFF"},
    "fullday":  {"name": "24 ساعة", "icon": "🕐", "color": "#E57373", "text": "#7A1212"},
    "off":      {"name": "إجازة", "icon": "⭕", "color": "#E0E0E0", "text": "#4A5568"},
}

def _get_services():
    """تهيئة الخدمات المطلوبة"""
    auth = st.session_state.auth_service
    
    cs = st.session_state.get("center_service")
    if not cs:
        from services.center_service import CenterService
        cs = CenterService(auth)
        st.session_state.center_service = cs
    
    es = st.session_state.get("employee_service")
    if not es:
        from services.employee_service import EmployeeService
        es = EmployeeService(auth)
        st.session_state.employee_service = es
    
    ss = st.session_state.get("shift_service")
    if not ss:
        from services.shift_service import ShiftService
        ss = ShiftService(auth)
        st.session_state.shift_service = ss
    
    return cs, es, ss

def show_shifts():
    """صفحة إدارة المناوبات - مع عرض أنيق وتعديل"""
    
    page_header("إدارة المناوبات", "جدولة وعرض مناوبات كوادر الإسعاف", "📅")
    
    cs, es, ss = _get_services()
    centers = cs.get_centers() or []
    
    if not centers:
        st.warning("❌ لا توجد مراكز متاحة")
        return
    
    # ── شريط التحكم العلوي ──
    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
    
    with col1:
        center_names = [c["name"] for c in centers]
        center_ids = [c["id"] for c in centers]
        selected_center = st.selectbox("🏥 المركز", center_names)
        center_id = center_ids[center_names.index(selected_center)]
    
    with col2:
        year = st.number_input("📅 السنة", 2020, 2030, datetime.now().year)
    
    with col3:
        month = st.number_input("📆 الشهر", 1, 12, datetime.now().month)
    
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        view_mode = st.radio("عرض", ["📋 جدول", "✏️ تعديل", "📊 إحصائيات"], horizontal=True)
    
    with col5:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 تحديث", use_container_width=True):
            st.rerun()
    
    # ── جلب البيانات ──
    with st.spinner("جاري تحميل البيانات..."):
        emp_result = es.get_employees(center_id=center_id, limit=100)
        employees = emp_result.get("items", []) if emp_result else []
        shifts = ss.get_shifts_by_month(center_id, year, month)
    
    # تحويل المناوبات إلى خريطة
    shifts_map = {}
    for shift in shifts:
        shift_date = shift.get("date", "").split("T")[0] if "T" in shift.get("date", "") else shift.get("date", "")
        try:
            day = int(shift_date.split("-")[2])
            for assignment in shift.get("assignments", []):
                emp_id = assignment.get("employee_id")
                if emp_id:
                    if emp_id not in shifts_map:
                        shifts_map[emp_id] = {}
                    shifts_map[emp_id][day] = shift.get("shift_type", "morning")
        except:
            continue
    
    if not employees:
        st.info("لا يوجد موظفون في هذا المركز")
        return
    
    days_in_month = calendar.monthrange(year, month)[1]
    
    # ===== وضع العرض (جدول) =====
    if view_mode == "📋 جدول":
        st.subheader(f"📋 جدول مناوبات {selected_center} - {MONTHS_AR[month]} {year}")
        
        # إنشاء DataFrame للعرض
        data = []
        for emp in employees:
            emp_id = str(emp["id"])
            emp_shifts = shifts_map.get(emp_id, {})
            row = {
                "الموظف": f"{emp['full_name']}",
                "الرقم": emp.get('emp_no', ''),
            }
            
            # إضافة الأيام
            for day in range(1, days_in_month + 1):
                shift_type = emp_shifts.get(day, "off")
                row[str(day)] = SHIFT_TYPES[shift_type]["icon"]
            
            data.append(row)
        
        if data:
            df = pd.DataFrame(data)
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "الموظف": st.column_config.TextColumn("الموظف", width="medium"),
                    "الرقم": st.column_config.TextColumn("الرقم", width="small"),
                    **{str(day): st.column_config.TextColumn(str(day), width="small") 
                       for day in range(1, days_in_month + 1)}
                }
            )
            
            # مفتاح الألوان
            st.markdown("### 🔑 دليل الرموز")
            cols = st.columns(len(SHIFT_TYPES))
            for i, (key, value) in enumerate(SHIFT_TYPES.items()):
                with cols[i]:
                    st.markdown(f"""
                    <div style="
                        background: {value['color']};
                        color: {value['text']};
                        padding: 0.5rem;
                        border-radius: 8px;
                        text-align: center;
                        font-weight: 700;
                    ">
                        {value['icon']} {value['name']}
                    </div>
                    """, unsafe_allow_html=True)
    
    # ===== وضع التعديل =====
    elif view_mode == "✏️ تعديل":
        st.subheader(f"✏️ تعديل مناوبات {selected_center} - {MONTHS_AR[month]} {year}")
        
        # اختيار موظف للتعديل
        emp_names = [f"{emp['full_name']} ({emp.get('emp_no', '')})" for emp in employees]
        emp_ids = [str(emp["id"]) for emp in employees]
        
        selected_emp_name = st.selectbox("👤 اختر الموظف", emp_names)
        selected_emp_id = emp_ids[emp_names.index(selected_emp_name)]
        selected_emp = employees[emp_ids.index(selected_emp_id)]
        
        # عرض جدول المناوبات للموظف المختار
        st.markdown("---")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown(f"**الموظف:** {selected_emp['full_name']}")
            st.markdown(f"**الرقم:** {selected_emp.get('emp_no', '')}")
        
        with col2:
            total_days = days_in_month
            worked_days = sum(1 for day in range(1, days_in_month + 1) 
                             if shifts_map.get(selected_emp_id, {}).get(day, "off") != "off")
            st.markdown(f"**أيام العمل:** {worked_days}")
            st.markdown(f"**أيام الإجازة:** {total_days - worked_days}")
        
        st.markdown("---")
        
        # عرض أيام الشهر بشكل شبكي للتعديل
        cols = st.columns(7)  # 7 أيام في الأسبوع
        weekdays = ["س", "ن", "ث", "ر", "خ", "ج", "س"]
        for i, day_name in enumerate(weekdays):
            cols[i].markdown(f"<center><b>{day_name}</b></center>", unsafe_allow_html=True)
        
        # ترتيب الأيام في أسابيع
        current_day = 1
        emp_shifts = shifts_map.get(selected_emp_id, {})
        
        # مصفوفة للتعديلات
        if "shift_changes" not in st.session_state:
            st.session_state.shift_changes = {}
        
        for week in range(6):  # max 6 weeks
            if current_day > days_in_month:
                break
                
            cols = st.columns(7)
            for day_in_week in range(7):
                if current_day <= days_in_month:
                    with cols[day_in_week]:
                        current_shift = emp_shifts.get(current_day, "off")
                        
                        # زر اليوم
                        if st.button(
                            f"{current_day}",
                            key=f"day_{selected_emp_id}_{current_day}",
                            use_container_width=True
                        ):
                            st.session_state.editing_day = {
                                "emp_id": selected_emp_id,
                                "emp_name": selected_emp['full_name'],
                                "day": current_day,
                                "current_shift": current_shift
                            }
                        
                        # عرض نوع المناوبة تحت الرقم
                        shift_info = SHIFT_TYPES[current_shift]
                        st.markdown(
                            f"<center style='background:{shift_info['color']}; "
                            f"color:{shift_info['text']}; border-radius:4px; "
                            f"padding:2px; font-size:0.7rem;'>{shift_info['icon']}</center>",
                            unsafe_allow_html=True
                        )
                    
                    current_day += 1
        
        # نافذة تعديل المناوبة
        if "editing_day" in st.session_state:
            edit = st.session_state.editing_day
            with st.expander(f"✏️ تعديل يوم {edit['day']} لـ {edit['emp_name']}", expanded=True):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    new_shift = st.selectbox(
                        "نوع المناوبة",
                        options=list(SHIFT_TYPES.keys()),
                        format_func=lambda x: f"{SHIFT_TYPES[x]['icon']} {SHIFT_TYPES[x]['name']}",
                        index=list(SHIFT_TYPES.keys()).index(edit['current_shift'])
                    )
                
                with col2:
                    st.write("")
                    st.write("")
                    if st.button("💾 حفظ", type="primary", use_container_width=True):
                        st.success(f"✅ تم تحديث المناوبة إلى {SHIFT_TYPES[new_shift]['name']}")
                        del st.session_state.editing_day
                        st.rerun()
                
                with col3:
                    st.write("")
                    st.write("")
                    if st.button("❌ إلغاء", use_container_width=True):
                        del st.session_state.editing_day
                        st.rerun()
    
    # ===== وضع الإحصائيات =====
    elif view_mode == "📊 إحصائيات":
        st.subheader(f"📊 إحصائيات {selected_center} - {MONTHS_AR[month]} {year}")
        
        total_employees = len(employees)
        
        if total_employees > 0:
            # إحصائيات سريعة
            col1, col2, col3, col4 = st.columns(4)
            
            total_shifts = 0
            shifts_count = {stype: 0 for stype in SHIFT_TYPES}
            
            for emp in employees:
                emp_id = str(emp["id"])
                emp_shifts = shifts_map.get(emp_id, {})
                for day in range(1, days_in_month + 1):
                    stype = emp_shifts.get(day, "off")
                    shifts_count[stype] += 1
                    if stype != "off":
                        total_shifts += 1
            
            with col1:
                st.metric("👥 إجمالي الموظفين", total_employees)
            with col2:
                st.metric("📅 إجمالي المناوبات", total_shifts)
            with col3:
                avg = total_shifts / days_in_month if days_in_month > 0 else 0
                st.metric("📊 متوسط يومي", f"{avg:.1f}")
            with col4:
                if total_employees > 0:
                    coverage = (total_shifts / (total_employees * days_in_month)) * 100
                    st.metric("✅ نسبة التغطية", f"{coverage:.1f}%")
            
            st.markdown("---")
            
            # رسم بياني لتوزيع المناوبات
            import plotly.express as px
            df = pd.DataFrame({
                "النوع": [SHIFT_TYPES[k]['name'] for k in shifts_count.keys()],
                "العدد": list(shifts_count.values())
            })
            fig = px.pie(df, values='العدد', names='النوع', 
                        title="توزيع أنواع المناوبات",
                        color_discrete_sequence=["#FFB74D", "#64B5F6", "#4A6FA5", "#E57373", "#E0E0E0"])
            st.plotly_chart(fig, use_container_width=True)