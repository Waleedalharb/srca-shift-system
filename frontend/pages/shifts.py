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

# ===== دالة حساب ساعات الموظف حسب فئته =====
def calculate_employee_hours(employee_data, emp_shifts, days_in_month, center_name):
    """
    حساب ساعات الموظف حسب فئته ونظام العمل
    """
    emp_code = employee_data.get('emp_code', '')
    
    # ===== المركز الرئيسي للقطاع =====
    if center_name == "المركز الرئيسي للقطاع":
        
        # 1. قيادات (A0, B0, C0, D0) - نظام ورديات 12 ساعة
        if emp_code.endswith('0') and len(emp_code) <= 3 and emp_code[0] in 'ABCD':
            working_days = 0
            for day in range(1, days_in_month + 1):
                shift_type = emp_shifts.get(day)
                if shift_type and shift_type != 'V':  # أي يوم عمل
                    working_days += 1
            return working_days * 12  # كل وردية 12 ساعة
        
        # 2. عمليات (XW1, XW2...) - ورديات 12 ساعة
        elif emp_code.startswith('XW'):
            total = 0
            for day in range(1, days_in_month + 1):
                shift_type = emp_shifts.get(day)
                if shift_type and shift_type != 'V':
                    total += 12  # كل وردية عمليات 12 ساعة
            return total
        
        # 3. دعم (Y, YY, Z) - إداري 8 ساعات
        elif emp_code in ['Y', 'YY', 'Z']:
            working_days = 0
            for day in range(1, days_in_month + 1):
                shift_type = emp_shifts.get(day)
                if shift_type and shift_type != 'V':
                    working_days += 1
            return working_days * 8  # دوام رسمي 8 ساعات
        
        # 4. تدخل سريع (RR) - حسب المناوبة
        elif emp_code.startswith('RR'):
            total = 0
            for day in range(1, days_in_month + 1):
                shift_type = emp_shifts.get(day)
                if shift_type and shift_type in SHIFT_TYPES:
                    total += SHIFT_TYPES[shift_type]["hours"]
            return total
        
        # 5. أي تصنيف آخر في المركز الرئيسي
        else:
            total = 0
            for day in range(1, days_in_month + 1):
                shift_type = emp_shifts.get(day)
                if shift_type and shift_type in SHIFT_TYPES:
                    total += SHIFT_TYPES[shift_type]["hours"]
            return total
    
    # ===== باقي المراكز =====
    # موظف عادي - حسب ساعات المناوبة
    else:
        total = 0
        for day in range(1, days_in_month + 1):
            shift_type = emp_shifts.get(day)
            if shift_type and shift_type in SHIFT_TYPES:
                total += SHIFT_TYPES[shift_type]["hours"]
        return total

# ===== دالة عرض تقرير الطباعة (نسخة محسنة نهائية) =====
def show_printable_report(employee_data, shifts_data, year, month, center_name, employee_name):
    """
    عرض تقرير المناوبات بشكل مناسب للطباعة - نسخة محسنة
    """
    days_in_month = calendar.monthrange(year, month)[1]
    
    # تنسيق خاص للطباعة
    st.markdown("""
    <style>
    @media print {
        .stAppHeader, .stSidebar, .stDeployButton, footer, header,
        .stButton, .stSelectbox, .stNumberInput, .stRadio,
        [data-testid="stDecoration"], [data-testid="stToolbar"] {
            display: none !important;
        }
        .main > div {
            padding: 0 !important;
            max-width: 100% !important;
        }
        body {
            background: white;
            font-family: 'Arial', sans-serif;
        }
        .report-container {
            direction: rtl;
            padding: 20px;
        }
        .report-header {
            text-align: center;
            margin-bottom: 20px;
            border-bottom: 2px solid #1e3c72;
            padding-bottom: 10px;
        }
        .report-header h1 {
            color: #1e3c72;
            font-size: 24px;
            margin: 5px 0;
        }
        .report-header h2 {
            color: #2a5298;
            font-size: 20px;
            margin: 5px 0;
        }
        .report-header h3 {
            color: #666;
            font-size: 16px;
            margin: 5px 0;
        }
        .info-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .info-table td {
            padding: 10px;
            border: 1px solid #dee2e6;
            font-size: 14px;
        }
        .info-table td:first-child {
            font-weight: bold;
            background: #e9ecef;
            width: 150px;
        }
        .shifts-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            direction: rtl;
        }
        .shifts-table th {
            background: #1e3c72;
            color: white;
            padding: 10px;
            font-size: 14px;
            text-align: center;
        }
        .shifts-table td {
            border: 1px solid #dee2e6;
            padding: 8px;
            text-align: center;
            vertical-align: middle;
            height: 70px;
        }
        .day-number {
            font-weight: bold;
            font-size: 14px;
            color: #1e3c72;
            margin-bottom: 5px;
        }
        .shift-code {
            font-weight: bold;
            font-size: 16px;
        }
        .weekend-day {
            background: #fff3e0;
        }
        .empty-day {
            background: #f5f5f5;
        }
        .V {
            background: #f8d7da;
            color: #721c24;
        }
        .total-hours-box {
            background: #e8f5e9;
            padding: 12px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: center;
            font-size: 16px;
            font-weight: bold;
            color: #2e7d32;
            border-right: 4px solid #2e7d32;
        }
        .footer {
            margin-top: 30px;
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: #666;
        }
        .print-button {
            display: none !important;
        }
        @media screen {
            .print-button {
                display: block !important;
                text-align: center;
                margin: 20px;
            }
            .print-button button {
                background: #CE2E26;
                color: white;
                padding: 10px 30px;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                cursor: pointer;
            }
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
                    if shift_type and shift_type != "off":
                        emp_shifts[day] = shift_type
        except:
            continue
    
    # حساب إجمالي الساعات باستخدام الدالة الذكية
    total_hours = calculate_employee_hours(employee_data, emp_shifts, days_in_month, center_name)
    
    # بناء جدول الأيام كامل (كل أيام الشهر في جدول واحد)
    html_content = f"""
    <div class="report-container">
        <div class="report-header">
            <h1>المملكة العربية السعودية</h1>
            <h2>هيئة الهلال الأحمر السعودي</h2>
            <h3>الإدارة التنفيذية للشؤون الإسعافية</h3>
        </div>
        
        <table class="info-table">
            <tr>
                <td>اسم الموظف</td>
                <td>{employee_name}</td>
                <td>الرقم الوظيفي</td>
                <td>{employee_data.get('emp_no', '')}</td>
            </tr>
            <tr>
                <td>المركز</td>
                <td>{center_name}</td>
                <td>الشهر</td>
                <td>{calendar.month_name[month]} {year}</td>
            </tr>
            <tr>
                <td>تاريخ التقرير</td>
                <td>{datetime.now().strftime('%Y-%m-%d')}</td>
                <td>إجمالي الساعات</td>
                <td><strong>{total_hours} ساعة</strong></td>
            </tr>
        </table>
        
        <div class="total-hours-box">
            إجمالي ساعات العمل للشهر: {total_hours} ساعة
        </div>
    """
    
    # أيام الأسبوع بالعربية
    weekdays_ar = ["الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]
    
    # حساب أول يوم في الشهر (0 = الاثنين، 6 = الأحد في Python)
    first_day = calendar.weekday(year, month, 1)  # 0 = الاثنين
    
    # إنشاء شبكة 6 أسابيع × 7 أيام
    calendar_days = []
    week = []
    
    # تعبئة الأيام الفارغة قبل أول يوم
    for i in range(first_day):
        week.append("")
    
    # تعبئة أيام الشهر
    for day in range(1, days_in_month + 1):
        week.append(day)
        if len(week) == 7:
            calendar_days.append(week)
            week = []
    
    # تعبئة الأيام الفارغة بعد آخر يوم
    if week:
        while len(week) < 7:
            week.append("")
        calendar_days.append(week)
    
    # بناء جدول واحد لكل أيام الشهر
    html_content += '<table class="shifts-table">'
    
    # صف رؤوس الأيام
    html_content += '<tr>'
    for day_name in weekdays_ar:
        html_content += f'<th>{day_name}</th>'
    html_content += '</tr>'
    
    # عرض كل أسبوع في صف
    for week in calendar_days:
        html_content += '<tr>'
        for i, day_num in enumerate(week):
            weekend_class = 'weekend-day' if weekdays_ar[i] in ['الجمعة', 'السبت'] else ''
            
            if day_num:
                shift_type = emp_shifts.get(day_num)
                if shift_type:
                    v_class = 'V' if shift_type == 'V' else ''
                    html_content += f'<td class="{weekend_class} {v_class}"><div class="day-number">{day_num}</div><div class="shift-code">{shift_type}</div></td>'
                else:
                    html_content += f'<td class="{weekend_class} empty-day"><div class="day-number">{day_num}</div><div>-</div></td>'
            else:
                html_content += f'<td class="empty-day"></td>'
        html_content += '</tr>'
    
    html_content += '</table>'
    
    # تذييل التقرير
    html_content += f"""
        <div class="footer">
            <div>توقيع المشرف: ________________</div>
            <div>الختم: ________________</div>
            <div>تاريخ الطباعة: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
        </div>
    </div>
    """
    
    # عرض التقرير في Streamlit
    st.markdown(html_content, unsafe_allow_html=True)
    
    # زر الطباعة (يظهر فقط على الشاشة)
    st.markdown("""
    <div class="print-button">
        <button onclick="window.print()">🖨️ طباعة التقرير</button>
    </div>
    """, unsafe_allow_html=True)
    
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
    """صفحة إدارة المناوبات"""
    
    # ===== متغير للتحكم بإعادة التحميل (الحل الجذري) =====
    if 'reload_shifts' in st.session_state and st.session_state.reload_shifts:
        st.session_state.shift_service = None
        st.session_state.reload_shifts = False
        st.cache_data.clear()
    
    page_header("📅 إدارة المناوبات", "عرض، إضافة، تعديل، توليد تلقائي للمناوبات", "⏰")
    
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
        view_mode = st.radio("عرض", ["📋 الجدول", "✏️ تعديل", "➕ إضافة", "⚡ توليد تلقائي", "🔄 تكميل الفرق"], horizontal=True)
    
    # جلب الموظفين
    employees = es.get_employees(center_id=center_id).get("items", [])
    
    if not employees:
        st.warning(f"⚠️ لا يوجد موظفون في {selected_center}")
        return
    
    # جلب المناوبات للشهر المحدد
    with st.spinner("جاري تحميل المناوبات..."):
        shifts = ss.get_shifts_by_month(center_id, year, month)
    
    # تحويل المناوبات إلى خريطة
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
                    if shift_type and shift_type != "off":
                        shifts_map[emp_id][day] = shift_type
        except:
            continue
    
    days_in_month = calendar.monthrange(year, month)[1]
    avg_monthly_hours = days_in_month * 8  # متوسط ساعات الشهر
    
    # ===== عرض الجدول =====
    if view_mode == "📋 الجدول":
        st.subheader(f"📋 جدول مناوبات {selected_center} - {month}/{year}")
        
        table_data = []
        total_hours_all = 0
        
        for emp in employees:
            emp_id = str(emp["id"])
            emp_shifts = shifts_map.get(emp_id, {})
            
            total_hours = 0
            for day in range(1, days_in_month + 1):
                shift_type = emp_shifts.get(day)
                if shift_type and shift_type in SHIFT_TYPES:
                    total_hours += SHIFT_TYPES[shift_type]["hours"]
            
            total_hours_all += total_hours
            
            # حساب نسبة الإنجاز
            completion_rate = int((total_hours / avg_monthly_hours) * 100) if avg_monthly_hours > 0 else 0
            
            row = {
                "الموظف": emp['full_name'],
                "الرقم": emp.get('emp_no', ''),
                "إجمالي الساعات": f"{total_hours} س",
                "نسبة الإنجاز": f"{completion_rate}%",
                "id": emp_id
            }
            
            for day in range(1, days_in_month + 1):
                shift_type = emp_shifts.get(day)
                if shift_type:
                    row[str(day)] = shift_type
                else:
                    row[str(day)] = ""
            
            table_data.append(row)
        
        if table_data:
            df = pd.DataFrame(table_data)
            
            # فلتر إظهار الموظفين بدون مناوبات
            show_empty = st.checkbox("🔍 إظهار الموظفين بدون مناوبات فقط")
            if show_empty:
                df = df[df["إجمالي الساعات"] == "0 س"]
            
            display_cols = ["الموظف", "الرقم", "إجمالي الساعات", "نسبة الإنجاز"] + [str(d) for d in range(1, days_in_month + 1)]
            
            column_config = {}
            for day in range(1, days_in_month + 1):
                column_config[str(day)] = st.column_config.TextColumn(
                    str(day),
                    width="small",
                    help=f"يوم {day}"
                )
            
            st.dataframe(df[display_cols], use_container_width=True, hide_index=True, column_config=column_config)
            
            # زر نسخ الجدول
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("📋 نسخ الجدول", use_container_width=True):
                    df_to_copy = df[display_cols].to_csv(index=False)
                    st.code(df_to_copy)
                    st.success("✅ تم نسخ الجدول")
            
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
        
        emp_names = [f"{e['full_name']} ({e.get('emp_no', '')})" for e in employees]
        selected_emp_name = st.selectbox("👤 اختر الموظف", emp_names)
        selected_emp = employees[emp_names.index(selected_emp_name)]
        emp_id = str(selected_emp["id"])
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🖨️ عرض تقرير قابل للطباعة", use_container_width=True):
                show_printable_report(selected_emp, shifts, year, month, selected_center, selected_emp['full_name'])
                st.stop()
        
        st.markdown("---")
        
        # تبويبات التعديل
        edit_tabs = st.tabs(["👤 موظف واحد", "👥 فريق كامل", "📊 أنماط التناوب"])
        
        # ===== تبويب 1: موظف واحد =====
        with edit_tabs[0]:
            st.markdown(f"**تعديل مناوبات:** {selected_emp['full_name']}")
            emp_shifts = shifts_map.get(emp_id, {})
            
            edit_type = st.radio("نوع التعديل", ["يومي", "نطاق أيام"], horizontal=True)
            
            if edit_type == "يومي":
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    day = st.number_input("اليوم", 1, days_in_month, 1, key="single_day")
                with col2:
                    shift_options = [""] + list(SHIFT_TYPES.keys())
                    current_shift = emp_shifts.get(day, "")
                    current_index = shift_options.index(current_shift) if current_shift in shift_options else 0
                    new_shift = st.selectbox(
                        "المناوبة",
                        options=shift_options,
                        format_func=lambda x: "بدون مناوبة" if x == "" else f"{x} - {SHIFT_TYPES[x]['name']}",
                        index=current_index,
                        key="single_shift"
                    )
                with col3:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🗑️ حذف", key="delete_single", use_container_width=True):
                        date_str = f"{year}-{month:02d}-{day:02d}"
                        if ss.update_employee_shift(emp_id, date_str, "off"):
                            st.success(f"✅ تم حذف مناوبة يوم {day}")
                            # الحل الجذري
                            st.session_state.reload_shifts = True
                            st.rerun()
                
                if st.button("💾 حفظ التغيير", key="save_single", use_container_width=True, type="primary"):
                    if new_shift:
                        date_str = f"{year}-{month:02d}-{day:02d}"
                        if ss.update_employee_shift(emp_id, date_str, new_shift):
                            st.success(f"✅ تم تحديث يوم {day} إلى {new_shift}")
                            # الحل الجذري
                            st.session_state.reload_shifts = True
                            st.rerun()
            
            else:  # نطاق أيام
                col1, col2 = st.columns(2)
                with col1:
                    from_day = st.number_input("من يوم", 1, days_in_month, 1, key="range_from")
                with col2:
                    to_day = st.number_input("إلى يوم", from_day, days_in_month, from_day, key="range_to")
                
                shift_options = [""] + list(SHIFT_TYPES.keys())
                new_shift = st.selectbox(
                    "المناوبة",
                    options=shift_options,
                    format_func=lambda x: "بدون مناوبة" if x == "" else f"{x} - {SHIFT_TYPES[x]['name']}",
                    key="range_shift"
                )
                
                if st.button("💾 تطبيق على النطاق", key="save_range", use_container_width=True, type="primary"):
                    success_count = 0
                    for day in range(from_day, to_day + 1):
                        date_str = f"{year}-{month:02d}-{day:02d}"
                        shift_value = new_shift if new_shift else "off"
                        if ss.update_employee_shift(emp_id, date_str, shift_value):
                            success_count += 1
                    
                    st.success(f"✅ تم تحديث {success_count} يوم")
                    # الحل الجذري
                    st.session_state.reload_shifts = True
                    st.rerun()
        
        # ===== تبويب 2: فريق كامل =====
        with edit_tabs[1]:
            st.markdown("### 👥 جدولة فريق كامل")
            
            teams = {}
            for emp in employees:
                code = emp.get('emp_code', '')
                if code and code[0] in 'ABCD':
                    team = code[0]
                    if team not in teams:
                        teams[team] = []
                    teams[team].append(emp)
            
            if teams:
                team_options = [f"الفريق {team} ({len(members)} موظف)" for team, members in teams.items()]
                selected_team = st.selectbox("اختر الفريق", team_options)
                team_letter = list(teams.keys())[team_options.index(selected_team)]
                team_members = teams[team_letter]
                
                st.markdown("**أفراد الفريق:**")
                for member in team_members:
                    st.markdown(f"- {member['full_name']} ({member.get('emp_no', '')})")
                
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                with col1:
                    from_day = st.number_input("من يوم", 1, days_in_month, 1, key="team_from")
                with col2:
                    to_day = st.number_input("إلى يوم", from_day, days_in_month, from_day, key="team_to")
                
                team_shift = st.selectbox(
                    "المناوبة للفريق كامل",
                    options=[""] + list(SHIFT_TYPES.keys()),
                    format_func=lambda x: "بدون مناوبة" if x == "" else f"{x} - {SHIFT_TYPES[x]['name']}",
                    key="team_shift"
                )
                
                if st.button("✅ تطبيق على الفريق", key="apply_team", use_container_width=True, type="primary"):
                    success_count = 0
                    total = 0
                    for member in team_members:
                        for day in range(from_day, to_day + 1):
                            date_str = f"{year}-{month:02d}-{day:02d}"
                            shift_value = team_shift if team_shift else "off"
                            if ss.update_employee_shift(str(member["id"]), date_str, shift_value):
                                success_count += 1
                            total += 1
                    
                    st.success(f"✅ تم تحديث {success_count} مناوبة من أصل {total}")
                    # الحل الجذري
                    st.session_state.reload_shifts = True
                    st.rerun()
            else:
                st.info("لا توجد فرق واضحة في هذا المركز")
        
        # ===== تبويب 3: أنماط التناوب =====
        with edit_tabs[2]:
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
            
            if st.button("✅ تطبيق النمط على الموظف", use_container_width=True, type="primary"):
                success_count = 0
                for i, day in enumerate(range(start_day, days_in_month + 1)):
                    pattern_idx = (i) % len(pattern)
                    shift_type = pattern[pattern_idx]
                    if shift_type:
                        date_str = f"{year}-{month:02d}-{day:02d}"
                        if ss.update_employee_shift(emp_id, date_str, shift_type):
                            success_count += 1
                
                st.success(f"✅ تم تطبيق نمط {selected_pattern} على {success_count} يوم")
                # الحل الجذري
                st.session_state.reload_shifts = True
                st.rerun()
    
    # ===== وضع التكميل التلقائي =====
    elif view_mode == "🔄 تكميل الفرق":
        st.subheader("🔄 تكميل تلقائي للفرق")
        st.markdown("يقوم النظام بتحليل جدول المناوبات الحالي واقتراح تكميل للفرق حسب الأنماط")
        
        # استخراج الفرق
        teams_data = {}
        for emp in employees:
            code = emp.get('emp_code', '')
            if code and code[0] in 'ABCD':
                team = code[0]
                if team not in teams_data:
                    teams_data[team] = []
                teams_data[team].append(emp)
        
        if not teams_data:
            st.warning("⚠️ لا توجد فرق واضحة في هذا المركز")
            return
        
        # تحليل الوضع الحالي لكل فريق
        st.markdown("### 📊 تحليل الفرق")
        
        for team_letter, team_members in teams_data.items():
            with st.expander(f"الفريق {team_letter} - {len(team_members)} موظف"):
                
                # تحليل أيام الفريق
                team_shifts = {}
                for member in team_members:
                    emp_id = str(member["id"])
                    emp_shifts = shifts_map.get(emp_id, {})
                    team_shifts[member['full_name']] = emp_shifts
                
                # حساب التغطية لكل يوم
                coverage = {}
                for day in range(1, days_in_month + 1):
                    day_coverage = 0
                    day_details = []
                    for member in team_members:
                        emp_id = str(member["id"])
                        shift_type = shifts_map.get(emp_id, {}).get(day)
                        if shift_type:
                            day_coverage += 1
                            day_details.append(f"{member['full_name']}: {shift_type}")
                    coverage[day] = {
                        "count": day_coverage,
                        "total": len(team_members),
                        "details": day_details
                    }
                
                # عرض أيام النقص
                low_coverage_days = [day for day, data in coverage.items() if data["count"] < data["total"]]
                
                if low_coverage_days:
                    st.warning(f"⚠️ أيام بها نقص: {len(low_coverage_days)} يوم")
                    
                    # عرض أيام النقص في جدول
                    df_coverage = pd.DataFrame([
                        {
                            "اليوم": day,
                            "التغطية": f"{coverage[day]['count']}/{coverage[day]['total']}",
                            "النسبة": f"{int(coverage[day]['count']/coverage[day]['total']*100)}%"
                        }
                        for day in low_coverage_days[:10]
                    ])
                    st.dataframe(df_coverage, use_container_width=True, hide_index=True)
                    
                    # خيارات التكميل
                    st.markdown("#### 🛠️ خيارات التكميل")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        tkmilia_type = st.selectbox(
                            "نوع التكميل",
                            ["تكميلية صباحية (CP8)", "تكميلية يوم كامل (CP24)", "تكميلية ليلية (LN8)"],
                            key=f"tkmilia_type_{team_letter}"
                        )
                    with col2:
                        tkmilia_days = st.multiselect(
                            "اختر الأيام للتكميل",
                            low_coverage_days,
                            default=low_coverage_days[:3],
                            key=f"tkmilia_days_{team_letter}"
                        )
                    
                    # اقتراح الموظفين المتاحين
                    available_members = []
                    for member in team_members:
                        emp_id = str(member["id"])
                        member_shifts = shifts_map.get(emp_id, {})
                        # نشوف هل عنده أيام فاضية في الأيام المختارة
                        available_for_days = []
                        for day in tkmilia_days:
                            if day not in member_shifts:
                                available_for_days.append(day)
                        if available_for_days:
                            available_members.append({
                                "name": member['full_name'],
                                "id": member['id'],
                                "available_days": available_for_days
                            })
                    
                    if available_members:
                        st.markdown("**👥 الموظفون المتاحون للتكميل:**")
                        for am in available_members:
                            st.markdown(f"- {am['name']}: متاح لـ {len(am['available_days'])} يوم ({', '.join(map(str, am['available_days']))})")
                        
                        # تطبيق التكميل
                        if st.button(f"✅ تطبيق التكميل للفريق {team_letter}", key=f"apply_tkmilia_{team_letter}", use_container_width=True):
                            success_count = 0
                            
                            # تحويل نوع التكميل إلى رمز
                            tkmilia_map = {
                                "تكميلية صباحية (CP8)": "CP8",
                                "تكميلية يوم كامل (CP24)": "CP24",
                                "تكميلية ليلية (LN8)": "LN8"
                            }
                            tkmilia_code = tkmilia_map[tkmilia_type]
                            
                            # توزيع الأيام على الموظفين
                            days_assigned = set()
                            for day in tkmilia_days:
                                if day not in days_assigned:
                                    # نختار موظف متاح لهذا اليوم
                                    for am in available_members:
                                        if day in am['available_days'] and day not in days_assigned:
                                            date_str = f"{year}-{month:02d}-{day:02d}"
                                            if ss.update_employee_shift(str(am['id']), date_str, tkmilia_code):
                                                success_count += 1
                                                days_assigned.add(day)
                                                break
                            
                            if success_count > 0:
                                st.success(f"✅ تم إضافة {success_count} تكميلية للفريق {team_letter}")
                                # الحل الجذري
                                st.session_state.reload_shifts = True
                                st.rerun()
                else:
                    st.success(f"✅ الفريق {team_letter} مكتمل التغطية!")
        
        # ===== تكميل شامل للمركز =====
        st.markdown("---")
        st.markdown("### 🏥 تكميل شامل للمركز")
        
        if st.button("🔄 تشغيل التكميل الشامل للمركز", use_container_width=True, type="primary"):
            total_tkmilia = 0
            progress_bar = st.progress(0)
            
            all_days = list(range(1, days_in_month + 1))
            total_days = len(all_days)
            
            for day_idx, day in enumerate(all_days):
                # نشوف عدد الموظفين المناوبين في هذا اليوم
                day_workers = 0
                day_workers_list = []
                for emp in employees:
                    emp_id = str(emp["id"])
                    if shifts_map.get(emp_id, {}).get(day):
                        day_workers += 1
                        day_workers_list.append(emp)
                
                # إذا كان العدد قليل (أقل من 50%) نقترح تكميل
                if day_workers < len(employees) * 0.5:
                    # نبحث عن موظفين فاضيين في هذا اليوم
                    available_for_day = []
                    for emp in employees:
                        emp_id = str(emp["id"])
                        if day not in shifts_map.get(emp_id, {}):
                            available_for_day.append(emp)
                    
                    if available_for_day:
                        # نختار أول موظف متاح
                        emp_to_add = available_for_day[0]
                        date_str = f"{year}-{month:02d}-{day:02d}"
                        if ss.update_employee_shift(str(emp_to_add["id"]), date_str, "CP8"):
                            total_tkmilia += 1
                
                progress_bar.progress((day_idx + 1) / total_days)
            
            st.success(f"✅ تم إضافة {total_tkmilia} تكميلية للمركز")
            # الحل الجذري
            st.session_state.reload_shifts = True
            st.rerun()
    
    # ===== وضع الإضافة =====
    elif view_mode == "➕ إضافة":
        st.subheader("➕ إضافة مناوبة جديدة")
        
        with st.form("add_shift_form"):
            shift_date = st.date_input("📅 التاريخ", value=datetime(year, month, 1))
            shift_type = st.selectbox(
                "⏰ نوع المناوبة",
                options=list(SHIFT_TYPES.keys()),
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
                    # الحل الجذري
                    st.session_state.reload_shifts = True
                    st.rerun()
    
    # ===== وضع التوليد التلقائي =====
    elif view_mode == "⚡ توليد تلقائي":
        st.subheader("⚡ توليد مناوبات تلقائي للفرق")
        
        # استخراج الفرق
        teams_data = {}
        for emp in employees:
            code = emp.get('emp_code', '')
            if code and code[0] in 'ABCD':
                team = code[0]
                if team not in teams_data:
                    teams_data[team] = []
                teams_data[team].append(emp)
        
        if not teams_data:
            st.warning("⚠️ لا توجد فرق واضحة في هذا المركز")
            return
        
        col1, col2 = st.columns(2)
        with col1:
            team_options = [f"الفريق {team} ({len(members)} موظف)" for team, members in teams_data.items()]
            team_options.append("جميع الفرق")
            selected_team_display = st.selectbox("👥 اختر الفريق", team_options)
            
            if selected_team_display == "جميع الفرق":
                team_members = []
                for team in teams_data.values():
                    team_members.extend(team)
            else:
                team_letter = list(teams_data.keys())[team_options.index(selected_team_display)]
                team_members = teams_data[team_letter]
        
        with col2:
            generation_patterns = {
                "نظام 5 أيام عمل + 2 إجازة (صباحي)": {
                    "pattern": ["D8", "D8", "D8", "D8", "D8", "", ""],
                    "description": "أحد - خميس صباحي، جمعة - سبت إجازة"
                },
                "نظام 5 أيام عمل + 2 إجازة (ليلي)": {
                    "pattern": ["N8", "N8", "N8", "N8", "N8", "", ""],
                    "description": "أحد - خميس ليلي، جمعة - سبت إجازة"
                },
                "نظام 2+2+4": {
                    "pattern": ["D12", "D12", "N12", "N12", "", "", "", ""],
                    "description": "2 صباحي، 2 ليلي، 4 إجازة"
                },
                "نظام 3+3+3": {
                    "pattern": ["D12", "D12", "D12", "N12", "N12", "N12", "", "", ""],
                    "description": "3 صباحي، 3 ليلي، 3 إجازة"
                },
                "نظام تداخلي": {
                    "pattern": ["O8", "O8", ""],
                    "description": "2 تداخلي، 1 إجازة"
                },
                "نظام نهاية أسبوع": {
                    "pattern": ["D8", "D8", "N8", "N8", "", "", ""],
                    "description": "أحد-اثنين صباحي، ثلاثاء-أربعاء ليلي، خميس-سبت إجازة"
                }
            }
            
            selected_pattern = st.selectbox("📊 اختر نمط التناوب", list(generation_patterns.keys()))
            pattern_info = generation_patterns[selected_pattern]
            st.caption(f"📝 {pattern_info['description']}")
            
            pattern = pattern_info["pattern"]
            st.markdown("**نمط الدورة:**")
            pattern_cols = st.columns(len(pattern))
            for i, p in enumerate(pattern):
                with pattern_cols[i]:
                    if p:
                        info = SHIFT_TYPES.get(p, {})
                        bg_color = info.get('color', '#E0E0E0')
                        st.markdown(f"<div style='background:{bg_color}; color:black; padding:0.3rem; border-radius:5px; text-align:center;'>{p}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='background:#E0E0E0; padding:0.3rem; border-radius:5px; text-align:center;'>إجازة</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            start_day = st.number_input("📅 بدء من يوم", 1, days_in_month, 1)
        with col2:
            rotation = st.selectbox("🔄 خيار التطبيق", ["نفس البداية للكل", "تدوير البداية"])
        with col3:
            ignore_weekends = st.checkbox("🚫 تجاهل عطل نهاية الأسبوع (جمعة/سبت)")
        
        st.markdown("---")
        st.markdown(f"**👥 الموظفون المشمولون ({len(team_members)}):**")
        
        with st.expander("عرض قائمة الموظفين"):
            for member in team_members:
                st.markdown(f"- {member['full_name']} ({member.get('emp_no', '')})")
        
        col1, col2 = st.columns([3, 1])
        with col2:
            generate_btn = st.button("⚡ توليد المناوبات", use_container_width=True, type="primary")
        
        if generate_btn:
            if not team_members:
                st.error("❌ لا يوجد موظفون في الفريق المحدد")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                total_updates = 0
                total_members = len(team_members)
                
                for member_idx, member in enumerate(team_members):
                    status_text.text(f"جاري توليد مناوبات {member['full_name']}...")
                    
                    if rotation == "تدوير البداية":
                        member_start = start_day + member_idx
                        if member_start > days_in_month:
                            member_start = ((member_start - 1) % days_in_month) + 1
                    else:
                        member_start = start_day
                    
                    day = member_start
                    pattern_idx = 0
                    
                    while day <= days_in_month:
                        # تجاهل عطل نهاية الأسبوع
                        if ignore_weekends:
                            current_date = datetime(year, month, day)
                            if current_date.weekday() in [4, 5]:  # جمعة = 4, سبت = 5
                                day += 1
                                continue
                        
                        shift_type = pattern[pattern_idx % len(pattern)]
                        if shift_type:
                            date_str = f"{year}-{month:02d}-{day:02d}"
                            if ss.update_employee_shift(str(member["id"]), date_str, shift_type):
                                total_updates += 1
                        day += 1
                        pattern_idx += 1
                    
                    progress_bar.progress((member_idx + 1) / total_members)
                
                status_text.text("")
                st.success(f"✅ تم توليد {total_updates} مناوبة لـ {total_members} موظف")
                st.balloons()
                
                if st.button("🔄 تحديث وعرض الجدول", use_container_width=True):
                    st.cache_data.clear()
                    st.rerun()