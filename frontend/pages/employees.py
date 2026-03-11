# frontend/pages/employees.py
import streamlit as st
import pandas as pd
from datetime import datetime
from utils.helpers import page_header, section_title
from typing import Dict, List, Any, Optional

# ============================================================================
# نظام الترميز المتكامل (Complete Coding System)
# ============================================================================

# 1. رموز المناوبات (Shift Types)
SHIFT_TYPES = {
    'A': {'name': 'صباحية', 'icon': '🌅', 'color': '#FFB74D'},
    'B': {'name': 'مسائية', 'icon': '🌆', 'color': '#4A6FA5'},
    'C': {'name': 'ليلية', 'icon': '🌙', 'color': '#2D4A6E'},
    'D': {'name': 'صباحية', 'icon': '🌅', 'color': '#FFB74D'},
    'O': {'name': 'تداخلية (Overlap)', 'icon': '🔄', 'color': '#45CFEF'},
    'RR': {'name': 'تدخل سريع', 'icon': '⚡', 'color': '#CE2E26'},
    'XW': {'name': 'عمليات (حالي)', 'icon': '🖥️', 'color': '#513A87'},
    'C00': {'name': 'عمليات (مستقبلي)', 'icon': '💻', 'color': '#3B4A82'},
}

# 2. رموز المراكز (Center Codes)
CENTER_CODES = {
    # المراكز الحقيقية (1-10)
    1: {'name': 'المنصور', 'city': 'الرياض', 'is_virtual': False},
    2: {'name': 'الخالدية', 'city': 'الرياض', 'is_virtual': False},
    3: {'name': 'منفوحة', 'city': 'الرياض', 'is_virtual': False},
    4: {'name': 'طريق الخرج', 'city': 'الرياض', 'is_virtual': False},
    5: {'name': 'العزيزية/الدار البيضاء', 'city': 'الرياض', 'is_virtual': False},
    6: {'name': 'الإسكان', 'city': 'الرياض', 'is_virtual': False},
    7: {'name': 'الحائر', 'city': 'الرياض', 'is_virtual': False},
    8: {'name': 'الشفاء', 'city': 'الرياض', 'is_virtual': False},
    9: {'name': 'عكاظ', 'city': 'الرياض', 'is_virtual': False},
    10: {'name': 'ديراب', 'city': 'الرياض', 'is_virtual': False},
    
    # المراكز الوهمية (قوى دعم متنقلة)
    12: {'name': 'قوة دعم متحركة 1', 'city': 'متنقل', 'is_virtual': True},
    14: {'name': 'قوة دعم متحركة 2', 'city': 'متنقل', 'is_virtual': True},
}

# 3. رموز الوحدات الخاصة (Special Units)
SPECIAL_UNITS = {
    'ST': {'name': 'وحدة نقل', 'icon': '🚛', 'color': '#64748B'},
    'TT': {'name': 'باص استجابة', 'icon': '🚑', 'color': '#CE2E26'},
    'XX': {'name': 'إجازة', 'icon': '🏖️', 'color': '#9CA3AF'},
    'Y': {'name': 'إداري', 'icon': '📋', 'color': '#475569'},
    'YY': {'name': 'صيانة مركبات', 'icon': '🔧', 'color': '#6B7280'},
    'YYY': {'name': 'تموين طبي', 'icon': '💊', 'color': '#42924B'},
    'YYYY': {'name': 'أوكسجين', 'icon': '💨', 'color': '#45CFEF'},
    'Z': {'name': 'صيانة أجهزة', 'icon': '⚙️', 'color': '#F1B944'},
}

# 4. رموز القيادة (Leadership Codes)
LEADERSHIP_TYPES = {
    'chief_paramedic': 'كبير مسعفين',
    'assistant_chief': 'مساعد كبير مسعفين',
}

# 5. أنواع الموظفين (للتوافق مع النظام القديم)
EMP_TYPE_LABELS = {
    "chief_paramedic": "كبير مسعفين",
    "assistant_chief": "مساعد كبير مسعفين",
    "field_leader": "قيادة ميدانية",
    "operations_control": "تحكم عملياتي",
    "response_coordinator": "تنسيق استجابة",
    "paramedic": "أخصائي اسعاف",
    "emt": "فني اسعاف",
    "health_assistant": "مساعد صحي",
    "logistic_support": "دعم لوجستي",
    "admin": "إداري"
}

EMP_TYPE_COLORS = {
    "chief_paramedic": "#CE2E26",
    "assistant_chief": "#B71C1C",
    "field_leader": "#3B4A82",
    "operations_control": "#45CFEF",
    "response_coordinator": "#513A87",
    "paramedic": "#42924B",
    "emt": "#F1B944",
    "health_assistant": "#FF7C10",
    "logistic_support": "#64748B",
    "admin": "#475569"
}

# ============================================================================
# دوال فك الترميز (Decoding Functions)
# ============================================================================

def is_hq_employee(emp_code: str) -> bool:
    """التحقق إذا كان الموظف تابعاً للمركز الرئيسي"""
    if not emp_code:
        return False
    
    # القيادات (A0, B0, C0, D0)
    if emp_code.endswith('0') and len(emp_code) <= 3 and emp_code[0] in 'ABCD':
        return True
    
    # العمليات (XW1 → XW5)
    if emp_code.startswith('XW'):
        return True
    
    # الوحدات الخاصة والدعم (ST, TT, Y, YY, YYY, YYYY, Z)
    if emp_code in SPECIAL_UNITS:
        return True
    
    return False

def decode_employee_code(code: str) -> Dict[str, Any]:
    """فك شفرة الموظف بشكل كامل"""
    if not code:
        return {'type': 'غير معروف', 'category': 'unknown', 'original': code}
    
    # 1. المركز الرئيسي (للقادة والعمليات والدعم)
    if is_hq_employee(code):
        # القيادة (A0, B0, C0, D0)
        if code.endswith('0') and len(code) <= 3 and code[0] in 'ABCD':
            shift = code[0]
            return {
                'type': 'قيادة',
                'category': 'leadership',
                'shift': shift,
                'shift_name': SHIFT_TYPES.get(shift, {}).get('name', ''),
                'icon': '👑',
                'color': '#CE2E26',
                'center': 'المركز الرئيسي للقطاع',
                'center_id': 'HQ',
                'is_hq': True,
                'original': code
            }
        
        # العمليات (XW1 → XW5)
        if code.startswith('XW'):
            return {
                'type': 'عمليات',
                'category': 'operations',
                'icon': '🖥️',
                'color': '#513A87',
                'center': 'المركز الرئيسي للقطاع',
                'center_id': 'HQ',
                'is_hq': True,
                'original': code
            }
        
        # الوحدات الخاصة والدعم
        if code in SPECIAL_UNITS:
            unit = SPECIAL_UNITS[code]
            category = 'special_unit' if code in ['ST', 'TT'] else 'support'
            return {
                'type': unit['name'],
                'category': category,
                'icon': unit['icon'],
                'color': unit['color'],
                'center': 'المركز الرئيسي للقطاع',
                'center_id': 'HQ',
                'is_hq': True,
                'original': code
            }
    
    # 2. رموز التدخل السريع (RR)
    if code.startswith('RR') and len(code) > 2:
        shift = code[2:]
        shift_info = SHIFT_TYPES.get(shift, {})
        return {
            'type': 'تدخل سريع',
            'category': 'rapid_response',
            'shift': shift,
            'shift_name': shift_info.get('name', ''),
            'icon': '⚡',
            'color': '#CE2E26',
            'original': code
        }
    
    # 3. الرموز العادية (A1, B7, O12, etc.)
    if code and code[0] in 'ABCDO':
        shift = code[0]
        shift_info = SHIFT_TYPES.get(shift, {})
        
        # معالجة الرقم
        center_part = code[1:]
        if center_part.isdigit():
            center_num = int(center_part)
            center_info = CENTER_CODES.get(center_num, {
                'name': f'مركز {center_num}',
                'is_virtual': False
            })
            
            return {
                'type': 'مناوبة',
                'category': 'shift',
                'shift': shift,
                'shift_name': shift_info.get('name', ''),
                'icon': shift_info.get('icon', '👤'),
                'color': shift_info.get('color', '#64748B'),
                'center_num': center_num,
                'center_name': center_info['name'],
                'is_virtual': center_info.get('is_virtual', False),
                'original': code
            }
    
    # 4. إذا ما تطابق مع أي شيء
    return {
        'type': 'غير معروف',
        'category': 'unknown',
        'icon': '❓',
        'color': '#9CA3AF',
        'original': code
    }

def get_employee_type_label(emp_type: str) -> str:
    """تحويل نوع الموظف إلى نص عربي"""
    return EMP_TYPE_LABELS.get(emp_type, emp_type)

def get_employee_color(emp_type: str) -> str:
    """تحديد لون الموظف حسب نوعه"""
    return EMP_TYPE_COLORS.get(emp_type, '#475569')

# ============================================================================
# دوال العرض (Display Functions)
# ============================================================================

def employee_card(emp: Dict[str, Any]):
    """بطاقة موظف مع أيقونة حسب نوعه"""
    emp_code = emp.get('emp_code', '')
    decoded = decode_employee_code(emp_code)
    
    # معلومات أساسية
    full_name = emp.get('full_name', '')
    emp_no = emp.get('emp_no', '')
    
    # تحديد الأيقونة واللون
    icon = decoded.get('icon', '👤')
    bg_color = decoded.get('color', '#475569')
    emp_type_display = decoded.get('type', EMP_TYPE_LABELS.get(emp.get('employee_type', ''), ''))
    center = decoded.get('center_name', decoded.get('center', ''))
    
    # الحالة
    status = "🟢 نشط" if emp.get('is_active', True) else "🔴 غير نشط"
    on_duty = "🚑 على رأس العمل" if emp.get('is_on_duty') else "⏸️ في الإجازة"
    
    st.markdown(f"""
    <div style="background: white; border-radius: 16px; padding: 1.2rem; border: 1px solid #E2E8F0; margin-bottom: 1rem; direction: rtl; border-right: 4px solid {bg_color};">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div style="width: 48px; height: 48px; background: {bg_color}20; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem;">
                {icon}
            </div>
            <div style="flex: 1;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="margin: 0; font-size: 1rem; color: #1A1A2E; font-weight: 700;">{full_name}</h4>
                    <span style="background: {bg_color}10; color: {bg_color}; padding: 0.2rem 0.8rem; border-radius: 20px; font-size: 0.75rem; font-weight: 700;">
                        {emp_type_display}
                    </span>
                </div>
                <p style="margin: 0.3rem 0 0 0; color: #64748B; font-size: 0.8rem;">
                    #{emp_no} · {status} · {on_duty}
                </p>
                {f'<p style="margin: 0.2rem 0 0 0; color: #3B4A82; font-size: 0.75rem;">📍 {center}</p>' if center else ''}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_hq_dashboard(hq_employees: List[Dict[str, Any]]):
    """لوحة معلومات المركز الرئيسي"""
    if not hq_employees:
        st.info("لا يوجد موظفون في المركز الرئيسي")
        return
    
    st.markdown("### 🏢 المركز الرئيسي للقطاع")
    
    # تصنيف الموظفين
    leadership = []
    operations = []
    support = []
    special = []
    
    for emp in hq_employees:
        code = emp.get('emp_code', '')
        if code.endswith('0') and code[0] in 'ABCD':
            leadership.append(emp)
        elif code.startswith('XW'):
            operations.append(emp)
        elif code in ['ST', 'TT']:
            special.append(emp)
        elif code in ['Y', 'YY', 'YYY', 'YYYY', 'Z']:
            support.append(emp)
    
    # إحصائيات سريعة
    cols = st.columns(5)
    with cols[0]:
        st.metric("👥 الإجمالي", len(hq_employees))
    with cols[1]:
        st.metric("👑 القيادات", len(leadership))
    with cols[2]:
        st.metric("🖥️ العمليات", len(operations))
    with cols[3]:
        st.metric("📋 الدعم", len(support))
    with cols[4]:
        st.metric("🚛 وحدات خاصة", len(special))
    
    # تبويبات للعرض
    if leadership or operations or support or special:
        tab1, tab2, tab3, tab4 = st.tabs(["👑 القيادات", "🖥️ العمليات", "📋 الدعم", "🚛 وحدات خاصة"])
        
        with tab1:
            for emp in leadership:
                employee_card(emp)
        
        with tab2:
            for emp in operations:
                employee_card(emp)
        
        with tab3:
            for emp in support:
                employee_card(emp)
        
        with tab4:
            for emp in special:
                employee_card(emp)

# ============================================================================
# دوال الخدمات (Service Functions)
# ============================================================================

def _get_services():
    """تهيئة الخدمات"""
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

def has_permission(required_role):
    """التحقق من صلاحية المستخدم"""
    user_role = st.session_state.get("user_role", "emt")
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
    return st.session_state.get("user_center_id")

def get_user_employee_id():
    return st.session_state.get("user_employee_id")

# ============================================================================
# دوال استيراد Excel
# ============================================================================

def import_employees_from_excel(uploaded_file, es, cs):
    """استيراد الموظفين من ملف Excel"""
    try:
        df = pd.read_excel(uploaded_file)
        
        # التحقق من الأعمدة المطلوبة
        required = ['الاسم', 'الكود', 'طبيعة العمل']
        missing = [col for col in required if col not in df.columns]
        if missing:
            st.error(f"❌ الأعمدة المفقودة: {missing}")
            return 0, len(df)
        
        # تحويل المسميات
        type_mapping = {
            'كبير مسعفين': 'chief_paramedic',
            'مساعد كبير مسعفين': 'assistant_chief',
            'قيادة ميدانية': 'field_leader',
            'تحكم عملياتي': 'operations_control',
            'تنسيق استجابة': 'response_coordinator',
            'أخصائي اسعاف': 'paramedic',
            'فني اسعاف': 'emt',
            'مساعد صحي': 'health_assistant',
            'دعم لوجستي': 'logistic_support',
            'إداري': 'admin'
        }
        
        # الحصول على مركز (سنستخدم المركز الرئيسي للموظفين الجدد)
        centers = cs.get_centers()
        default_center_id = str(centers[0]['id']) if centers else None
        
        if not default_center_id:
            st.error("❌ لا يوجد مراكز في النظام")
            return 0, len(df)
        
        success = 0
        failed = 0
        errors = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, row in df.iterrows():
            status_text.text(f"جاري استيراد {idx+1}/{len(df)}...")
            
            try:
                emp_no = str(row['الكود']).strip()
                job_title = str(row['طبيعة العمل']).strip()
                emp_type = type_mapping.get(job_title, 'admin')
                
                employee_data = {
                    'emp_no': emp_no,
                    'full_name': str(row['الاسم']).strip(),
                    'employee_type': emp_type,
                    'center_id': default_center_id,
                    'is_active': True
                }
                
                if es.create_employee(employee_data):
                    success += 1
                else:
                    failed += 1
                    errors.append(f"سطر {idx+2}: فشل إضافة {employee_data['full_name']}")
                    
            except Exception as e:
                failed += 1
                errors.append(f"سطر {idx+2}: {str(e)}")
            
            progress_bar.progress((idx + 1) / len(df))
        
        if errors:
            st.warning(f"⚠️ يوجد {len(errors)} خطأ")
            for err in errors[:5]:
                st.warning(err)
        
        return success, failed
        
    except Exception as e:
        st.error(f"❌ خطأ في معالجة الملف: {str(e)}")
        return 0, 0

# ============================================================================
# الصفحة الرئيسية
# ============================================================================

def show_employees():
    """صفحة إدارة الموظفين"""
    
    # مسح الكاش إذا طلب
    if st.session_state.get("force_reload_employees", False):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.session_state.force_reload_employees = False
    
    user_role = st.session_state.get("user_role", "emt")
    
    if user_role == "chief_paramedic":
        page_header("إدارة جميع الموظفين", "عرض وإضافة وتعديل جميع كوادر القطاع", "👥")
    elif user_role == "field_leader":
        page_header("إدارة فريق المركز", "عرض وإضافة وتعديل موظفي مركزك", "👥")
    elif user_role in ["paramedic", "emt", "health_assistant"]:
        page_header("ملفي الشخصي", "عرض بياناتي وجدول مناوباتي", "👤")
    else:
        page_header("الموظفين", "عرض بيانات الموظفين", "👥")
    
    es, cs = _get_services()
    centers = cs.get_centers() or []
    user_center_id = get_user_center()
    
    # التبويبات الرئيسية
    if has_permission("manage_all") or has_permission("manage_station"):
        tabs = st.tabs(["📋 قائمة الموظفين", "➕ إضافة موظف"])
    else:
        tabs = st.tabs(["📋 بياناتي", "📅 جدول مناوباتي"])
    
    # ===== قسم استيراد Excel =====
    with st.expander("📥 استيراد موظفين من Excel", expanded=False):
        st.markdown("""
        <div style="background: #F0F9FF; padding: 1rem; border-radius: 12px; margin-bottom: 1rem;">
            <h5 style="margin: 0 0 0.5rem 0;">📌 تعليمات:</h5>
            <ul style="margin: 0; padding-right: 1.5rem; font-size: 0.9rem;">
                <li>الملف يجب أن يكون بصيغة Excel (.xlsx)</li>
                <li>الأعمدة المطلوبة: <b>الاسم، الكود، طبيعة العمل</b></li>
                <li>الموظفون الجدد يُضافون، والموجودون يُحدثون</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "📤 اختر ملف Excel",
            type=['xlsx', 'xls'],
            key="emp_upload_excel"
        )
        
        if uploaded_file:
            try:
                df_preview = pd.read_excel(uploaded_file)
                st.dataframe(df_preview.head(5), use_container_width=True)
                st.caption(f"إجمالي {len(df_preview)} موظف في الملف")
                
                if st.button("🚀 بدء الاستيراد", use_container_width=True, type="primary"):
                    success, failed = import_employees_from_excel(uploaded_file, es, cs)
                    
                    if success > 0:
                        st.success(f"✅ تم استيراد {success} موظف بنجاح!")
                        st.balloons()
                    if failed > 0:
                        st.warning(f"⚠️ فشل استيراد {failed} موظف")
                    
                    # عرض إحصائيات
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("✅ نجاح", success)
                    with col2:
                        st.metric("❌ فشل", failed)
                    with col3:
                        st.metric("📦 إجمالي", len(df_preview))
                    
                    # زر تحديث
                    if success > 0:
                        if st.button("🔄 تحديث القائمة", use_container_width=True):
                            st.session_state.force_reload_employees = True
                            st.rerun()
                            
            except Exception as e:
                st.error(f"❌ خطأ في قراءة الملف: {str(e)}")
    
    # ===== تبويب 1: قائمة الموظفين =====
    with tabs[0]:
        if user_role in ["paramedic", "emt", "health_assistant"]:
            emp_id = get_user_employee_id()
            if emp_id:
                employee = es.get_employee(emp_id)
                if employee:
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.markdown(f"""<div style="background: linear-gradient(135deg, #3B4A82 0%, #1A2B5C 100%); color: white; padding: 2rem; border-radius: 16px; text-align: center;"><div style="font-size: 3rem;">👤</div><h3>{employee.get('full_name', '')}</h3><p>#{employee.get('emp_no', '')}</p></div>""", unsafe_allow_html=True)
                    with col2:
                        st.markdown("### 📋 معلومات الاتصال")
                        st.markdown(f"""- **📱 الجوال:** {employee.get('phone', '—')}\n- **📧 البريد:** {employee.get('email', '—')}\n- **📌 النوع:** {get_employee_type_label(employee.get('employee_type', ''))}""")
            return
        
        # جلب البيانات
        with st.spinner("جاري التحميل..."):
            result = es.get_employees(limit=500)
        
        all_employees = result.get("items", []) if result else []
        
        # إضافة حقل emp_code من البيانات (افتراضياً من emp_no أو أي حقل آخر)
        for emp in all_employees:
            if 'emp_code' not in emp:
                emp['emp_code'] = emp.get('emp_no', '')
        
        # تقسيم الموظفين
        hq_employees = [e for e in all_employees if is_hq_employee(e.get('emp_code', ''))]
        center_employees = [e for e in all_employees if not is_hq_employee(e.get('emp_code', ''))]
        
        # إحصائيات سريعة
        total = len(all_employees)
        on_duty = sum(1 for e in all_employees if e.get("is_on_duty"))
        active = sum(1 for e in all_employees if e.get("is_active", True))
        
        cols = st.columns(3)
        cols[0].metric("👥 إجمالي", total)
        cols[1].metric("🚑 على رأس العمل", on_duty)
        cols[2].metric("✅ نشطين", active)
        
        st.markdown("---")
        
        # عرض الموظفين
        if hq_employees:
            display_hq_dashboard(hq_employees)
            st.markdown("---")
        
        if center_employees:
            st.markdown("### 🏥 موظفو المراكز")
            
            # فلترة حسب المركز
            center_options = ["الكل"] + [c['name'] for c in centers]
            selected_center = st.selectbox("🏥 المركز", center_options)
            
            if selected_center == "الكل":
                filtered = center_employees
            else:
                center_id = next((c['id'] for c in centers if c['name'] == selected_center), None)
                filtered = [e for e in center_employees if str(e.get('center_id')) == str(center_id)]
            
            if filtered:
                if st.session_state.get("is_mobile", False):
                    for emp in filtered:
                        employee_card(emp)
                else:
                    df_data = []
                    for emp in filtered:
                        decoded = decode_employee_code(emp.get('emp_code', ''))
                        df_data.append({
                            "الرقم الوظيفي": emp.get("emp_no", ""),
                            "الاسم": emp.get("full_name", ""),
                            "النوع": get_employee_type_label(emp.get("employee_type", "")),
                            "على رأس العمل": "🚑" if emp.get("is_on_duty") else "—",
                            "الحالة": "✅" if emp.get("is_active", True) else "❌",
                            "id": emp.get("id", "")
                        })
                    df = pd.DataFrame(df_data)
                    st.dataframe(df, use_container_width=True, hide_index=True, column_config={"id": None})
            else:
                st.info("لا يوجد موظفون")
    
    # ===== تبويب 2: إضافة موظف =====
    with tabs[1]:
        if user_role in ["paramedic", "emt", "health_assistant"]:
            st.subheader("📅 جدول مناوباتي")
            return
        
        st.subheader("➕ إضافة موظف جديد")
        with st.form("add_employee_form"):
            c1, c2 = st.columns(2)
            with c1:
                emp_no = st.text_input("📋 الرقم الوظيفي *")
                full_name = st.text_input("👤 الاسم الكامل *")
                employee_type = st.selectbox("📌 الفئة", list(EMP_TYPE_LABELS.keys()), format_func=lambda x: EMP_TYPE_LABELS.get(x, x))
                hire_date = st.date_input("📅 تاريخ التعيين", value=datetime.now())
            with c2:
                national_id = st.text_input("🆔 رقم الهوية")
                phone = st.text_input("📱 الجوال")
                email = st.text_input("📧 البريد")
                
                center_opts = {c["name"]: c["id"] for c in centers}
                sel_center = st.selectbox("🏥 المركز *", list(center_opts.keys()))
                center_id = center_opts.get(sel_center)
            
            certifications = st.multiselect("📜 الشهادات", ["ACLS","PHTLS","BLS","PALS","ITLS","ATLS","EMT-P"])
            notes = st.text_area("📝 ملاحظات")
            
            if st.form_submit_button("✅ إضافة", use_container_width=True, type="primary"):
                if not emp_no or not full_name:
                    st.error("❌ الرقم الوظيفي والاسم مطلوبان")
                elif not center_id:
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
                        "notes": notes or None
                    }
                    if es.create_employee(data):
                        st.success(f"✅ تم إضافة {full_name}")
                        st.balloons()
                        st.rerun()
    
    # ===== قسم التعديل =====
    if "editing_employee" in st.session_state:
        st.markdown("---")
        emp = st.session_state.editing_employee
        st.subheader(f"✏️ تعديل: {emp.get('full_name','')}")
        
        with st.form("edit_employee_form"):
            c1, c2 = st.columns(2)
            with c1:
                emp_no = st.text_input("📋 الرقم الوظيفي", value=emp.get("emp_no",""), disabled=True)
                full_name = st.text_input("👤 الاسم الكامل *", value=emp.get("full_name",""))
                national_id = st.text_input("🆔 رقم الهوية", value=emp.get("national_id",""))
                hire_date = st.date_input("📅 تاريخ التعيين", value=datetime.strptime(emp.get("hire_date","2020-01-01"), "%Y-%m-%d").date() if emp.get("hire_date") else datetime.now())
            with c2:
                phone = st.text_input("📱 الجوال", value=emp.get("phone",""))
                email = st.text_input("📧 البريد", value=emp.get("email",""))
                
                type_list = list(EMP_TYPE_LABELS.keys())
                current_type = emp.get("employee_type", "admin")
                type_index = type_list.index(current_type) if current_type in type_list else 0
                employee_type = st.selectbox("📌 الفئة", type_list, index=type_index, format_func=lambda x: EMP_TYPE_LABELS.get(x, x))
                
                center_opts = {c["name"]: c["id"] for c in centers}
                current_center = next((c["name"] for c in centers if c["id"] == emp.get("center_id")), "")
                sel_center = st.selectbox("🏥 المركز", list(center_opts.keys()), index=list(center_opts.keys()).index(current_center) if current_center in center_opts else 0)
            
            certifications = st.multiselect("📜 الشهادات", ["ACLS","PHTLS","BLS","PALS","ITLS","ATLS","EMT-P"], default=emp.get("certifications", []))
            
            col1, col2, col3 = st.columns(3)
            with col1:
                is_active = st.checkbox("✅ نشط", value=emp.get("is_active", True))
            with col2:
                is_on_duty = st.checkbox("🚑 على رأس العمل", value=emp.get("is_on_duty", False))
            with col3:
                is_available = st.checkbox("🟢 متاح", value=emp.get("is_available", True))
            
            notes = st.text_area("📝 ملاحظات", value=emp.get("notes", ""))
            
            col1, col2, col3 = st.columns(3)
            with col1:
                save = st.form_submit_button("💾 حفظ", use_container_width=True, type="primary")
            with col2:
                cancel = st.form_submit_button("❌ إلغاء", use_container_width=True)
            with col3:
                delete = st.form_submit_button("🗑️ حذف", use_container_width=True)
            
            if save:
                data = {
                    "full_name": full_name,
                    "employee_type": employee_type,
                    "center_id": str(center_opts[sel_center]),
                    "phone": phone or None,
                    "email": email or None,
                    "national_id": national_id or None,
                    "hire_date": hire_date.isoformat() if hire_date else None,
                    "certifications": certifications,
                    "is_active": is_active,
                    "is_on_duty": is_on_duty,
                    "is_available": is_available,
                    "notes": notes or None
                }
                if es.update_employee(emp["id"], data):
                    st.success("✅ تم التحديث")
                    st.cache_data.clear()
                    st.session_state.force_reload_employees = True
                    del st.session_state.editing_employee
                    st.rerun()
            
            if cancel:
                del st.session_state.editing_employee
                st.rerun()
            
            if delete:
                if st.session_state.get("user_role") == "chief_paramedic":
                    if es.delete_employee(emp["id"]):
                        st.success(f"✅ تم حذف {emp['full_name']}")
                        st.session_state.force_reload_employees = True
                        del st.session_state.editing_employee
                        st.rerun()
                else:
                    st.error("❌ فقط كبير المسعفين يمكنه الحذف")