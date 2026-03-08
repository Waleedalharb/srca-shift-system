# frontend/pages/employees.py
import streamlit as st
import pandas as pd
from datetime import datetime
from utils.helpers import page_header, section_title

# ─── أنواع الموظفين (محدث من ملف Excel) ─────────────────────────────────────
EMP_TYPE_LABELS = {
    # القيادات
    "chief_paramedic": "كبير مسعفين",
    "assistant_chief": "مساعد كبير مسعفين",
    "field_leader": "قيادة ميدانية",
    
    # العمليات
    "operations_control": "تحكم عملياتي",
    "response_coordinator": "تنسيق استجابة",
    
    # الطواقم الإسعافية
    "paramedic": "أخصائي اسعاف",
    "emt": "فني اسعاف",
    "health_assistant": "مساعد صحي",
    
    # الدعم
    "logistic_support": "دعم لوجستي",
    "admin": "إداري"
}

EMP_TYPE_COLORS = {
    # القيادات
    "chief_paramedic": "#CE2E26",      # أحمر
    "assistant_chief": "#B71C1C",      # أحمر غامق
    "field_leader": "#3B4A82",         # كحلي
    
    # العمليات
    "operations_control": "#45CFEF",   # أزرق فاتح
    "response_coordinator": "#513A87", # بنفسجي
    
    # الطواقم الإسعافية
    "paramedic": "#42924B",            # أخضر
    "emt": "#F1B944",                  # ذهبي
    "health_assistant": "#FF7C10",     # برتقالي
    
    # الدعم
    "logistic_support": "#64748B",     # رمادي
    "admin": "#475569"                  # رمادي غامق
}

# دالة لتحويل النص من Excel إلى المفتاح الصحيح
def get_employee_type_key(job_title):
    """تحويل المسمى الوظيفي من Excel إلى المفتاح الداخلي"""
    job_title = str(job_title).strip()
    
    mapping = {
        "كبير مسعفين": "chief_paramedic",
        "مساعد كبير مسعفين": "assistant_chief",
        "تحكم عملياتي": "operations_control",
        "تنسيق استجابة": "response_coordinator",
        "أخصائي اسعاف": "paramedic",
        "فني اسعاف": "emt",
        "مساعد صحي": "health_assistant",
        "دعم لوجستي": "logistic_support",
        "إداري": "admin"
    }
    
    for key, value in mapping.items():
        if key in job_title:
            return value
    return "admin"  # افتراضي

# ─── دوال التحقق من الصلاحية ─────────────────────────────────────────────────
def has_permission(required_role):
    """التحقق من صلاحية المستخدم"""
    user_role = st.session_state.get("user_role", "emt")
    
    # صلاحيات كل دور
    permissions = {
        "chief_paramedic": ["view_all", "manage_all", "approve_all"],
        "assistant_chief": ["view_all", "manage_all"],
        "field_leader": ["view_station", "manage_station", "approve_station"],
        "operations_supervisor": ["view_all", "manage_shifts"],
        "operations_control": ["view_all"],
        "response_coordinator": ["view_all"],
        "paramedic": ["view_self", "request_leave"],
        "emt": ["view_self", "request_leave"],
        "health_assistant": ["view_self", "request_leave"],
        "logistic_support": ["view_all"],
        "admin": ["view_all", "manage_employees"]
    }
    
    return required_role in permissions.get(user_role, [])

def get_user_center():
    """الحصول على مركز المستخدم الحالي"""
    return st.session_state.get("user_center_id")

def get_user_employee_id():
    """الحصول على معرف الموظف للمستخدم الحالي"""
    return st.session_state.get("user_employee_id")

# ─── دالة التحهيز ─────────────────────────────────────────────────────────────
def _get_services():
    auth = st.session_state.auth_service
    
    es = st.session_state.get("employee_service")
    cs = st.session_state.get("center_service")
    
    if not es:
        from services.employee_service import EmployeeService
        from services.center_service import CenterService
        es = EmployeeService(auth)
        cs = CenterService(auth)
        st.session_state.employee_service = es
        st.session_state.center_service = cs
    
    return es, cs

# ─── بطاقة موظف ───────────────────────────────────────────────────────────────
def employee_card(emp):
    """بطاقة موظف - تصميم نظيف مع التصنيفات الجديدة"""
    
    # تحديد النوع بالعربية
    emp_type = EMP_TYPE_LABELS.get(emp.get('employee_type', 'admin'), "إداري")
    emp_color = EMP_TYPE_COLORS.get(emp.get('employee_type', 'admin'), "#475569")
    
    # الحالة
    status = "🟢 نشط" if emp.get('is_active', True) else "🔴 غير نشط"
    on_duty = "🚑 على رأس العمل" if emp.get('is_on_duty') else "⏸️ في الإجازة"
    
    st.markdown(f"""
    <div style="
        background: white;
        border-radius: 16px;
        padding: 1.2rem;
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
        margin-bottom: 1rem;
        direction: rtl;
        transition: all 0.2s ease;
        border-right: 4px solid {emp_color};
    ">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div style="
                width: 48px;
                height: 48px;
                background: #F8FAFC;
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.5rem;
                border: 1px solid #E2E8F0;
            ">👤</div>
            <div style="flex: 1;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="margin: 0; font-size: 1rem; color: #1A1A2E;
                        font-weight: 700;">{emp.get('full_name', '')}</h4>
                    <span style="
                        background: {emp_color}10;
                        color: {emp_color};
                        padding: 0.2rem 0.8rem;
                        border-radius: 20px;
                        font-size: 0.75rem;
                        font-weight: 700;
                    ">{emp_type}</span>
                </div>
                <p style="margin: 0.3rem 0 0 0; color: #64748B; font-size: 0.8rem;">
                    #{emp.get('emp_no', '')} · {status} · {on_duty}
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─── الصفحة الرئيسية ──────────────────────────────────────────────────────────
def show_employees():
    """صفحة إدارة الموظفين - مع التصنيفات المحدثة"""
    
    # معلومات المستخدم
    user_role = st.session_state.get("user_role", "emt")
    username = st.session_state.get("username", "")
    
    # عنوان حسب الصلاحية
    if user_role == "chief_paramedic":
        page_header("إدارة جميع الموظفين", "عرض وإضافة وتعديل جميع كوادر القطاع", "👥")
    elif user_role == "assistant_chief":
        page_header("إدارة الموظفين", "عرض وإدارة كوادر القطاع", "👥")
    elif user_role == "field_leader":
        page_header("إدارة فريق المركز", "عرض وإضافة وتعديل موظفي مركزك", "👥")
    elif user_role in ["paramedic", "emt", "health_assistant"]:
        page_header("ملفي الشخصي", "عرض بياناتي وجدول مناوباتي", "👤")
    else:
        page_header("الموظفين", "عرض بيانات الموظفين", "👥")
    
    es, cs = _get_services()
    centers = cs.get_centers() or []
    
    # الحصول على مركز المستخدم (للمشرفين)
    user_center_id = get_user_center()
    
    # تبويبات حسب الصلاحية
    if has_permission("manage_all") or has_permission("manage_station"):
        tabs = st.tabs(["📋 قائمة الموظفين", "➕ إضافة موظف", "📊 إحصائيات"])
    else:
        tabs = st.tabs(["📋 بياناتي", "📅 جدول مناوباتي"])
    
    # ══════════════════════════════════════════════════════
    # تبويب 1 — القائمة / بياناتي
    # ══════════════════════════════════════════════════════
    with tabs[0]:
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
        
        # للموظف العادي - يعرض بياناته فقط
        if user_role in ["paramedic", "emt", "health_assistant"]:
            emp_id = get_user_employee_id()
            if emp_id:
                employee = es.get_employee(emp_id)
                if employee:
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, #3B4A82 0%, #1A2B5C 100%);
                            color: white;
                            padding: 2rem;
                            border-radius: 16px;
                            text-align: center;
                        ">
                            <div style="font-size: 3rem; margin-bottom: 0.5rem;">👤</div>
                            <h3 style="margin: 0;">{employee.get('full_name', '')}</h3>
                            <p style="margin: 0; opacity: 0.8;">#{employee.get('emp_no', '')}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown("### 📋 معلومات الاتصال")
                        st.markdown(f"""
                        - **📱 الجوال:** {employee.get('phone', '—')}
                        - **📧 البريد:** {employee.get('email', '—')}
                        - **📅 تاريخ التعيين:** {employee.get('hire_date', '—')}
                        - **📌 النوع:** {EMP_TYPE_LABELS.get(employee.get('employee_type'), '—')}
                        """)
                        
                        st.markdown("### 📜 الشهادات")
                        certs = employee.get('certifications', [])
                        if certs:
                            for cert in certs:
                                st.markdown(f"- ✅ {cert}")
                        else:
                            st.markdown("لا توجد شهادات مسجلة")
            return
        
        # ===== للمشرفين =====
        # شريط الفلترة
        with st.container():
            # استخدام expander للآيباد
            if st.session_state.get("is_mobile", False):
                with st.expander("🔍 خيارات البحث", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        if user_role == "field_leader" and user_center_id:
                            center_opts = {}
                            for c in centers:
                                if c["id"] == user_center_id:
                                    center_opts[c["name"]] = c["id"]
                                    break
                        else:
                            center_opts = {"جميع المراكز": None}
                            for c in centers:
                                center_opts[c["name"]] = c["id"]
                        
                        sel_center = st.selectbox("🏥 المركز", list(center_opts.keys()), key="emp_filter_center")
                    
                    with col2:
                        type_opts = {
                            "الكل": None,
                            "كبير مسعفين": "chief_paramedic",
                            "مساعد كبير مسعفين": "assistant_chief",
                            "قيادة ميدانية": "field_leader",
                            "تحكم عملياتي": "operations_control",
                            "تنسيق استجابة": "response_coordinator",
                            "أخصائي اسعاف": "paramedic",
                            "فني اسعاف": "emt",
                            "مساعد صحي": "health_assistant",
                            "دعم لوجستي": "logistic_support",
                            "إداري": "admin"
                        }
                        sel_type = st.selectbox("👤 النوع", list(type_opts.keys()), key="emp_filter_type")
                    
                    search = st.text_input("🔍 بحث", placeholder="اسم أو رقم...", key="emp_search")
            else:
                # للشاشات الكبيرة
                fc1, fc2, fc3 = st.columns([2, 2, 3])
                
                if user_role == "field_leader" and user_center_id:
                    center_opts = {}
                    for c in centers:
                        if c["id"] == user_center_id:
                            center_opts[c["name"]] = c["id"]
                            break
                else:
                    center_opts = {"جميع المراكز": None}
                    for c in centers:
                        center_opts[c["name"]] = c["id"]
                
                with fc1:
                    sel_center = st.selectbox("🏥 المركز", list(center_opts.keys()), key="emp_filter_center")
                
                with fc2:
                    type_opts = {
                        "جميع الأنواع": None,
                        "كبير مسعفين": "chief_paramedic",
                        "مساعد كبير مسعفين": "assistant_chief",
                        "قيادة ميدانية": "field_leader",
                        "تحكم عملياتي": "operations_control",
                        "تنسيق استجابة": "response_coordinator",
                        "أخصائي اسعاف": "paramedic",
                        "فني اسعاف": "emt",
                        "مساعد صحي": "health_assistant",
                        "دعم لوجستي": "logistic_support",
                        "إداري": "admin"
                    }
                    sel_type = st.selectbox("👤 النوع", list(type_opts.keys()), key="emp_filter_type")
                
                with fc3:
                    search = st.text_input("🔍 بحث بالاسم أو الرقم الوظيفي",
                                        placeholder="اكتب للبحث...", key="emp_search")
        
        # جلب البيانات
        with st.spinner("جاري التحميل..."):
            if user_role == "field_leader" and user_center_id:
                result = es.get_employees(
                    center_id=user_center_id,
                    search=search or None,
                )
            else:
                result = es.get_employees(
                    center_id=center_opts.get(sel_center),
                    search=search or None,
                )
        
        employees = result.get("items", []) if result else []
        total = result.get("total", len(employees)) if result else 0
        
        # تصفية إضافية بالنوع
        sel_type_val = type_opts.get(sel_type)
        if sel_type_val:
            employees = [e for e in employees if e.get("employee_type") == sel_type_val]
        
        # إحصائيات سريعة
        on_duty = sum(1 for e in employees if e.get("is_on_duty"))
        active = sum(1 for e in employees if e.get("is_active", True))
        
        st.markdown("<div style='margin-top:0.75rem;margin-bottom:0.75rem;'></div>", unsafe_allow_html=True)
        
        cols = st.columns(3)
        cols[0].metric("👥 إجمالي", total)
        cols[1].metric("🚑 على رأس العمل", on_duty)
        cols[2].metric("✅ نشطين", active)
        
        st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)
        
        if employees:
            # عرض بطاقات للآيباد
            if st.session_state.get("is_mobile", False):
                for emp in employees:
                    employee_card(emp)
                    
                    if has_permission("manage_all") or has_permission("manage_station"):
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✏️ تعديل", key=f"edit_{emp['id']}", use_container_width=True):
                                st.session_state.editing_employee = emp
                                st.session_state.active_emp_tab = 2
                                st.rerun()
                        with col2:
                            if has_permission("manage_all"):
                                if st.button("🗑️ حذف", key=f"del_{emp['id']}", use_container_width=True):
                                    if es.delete_employee(emp["id"]):
                                        st.success(f"✅ تم حذف {emp['full_name']}")
                                        st.rerun()
                        st.markdown("---")
            else:
                # جدول البيانات للشاشات الكبيرة
                df_data = []
                for emp in employees:
                    df_data.append({
                        "الرقم الوظيفي": emp.get("emp_no", ""),
                        "الاسم": emp.get("full_name", ""),
                        "النوع": EMP_TYPE_LABELS.get(emp.get("employee_type",""), "-"),
                        "على رأس العمل": "🚑 نعم" if emp.get("is_on_duty") else "—",
                        "الحالة": "✅ نشط" if emp.get("is_active", True) else "❌ متوقف",
                        "الجوال": emp.get("phone", "—"),
                        "id": emp.get("id", "")
                    })
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True, hide_index=True,
                            column_config={"id": None})
                
                if has_permission("manage_all") or has_permission("manage_station"):
                    st.markdown("<hr style='border-color:#E2E8F0;margin:1.25rem 0;'>", unsafe_allow_html=True)
                    st.markdown("### ⚙️ إدارة الموظفين")
                    
                    for emp in employees[:5]:
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            st.write(f"**{emp['full_name']}** ({emp.get('emp_no', '')})")
                        with col2:
                            if st.button("✏️ تعديل", key=f"edit_{emp['id']}"):
                                st.session_state.editing_employee = emp
                                st.session_state.active_emp_tab = 2
                                st.rerun()
                        with col3:
                            if has_permission("manage_all"):
                                if st.button("🗑️ حذف", key=f"del_{emp['id']}"):
                                    if es.delete_employee(emp["id"]):
                                        st.success(f"✅ تم حذف {emp['full_name']}")
                                        st.rerun()
        else:
            st.info("لا يوجد موظفون")
    
    # ══════════════════════════════════════════════════════
    # تبويب 2 — إضافة موظف
    # ══════════════════════════════════════════════════════
    with tabs[1]:
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
        
        if user_role in ["paramedic", "emt", "health_assistant"]:
            st.subheader("📅 جدول مناوباتي")
            from pages.shifts import show_employee_shifts
            emp_id = get_user_employee_id()
            if emp_id:
                show_employee_shifts(emp_id)
            else:
                st.info("لا يوجد جدول مناوبات")
            return
        
        st.subheader("➕ إضافة موظف جديد")
        
        with st.form("add_employee_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            
            with c1:
                emp_no = st.text_input("📋 الرقم الوظيفي *", placeholder="مثال: 5001")
                full_name = st.text_input("👤 الاسم الكامل *", placeholder="الاسم الرباعي")
                employee_type = st.selectbox(
                    "📌 الفئة الوظيفية",
                    list(EMP_TYPE_LABELS.keys()),
                    format_func=lambda x: EMP_TYPE_LABELS.get(x, x)
                )
                hire_date = st.date_input("📅 تاريخ التعيين", value=datetime.now())
            
            with c2:
                national_id = st.text_input("🆔 رقم الهوية", placeholder="10 أرقام")
                phone = st.text_input("📱 رقم الجوال", placeholder="05xxxxxxxx")
                email = st.text_input("📧 البريد الإلكتروني", placeholder="name@srca.gov.sa")
                
                if user_role == "field_leader" and user_center_id:
                    center_name = next((c["name"] for c in centers if c["id"] == user_center_id), "")
                    st.text_input("🏥 المركز", value=center_name, disabled=True)
                    center_id = user_center_id
                else:
                    center_opts = {c["name"]: c["id"] for c in centers}
                    sel_center = st.selectbox("🏥 المركز *", list(center_opts.keys()) or ["لا توجد مراكز"])
                    center_id = center_opts.get(sel_center)
            
            certifications = st.multiselect("📜 الشهادات والتدريبات",
                ["ACLS","PHTLS","BLS","PALS","ITLS","ATLS","EMT-P","HAZMAT","MCMS"])
            
            notes = st.text_area("📝 ملاحظات", placeholder="أي معلومات إضافية...")
            
            submitted = st.form_submit_button("✅ إضافة الموظف", use_container_width=True, type="primary")
            
            if submitted:
                if not emp_no or not full_name:
                    st.error("❌ الرقم الوظيفي والاسم مطلوبان")
                elif not center_id and user_role != "field_leader":
                    st.error("❌ الرجاء اختيار المركز")
                else:
                    data = {
                        "emp_no": emp_no,
                        "full_name": full_name,
                        "employee_type": employee_type,
                        "center_id": str(center_id),
                        "national_id": national_id or None,
                        "phone": phone or None,
                        "email": email or None,
                        "hire_date": hire_date.isoformat() if hire_date else None,
                        "certifications": certifications,
                        "notes": notes or None,
                    }
                    
                    res = es.create_employee(data)
                    if res:
                        st.success(f"✅ تم إضافة الموظف **{full_name}** بنجاح!")
                        st.balloons()
                        st.rerun()
    
    # ══════════════════════════════════════════════════════
    # تبويب 3 — تعديل موظف
    # ══════════════════════════════════════════════════════
    if len(tabs) > 2:
        with tabs[2]:
            st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
            
            if "editing_employee" not in st.session_state:
                st.info("👈 اختر موظفاً من تبويب «قائمة الموظفين» ثم اضغط «تعديل»")
            else:
                emp = st.session_state.editing_employee
                
                st.subheader(f"✏️ تعديل بيانات: {emp.get('full_name','')}")
                
                with st.form("edit_employee_form"):
                    c1, c2 = st.columns(2)
                    
                    with c1:
                        emp_no = st.text_input("📋 الرقم الوظيفي", value=emp.get("emp_no",""))
                        full_name = st.text_input("👤 الاسم الكامل", value=emp.get("full_name",""))
                        type_list = list(EMP_TYPE_LABELS.keys())
                        current_type = emp.get("employee_type", "admin")
                        type_index = type_list.index(current_type) if current_type in type_list else 0
                        employee_type = st.selectbox(
                            "📌 الفئة",
                            type_list,
                            index=type_index,
                            format_func=lambda x: EMP_TYPE_LABELS.get(x, x)
                        )
                    
                    with c2:
                        phone = st.text_input("📱 الجوال", value=emp.get("phone",""))
                        email = st.text_input("📧 البريد", value=emp.get("email",""))
                        
                        center_opts = {c["name"]: c["id"] for c in centers}
                        current_center = next((c["name"] for c in centers if c["id"] == emp.get("center_id")), "")
                        sel_center = st.selectbox(
                            "🏥 المركز", 
                            list(center_opts.keys()),
                            index=list(center_opts.keys()).index(current_center) if current_center in center_opts else 0
                        )
                    
                    is_active = st.checkbox("✅ الموظف نشط", value=emp.get("is_active", True))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        save = st.form_submit_button("💾 حفظ التغييرات", use_container_width=True, type="primary")
                    with col2:
                        cancel = st.form_submit_button("❌ إلغاء", use_container_width=True)
                    
                    if save:
                        data = {
                            "full_name": full_name,
                            "employee_type": employee_type,
                            "center_id": str(center_opts[sel_center]),
                            "phone": phone or None,
                            "email": email or None,
                            "is_active": is_active,
                        }
                        
                        res = es.update_employee(emp["id"], data)
                        if res:
                            st.success("✅ تم تحديث البيانات بنجاح")
                            del st.session_state.editing_employee
                            st.rerun()
                    
                    if cancel:
                        del st.session_state.editing_employee
                        st.rerun()