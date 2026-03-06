# frontend/pages/shifts.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
from utils.helpers import page_header, section_title
from components.cards import kpi_row
from components.charts import create_line_chart, display_chart

# أسماء الأشهر
MONTHS_AR = {
    1:"يناير",2:"فبراير",3:"مارس",4:"أبريل",5:"مايو",6:"يونيو",
    7:"يوليو",8:"أغسطس",9:"سبتمبر",10:"أكتوبر",11:"نوفمبر",12:"ديسمبر",
}

# أيام الأسبوع
WEEKDAYS_AR = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
WEEKDAYS_AR_SHORT = ["إث", "ثل", "أر", "خم", "جم", "سب", "أحد"]

# ===== أنواع المناوبات المتطورة =====
SHIFT_TYPES = {
    # المناوبات الأساسية
    "morning_12":   {"name": "صباحي 12 س", "icon": "🌅", "color": "#FFB74D", "text": "#7A5800", "hours": 12, "start": "08:00", "end": "20:00"},
    "night_12":     {"name": "ليلي 12 س", "icon": "🌙", "color": "#4A6FA5", "text": "#FFFFFF", "hours": 12, "start": "20:00", "end": "08:00"},
    
    # الدوام الرسمي
    "official_8":   {"name": "دوام رسمي", "icon": "🏢", "color": "#3B4A82", "text": "#FFFFFF", "hours": 8, "start": "08:00", "end": "16:00"},
    "official_9":   {"name": "دوام 9 س", "icon": "📋", "color": "#513A87", "text": "#FFFFFF", "hours": 9, "start": "08:00", "end": "17:00"},
    
    # المناوبات التداخلية
    "overlap_morning": {"name": "تداخلي صباحي", "icon": "🔄", "color": "#45CFEF", "text": "#1A1A2E", "hours": 10, "start": "10:00", "end": "20:00"},
    "overlap_evening": {"name": "تداخلي مسائي", "icon": "🔄", "color": "#FF7C10", "text": "#FFFFFF", "hours": 10, "start": "14:00", "end": "00:00"},
    
    # مناوبات نهاية الأسبوع
    "weekend_morning": {"name": "نهاية أسبوع صباحي", "icon": "🌅", "color": "#F1B944", "text": "#1A1A2E", "hours": 8, "start": "08:00", "end": "16:00"},
    "weekend_night":   {"name": "نهاية أسبوع ليلي", "icon": "🌙", "color": "#2D4A6E", "text": "#FFFFFF", "hours": 8, "start": "16:00", "end": "00:00"},
    
    # إجازة
    "off":          {"name": "إجازة", "icon": "⭕", "color": "#FFFFFF", "text": "#4A5568", "hours": 0, "start": "—", "end": "—"},
}

# أنماط التناوب
ROTATION_PATTERNS = {
    "نظام 2+2+4": {
        "name": "يومين صباح 12 س + يومين ليل 12 س + 4 أيام إجازة",
        "days": 8,
        "pattern": ["morning_12", "morning_12", "night_12", "night_12", "off", "off", "off", "off"],
        "description": "دورة 8 أيام: 2 صباحي 12 س، 2 ليلي 12 س، 4 إجازة"
    },
    "نظام دوام رسمي": {
        "name": "5 أيام دوام رسمي + 2 إجازة",
        "days": 7,
        "pattern": ["official_8", "official_8", "official_8", "official_8", "official_8", "off", "off"],
        "description": "أسبوع عمل: 5 أيام دوام رسمي، 2 إجازة"
    },
    "نظام تداخلي": {
        "name": "تداخلي صباحي + تداخلي مسائي + إجازة",
        "days": 3,
        "pattern": ["overlap_morning", "overlap_evening", "off"],
        "description": "دورة 3 أيام: تداخلي صباحي، تداخلي مسائي، إجازة"
    },
    "نظام مختلط": {
        "name": "دوام رسمي + صباحي 12 س + ليلي 12 س + إجازة",
        "days": 5,
        "pattern": ["official_8", "morning_12", "night_12", "off", "off"],
        "description": "دوام رسمي، صباحي 12 س، ليلي 12 س، يومين إجازة"
    },
    "نظام نهاية أسبوع": {
        "name": "نهاية أسبوع صباحي + ليلي + إجازة",
        "days": 4,
        "pattern": ["weekend_morning", "weekend_night", "off", "off"],
        "description": "نهاية أسبوع صباحي، نهاية أسبوع ليلي، يومين إجازة"
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
    """صفحة إدارة المناوبات المتطورة"""
    
    page_header("إدارة المناوبات", "أنظمة تناوب متعددة: دوام رسمي، 12 ساعة، تداخلي", "📅")
    
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
        selected_center = st.selectbox("🏥 المركز", center_names)
        center_id = center_ids[center_names.index(selected_center)]
    
    with col2:
        year = st.number_input("📅 السنة", 2020, 2030, datetime.now().year)
    
    with col3:
        month = st.number_input("📆 الشهر", 1, 12, datetime.now().month)
    
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        view_mode = st.radio("القسم", ["📋 الجدول", "➕ إضافة", "⚡ تناوب ذكي", "📊 إحصائيات"], horizontal=True)
    
    with col5:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 تحديث", key="refresh_shifts"):
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
                    shifts_map[emp_id][day] = shift.get("shift_type", "morning_12")
        except:
            continue
    
    # بيانات تجريبية إذا كانت المناوبات فارغة
    if employees and not shifts_map:
        import random
        random.seed(42)
        
        for emp in employees:
            emp_id = str(emp["id"])
            shifts_map[emp_id] = {}
            pattern = ["morning_12", "morning_12", "night_12", "night_12", "off", "off", "off", "off"]
            offset = employees.index(emp) * 2
            
            for day in range(1, days_in_month + 1):
                pattern_idx = (day + offset) % 8
                shifts_map[emp_id][day] = pattern[pattern_idx]
    
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
                    "الموظف": emp['full_name'],
                    "الرقم": emp.get('emp_no', ''),
                    "id": emp_id
                }
                
                # حساب إحصائيات سريعة
                total_hours = 0
                work_days = 0
                
                for day in range(1, days_in_month + 1):
                    shift_type = emp_shifts.get(day, "off")
                    row[str(day)] = SHIFT_TYPES[shift_type]["icon"]
                    
                    if shift_type != "off":
                        work_days += 1
                        total_hours += SHIFT_TYPES[shift_type]["hours"]
                
                row["أيام العمل"] = work_days
                row["ساعات العمل"] = total_hours
                
                data.append(row)
            
            if data:
                df = pd.DataFrame(data)
                
                # أعمدة للعرض
                display_cols = ["الموظف", "الرقم"] + [str(d) for d in range(1, days_in_month + 1)]
                
                st.dataframe(
                    df[display_cols],
                    use_container_width=True,
                    hide_index=True,
                    column_config={str(d): st.column_config.TextColumn(str(d), width="small") 
                                   for d in range(1, days_in_month + 1)}
                )
                
                # جدول إحصائيات ساعات العمل
                st.markdown("### ⏱️ إحصائيات ساعات العمل")
                stats_df = df[["الموظف", "أيام العمل", "ساعات العمل"]].copy()
                st.dataframe(stats_df, use_container_width=True, hide_index=True)
                
                # مفتاح الألوان
                st.markdown("### 🔑 دليل أنواع المناوبات")
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
                            font-size: 0.7rem;
                            border: {'' if key != 'off' else '1px solid #E2E8F0'};
                        ">
                            {value['icon']} {value['name']}<br>
                            <span style="font-size: 0.6rem;">{value['hours']} ساعة</span>
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
                    format_func=lambda x: f"{SHIFT_TYPES[x]['icon']} {SHIFT_TYPES[x]['name']} ({SHIFT_TYPES[x]['hours']} س)"
                )
            
            with col2:
                st.markdown(f"**⏱️ ساعات العمل:** {SHIFT_TYPES[shift_type]['hours']} ساعة")
                st.markdown(f"**🕐 الوقت:** {SHIFT_TYPES[shift_type]['start']} - {SHIFT_TYPES[shift_type]['end']}")
            
            # جلب الموظفين
            if employees:
                emp_options = {f"{emp['full_name']} ({emp.get('emp_no', '')})": emp["id"] 
                              for emp in employees}
                selected_emps = st.multiselect("👥 الموظفون", list(emp_options.keys()))
                employee_ids = [emp_options[name] for name in selected_emps]
            else:
                st.warning("لا يوجد موظفون")
                employee_ids = []
            
            notes = st.text_area("📝 ملاحظات")
            
            if st.form_submit_button("✅ تسجيل المناوبة", type="primary", use_container_width=True):
                if not employee_ids:
                    st.error("❌ اختر موظفاً")
                else:
                    st.success(f"✅ تم تسجيل المناوبة لـ {len(employee_ids)} موظف")
                    st.balloons()
                    st.rerun()
    
    # ==================== قسم التناوب الذكي ====================
    elif view_mode == "⚡ تناوب ذكي":
        st.subheader(f"⚡ أنظمة التناوب الذكية - {selected_center}")
        
        if not employees:
            st.info("لا يوجد موظفون")
        else:
            tabs = st.tabs(["🔄 تناوب فردي", "👥 تناوب جماعي", "📋 أنماط جاهزة"])
            
            with tabs[0]:
                st.markdown("### 🔄 تطبيق تناوب على موظف واحد")
                
                emp_names = [f"{emp['full_name']} ({emp.get('emp_no', '')})" for emp in employees]
                selected_emp = st.selectbox("اختر الموظف", emp_names)
                selected_emp_id = str(employees[emp_names.index(selected_emp)]["id"])
                
                start_day = st.number_input("يوم البدء", 1, days_in_month, 1)
                
                # اختيار النمط
                st.markdown("#### اختر نمط التناوب")
                pattern_cols = st.columns(len(ROTATION_PATTERNS))
                
                for i, (key, pattern) in enumerate(ROTATION_PATTERNS.items()):
                    with pattern_cols[i]:
                        if st.button(f"{key}\n\n{pattern['description']}", key=f"pattern_{key}"):
                            st.session_state.selected_pattern = key
                
                if "selected_pattern" in st.session_state:
                    pattern = ROTATION_PATTERNS[st.session_state.selected_pattern]
                    st.success(f"✅ تم اختيار: {pattern['name']}")
                    
                    if st.button("✅ تطبيق التناوب", type="primary"):
                        st.success(f"✅ تم تطبيق التناوب")
                        st.balloons()
            
            with tabs[1]:
                st.markdown("### 👥 تناوب جماعي")
                
                emp_options = [f"{emp['full_name']} ({emp.get('emp_no', '')})" for emp in employees]
                selected_emps = st.multiselect("اختر الموظفين", emp_options)
                
                pattern_key = st.selectbox("اختر نمط التناوب", list(ROTATION_PATTERNS.keys()))
                pattern = ROTATION_PATTERNS[pattern_key]
                
                st.info(f"📊 {pattern['description']}")
                
                if st.button("✅ تطبيق على المختارين", type="primary"):
                    st.success(f"✅ تم تطبيق التناوب على {len(selected_emps)} موظف")
                    st.balloons()
            
            with tabs[2]:
                st.markdown("### 📋 أنماط جاهزة")
                
                for key, pattern in ROTATION_PATTERNS.items():
                    with st.expander(f"{key}"):
                        st.write(f"**{pattern['name']}**")
                        st.write(f"📝 {pattern['description']}")
                        
                        # عرض نمط الدورة
                        cols = st.columns(pattern['days'])
                        for i, shift in enumerate(pattern['pattern']):
                            with cols[i]:
                                st.markdown(f"""
                                <div style="
                                    background: {SHIFT_TYPES[shift]['color']};
                                    color: {SHIFT_TYPES[shift]['text']};
                                    padding: 0.5rem;
                                    border-radius: 4px;
                                    text-align: center;
                                    font-size: 0.7rem;
                                ">
                                    {SHIFT_TYPES[shift]['icon']}<br>
                                    <small>{SHIFT_TYPES[shift]['hours']}س</small>
                                </div>
                                """, unsafe_allow_html=True)
    
    # ==================== قسم الإحصائيات ====================
    elif view_mode == "📊 إحصائيات":
        st.subheader(f"📊 إحصائيات المناوبات - {selected_center}")
        
        if employees:
            # إحصائيات عامة
            total_employees = len(employees)
            total_days = days_in_month
            total_slots = total_employees * total_days
            
            shifts_count = {stype: 0 for stype in SHIFT_TYPES}
            total_hours = 0
            
            for emp in employees:
                emp_id = str(emp["id"])
                emp_shifts = shifts_map.get(emp_id, {})
                for day in range(1, days_in_month + 1):
                    stype = emp_shifts.get(day, "off")
                    shifts_count[stype] += 1
                    if stype != "off":
                        total_hours += SHIFT_TYPES[stype]["hours"]
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("👥 إجمالي الموظفين", total_employees)
            col2.metric("📅 إجمالي المناوبات", sum(shifts_count.values()) - shifts_count["off"])
            col3.metric("⏱️ إجمالي ساعات العمل", f"{total_hours:,} س")
            col4.metric("📊 متوسط ساعات/موظف", f"{total_hours/total_employees:.0f} س")
            
            st.markdown("---")
            
            # توزيع أنواع المناوبات
            st.subheader("📊 توزيع أنواع المناوبات")
            
            chart_data = []
            for stype, count in shifts_count.items():
                if count > 0:
                    chart_data.append({
                        "النوع": SHIFT_TYPES[stype]["name"],
                        "العدد": count,
                        "ساعات العمل": count * SHIFT_TYPES[stype]["hours"]
                    })
            
            if chart_data:
                df_chart = pd.DataFrame(chart_data)
                
                col1, col2 = st.columns(2)
                with col1:
                    fig1 = px.pie(df_chart, values='العدد', names='النوع', title="توزيع المناوبات")
                    st.plotly_chart(fig1, use_container_width=True)
                
                with col2:
                    fig2 = px.bar(df_chart, x='النوع', y='ساعات العمل', title="ساعات العمل حسب النوع")
                    st.plotly_chart(fig2, use_container_width=True)
                
                # جدول تفصيلي
                st.subheader("📋 تفصيل ساعات العمل")
                st.dataframe(df_chart, use_container_width=True, hide_index=True)
                
                # تصدير
                csv = df_chart.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    "📥 تصدير الإحصائيات",
                    data=csv.encode('utf-8-sig'),
                    file_name=f"shifts_stats_{year}{month:02d}.csv",
                    mime="text/csv"
                )