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

# ===== دوال الحفظ في session_state =====
def _get_saved_attendance(center_id, selected_date):
    """استرجاع البيانات المحفوظة من session_state"""
    key = f"attendance_{center_id}_{selected_date}"
    return st.session_state.get(key, None)

def _save_attendance_to_session(center_id, selected_date, data, delegator, substitute, notes):
    """حفظ البيانات في session_state"""
    key = f"attendance_{center_id}_{selected_date}"
    st.session_state[key] = {
        "data": data,
        "delegator": delegator,
        "substitute": substitute,
        "notes": notes,
        "saved_at": datetime.now().isoformat()
    }

def show_attendance():
    """صفحة التكميل الذكي - مع حفظ البيانات في session_state"""
    
    # التحقق من حالة الطباعة أولاً
    if st.session_state.get("print_page", False):
        try:
            from pages.print_attendance import show_print_attendance
            show_print_attendance(
                st.session_state.print_data,
                st.session_state.print_center,
                st.session_state.print_date.strftime("%Y-%m-%d")
            )
        except Exception as e:
            st.error(f"⚠️ خطأ في تحميل صفحة الطباعة: {e}")
            st.session_state.print_page = False
            st.rerun()
        return
    
    page_header("📋 التكميل الذكي", "تسجيل الحضور مع حفظ تلقائي", "📝")
    
    from utils.supabase_storage import SupabaseStorage
    storage = SupabaseStorage()
    
    # تبويبات
    tabs = st.tabs(["📝 تسجيل التكميل", "📜 تاريخ التكميل"])
    
    # ===== تبويب تسجيل التكميل =====
    with tabs[0]:
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
        
        # ===== فلترة الموظفين: نحذف اللي في إجازة =====
        active_employees = []
        for emp in employees:
            emp_id = str(emp["id"])
            shift_type = planned_map.get(emp_id, "off")
            if shift_type != "off":  # فقط الموظفين اللي عندهم مناوبة (مو إجازة)
                active_employees.append(emp)
        
        if not active_employees:
            st.info("ℹ️ لا يوجد موظفون على رأس العمل لهذا اليوم (الكل في إجازة)")
            return
        
        st.success(f"✅ عدد الموظفين المطلوب حضورهم: {len(active_employees)}")
        
        # ===== استرجاع البيانات المحفوظة إذا وجدت =====
        saved_data = _get_saved_attendance(center_id, selected_date)
        if saved_data:
            st.info("📋 تم تحميل تكميل سابق لهذا اليوم")
        
        # ===== نموذج التكميل =====
        st.markdown("---")
        st.markdown("### 📝 تسجيل الحضور")
        
        attendance_data = []
        
        for emp in active_employees:
            emp_id = str(emp["id"])
            planned_shift = planned_map.get(emp_id, "off")
            planned_info = SHIFT_TYPES.get(planned_shift, SHIFT_TYPES["off"])
            
            # البحث عن بيانات محفوظة لهذا الموظف
            saved_emp_data = None
            if saved_data and "data" in saved_data:
                saved_emp_data = next((item for item in saved_data["data"] if item["employee_id"] == emp_id), None)
            
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
                    # نوع المناوبة الفعلية (مع استرجاع القيمة المحفوظة)
                    default_shift_index = list(SHIFT_TYPES.keys()).index(planned_shift) if planned_shift in SHIFT_TYPES else 0
                    if saved_emp_data and saved_emp_data.get("actual_shift"):
                        try:
                            default_shift_index = list(SHIFT_TYPES.keys()).index(saved_emp_data["actual_shift"])
                        except:
                            pass
                    
                    actual_shift = st.selectbox(
                        "المناوبة الفعلية",
                        options=list(SHIFT_TYPES.keys()),
                        format_func=lambda x: f"{SHIFT_TYPES[x]['icon']} {SHIFT_TYPES[x]['name']}",
                        index=default_shift_index,
                        key=f"shift_{emp_id}"
                    )
                
                with col2:
                    # الحالة (مع استرجاع القيمة المحفوظة)
                    default_status = saved_emp_data.get("status", "حاضر") if saved_emp_data else "حاضر"
                    status_options = ["حاضر", "غائب", "متأخر", "مهمة رسمية"]
                    default_status_index = status_options.index(default_status) if default_status in status_options else 0
                    
                    status = st.selectbox(
                        "الحالة",
                        status_options,
                        index=default_status_index,
                        key=f"status_{emp_id}"
                    )
                
                with col3:
                    # وقت الحضور الفعلي (مع استرجاع القيمة المحفوظة)
                    default_start = safe_time(saved_emp_data.get("actual_start", planned_info['start']) if saved_emp_data else planned_info['start'])
                    actual_start = st.time_input(
                        "⏰ وقت الحضور",
                        value=default_start,
                        key=f"start_{emp_id}"
                    )
                
                with col4:
                    # وقت الانصراف الفعلي (مع استرجاع القيمة المحفوظة)
                    default_end = safe_time(saved_emp_data.get("actual_end", planned_info['end']) if saved_emp_data else planned_info['end'])
                    actual_end = st.time_input(
                        "🕒 وقت الانصراف",
                        value=default_end,
                        key=f"end_{emp_id}"
                    )
                
                with col5:
                    # وقت التأخير (يظهر فقط إذا كان متأخر)
                    if status == "متأخر":
                        default_late = time(8, 15)
                        if saved_emp_data and saved_emp_data.get("late_time"):
                            try:
                                default_late = datetime.strptime(saved_emp_data["late_time"], "%H:%M").time()
                            except:
                                pass
                        late_time = st.time_input(
                            "⏱️ وقت التأخير",
                            value=default_late,
                            key=f"late_{emp_id}"
                        )
                    else:
                        late_time = None
                        st.markdown("—")
                
                attendance_data.append({
                    "employee_id": emp_id,
                    "employee_name": emp['full_name'],
                    "emp_no": emp.get('emp_no', ''),
                    "planned_shift": planned_info['name'],
                    "planned_start": planned_info['start'],
                    "planned_end": planned_info['end'],
                    "actual_shift": actual_shift,
                    "status": status,
                    "actual_start": actual_start.strftime("%H:%M") if actual_start else "",
                    "actual_end": actual_end.strftime("%H:%M") if actual_end else "",
                    "late_time": late_time.strftime("%H:%M") if late_time else ""
                })
                
                st.markdown("---")
        
        # ===== التوكيل والبديل (مع استرجاع القيم المحفوظة) =====
        st.markdown("### 🔄 التوكيل والبديل")
        
        emp_options = [f"{e['full_name']} ({e.get('emp_no', '')})" for e in active_employees]
        
        # القيم المحفوظة للتوكيل
        saved_delegator = saved_data.get("delegator", "لا يوجد") if saved_data else "لا يوجد"
        saved_substitute = saved_data.get("substitute", "لا يوجد") if saved_data else "لا يوجد"
        saved_notes = saved_data.get("notes", "") if saved_data else ""
        
        col1, col2 = st.columns(2)
        
        with col1:
            delegator_options = ["لا يوجد"] + emp_options
            delegator_index = 0
            if saved_delegator in delegator_options:
                delegator_index = delegator_options.index(saved_delegator)
            delegator = st.selectbox("👤 الموكل (الموظف الأساسي)", delegator_options, index=delegator_index)
        
        with col2:
            substitute_options = ["لا يوجد"] + emp_options
            substitute_index = 0
            if saved_substitute in substitute_options:
                substitute_index = substitute_options.index(saved_substitute)
            substitute = st.selectbox("🔄 البديل", substitute_options, index=substitute_index)
        
        notes = st.text_area("📝 ملاحظات", value=saved_notes, placeholder="أي ملاحظات إضافية...")
        
        # ===== أزرار التحكم =====
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 حفظ التكميل", type="primary", use_container_width=True):
                # حفظ في session_state
                _save_attendance_to_session(center_id, selected_date, attendance_data, delegator, substitute, notes)
                st.success("✅ تم حفظ التكميل محلياً")
                
                # رفع التقرير إلى Supabase
                with st.spinner("جاري رفع التقرير إلى التخزين السحابي..."):
                    upload_result = storage.upload_attendance_report(
                        attendance_data, 
                        selected_center, 
                        selected_date
                    )
                
                if upload_result and upload_result.get("success"):
                    st.info(f"📤 تم حفظ التقرير في التخزين السحابي")
                    if upload_result.get("url"):
                        st.markdown(f"🔗 [رابط التقرير]({upload_result['url']})")
                
                # عرض التقرير النهائي
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
                        "مهمة رسمية": "🟠"
                    }.get(item['status'], "⚪")
                    
                    # حساب التأخير
                    late_info = item['late_time'] if item['late_time'] else ""
                    
                    report_data.append({
                        "الموظف": item['employee_name'],
                        "المخطط": item['planned_shift'],
                        "الفعلية": actual_info['name'],
                        "الحالة": f"{status_color} {item['status']}",
                        "الحضور": item['actual_start'],
                        "الانصراف": item['actual_end'],
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
        
        with col2:
            # زر تحديث الصفحة
            if st.button("🔄 تحديث الصفحة", use_container_width=True):
                st.rerun()
        
        with col3:
            # زر طباعة التقرير
            if st.button("🖨️ طباعة التقرير", use_container_width=True):
                # تجهيز بيانات الطباعة
                print_data = []
                for item in attendance_data:
                    emp = next((e for e in active_employees if str(e["id"]) == item["employee_id"]), {})
                    actual_info = SHIFT_TYPES.get(item['actual_shift'], SHIFT_TYPES["off"])
                    print_data.append({
                        "emp_no": item.get("emp_no", ""),
                        "employee_name": item["employee_name"],
                        "status": item["status"],
                        "planned_shift": item["planned_shift"],
                        "actual_shift_name": actual_info['name'],
                        "planned_start": item["planned_start"],
                        "planned_end": item["planned_end"],
                        "actual_start": item["actual_start"],
                        "actual_end": item["actual_end"],
                        "late_time": item["late_time"],
                        "notes": notes if notes else ""
                    })
                
                # تخزين البيانات في session_state
                st.session_state.print_data = print_data
                st.session_state.print_center = selected_center
                st.session_state.print_date = selected_date
                st.session_state.print_page = True
                st.rerun()
    
    # ===== تبويب تاريخ التكميل =====
    with tabs[1]:
        st.subheader("📜 تاريخ التكميل اليومي")
        
        # فلترة حسب المركز
        all_centers = cs.get_centers() or []
        center_names = ["الكل"] + [c["name"] for c in all_centers]
        filter_center = st.selectbox("🏥 تصفية حسب المركز", center_names)
        
        # جلب التاريخ
        with st.spinner("جاري تحميل التاريخ..."):
            if filter_center == "الكل":
                history = storage.get_attendance_history()
            else:
                history = storage.get_attendance_history(center_name=filter_center)
        
        if history:
            # تحويل إلى DataFrame
            df_history = pd.DataFrame(history)
            
            # تنسيق الأعمدة
            df_history['report_date'] = pd.to_datetime(df_history['report_date']).dt.strftime('%Y-%m-%d')
            df_history['created_at'] = pd.to_datetime(df_history['created_at']).dt.strftime('%Y-%m-%d %H:%M')
            
            # إعادة تسمية الأعمدة
            df_history = df_history.rename(columns={
                'center_name': 'المركز',
                'report_date': 'التاريخ',
                'total_employees': 'الإجمالي',
                'present': 'حاضر',
                'absent': 'غائب',
                'late': 'متأخر',
                'created_by': 'بواسطة',
                'created_at': 'تاريخ الرفع'
            })
            
            st.dataframe(df_history[['المركز', 'التاريخ', 'الإجمالي', 'حاضر', 'غائب', 'متأخر', 'تاريخ الرفع']], 
                        use_container_width=True, hide_index=True)
            
            # عرض الروابط
            st.markdown("### 🔗 روابط التقارير")
            for idx, row in history[:5].iterrows():  # آخر 5 تقارير
                with st.container():
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        st.write(f"**{row['center_name']}**")
                    with col2:
                        st.write(f"{row['report_date']}")
                    with col3:
                        if row.get('file_url'):
                            st.link_button("📥 عرض", row['file_url'])
                    st.divider()
        else:
            st.info("لا توجد تقارير مرفوعة بعد")