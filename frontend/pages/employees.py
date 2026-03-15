# frontend/pages/employees.py
import streamlit as st
import pandas as pd
from datetime import datetime
from utils.helpers import page_header, section_title
from utils.constants import (
    SHIFT_TYPES, TEAM_CODES, CENTER_CODES, HQ_CENTER, SPECIAL_UNITS,
    EMP_TYPE_LABELS, EMP_TYPE_COLORS,
    get_center_name, is_virtual_center, get_shift_info, get_special_unit_info
)
from typing import Dict, List, Any, Optional
import requests
import random

# ============================================================================
# دوال فك الترميز (Decoding Functions) - النسخة النهائية
# ============================================================================

def get_shift_display_name(shift_code: str) -> str:
    """الحصول على اسم المناوبة من رمزها (للنظام الجديد)"""
    if shift_code in SHIFT_TYPES:
        return SHIFT_TYPES[shift_code]["name"]
    return shift_code

def is_hq_employee(emp_code: str) -> bool:
    """التحقق إذا كان الموظف تابعاً للمركز الرئيسي"""
    if not emp_code:
        return False
    
    # مدير القطاع (0) والقيادات (A0, B0, C0, D0)
    if emp_code == '0' or emp_code in ['A0', 'B0', 'C0', 'D0']:
        return True
    
    # العمليات (XW1 → XW5)
    if emp_code.startswith('XW'):
        return True
    
    # الوحدات الخاصة والدعم
    if emp_code in SPECIAL_UNITS or emp_code in ['AZ', 'BZ', 'CZ', 'DZ']:
        return True
    
    return False

def decode_employee_code(code: str) -> Dict[str, Any]:
    """فك شفرة الموظف حسب نظام الفرق - مع أولوية صحيحة للرموز"""
    if not code:
        return {'type': 'غير معروف', 'category': 'unknown', 'original': code}
    
    # ===== مدير القطاع (مشعل الحجيلي) =====
    if code == '0':
        return {
            'role': 'مدير القطاع',
            'team': 'الإدارة',
            'team_name': 'الإدارة',
            'type': 'قيادة',
            'category': 'leadership',
            'icon': '👑',
            'color': '#CE2E26',
            'center': 'المركز الرئيسي للقطاع',
            'center_id': 'HQ',
            'is_hq': True,
            'original': code
        }
    
    # ===== أعضاء الفرق (A1, A2, A10, B1, B2, B10, C3, ...) =====
    # هذا الشرط يجي قبل القيادات عشان A10 ما يروح للقيادات
    if code and code[0] in 'ABCD' and len(code) > 1 and code[1:].isdigit():
        team = code[0]
        center_num = int(code[1:])
        team_info = TEAM_CODES.get(team, {})
        center_info = CENTER_CODES.get(center_num, {
            'name': f'مركز {center_num}',
            'type': 'مركز',
            'is_virtual': False
        })
        
        return {
            'role': 'عضو فريق',
            'team': team,
            'team_name': team_info.get('name', f'الفريق {team}'),
            'type': 'مناوبة',
            'category': 'shift',
            'icon': '👤',
            'color': team_info.get('color', '#64748B'),
            'center_num': center_num,
            'center_name': center_info['name'],
            'center_type': center_info.get('type', 'مركز'),
            'is_virtual': center_info.get('is_virtual', False),
            'original': code
        }
    
    # ===== القيادات (A0, B0, C0, D0) فقط =====
    if code in ['A0', 'B0', 'C0', 'D0']:
        team = code[0]
        team_info = TEAM_CODES.get(team, {})
        return {
            'role': 'قائد فريق',
            'team': team,
            'team_name': team_info.get('name', f'الفريق {team}'),
            'type': 'قيادة',
            'category': 'leadership',
            'icon': '👑',
            'color': '#CE2E26',
            'center': 'المركز الرئيسي للقطاع',
            'center_id': 'HQ',
            'is_hq': True,
            'original': code
        }
    
    # ===== التحقق من رموز المناوبات =====
    if code in SHIFT_TYPES:
        shift_info = SHIFT_TYPES[code]
        return {
            'role': shift_info['name'],
            'type': shift_info['type'],
            'category': shift_info['category'],
            'icon': code,
            'color': shift_info['color'],
            'text_color': shift_info['text_color'],
            'hours': shift_info['hours'],
            'is_shift': True,
            'original': code
        }
    
    # ===== دعم الترميز القديم لمركز ديراب =====
    if code.lower() in ['aa', 'aa10']:
        return decode_employee_code('A10')
    if code.lower() in ['bb', 'bb10']:
        return decode_employee_code('B10')
    if code.lower() in ['cc', 'cc10']:
        return decode_employee_code('C10')
    if code.lower() in ['dd', 'dd10']:
        return decode_employee_code('D10')
    
    # ===== الترميز الجديد لمركز ديراب (A10, B10, C10, D10) =====
    if code in ['A10', 'B10', 'C10', 'D10']:
        team = code[0]
        center_num = 10
        team_info = TEAM_CODES.get(team, {})
        center_info = CENTER_CODES.get(center_num, {
            'name': f'مركز {center_num}',
            'type': 'مركز',
            'is_virtual': False
        })
        
        return {
            'role': 'عضو فريق',
            'team': team,
            'team_name': team_info.get('name', f'الفريق {team}'),
            'type': 'مناوبة',
            'category': 'shift',
            'icon': '👤',
            'color': team_info.get('color', '#64748B'),
            'center_num': center_num,
            'center_name': center_info['name'],
            'center_type': center_info.get('type', 'مركز'),
            'is_virtual': center_info.get('is_virtual', False),
            'original': code
        }
    
    # ===== فريق التداخلية (O12, O14, O14A) =====
    if code.startswith('O') and len(code) > 1:
        team = code
        team_name = "تداخلية"
        if code == 'O12':
            team_name = "تداخلية 12"
        elif code == 'O14':
            team_name = "تداخلية 14"
        elif code == 'O14A':
            team_name = "تداخلية 14A"
        return {
            'role': 'فريق تداخلية',
            'team': team,
            'team_name': team_name,
            'type': 'تداخلية',
            'category': 'overlap',
            'icon': '🔄',
            'color': '#45CFEF',
            'center': 'المركز الرئيسي للقطاع',
            'center_id': 'HQ',
            'is_hq': True,
            'original': code
        }
    
    # ===== فريق التدخل السريع (RR) =====
    if code.startswith('RR'):
        team = code
        team_name = "تدخل سريع"
        if len(code) > 2:
            team_name = f"تدخل سريع {code[2:]}"
        return {
            'role': 'فريق تدخل سريع',
            'team': team,
            'team_name': team_name,
            'type': 'تدخل سريع',
            'category': 'rapid_response',
            'icon': '⚡',
            'color': '#CE2E26',
            'center': 'المركز الرئيسي للقطاع',
            'center_id': 'HQ',
            'is_hq': True,
            'original': code
        }
    
    # ===== العمليات (XW) =====
    if code.startswith('XW'):
        team = code
        team_name = "عمليات"
        if len(code) > 2:
            team_name = f"عمليات {code[2:]}"
        return {
            'role': 'فريق عمليات',
            'team': team,
            'team_name': team_name,
            'type': 'عمليات',
            'category': 'operations',
            'icon': '🖥️',
            'color': '#513A87',
            'center': 'المركز الرئيسي للقطاع',
            'center_id': 'HQ',
            'is_hq': True,
            'original': code
        }
    
    # ===== الدعم اللوجستي (AZ, BZ, CZ, DZ) =====
    if code in ['AZ', 'BZ', 'CZ', 'DZ']:
        team = code[0]
        return {
            'role': 'دعم لوجستي',
            'team': f'{team}Z',
            'team_name': f'الدعم اللوجستي {team}',
            'type': 'دعم',
            'category': 'logistic',
            'icon': '📦',
            'color': '#64748B',
            'center': 'المركز الرئيسي للقطاع',
            'center_id': 'HQ',
            'is_hq': True,
            'original': code
        }
    
    # ===== الوحدات الخاصة (ST, TT, Y, YY, ...) =====
    if code in SPECIAL_UNITS:
        unit = SPECIAL_UNITS[code]
        return {
            'role': unit['name'],
            'team': code,
            'team_name': unit['name'],
            'type': unit['category'],
            'category': 'special',
            'icon': unit['icon'],
            'color': unit['color'],
            'center': 'المركز الرئيسي للقطاع',
            'center_id': 'HQ',
            'is_hq': True,
            'original': code
        }
    
    # ===== إذا ما تطابق مع أي شيء =====
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
    
    # النوع المعروض
    if decoded.get('role') == 'مدير القطاع':
        display_type = "مدير القطاع"
    elif decoded.get('role') == 'قائد فريق':
        display_type = f"{decoded['team_name']} - قائد"
    elif decoded.get('role') == 'عضو فريق':
        display_type = f"{decoded['team_name']}"
    elif decoded.get('is_shift'):
        display_type = decoded.get('type', '')
    else:
        display_type = decoded.get('type', EMP_TYPE_LABELS.get(emp.get('employee_type', ''), ''))
    
    # المركز
    if decoded.get('is_hq'):
        location = "🏢 " + decoded.get('center', 'المركز الرئيسي')
    else:
        center_name = decoded.get('center_name', '')
        center_type = decoded.get('center_type', '')
        location = f"📍 {center_name}"
        if decoded.get('is_virtual'):
            location += " (متنقل)"
    
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
                        {display_type}
                    </span>
                </div>
                <p style="margin: 0.3rem 0 0 0; color: #64748B; font-size: 0.8rem;">
                    #{emp_no} · {status} · {on_duty}
                </p>
                <p style="margin: 0.2rem 0 0 0; color: #3B4A82; font-size: 0.75rem;">{location}</p>
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
    leadership = []  # مدير القطاع والقيادات (0, A0, B0, C0, D0)
    operations = []   # العمليات (XW)
    rapid_response = []  # التدخل السريع (RR)
    support = []      # الدعم (Y, YY, ...)
    special = []      # وحدات خاصة (ST, TT)
    shift_employees = []  # باقي الموظفين
    
    for emp in hq_employees:
        code = emp.get('emp_code', '')
        
        # مدير القطاع والقيادات
        if code == '0' or code in ['A0', 'B0', 'C0', 'D0']:
            leadership.append(emp)
        
        # العمليات (XW)
        elif code.startswith('XW'):
            operations.append(emp)
        
        # التدخل السريع (RR)
        elif code.startswith('RR'):
            rapid_response.append(emp)
        
        # وحدات خاصة (ST, TT)
        elif code in ['ST', 'TT']:
            special.append(emp)
        
        # الدعم (Y, YY, YYY, YYYY, Z, AZ, BZ, CZ, DZ)
        elif code in SPECIAL_UNITS or code in ['AZ', 'BZ', 'CZ', 'DZ']:
            support.append(emp)
        
        # باقي الموظفين
        else:
            shift_employees.append(emp)
    
    # إحصائيات سريعة
    cols = st.columns(6)
    with cols[0]:
        st.metric("👥 الإجمالي", len(hq_employees))
    with cols[1]:
        st.metric("👑 القيادات", len(leadership))
    with cols[2]:
        st.metric("🖥️ العمليات", len(operations))
    with cols[3]:
        st.metric("⚡ تدخل سريع", len(rapid_response))
    with cols[4]:
        st.metric("📋 الدعم", len(support))
    with cols[5]:
        st.metric("🚛 وحدات خاصة", len(special))
    
    # تبويبات للعرض
    tab_names = []
    if leadership:
        tab_names.append("👑 القيادات")
    if operations:
        tab_names.append("🖥️ العمليات")
    if rapid_response:
        tab_names.append("⚡ تدخل سريع")
    if support:
        tab_names.append("📋 الدعم")
    if special:
        tab_names.append("🚛 وحدات خاصة")
    if shift_employees:
        tab_names.append("📊 مناوبات")
    
    if tab_names:
        tabs = st.tabs(tab_names)
        tab_idx = 0
        
        if leadership:
            with tabs[tab_idx]:
                for emp in leadership:
                    employee_card(emp)
            tab_idx += 1
        
        if operations:
            with tabs[tab_idx]:
                for emp in operations:
                    employee_card(emp)
            tab_idx += 1
        
        if rapid_response:
            with tabs[tab_idx]:
                for emp in rapid_response:
                    employee_card(emp)
            tab_idx += 1
        
        if support:
            with tabs[tab_idx]:
                for emp in support:
                    employee_card(emp)
            tab_idx += 1
        
        if special:
            with tabs[tab_idx]:
                for emp in special:
                    employee_card(emp)
            tab_idx += 1
        
        if shift_employees:
            with tabs[tab_idx]:
                for emp in shift_employees:
                    employee_card(emp)

# ============================================================================
# دوال الخدمات (Service Functions)
# ============================================================================

def _get_services():
    """تهيئة الخدمات"""
    auth = st.session_state.auth_service
    es = st.session_state.get("employee_service")
    cs = st.session_state.get("center_service")
    ss = st.session_state.get("shift_service")
    
    if not es:
        from services.employee_service import EmployeeService
        from services.center_service import CenterService
        from services.shift_service import ShiftService
        es = EmployeeService(auth)
        cs = CenterService(auth)
        ss = ShiftService(auth)
        st.session_state.employee_service = es
        st.session_state.center_service = cs
        st.session_state.shift_service = ss
    
    return es, cs, ss

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
# دوال تحويل وتنسيق الاستيراد
# ============================================================================

def convert_job_title(job_title):
    """تحويل المسمى الوظيفي إلى الكود الداخلي"""
    if pd.isna(job_title):
        return 'paramedic'
    
    job_title = str(job_title).strip()
    mapping = {
        'كبير مسعفين': 'chief_paramedic',
        'مساعد كبير مسعفين': 'assistant_chief',
        'قيادة ميدانية': 'field_leader',
        'تحكم عملياتي': 'operations_control',
        'تنسيق استجابة': 'response_coordinator',
        'أخصائي اسعاف': 'paramedic',
        'فني اسعاف': 'emt',
        'مساعد صحي': 'health_assistant',
        'دعم لوجستي': 'logistic_support',
        'إداري': 'admin',
        'مدير قطاع': 'chief_paramedic'
    }
    return mapping.get(job_title, 'paramedic')

def normalize_shift_code(code):
    """توحيد رموز المناوبات"""
    if pd.isna(code):
        return None
    
    code = str(code).upper().strip()
    
    # رموز معروفة
    valid_shifts = ['D12', 'N12', 'O12', 'V', 'VC', 'N8', 'O8', 'WO']
    
    if code in valid_shifts:
        # توحيد V و VC
        if code in ['V', 'VC']:
            return 'V'
        return code
    
    return None

def get_center_from_code(emp_code, cs):
    """تحديد المركز من كود الموظف"""
    if pd.isna(emp_code) or not emp_code or emp_code == 'nan':
        return None
    
    emp_code = str(emp_code).strip()
    centers = cs.get_centers()
    
    if not centers:
        return None
    
    # مدير القطاع والقيادات (0, A0, B0, C0, D0)
    if emp_code == '0' or emp_code in ['A0', 'B0', 'C0', 'D0']:
        hq_center = next((c for c in centers if c.get('code') == 'HQ'), None)
        return str(hq_center['id']) if hq_center else None
    
    # التداخلية والتدخل السريع (O12, O14, RR1, ...)
    if emp_code.startswith('O') or emp_code.startswith('RR'):
        center_12 = next((c for c in centers if c.get('code') == '12'), None)
        return str(center_12['id']) if center_12 else None
    
    # أعضاء الفرق (A1, A2, A10, B5, ...)
    if emp_code and emp_code[0] in 'ABCD' and len(emp_code) > 1 and emp_code[1:].isdigit():
        center_num = int(emp_code[1:])
        if 1 <= center_num <= 10:
            center = next((c for c in centers if c.get('code') == str(center_num)), None)
            return str(center['id']) if center else None
    
    # العمليات والدعم (XW1, Y, YY, ...)
    hq_center = next((c for c in centers if c.get('code') == 'HQ'), None)
    return str(hq_center['id']) if hq_center else None

# ============================================================================
# دالة استيراد Excel الشاملة (موظفين + مناوبات)
# ============================================================================

def import_complete_excel(uploaded_file, es, cs, ss):
    """استيراد كامل للموظفين والمناوبات (مع تحديث الموجود)"""
    try:
        # قراءة جميع الأوراق
        excel_file = pd.ExcelFile(uploaded_file)
        sheet_names = excel_file.sheet_names
        
        st.info(f"📑 تم العثور على {len(sheet_names)} أوراق")
        
        # ===== 1. استيراد/تحديث الموظفين من ورقة "الموظفين" =====
        employees_added = 0
        employees_updated = 0
        employees_failed = 0
        employees_data = {}  # {emp_no: {'id': id, 'emp_code': code, 'full_name': name}}
        
        if 'الموظفين' in sheet_names:
            df_employees = pd.read_excel(uploaded_file, sheet_name='الموظفين')
            st.write("📋 قراءة ورقة الموظفين...")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, row in df_employees.iterrows():
                status_text.text(f"جاري معالجة الموظفين {idx+1}/{len(df_employees)}...")
                
                try:
                    emp_no = str(row.get('رقم الموظف', '')).strip()
                    full_name = str(row.get('اسم الموظف', '')).strip()
                    job_title = str(row.get('طبيعة العمل', '')).strip()
                    emp_code = str(row.get('رمز الفرقة', '')).strip() if pd.notna(row.get('رمز الفرقة')) else ''
                    phone = str(row.get('رقم الجوال', '')).strip() if pd.notna(row.get('رقم الجوال')) else ''
                    
                    if not emp_no or not full_name:
                        employees_failed += 1
                        continue
                    
                    # تحويل المسمى الوظيفي
                    emp_type = convert_job_title(job_title)
                    
                    # تحديد المركز من الكود
                    center_id = get_center_from_code(emp_code, cs)
                    
                    if not center_id:
                        # استخدام المركز الرئيسي كبديل
                        centers = cs.get_centers()
                        hq_center = next((c for c in centers if c.get('code') == 'HQ'), None)
                        center_id = str(hq_center['id']) if hq_center else None
                    
                    # البحث عن الموظف القديم
                    existing = es.get_employees(search=emp_no)
                    
                    employee_data = {
                        'emp_no': emp_no,
                        'full_name': full_name,
                        'employee_type': emp_type,
                        'center_id': center_id,
                        'phone': phone,
                        'is_active': True
                    }
                    
                    if emp_code and emp_code != 'nan':
                        employee_data['emp_code'] = emp_code
                    
                    if existing and existing.get('items') and len(existing['items']) > 0:
                        # الموظف موجود → تحديث
                        emp_id = existing['items'][0]['id']
                        if es.update_employee(emp_id, employee_data):
                            employees_updated += 1
                            employees_data[emp_no] = {
                                'id': emp_id,
                                'emp_code': emp_code,
                                'full_name': full_name
                            }
                        else:
                            employees_failed += 1
                    else:
                        # موظف جديد → إضافة
                        result = es.create_employee(employee_data)
                        if result and result.get('id'):
                            employees_added += 1
                            employees_data[emp_no] = {
                                'id': result['id'],
                                'emp_code': emp_code,
                                'full_name': full_name
                            }
                        else:
                            employees_failed += 1
                        
                except Exception as e:
                    employees_failed += 1
                    print(f"خطأ في استيراد موظف: {e}")
                
                progress_bar.progress((idx + 1) / len(df_employees))
            
            status_text.text("")
            st.success(f"✅ الموظفين: {employees_added} جديد + {employees_updated} تحديث + {employees_failed} فشل")
        
        # ===== 2. تحديث المناوبات من ورقة "بيانات القطاع الجنوبي و الجدوله" =====
        shifts_success = 0
        shifts_failed = 0
        
        target_sheet = 'بيانات القطاع الجنوبي و الجدوله'
        if target_sheet in sheet_names and employees_data:
            df_schedule = pd.read_excel(uploaded_file, sheet_name=target_sheet, header=None)
            st.write("📅 تحديث جدول المناوبات...")
            
            # البحث عن بداية البيانات (الصف 10)
            start_row = None
            for i in range(20):
                if i < len(df_schedule) and pd.notna(df_schedule.iloc[i, 1]) and df_schedule.iloc[i, 1] == 'م':
                    start_row = i + 1  # الصف اللي بعده هو بداية البيانات
                    break
            
            if start_row:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # استخراج البيانات
                for idx in range(start_row, min(start_row + 200, len(df_schedule))):
                    row = df_schedule.iloc[idx]
                    
                    # الرقم التسلسلي (العمود B)
                    seq_num = str(row[1]).strip() if pd.notna(row[1]) else ''
                    if not seq_num or seq_num == 'nan' or seq_num == '':
                        continue
                    
                    # الكود (العمود C)
                    emp_no = str(row[2]).strip() if pd.notna(row[2]) else ''
                    
                    status_text.text(f"جاري استيراد مناوبات الموظف {emp_no}...")
                    
                    if emp_no and emp_no in employees_data:
                        employee_id = employees_data[emp_no]['id']
                        
                        # قراءة المناوبات للأيام 1-31 (الأعمدة G إلى AK)
                        for day in range(1, 32):
                            col_index = 5 + day  # G=6, H=7, ... AK=36
                            if col_index < len(row):
                                shift_code = row[col_index] if pd.notna(row[col_index]) else ''
                                
                                if shift_code and shift_code != '' and shift_code != 'nan':
                                    normalized_shift = normalize_shift_code(shift_code)
                                    
                                    if normalized_shift:
                                        # حساب التاريخ (نستخدم الشهر الحالي)
                                        year = datetime.now().year
                                        month = datetime.now().month
                                        date_str = f"{year}-{month:02d}-{day:02d}"
                                        
                                        # حفظ المناوبة
                                        if ss.update_employee_shift(str(employee_id), date_str, normalized_shift):
                                            shifts_success += 1
                                        else:
                                            shifts_failed += 1
                    else:
                        shifts_failed += 1
                    
                    progress_bar.progress((idx - start_row + 1) / (min(start_row + 200, len(df_schedule)) - start_row + 1))
                
                status_text.text("")
                st.success(f"✅ تم تحديث {shifts_success} مناوبة")
            else:
                st.warning("⚠️ لم يتم العثور على بداية جدول المناوبات")
        
        return employees_added, employees_updated, shifts_success
        
    except Exception as e:
        st.error(f"❌ خطأ في معالجة الملف: {str(e)}")
        return 0, 0, 0

# ============================================================================
# دالة استيراد Excel القديمة (للتوافق)
# ============================================================================

def import_employees_from_excel(uploaded_file, es, cs):
    """استيراد الموظفين من ملف Excel (للتوافق مع الكود القديم)"""
    try:
        # استخدام الدالة الشاملة مع تجاهل المناوبات
        ss = st.session_state.get("shift_service")
        if not ss:
            from services.shift_service import ShiftService
            ss = ShiftService(st.session_state.auth_service)
        
        added, updated, shifts = import_complete_excel(uploaded_file, es, cs, ss)
        return added + updated, 0
        
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
    
    es, cs, ss = _get_services()
    centers = cs.get_centers() or []
    user_center_id = get_user_center()
    
    # التبويبات الرئيسية
    if has_permission("manage_all") or has_permission("manage_station"):
        tabs = st.tabs(["📋 قائمة الموظفين", "➕ إضافة موظف"])
    else:
        tabs = st.tabs(["📋 بياناتي", "📅 جدول مناوباتي"])
    
    # ===== قسم استيراد Excel (محدث) =====
    with st.expander("📥 استيراد موظفين ومناوبات من Excel", expanded=False):
        st.markdown("""
        <div style="background: #F0F9FF; padding: 1rem; border-radius: 12px; margin-bottom: 1rem;">
            <h5 style="margin: 0 0 0.5rem 0;">📌 تعليمات:</h5>
            <ul style="margin: 0; padding-right: 1.5rem; font-size: 0.9rem;">
                <li>الملف يجب أن يحتوي على ورقتين: <b>الموظفين</b> و <b>بيانات القطاع الجنوبي و الجدوله</b></li>
                <li>سيتم إضافة الموظفين الجدد وتحديث الموجودين تلقائياً</li>
                <li>سيتم تحديث جدول المناوبات بالكامل</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "📤 اختر ملف Excel",
            type=['xlsx', 'xls'],
            key="emp_upload_complete"
        )
        
        if uploaded_file:
            try:
                # عرض معاينة للملف
                df_preview = pd.read_excel(uploaded_file, sheet_name=0, nrows=5)
                st.dataframe(df_preview.head(3), use_container_width=True)
                
                if st.button("🚀 بدء الاستيراد الشامل", use_container_width=True, type="primary"):
                    added, updated, shifts = import_complete_excel(uploaded_file, es, cs, ss)
                    
                    st.success(f"✅ تمت العملية بنجاح!")
                    
                    # عرض إحصائيات
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("🆕 موظفين جدد", added)
                    with col2:
                        st.metric("🔄 تم التحديث", updated)
                    with col3:
                        st.metric("📅 مناوبات", shifts)
                    with col4:
                        st.metric("📦 الإجمالي", added + updated)
                    
                    # زر تحديث
                    if added > 0 or updated > 0 or shifts > 0:
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
        
        # جلب البيانات مع كسر Cache
        with st.spinner("جاري التحميل..."):
            result = es.get_employees(limit=500, _cache_buster=random.randint(1, 10000))
        
        all_employees = result.get("items", []) if result else []
        
        # إضافة حقل emp_code من البيانات
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
            center_options = ["الكل"] + [c['name'] for c in centers if c.get('code') not in ['HQ', '0']]
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
                            "الفريق": decoded.get('team_name', '') or decoded.get('type', ''),
                            "الدور": decoded.get('role', ''),
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
                emp_code = st.text_input("🔤 رمز الموظف", placeholder="مثال: A1, B5, C10, D0, RR1, XW2")
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
                    if emp_code:
                        data["emp_code"] = emp_code
                    
                    if es.create_employee(data):
                        st.success(f"✅ تم إضافة {full_name}")
                        st.balloons()
                        st.rerun()
    
    # ===== قسم التعديل الجماعي =====
    if has_permission("manage_all"):
        with st.expander("✏️ تعديل جماعي للموظفين", expanded=False):
            st.markdown("""
            <div style="background: #F0F9FF; padding: 1rem; border-radius: 12px; margin-bottom: 1rem;">
                <h5 style="margin: 0 0 0.5rem 0;">📌 تعديل موظف:</h5>
                <p>أدخل الرقم الوظيفي وعدل البيانات</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 2])
            with col1:
                search_emp_no = st.text_input("🔍 الرقم الوظيفي", key="quick_edit_search")
            
            if search_emp_no:
                # البحث عن الموظف
                search_result = es.get_employees(search=search_emp_no)
                if search_result and search_result.get('items'):
                    emp = search_result['items'][0]
                    
                    st.markdown("---")
                    st.subheader(f"✏️ تعديل: {emp['full_name']}")
                    
                    with st.form("quick_edit_form"):
                        qc1, qc2 = st.columns(2)
                        with qc1:
                            new_name = st.text_input("الاسم", value=emp.get('full_name', ''))
                            new_type = st.selectbox(
                                "النوع", 
                                list(EMP_TYPE_LABELS.keys()),
                                index=list(EMP_TYPE_LABELS.keys()).index(emp.get('employee_type', 'admin')) if emp.get('employee_type') in EMP_TYPE_LABELS else 0,
                                format_func=lambda x: EMP_TYPE_LABELS.get(x, x)
                            )
                            new_code = st.text_input("الرمز", value=emp.get('emp_code', ''), placeholder="مثال: A1, B5, C10")
                        
                        with qc2:
                            center_list = [c['name'] for c in centers]
                            current_center = next((c['name'] for c in centers if c['id'] == emp.get('center_id')), "المركز الرئيسي")
                            new_center = st.selectbox(
                                "المركز",
                                center_list,
                                index=center_list.index(current_center) if current_center in center_list else 0
                            )
                            is_active = st.checkbox("نشط", value=emp.get('is_active', True))
                        
                        if st.form_submit_button("💾 حفظ", use_container_width=True, type="primary"):
                            # تحديد ID المركز
                            center_id = next((c['id'] for c in centers if c['name'] == new_center), None)
                            
                            if center_id:
                                data = {
                                    "full_name": new_name,
                                    "employee_type": new_type,
                                    "emp_code": new_code,
                                    "center_id": str(center_id),
                                    "is_active": is_active
                                }
                                if es.update_employee(emp['id'], data):
                                    st.success("✅ تم التحديث")
                                    st.session_state.force_reload_employees = True
                                    st.rerun()
                            else:
                                st.error("❌ المركز غير موجود")
                else:
                    st.warning("⚠️ لا يوجد موظف بهذا الرقم")
    
    # ===== منطقة الخطر (للإدارة العليا فقط) =====
    if has_permission("manage_all") and st.session_state.get("user_role") == "chief_paramedic":
        st.markdown("---")
        st.markdown("""
        <div style="background: #FFEBEE; border: 1.5px solid #FFCDD2; border-radius: 14px; padding: 1.25rem; direction: rtl; margin: 1.5rem 0;">
            <h4 style="color: #C62828; margin: 0 0 0.75rem; display: flex; align-items: center; gap: 0.5rem;">
                ⚠️ منطقة الخطر
            </h4>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col2:
            if st.button("🗑️ مسح جميع الموظفين", use_container_width=True, type="primary"):
                st.session_state.confirm_delete_all = True
        
        if st.session_state.get("confirm_delete_all", False):
            st.warning("⚠️ هل أنت متأكد؟ هذا الإجراء لا يمكن التراجع عنه!")
            col1, col2, col3, col4 = st.columns(4)
            with col2:
                if st.button("✅ نعم، متأكد", use_container_width=True):
                    try:
                        # جلب جميع الموظفين وحذفهم
                        result = es.get_employees(limit=1000)
                        employees_to_delete = result.get("items", [])
                        deleted_count = 0
                        
                        for emp in employees_to_delete:
                            if es.delete_employee(emp["id"]):
                                deleted_count += 1
                        
                        st.success(f"✅ تم حذف {deleted_count} موظف بنجاح")
                        st.session_state.force_reload_employees = True
                        st.session_state.confirm_delete_all = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ حدث خطأ: {str(e)}")
            
            with col3:
                if st.button("❌ إلغاء", use_container_width=True):
                    st.session_state.confirm_delete_all = False
                    st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ===== قسم التعديل القديم (للتوافق) =====
    if "editing_employee" in st.session_state:
        st.markdown("---")
        emp = st.session_state.editing_employee
        st.subheader(f"✏️ تعديل: {emp.get('full_name','')}")
        
        with st.form("edit_employee_form"):
            c1, c2 = st.columns(2)
            with c1:
                emp_no = st.text_input("📋 الرقم الوظيفي", value=emp.get("emp_no",""), disabled=True)
                full_name = st.text_input("👤 الاسم الكامل *", value=emp.get("full_name",""))
                emp_code = st.text_input("🔤 رمز الموظف", value=emp.get("emp_code",""), placeholder="مثال: A1, B5, C10")
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
                if emp_code:
                    data["emp_code"] = emp_code
                
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