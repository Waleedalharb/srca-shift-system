# frontend/pages/shifts.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
from utils.helpers import page_header, section_title
from components.cards import kpi_row
from components.charts import create_line_chart, display_chart
from utils.constants import SHIFT_TYPES, get_all_shift_codes, get_shift_info

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

# ===== دالة عرض تقرير الطباعة (بالنظام الجديد) =====
def show_printable_report(employee_data, shifts_data, year, month, center_name, employee_name):
    """
    عرض تقرير المناوبات بشكل مناسب للطباعة - النظام الجديد
    """
    days_in_month = calendar.monthrange(year, month)[1]
    
    # تنسيق خاص للطباعة
    st.markdown("""
    <style>
    @media print {
        .stAppHeader, .stSidebar, .stDeployButton, footer, header {
            display: none !important;
        }
        .main > div {
            padding: 0 !important;
        }
        button {
            display: none !important;
        }
    }
    .print-table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
        font-family: 'Cairo', sans-serif;
        direction: rtl;
    }
    .print-table th {
        background: #1e3c72;
        color: white;
        padding: 8px;
        text-align: center;
        font-size: 14px;
    }
    .print-table td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: center;
        vertical-align: middle;
        height: 70px;
    }
    .shift-code {
        font-weight: bold;
        font-size: 18px;
    }
    .weekend-day {
        background: #fff3e0;
    }
    .empty-day {
        background: #f5f5f5;
        color: #999;
    }
    .V {
        background: #f8d7da;
        color: #721c24;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # تحويل بيانات المناوبات للموظف
    emp_shifts = {}
    for shift in shifts_data:
        shift_date = shift.get("date", "").split("T")[0]
        try:
            day = int(shift_date.split("-")[2])
            for assignment in shift.get("assignments", []):
                if assignment.get("employee_id") == employee_data.get("id"):
                    shift_type = shift.get("shift_type")
                    if shift_type:  # فقط إذا كان في مناوبة
                        emp_shifts[day] = shift_type
        except:
            continue
    
    # حساب إجمالي الساعات
    total_hours = 0
    for day in range(1, days_in_month + 1):
        shift_type = emp_shifts.get(day)
        if shift_type and shift_type in SHIFT_TYPES:
            total_hours += SHIFT_TYPES[shift_type]["hours"]
    
    # معلومات التقرير
    st.markdown(f"""
    <div style="background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #ddd;">
        <h2 style="text-align: center; color: #1e3c72;">المملكة العربية السعودية</h2>
        <h3 style="text-align: center; color: #2a5298;">هيئة الهلال الأحمر السعودي</h3>
        <h4 style="text-align: center; color: #666;">الإدارة التنفيذية للشؤون الإسعافية</h4>
        
        <table style="width: 100%; margin-top: 20px;">
            <tr>
                <td><strong>اسم الموظف:</strong> {employee_name}</td>
                <td><strong>الرقم الوظيفي:</strong> {employee_data.get('emp_no', '')}</td>
            </tr>
            <tr>
                <td><strong>المركز:</strong> {center_name}</td>
                <td><strong>الشهر:</strong> {calendar.month_name[month]} {year}</td>
            </tr>
            <tr>
                <td><strong>تاريخ التقرير:</strong> {datetime.now().strftime('%Y-%m-%d')}</td>
                <td><strong>إجمالي الساعات:</strong> {total_hours} ساعة</td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)
    
    # بناء جدول الأيام (أسابيع)
    weeks_data = []
    week = []
    for day in range(1, days_in_month + 1):
        week.append(day)
        if len(week) == 7 or day == days_in_month:
            while len(week) < 7:
                week.append("")
            weeks_data.append(week)
            week = []
    
    # أيام الأسبوع
    weekdays_ar = ["الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]
    
    # عرض كل أسبوع في جدول
    for week_days in weeks_data:
        html = '<table class="print-table"><tr>'
        
        # رؤوس الأيام
        for day_name in weekdays_ar:
            html += f'<th>{day_name}</th>'
        html += '</tr><tr>'
        
        # محتوى الأيام
        for i, day_num in enumerate(week_days):
            weekend_class = 'weekend-day' if weekdays_ar[i] in ['الجمعة', 'السبت'] else ''
            
            if day_num:
                shift_type = emp_shifts.get(day_num)
                if shift_type:
                    shift_info = SHIFT_TYPES.get(shift_type, {})
                    v_class = 'V' if shift_type == 'V' else ''
                    html += f'<td class="{weekend_class} {v_class}"><span class="shift-code">{shift_type}</span></td>'
                else:
                    html += f'<td class="{weekend_class} empty-day">-</td>'
            else:
                html += f'<td class="empty-day">-</td>'
        
        html += '</tr></table>'
        st.markdown(html, unsafe_allow_html=True)
    
    # زر العودة
    if st.button("🔙 العودة للتعديل", use_container_width=True):
        st.rerun()

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
    """صفحة إدارة المناوبات - النظام الجديد"""
    
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
                    shift_type = shift.get("shift_type")
                    if shift_type:  # فقط إذا كان في مناوبة
                        shifts_map[emp_id][day] = shift_type
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
                shift_type = emp_shifts.get(day)
                if shift_type and shift_type in SHIFT_TYPES:
                    total_hours += SHIFT_TYPES[shift_type]["hours"]
            
            total_hours_all += total_hours
            
            row = {
                "الموظف": emp['full_name'],
                "الرقم": emp.get('emp_no', ''),
                "إجمالي الساعات": f"{total_hours} س",
                "id": emp_id
            }
            
            for day in range(1, days_in_month + 1):
                shift_type = emp_shifts.get(day)
                if shift_type:
                    row[str(day)] = shift_type  # الرمز نفسه D8, N12, V...
                else:
                    row[str(day)] = ""  # 👈 خانة فاضية
            
            table_data.append(row)
        
        if table_data:
            df = pd.DataFrame(table_data)
            display_cols = ["الموظف", "الرقم", "إجمالي الساعات"] + [str(d) for d in range(1, days_in_month + 1)]
            
            # تنسيق عرض الأعمدة
            column_config = {}
            for day in range(1, days_in_month + 1):
                column_config[str(day)] = st.column_config.TextColumn(
                    str(day),
                    width="small",
                    help=f"يوم {day}"
                )
            
            st.dataframe(
                df[display_cols], 
                use_container_width=True, 
                hide_index=True,
                column_config=column_config
            )
            
            # عرض إجمالي ساعات الفريق
            st.info(f"⏱️ **إجمالي ساعات العمل للفريق:** {total_hours_all} ساعة في {selected_center}")
            
            # دليل الرموز
            st.markdown("### 🔑 دليل الرموز")
            cols = st.columns(6)
            codes_to_show = ["D8", "N12", "O6", "V", "E", "M"]
            for i, code in enumerate(codes_to_show):
                if code in SHIFT_TYPES:
                    info = SHIFT_TYPES[code]
                    with cols[i % 6]:
                        st.markdown(f"<div style='background:{info['color']}; color:{info['text_color']}; padding:0.5rem; border-radius:8px; text-align:center;'><strong>{code}</strong> - {info['name']}</div>", unsafe_allow_html=True)
    
    # ===== وضع التعديل =====
    elif view_mode == "✏️ تعديل":
        st.subheader("✏️ تعديل المناوبات")
        
        # اختيار الموظف
        emp_names = [f"{e['full_name']} ({e.get('emp_no', '')})" for e in employees]
        selected_emp_name = st.selectbox("👤 اختر الموظف", emp_names)
        selected_emp = employees[emp_names.index(selected_emp_name)]
        emp_id = str(selected_emp["id"])
        
        # زر عرض التقرير
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🖨️ عرض تقرير قابل للطباعة", use_container_width=True):
                show_printable_report(selected_emp, shifts, year, month, selected_center, selected_emp['full_name'])
                st.stop()
        
        st.markdown("---")
        st.markdown(f"**تعديل مناوبات:** {selected_emp['full_name']}")
        
        # عرض أيام الشهر للتعديل
        emp_shifts = shifts_map.get(emp_id, {})
        
        # اختيار نوع التعديل
        edit_type = st.radio("نوع التعديل", ["يومي", "نطاق أيام", "تطبيق نمط"], horizontal=True)
        
        # الحصول على قائمة الرموز الجديدة
        shift_options = list(SHIFT_TYPES.keys())
        
        if edit_type == "يومي":
            col1, col2 = st.columns([1, 3])
            with col1:
                day = st.number_input("اليوم", 1, days_in_month, 1)
            with col2:
                current_shift = emp_shifts.get(day, "")
                current_index = shift_options.index(current_shift) if current_shift in shift_options else 0
                new_shift = st.selectbox(
                    "المناوبة",
                    options=shift_options,
                    format_func=lambda x: f"{x} - {SHIFT_TYPES[x]['name']}",
                    index=current_index
                )
            
            if st.button("💾 تحديث", use_container_width=True, type="primary"):
                date_str = f"{year}-{month:02d}-{day:02d}"
                success = ss.update_employee_shift(emp_id, date_str, new_shift)
                
                if success:
                    st.success(f"✅ تم تحديث يوم {day} إلى {new_shift}")
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
                options=shift_options,
                format_func=lambda x: f"{x} - {SHIFT_TYPES[x]['name']}"
            )
            
            if st.button("💾 تحديث النطاق", use_container_width=True, type="primary"):
                success_count = 0
                for day in range(from_day, to_day + 1):
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    if ss.update_employee_shift(emp_id, date_str, new_shift):
                        success_count += 1
                
                if success_count > 0:
                    st.success(f"✅ تم تحديث {success_count} يوم إلى {new_shift}")
                    st.cache_data.clear()
                    st.session_state.shift_service = None
                    st.rerun()
                else:
                    st.error("❌ فشل في تحديث المناوبات")
        
        else:  # تطبيق نمط
            st.markdown("#### أنماط التناوب")
            patterns = {
                "نظام 2+2+4": ["D12", "D12", "N12", "N12", "", "", "", ""],
                "نظام دوام رسمي": ["D8", "D8", "D8", "D8", "D8", "", ""],
                "نظام تداخلي": ["O8", "O8", ""],
                "نظام 3+3+3": ["D12", "D12", "D12", "N12", "N12", "N12", "", "", ""],
                "نظام نهاية أسبوع": ["D8", "D8", "N8", "N8", "", "", ""],
            }
            
            selected_pattern = st.selectbox("اختر النمط", list(patterns.keys()))
            pattern = patterns[selected_pattern]
            
            st.markdown("**نمط الدورة:**")
            cols = st.columns(len(pattern))
            for i, p in enumerate(pattern):
                with cols[i]:
                    if p:
                        info = SHIFT_TYPES.get(p, {})
                        bg_color = info.get('color', '#E0E0E0')
                        text_color = info.get('text_color', '#4A5568')
                        st.markdown(f"<div style='background:{bg_color}; color:{text_color}; padding:0.5rem; border-radius:8px; text-align:center;'>{p}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='background:#E0E0E0; color:#4A5568; padding:0.5rem; border-radius:8px; text-align:center;'>-</div>", unsafe_allow_html=True)
            
            start_day = st.number_input("بدءًا من يوم", 1, days_in_month, 1)
            
            if st.button("✅ تطبيق النمط", use_container_width=True, type="primary"):
                success_count = 0
                for i, day in enumerate(range(start_day, days_in_month + 1)):
                    pattern_idx = (i) % len(pattern)
                    shift_type = pattern[pattern_idx]
                    if shift_type:  # فقط إذا كان في مناوبة
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
                options=shift_options,
                format_func=lambda x: f"{x} - {SHIFT_TYPES[x]['name']} ({SHIFT_TYPES[x]['hours']} س)"
            )
            
            emp_options = {f"{e['full_name']} ({e.get('emp_no', '')})": e["id"] for e in employees}
            selected_emps = st.multiselect("👥 الموظفون", list(emp_options.keys()))
            employee_ids = [emp_options[name] for name in selected_emps]
            
            notes = st.text_area("📝 ملاحظات")
            
            if st.form_submit_button("✅ إضافة", use_container_width=True, type="primary"):
                if not employee_ids:
                    st.error("❌ اختر موظفًا واحدًا على الأقل")
                else:
                    success_count = 0
                    for emp_id in employee_ids:
                        date_str = shift_date.strftime("%Y-%m-%d")
                        if ss.save_shift(emp_id, date_str, shift_type):
                            success_count += 1
                    
                    st.success(f"✅ تم إضافة المناوبة لـ {success_count} موظف")
                    st.cache_data.clear()
                    st.session_state.shift_service = None
                    st.rerun()