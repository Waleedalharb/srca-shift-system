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
WEEKDAYS_AR_SHORT = ["إث", "ثل", "أر", "خم", "جم", "سب", "أحد"]

# أنواع المناوبات مع ألوانها - الإجازة بدون رمز
SHIFT_TYPES = {
    "morning":  {"name": "صباحي 12 س", "icon": "🌅", "color": "#FFB74D", "text": "#7A5800"},
    "night":    {"name": "ليلي 12 س", "icon": "🌙", "color": "#4A6FA5", "text": "#FFFFFF"},
    "off":      {"name": "إجازة", "icon": "", "color": "#FFFFFF", "text": "#4A5568"},
}

# أنماط التناوب حسب طريقتكم
ROTATION_PATTERNS = {
    "نظام 2+2+4": {
        "name": "يومين صباح + يومين ليل + 4 أيام إجازة",
        "days": 8,
        "pattern": ["morning", "morning", "night", "night", "off", "off", "off", "off"],
        "description": "دورة 8 أيام: 2 صباحي، 2 ليلي، 4 إجازة"
    },
    "نظام 3+3+3": {
        "name": "3 أيام صباح + 3 أيام ليل + 3 أيام إجازة",
        "days": 9,
        "pattern": ["morning", "morning", "morning", "night", "night", "night", "off", "off", "off"],
        "description": "دورة 9 أيام: 3 صباحي، 3 ليلي، 3 إجازة"
    },
    "نظام 4+4+4": {
        "name": "4 أيام صباح + 4 أيام ليل + 4 أيام إجازة",
        "days": 12,
        "pattern": ["morning"]*4 + ["night"]*4 + ["off"]*4,
        "description": "دورة 12 يوم: 4 صباحي، 4 ليلي، 4 إجازة"
    },
    "نظام 1+1+2": {
        "name": "يوم صباح + يوم ليل + يومين إجازة",
        "days": 4,
        "pattern": ["morning", "night", "off", "off"],
        "description": "دورة 4 أيام: 1 صباحي، 1 ليلي، 2 إجازة"
    }
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
    """صفحة إدارة المناوبات - نظام التناوب الذكي"""
    
    # إضافة زر تحديث مع key فريد
    col1, col2, col3 = st.columns([8, 1, 1])
    with col2:
        if st.button("🔄 تحديث", key="refresh_top", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col3:
        if st.button("🗑️ مسح كاش", key="clear_cache_top", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    page_header("إدارة المناوبات", "نظام التناوب: يومين صباح + يومين ليل + 4 أيام إجازة", "📅")
    
    cs, es, ss = _get_services()
    centers = cs.get_centers() or []
    
    if not centers:
        st.warning("❌ لا توجد مراكز متاحة")
        return
    
    # ── شريط التحكم العلوي ──
    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1.5, 1])
    
    with col1:
        center_names = [c["name"] for c in centers]
        center_ids = [c["id"] for c in centers]
        selected_center = st.selectbox("🏥 المركز", center_names, key="center_select")
        center_id = center_ids[center_names.index(selected_center)]
    
    with col2:
        year = st.number_input("📅 السنة", 2020, 2030, datetime.now().year, key="year_input")
    
    with col3:
        month = st.number_input("📆 الشهر", 1, 12, datetime.now().month, key="month_input")
    
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        view_mode = st.radio("القسم", ["📋 الجدول", "➕ إضافة", "⚡ تناوب ذكي", "📊 إحصائيات"], horizontal=True, key="view_mode")
    
    with col5:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 تحديث", key="refresh_bottom", use_container_width=True):
            st.rerun()
    
    # ── جلب البيانات ──
    with st.spinner("جاري تحميل البيانات..."):
        emp_result = es.get_employees(center_id=center_id, limit=100)
        employees = emp_result.get("items", []) if emp_result else []
        shifts = ss.get_shifts_by_month(center_id, year, month)
    
    days_in_month = calendar.monthrange(year, month)[1]
    
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
    
    # ✅ إذا كانت المناوبات فارغة والموظفين موجودين، نضيف مناوبات تجريبية تلقائية
    if employees and not shifts_map:
        st.info("ℹ️ لا توجد مناوبات مسجلة. جاري إنشاء مناوبات تجريبية تلقائية...")
        
        import random
        random.seed(42)  # لتكرار نفس النتائج في كل مرة
        
        for emp in employees:
            emp_id = str(emp["id"])
            shifts_map[emp_id] = {}
            
            # نظام 2+2+4 مع إزاحة حسب الموظف
            pattern = ["morning", "morning", "night", "night", "off", "off", "off", "off"]
            offset = employees.index(emp) * 2
            
            for day in range(1, days_in_month + 1):
                pattern_idx = (day + offset) % 8
                shifts_map[emp_id][day] = pattern[pattern_idx]
        
        st.success(f"✅ تم إنشاء مناوبات تجريبية لـ {len(employees)} موظف (نظام 2+2+4)")
    
    # ==================== قسم الجدول ====================
    if view_mode == "📋 الجدول":
        st.subheader(f"📋 جدول مناوبات {selected_center} - {MONTHS_AR[month]} {year}")
        
        if not employees:
            st.info("لا يوجد موظفون في هذا المركز")
        else:
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
                            border: {'' if key != 'off' else '1px solid #E2E8F0'};
                        ">
                            {value['icon']} {value['name']}
                        </div>
                        """, unsafe_allow_html=True)
    
    # ==================== قسم الإضافة ====================
    elif view_mode == "➕ إضافة":
        st.subheader(f"➕ إضافة مناوبة جديدة - {selected_center}")
        
        with st.form("add_shift_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                shift_date = st.date_input("📅 تاريخ المناوبة", value=datetime.now())
                shift_type = st.selectbox(
                    "⏰ نوع المناوبة",
                    options=list(SHIFT_TYPES.keys()),
                    format_func=lambda x: f"{SHIFT_TYPES[x]['icon']} {SHIFT_TYPES[x]['name']}"
                )
            
            with col2:
                start_time = st.text_input("🕐 وقت البدء", value="08:00")
                end_time = st.text_input("🕒 وقت الانتهاء", value="20:00")
            
            # جلب الموظفين للاختيار
            if employees:
                emp_options = {f"{emp['full_name']} ({emp.get('emp_no', '')})": emp["id"] 
                              for emp in employees}
                selected_emps = st.multiselect("👥 الموظفون", list(emp_options.keys()))
                employee_ids = [emp_options[name] for name in selected_emps]
            else:
                st.warning("لا يوجد موظفون في هذا المركز")
                employee_ids = []
            
            notes = st.text_area("📝 ملاحظات", placeholder="أي ملاحظات إضافية...")
            
            submitted = st.form_submit_button("✅ تسجيل المناوبة", type="primary", use_container_width=True)
            
            if submitted:
                if not employee_ids:
                    st.error("❌ الرجاء اختيار موظف واحد على الأقل")
                else:
                    # تحضير البيانات
                    shift_datetime = datetime.combine(shift_date, datetime.min.time())
                    
                    data = {
                        "date": shift_datetime.isoformat(),
                        "shift_type": shift_type,
                        "center_id": str(center_id),
                        "notes": notes if notes else None
                    }
                    
                    result = ss.create_shift(data)
                    
                    if result:
                        success_count = 0
                        for emp_id in employee_ids:
                            if ss.assign_employee(result["id"], emp_id):
                                success_count += 1
                        
                        if success_count > 0:
                            st.success(f"✅ تم تسجيل المناوبة لـ {success_count} موظف")
                            st.balloons()
                            st.rerun()
    
    # ==================== قسم التناوب الذكي ====================
    elif view_mode == "⚡ تناوب ذكي":
        st.subheader(f"⚡ نظام التناوب الذكي - {selected_center}")
        
        if not employees:
            st.info("لا يوجد موظفون في هذا المركز")
        else:
            # شرح النظام
            with st.expander("📖 شرح نظام التناوب", expanded=False):
                st.markdown("""
                ### نظام التناوب المعتاد:
                - **🌅 يومين صباحي** (12 ساعة)
                - **🌙 يومين ليلي** (12 ساعة)
                - **⭕ 4 أيام إجازة** (فارغة بدون رموز)
                
                **الدورة الكاملة = 8 أيام** (2+2+4)
                
                يمكنك:
                1. **اختيار موظف** وبدء التناوب من تاريخ محدد
                2. **تحديد نمط تناوب** مختلف (3+3+3 أو 4+4+4)
                3. **تطبيق التناوب** على عدة موظفين دفعة واحدة
                """)
            
            # تبويبات التناوب الذكي
            smart_tabs = st.tabs(["🔄 تناوب فردي", "👥 تناوب جماعي", "📅 تناوب مخصص"])
            
            # ===== التبويب 1: تناوب فردي =====
            with smart_tabs[0]:
                st.markdown("### 🔄 تطبيق تناوب على موظف واحد")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # اختيار الموظف
                    emp_names = [f"{emp['full_name']} ({emp.get('emp_no', '')})" for emp in employees]
                    selected_emp = st.selectbox("اختر الموظف", emp_names, key="single_emp")
                    selected_emp_id = str(employees[emp_names.index(selected_emp)]["id"])
                
                with col2:
                    # اختيار تاريخ البداية
                    start_day = st.number_input("يوم البدء", 1, days_in_month, 1, key="start_day")
                    start_date = f"{year}-{month:02d}-{start_day:02d}"
                
                # اختيار نمط التناوب
                st.markdown("#### اختر نمط التناوب")
                pattern_cols = st.columns(len(ROTATION_PATTERNS))
                
                selected_pattern = None
                for i, (pattern_key, pattern_info) in enumerate(ROTATION_PATTERNS.items()):
                    with pattern_cols[i]:
                        if st.button(
                            f"{pattern_key}\n\n{pattern_info['description']}",
                            key=f"pattern_{pattern_key}",
                            use_container_width=True
                        ):
                            selected_pattern = pattern_key
                
                if selected_pattern:
                    pattern_info = ROTATION_PATTERNS[selected_pattern]
                    st.success(f"✅ تم اختيار: {pattern_info['name']}")
                    
                    # عرض معاينة للتناوب
                    st.markdown("#### معاينة التناوب:")
                    preview_days = min(16, days_in_month - start_day + 1)
                    
                    preview_cols = st.columns(preview_days)
                    for i in range(preview_days):
                        day_num = start_day + i
                        pattern_idx = i % pattern_info['days']
                        shift_type = pattern_info['pattern'][pattern_idx]
                        
                        with preview_cols[i]:
                            st.markdown(f"<center><b>{day_num}</b></center>", unsafe_allow_html=True)
                            if shift_type != "off":
                                st.markdown(
                                    f"<center style='background:{SHIFT_TYPES[shift_type]['color']}; "
                                    f"color:{SHIFT_TYPES[shift_type]['text']}; border-radius:4px; "
                                    f"padding:5px;'>{SHIFT_TYPES[shift_type]['icon']}</center>",
                                    unsafe_allow_html=True
                                )
                            else:
                                st.markdown("<center>—</center>", unsafe_allow_html=True)
                    
                    if st.button("✅ تطبيق التناوب", type="primary", key="apply_single", use_container_width=True):
                        # تحديث shifts_map
                        for day in range(start_day, days_in_month + 1):
                            pattern_idx = (day - start_day) % pattern_info['days']
                            shift_type = pattern_info['pattern'][pattern_idx]
                            
                            if selected_emp_id not in shifts_map:
                                shifts_map[selected_emp_id] = {}
                            shifts_map[selected_emp_id][day] = shift_type
                        
                        st.success(f"✅ تم تطبيق تناوب '{selected_pattern}' على الموظف من تاريخ {start_date}")
                        st.balloons()
                        st.rerun()
            
            # ===== التبويب 2: تناوب جماعي =====
            with smart_tabs[1]:
                st.markdown("### 👥 تطبيق تناوب على عدة موظفين")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # اختيار الموظفين
                    emp_options = [f"{emp['full_name']} ({emp.get('emp_no', '')})" for emp in employees]
                    selected_emps = st.multiselect("اختر الموظفين", emp_options, key="multi_emps")
                
                with col2:
                    # اختيار نمط التناوب
                    pattern_key = st.selectbox(
                        "اختر نمط التناوب",
                        options=list(ROTATION_PATTERNS.keys()),
                        key="pattern_select",
                        format_func=lambda x: ROTATION_PATTERNS[x]['name']
                    )
                    pattern_info = ROTATION_PATTERNS[pattern_key]
                    
                    st.info(f"📊 {pattern_info['description']}")
                
                # اختيار تاريخ البداية
                start_day = st.number_input("يوم البدء للجميع", 1, days_in_month, 1, key="multi_start")
                
                if st.button("✅ تطبيق التناوب الجماعي", type="primary", key="apply_multi", use_container_width=True):
                    for emp_name in selected_emps:
                        emp_idx = emp_options.index(emp_name)
                        emp_id = str(employees[emp_idx]["id"])
                        
                        for day in range(start_day, days_in_month + 1):
                            pattern_idx = (day - start_day + emp_idx * 2) % pattern_info['days']
                            shift_type = pattern_info['pattern'][pattern_idx]
                            
                            if emp_id not in shifts_map:
                                shifts_map[emp_id] = {}
                            shifts_map[emp_id][day] = shift_type
                    
                    st.success(f"✅ تم تطبيق التناوب على {len(selected_emps)} موظف")
                    st.balloons()
                    st.rerun()
            
            # ===== التبويب 3: تناوب مخصص =====
            with smart_tabs[2]:
                st.markdown("### 📅 تصميم تناوب مخصص")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # اختيار الموظفين
                    custom_emps = st.multiselect(
                        "اختر الموظفين",
                        [f"{emp['full_name']} ({emp.get('emp_no', '')})" for emp in employees],
                        key="custom_emps"
                    )
                
                with col2:
                    # طول الدورة
                    cycle_length = st.number_input("طول الدورة (أيام)", 2, 14, 8, key="cycle_length")
                
                st.markdown("#### صمم نمط الدورة:")
                
                # عرض أيام الدورة
                cycle_cols = st.columns(cycle_length)
                cycle_pattern = []
                
                for i in range(cycle_length):
                    with cycle_cols[i]:
                        st.markdown(f"<center><b>يوم {i+1}</b></center>", unsafe_allow_html=True)
                        shift = st.selectbox(
                            "",
                            options=["morning", "night", "off"],
                            format_func=lambda x: {
                                "morning": "🌅 صباحي",
                                "night": "🌙 ليلي",
                                "off": "⭕ إجازة"
                            }[x],
                            key=f"cycle_day_{i}",
                            label_visibility="collapsed"
                        )
                        cycle_pattern.append(shift)
                
                # عرض معاينة للدورة
                st.markdown("#### معاينة الدورة:")
                preview_cols = st.columns(cycle_length)
                for i, shift in enumerate(cycle_pattern):
                    with preview_cols[i]:
                        if shift != "off":
                            st.markdown(
                                f"<center style='background:{SHIFT_TYPES[shift]['color']}; "
                                f"color:{SHIFT_TYPES[shift]['text']}; border-radius:4px; "
                                f"padding:5px;'>{SHIFT_TYPES[shift]['icon']}</center>",
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown("<center>—</center>", unsafe_allow_html=True)
                
                if st.button("✅ تطبيق النمط المخصص", type="primary", key="apply_custom", use_container_width=True):
                    start_day = 1
                    for emp_name in custom_emps:
                        emp_idx = [f"{emp['full_name']} ({emp.get('emp_no', '')})" for emp in employees].index(emp_name)
                        emp_id = str(employees[emp_idx]["id"])
                        
                        for day in range(start_day, days_in_month + 1):
                            pattern_idx = (day - start_day + emp_idx) % cycle_length
                            shift_type = cycle_pattern[pattern_idx]
                            
                            if emp_id not in shifts_map:
                                shifts_map[emp_id] = {}
                            shifts_map[emp_id][day] = shift_type
                    
                    st.success(f"✅ تم تطبيق النمط المخصص على {len(custom_emps)} موظف")
                    st.balloons()
                    st.rerun()
    
    # ==================== قسم الإحصائيات ====================
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
                st.metric("🌅 مناوبات صباحية", shifts_count.get("morning", 0))
            with col3:
                st.metric("🌙 مناوبات ليلية", shifts_count.get("night", 0))
            with col4:
                st.metric("⭕ أيام إجازة", shifts_count.get("off", 0))
            
            st.markdown("---")
            
            # رسم بياني
            import plotly.express as px
            df_pie = pd.DataFrame({
                "النوع": ["صباحي", "ليلي", "إجازة"],
                "العدد": [
                    shifts_count.get("morning", 0),
                    shifts_count.get("night", 0),
                    shifts_count.get("off", 0)
                ]
            })
            fig = px.pie(df_pie, values='العدد', names='النوع', 
                        title="توزيع المناوبات",
                        color_discrete_sequence=["#FFB74D", "#4A6FA5", "#E0E0E0"])
            st.plotly_chart(fig, use_container_width=True)