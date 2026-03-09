# frontend/pages/attendance.py
import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta
from utils.helpers import page_header
import hashlib
import json
import os

# دالة مساعدة للوقت الآمن
def safe_time(time_str, default="08:00"):
    """تحويل النص إلى وقت بأمان"""
    if time_str == "--:--" or not time_str:
        return datetime.strptime(default, "%H:%M").time()
    try:
        return datetime.strptime(time_str, "%H:%M").time()
    except:
        return datetime.strptime(default, "%H:%M").time()

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
    """تهيئة الخ services"""
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

def _get_user_session_key():
    """مفتاح فريد لكل مستخدم وجهاز"""
    user = st.session_state.get("username", "guest")
    device = hashlib.md5(str(st.session_state.get("session_id", "")).encode()).hexdigest()[:8]
    return f"{user}_{device}"

def _save_attendance_permanent(data):
    """حفظ في ملف JSON محلي"""
    try:
        filename = f"attendance_data_{_get_user_session_key()}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def _load_attendance_permanent():
    """تحميل من ملف JSON"""
    try:
        filename = f"attendance_data_{_get_user_session_key()}.json"
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}

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
    """صفحة التكميل - مع كل الميزات"""
    
    # التحقق من حالة الطباعة
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
    
    page_header("📋 التكميل الذكي", "تسجيل الحضور مع حفظ دائم", "📝")
    
    # استبدال Supabase بـ LocalStorage
    from utils.local_storage import LocalStorage
    storage = LocalStorage()
    
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
        
        # اختيار التاريخ والمركز
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
        
        # جلب المناوبات المخطط لها
        with st.spinner("جاري تحميل المناوبات..."):
            planned_shifts = ss.get_shifts_by_date(center_id, selected_date)
        
        # خريطة المناوبات
        planned_map = {}
        for shift in planned_shifts:
            for assignment in shift.get("assignments", []):
                emp_id = assignment.get("employee_id")
                if emp_id:
                    planned_map[emp_id] = shift.get("shift_type", "off")
        
        # فلترة الموظفين
        active_employees = []
        for emp in employees:
            emp_id = str(emp["id"])
            shift_type = planned_map.get(emp_id, "off")
            if shift_type != "off":
                active_employees.append(emp)
        
        if not active_employees:
            st.info("ℹ️ لا يوجد موظفون على رأس العمل لهذا اليوم")
            return
        
        st.success(f"✅ عدد الموظفين: {len(active_employees)}")
        
        # استرجاع البيانات المحفوظة
        saved_data = _get_saved_attendance(center_id, selected_date)
        permanent_data = _load_attendance_permanent()
        day_key = f"{selected_date}_{selected_center}"
        permanent_day = permanent_data.get(day_key, {})
        
        if saved_data or permanent_day:
            st.info("📋 تم تحميل تكميل سابق")
        
        # نموذج التكميل - داخل الـ Form
        with st.form("attendance_form"):
            attendance_data = []
            
            for emp in active_employees:
                emp_id = str(emp["id"])
                planned_shift = planned_map.get(emp_id, "off")
                planned_info = SHIFT_TYPES.get(planned_shift, SHIFT_TYPES["off"])
                
                # بحث عن بيانات محفوظة
                saved_emp_data = None
                if saved_data and "data" in saved_data:
                    saved_emp_data = next((item for item in saved_data["data"] if item["employee_id"] == emp_id), None)
                
                emp_key = f"{day_key}_{emp['emp_no']}"
                permanent_emp = permanent_day.get(emp_key, {})
                
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
                    
                    # بيانات الحضور
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        # نوع المناوبة الفعلية
                        default_shift_index = list(SHIFT_TYPES.keys()).index(planned_shift) if planned_shift in SHIFT_TYPES else 0
                        if saved_emp_data and saved_emp_data.get("actual_shift"):
                            try:
                                default_shift_index = list(SHIFT_TYPES.keys()).index(saved_emp_data["actual_shift"])
                            except:
                                pass
                        elif permanent_emp.get("actual_shift"):
                            try:
                                default_shift_index = list(SHIFT_TYPES.keys()).index(permanent_emp["actual_shift"])
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
                        # الحالة
                        default_status = "حاضر"
                        if saved_emp_data and saved_emp_data.get("status"):
                            default_status = saved_emp_data["status"]
                        elif permanent_emp.get("status"):
                            default_status = permanent_emp["status"]
                        
                        status_options = ["حاضر", "غائب", "متأخر", "مهمة رسمية", "إجازة"]
                        default_status_index = status_options.index(default_status) if default_status in status_options else 0
                        
                        status = st.selectbox(
                            "الحالة",
                            status_options,
                            index=default_status_index,
                            key=f"status_{emp_id}"
                        )
                    
                    with col3:
                        # وقت الحضور
                        default_start = safe_time(planned_info['start'])
                        if saved_emp_data and saved_emp_data.get("actual_start"):
                            default_start = safe_time(saved_emp_data["actual_start"])
                        elif permanent_emp.get("check_in"):
                            default_start = safe_time(permanent_emp["check_in"])
                        
                        actual_start = st.time_input(
                            "⏰ وقت الحضور",
                            value=default_start,
                            key=f"start_{emp_id}"
                        )
                    
                    with col4:
                        # وقت الانصراف
                        default_end = safe_time(planned_info['end'])
                        if saved_emp_data and saved_emp_data.get("actual_end"):
                            default_end = safe_time(saved_emp_data["actual_end"])
                        elif permanent_emp.get("check_out"):
                            default_end = safe_time(permanent_emp["check_out"])
                        
                        actual_end = st.time_input(
                            "🕒 وقت الانصراف",
                            value=default_end,
                            key=f"end_{emp_id}"
                        )
                    
                    with col5:
                        # وقت التأخير
                        if status == "متأخر":
                            default_late = time(8, 15)
                            if saved_emp_data and saved_emp_data.get("late_time"):
                                try:
                                    default_late = datetime.strptime(saved_emp_data["late_time"], "%H:%M").time()
                                except:
                                    pass
                            elif permanent_emp.get("late_time"):
                                try:
                                    default_late = datetime.strptime(permanent_emp["late_time"], "%H:%M").time()
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
            
            # التوكيل والبديل
            st.markdown("### 🔄 التوكيل والبديل")
            
            emp_options = [f"{e['full_name']} ({e.get('emp_no', '')})" for e in active_employees]
            
            saved_delegator = "لا يوجد"
            saved_substitute = "لا يوجد"
            saved_notes = ""
            
            if saved_data:
                saved_delegator = saved_data.get("delegator", "لا يوجد")
                saved_substitute = saved_data.get("substitute", "لا يوجد")
                saved_notes = saved_data.get("notes", "")
            elif permanent_day:
                saved_delegator = permanent_day.get("delegator", "لا يوجد")
                saved_substitute = permanent_day.get("substitute", "لا يوجد")
                saved_notes = permanent_day.get("notes", "")
            
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
            
            # زر الحفظ داخل الـ Form
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                submitted = st.form_submit_button("💾 حفظ", type="primary", use_container_width=True)
            
            if submitted:
                # حفظ في session_state
                _save_attendance_to_session(center_id, selected_date, attendance_data, delegator, substitute, notes)
                
                # حفظ في ملف JSON
                day_data = {}
                for item in attendance_data:
                    emp_key = f"{day_key}_{item['emp_no']}"
                    day_data[emp_key] = {
                        "status": item['status'],
                        "check_in": item['actual_start'],
                        "check_out": item['actual_end'],
                        "late_time": item['late_time'],
                        "actual_shift": item['actual_shift']
                    }
                day_data["delegator"] = delegator
                day_data["substitute"] = substitute
                day_data["notes"] = notes
                
                permanent_data[day_key] = day_data
                _save_attendance_permanent(permanent_data)
                
                # حفظ محلياً (بدون Supabase)
                with st.spinner("جاري حفظ التقرير..."):
                    upload_result = storage.save_attendance_report(
                        attendance_data, 
                        selected_center, 
                        selected_date
                    )
                
                if upload_result and upload_result.get("success"):
                    st.info(f"📤 تم حفظ التقرير محلياً")
                
                st.success("✅ تم الحفظ بنجاح")
                st.balloons()
        
        # أزرار خارج الـ Form
        col1, col2, col3, col4 = st.columns(4)
        
        with col2:
            if st.button("🖨️ طباعة", use_container_width=True):
                # تجهيز بيانات الطباعة
                print_data = []
                for item in attendance_data:
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
                
                st.session_state.print_data = print_data
                st.session_state.print_center = selected_center
                st.session_state.print_date = selected_date
                st.session_state.print_page = True
                st.rerun()
        
        with col3:
            if st.button("🔄 تحديث", use_container_width=True):
                st.rerun()
        
        with col4:
            if st.button("❌ إلغاء", use_container_width=True):
                st.session_state.print_page = False
                st.rerun()
    
    # ===== تبويب تاريخ التكميل (نسخة محسنة) =====
    with tabs[1]:
        st.subheader("📜 أرشيف التكميل اليومي")
        
        # ─── شريط البحث والفلترة ───
        with st.expander("🔍 خيارات البحث المتقدم", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # فلترة حسب المركز
                all_centers = cs.get_centers() or []
                center_names = ["📋 الكل"] + [c["name"] for c in all_centers]
                filter_center = st.selectbox("🏥 المركز", center_names, key="history_center")
                if filter_center == "📋 الكل":
                    filter_center = None
            
            with col2:
                # فلترة حسب التاريخ
                today = date.today()
                date_options = {
                    "📅 اليوم": today,
                    "📆 هذا الأسبوع": today - timedelta(days=7),
                    "📅 هذا الشهر": today - timedelta(days=30),
                    "🗓️ هذا العام": today - timedelta(days=365),
                    "🎯 تاريخ محدد": None
                }
                filter_date_range = st.selectbox("📆 الفترة", list(date_options.keys()), key="history_date_range")
                
                if filter_date_range == "🎯 تاريخ محدد":
                    filter_date = st.date_input("اختر التاريخ", value=today, key="history_specific_date")
                else:
                    filter_date = date_options[filter_date_range]
            
            with col3:
                # بحث نصي
                search_text = st.text_input("🔎 بحث في التقارير", placeholder="اسم الموظف، ملاحظات...", key="history_search")
        
        # ─── جلب التاريخ من LocalStorage ───
        with st.spinner("📂 جاري تحميل الأرشيف..."):
            history = storage.get_attendance_history()
        
        if history:
            # تحويل إلى DataFrame للتصفية
            df_history = pd.DataFrame(history)
            df_history['report_date'] = pd.to_datetime(df_history['report_date'])
            
            # تطبيق الفلاتر
            filtered_df = df_history.copy()
            
            # فلترة حسب المركز
            if filter_center:
                filtered_df = filtered_df[filtered_df['center_name'] == filter_center]
            
            # فلترة حسب التاريخ
            if filter_date and filter_date_range != "🎯 تاريخ محدد":
                filtered_df = filtered_df[filtered_df['report_date'] >= pd.Timestamp(filter_date)]
            
            # فلترة حسب البحث النصي
            if search_text:
                mask = filtered_df['center_name'].str.contains(search_text, case=False, na=False) | \
                       filtered_df['file_path'].str.contains(search_text, case=False, na=False)
                filtered_df = filtered_df[mask]
            
            # إحصائيات سريعة
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("📊 إجمالي التقارير", len(filtered_df))
            col2.metric("🏥 مراكز", filtered_df['center_name'].nunique())
            col3.metric("📅 أيام", filtered_df['report_date'].dt.date.nunique())
            col4.metric("🕒 آخر تحديث", filtered_df['timestamp'].max() if not filtered_df.empty else "—")
            
            st.markdown("---")
            
            if not filtered_df.empty:
                # عرض التقارير في بطاقات
                for idx, row in filtered_df.sort_values('report_date', ascending=False).iterrows():
                    with st.container():
                        # تحديد لون البطاقة حسب التاريخ
                        is_today = row['report_date'].date() == date.today()
                        bg_color = "#FFF9E6" if is_today else "white"
                        border_color = "#CE2E26" if is_today else "#E2E8F0"
                        
                        col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1, 1, 1])
                        
                        with col1:
                            st.markdown(f"""
                            <div style="
                                background: {bg_color};
                                padding: 0.8rem;
                                border-radius: 8px;
                                border-right: 3px solid {border_color};
                            ">
                                <strong>🏥 {row['center_name']}</strong><br>
                                <span style="color: #64748B; font-size: 0.8rem;">
                                    📅 {row['report_date'].strftime('%Y-%m-%d')}
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown(f"""
                            <div style="padding: 0.8rem;">
                                <span style="color: #475569;">⏱️ {row['timestamp']}</span>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col3:
                            if st.button("👁️ عرض", key=f"view_{idx}", use_container_width=True):
                                # تجهيز بيانات للعرض
                                st.session_state.preview_report = {
                                    "center": row['center_name'],
                                    "date": row['report_date'].strftime('%Y-%m-%d'),
                                    "file": row['file_path']
                                }
                                st.info("📄 جاري تجهيز التقرير...")
                        
                        with col4:
                            if st.button("🖨️ طباعة", key=f"print_{idx}", use_container_width=True):
                                # محاولة قراءة الملف
                                try:
                                    if os.path.exists(row['file_path']):
                                        df = pd.read_csv(row['file_path'])
                                        st.dataframe(df)
                                    else:
                                        st.warning("⚠️ ملف التقرير غير موجود")
                                except:
                                    st.warning("⚠️ لا يمكن قراءة الملف")
                        
                        with col5:
                            if st.button("📥 CSV", key=f"csv_{idx}", use_container_width=True):
                                try:
                                    if os.path.exists(row['file_path']):
                                        with open(row['file_path'], 'rb') as f:
                                            st.download_button(
                                                "تحميل",
                                                data=f,
                                                file_name=f"تقرير_{row['center_name']}_{row['report_date'].strftime('%Y%m%d')}.csv",
                                                mime="text/csv",
                                                key=f"download_{idx}"
                                            )
                                except:
                                    st.warning("⚠️ الملف غير متوفر")
                        
                        st.markdown("---")
                
                # زر تصدير كل النتائج
                if st.button("📥 تصدير كل النتائج كـ CSV", use_container_width=True):
                    csv = filtered_df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        "تحميل",
                        data=csv,
                        file_name=f"تقرير_التكميل_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            else:
                st.info("ℹ️ لا توجد تقارير تطابق بحثك")
        else:
            st.info("📭 لا توجد تقارير محفوظة بعد")
            
            # زر تجريبي لإضافة تقرير تجريبي
            if st.button("➕ إضافة تقرير تجريبي", use_container_width=True):
                demo_data = [{
                    "center_name": "مركز الحائر",
                    "report_date": date.today().strftime("%Y-%m-%d"),
                    "file_path": "/opt/reports/attendance/demo.csv",
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                }]
                st.session_state.attendance_history = demo_data
                st.rerun()