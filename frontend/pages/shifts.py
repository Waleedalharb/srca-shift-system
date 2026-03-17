# frontend/pages/shifts.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
from utils.helpers import page_header, section_title
from components.cards import kpi_row
from components.charts import create_line_chart, display_chart
from utils.constants import SHIFT_TYPES, get_all_shift_codes, get_shift_info
import random
import requests
from config import config
import time  # 👈 لقياس الأداء

# ============================================================================
# ✅ تحسين: دوال التخزين المؤقت (Caching) - مع underscore للمعاملات
# ============================================================================

@st.cache_data(ttl=300, show_spinner="جاري تحميل الموظفين...")
def get_employees_cached(_es, center_id, cache_buster=None):
    """تخزين الموظفين في الكاش لمدة 5 دقائق"""
    return _es.get_employees(
        center_id=center_id,
        _cache_buster=cache_buster or random.randint(1, 10000)
    ).get("items", [])

@st.cache_data(ttl=60, show_spinner="جاري تحميل المناوبات...")  # 👈 رجعناها 60 ثانية
def get_shifts_cached(_ss, center_id, year, month):
    """تخزين المناوبات في الكاش لمدة دقيقة"""
    return _ss.get_shifts_by_month(center_id, year, month)

@st.cache_data(ttl=300, show_spinner=False)
def get_employees_dict_cached(_es):
    """تخزين قاموس الموظفين (للربط السريع) - يستخدم في الاستيراد"""
    all_employees = _es.get_employees(limit=500).get("items", [])
    emp_dict = {}
    for emp in all_employees:
        emp_no = emp.get('emp_no')
        if emp_no:
            emp_dict[str(emp_no).strip()] = emp
    return emp_dict

@st.cache_data(ttl=600, show_spinner=False)
def get_centers_cached(_cs):
    """تخزين المراكز في الكاش لمدة 10 دقائق"""
    return _cs.get_centers() or []

# ============================================================================
# دوال مساعدة لاستيراد المناوبات
# ============================================================================

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
    # إذا الرمز غير معروف، نرجعه كما هو (النظام سيأخذه)
    return code

def import_shifts_from_master_sheet(uploaded_file, ss, year, month):
    """استيراد المناوبات من ورقة 'بيانات ومعلومات القطاع الجنوبي'"""
    try:
        excel_file = pd.ExcelFile(uploaded_file)
        sheet_names = excel_file.sheet_names
        
        # ✅ نبحث عن الورقة الصحيحة
        target_sheet = 'بيانات ومعلومات القطاع الجنوبي'
        if target_sheet not in sheet_names:
            st.warning(f"⚠️ لم يتم العثور على ورقة '{target_sheet}'")
            st.info(f"الأوراق الموجودة: {', '.join(sheet_names)}")
            return 0, 0
        
        # قراءة الورقة بدون header
        df = pd.read_excel(uploaded_file, sheet_name=target_sheet, header=None)
        
        # ✅ نبدأ من الصف 10 مباشرة (index 9 في Python)
        start_row = 9  # الصف 10 (لأن العد يبدأ من 0)
        
        st.success(f"✅ بدأنا القراءة من الصف 10 في ورقة '{target_sheet}'")
        
        # ✅ تحسين: استخدام الكاش لجلب الموظفين
        cs, es, _ = _get_services()
        emp_dict = get_employees_dict_cached(es)
        
        st.info(f"✅ تم تحميل {len(emp_dict)} موظف من قاعدة البيانات")
        
        # ===== تشخيص: عرض أول 5 صفوف من الملف =====
        st.write("🔍 **عينة من أول 5 صفوف في الملف:**")
        sample_data = []
        for i in range(start_row, min(start_row + 5, len(df))):
            row_data = df.iloc[i]
            code = str(row_data[1]).strip() if pd.notna(row_data[1]) else 'فارغ'  # العمود B (الكود)
            name = str(row_data[2]).strip() if pd.notna(row_data[2]) else 'فارغ'  # العمود C (الاسم)
            sample_data.append(f"الصف {i+1}: الكود={code}, الاسم={name}")
        
        for line in sample_data:
            st.write(line)
        # =============================================
        
        success = 0
        failed = 0
        errors = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # ✅ نقرأ كل الصفوف حتى نهاية الملف
        total_rows = len(df) - start_row
        batch_data = []  # 👈 تجميع للتحديث الدفعي
        
        for idx in range(start_row, len(df)):
            row = df.iloc[idx]
            
            # الكود (الرقم الوظيفي) - العمود B (index 1) - هذا هو المهم للربط
            emp_no = str(row[1]).strip() if pd.notna(row[1]) else ''
            
            # الاسم - العمود C (index 2) - للعرض فقط
            emp_name = str(row[2]).strip() if pd.notna(row[2]) else ''
            
            # نتأكد إن الكود موجود
            if not emp_no or emp_no == 'فارغ':
                continue
            
            status_text.text(f"جاري استيراد مناوبات: {emp_name} (كود: {emp_no})...")
            
            if emp_no in emp_dict:
                employee_id = emp_dict[emp_no]['id']
                
                # قراءة المناوبات للأيام 1-31 (الأعمدة G إلى AK)
                # G = index 6, H=7, ... AK=36
                for day in range(1, 32):
                    col_index = 5 + day  # 5+1=6 (G), 5+2=7 (H), ...
                    if col_index < len(row):
                        shift_code = row[col_index] if pd.notna(row[col_index]) else ''
                        
                        if shift_code and str(shift_code).strip() not in ['', 'nan']:
                            normalized = normalize_shift_code(str(shift_code))
                            
                            if normalized:
                                date_str = f"{year}-{month:02d}-{day:02d}"
                                # ✅ تحسين: تجميع للتحديث الدفعي
                                batch_data.append({
                                    "employee_id": str(employee_id),
                                    "date": date_str,
                                    "shift_type": normalized
                                })
                                success += 1
                            else:
                                # حتى لو الرمز غير معروف، نحاول نحفظه
                                date_str = f"{year}-{month:02d}-{day:02d}"
                                batch_data.append({
                                    "employee_id": str(employee_id),
                                    "date": date_str,
                                    "shift_type": str(shift_code)
                                })
                                success += 1
            else:
                failed += 1
                errors.append(f"⚠️ الموظف بكود {emp_no} غير موجود في قاعدة البيانات")
            
            progress_bar.progress((idx - start_row + 1) / total_rows)
            
            # ✅ تحسين: كل 500 مناوبة نرسل دفعة
            if len(batch_data) >= 500:
                if hasattr(ss, 'batch_update_shifts'):
                    ss.batch_update_shifts(batch_data)
                else:
                    # إذا ما في batch update، نستخدم الطريقة القديمة
                    for item in batch_data:
                        ss.update_employee_shift(item["employee_id"], item["date"], item["shift_type"])
                batch_data = []
                status_text.text(f"✅ تم استيراد {success} مناوبة...")
        
        # ✅ تحسين: نرسل آخر دفعة
        if batch_data:
            if hasattr(ss, 'batch_update_shifts'):
                ss.batch_update_shifts(batch_data)
            else:
                for item in batch_data:
                    ss.update_employee_shift(item["employee_id"], item["date"], item["shift_type"])
        
        status_text.text("")
        
        if errors:
            with st.expander(f"🔍 عرض الأخطاء والتحذيرات ({len(errors)})"):
                for err in errors[:30]:
                    st.warning(err)
        
               # 🔥🔥🔥 الحل النهائي لمشكلة انعكاس الجدول 🔥🔥🔥
        if success > 0:
            # 1. مسح كل أنواع الكاش
            st.cache_data.clear()
            st.cache_resource.clear()
            
            # 2. إعادة تعيين الـ Session State
            st.session_state.reload_shifts = True
            st.session_state.refresh_shifts_data = True
            st.session_state.shift_service = None
            st.session_state.import_completed = True  # 👈 أضفنا هذا
            st.session_state.import_count = success    # 👈 أضفنا هذا
            
            # 3. مسح المتغيرات المخزنة في Session State
            keys_to_clear = []
            for key in st.session_state.keys():
                if key.startswith('get_') or 'shifts' in key or 'employees' in key or 'centers' in key:
                    keys_to_clear.append(key)
            for key in keys_to_clear:
                del st.session_state[key]
            
            # 4. 👈 نحذف st.rerun() ونخلي المستخدم يضغط بنفسه
            st.success(f"✅ تم استيراد {success} مناوبة بنجاح!")
            st.balloons()
            st.info("👆 اضغط على زر '🔄 تحديث الجدول' في أعلى الصفحة لمشاهدة البيانات الجديدة")
            
            # 5. نرجع النتيجة بدون rerun
            return success, failed
        
    except Exception as e:
        st.error(f"❌ خطأ في معالجة الملف: {str(e)}")
        return 0, 0

# ===== دالة استيراد المناوبات من Excel (للتوافق مع الكود القديم) =====
def import_shifts_from_excel(uploaded_file, ss, employees, year, month):
    """استيراد المناوبات من ملف Excel (نسخة احتياطية)"""
    try:
        df = pd.read_excel(uploaded_file)
        
        # التحقق من الأعمدة المطلوبة
        required = ['الرقم الوظيفي', 'اليوم', 'المناوبة']
        missing = [col for col in required if col not in df.columns]
        if missing:
            st.error(f"❌ الأعمدة المفقودة: {missing}")
            return 0, len(df)
        
        # إنشاء قاموس للموظفين (الرقم الوظيفي -> id)
        emp_dict = {emp.get('emp_no'): emp['id'] for emp in employees if emp.get('emp_no')}
        
        success = 0
        failed = 0
        errors = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        batch_data = []
        
        for idx, row in df.iterrows():
            status_text.text(f"جاري استيراد {idx+1}/{len(df)}...")
            
            try:
                emp_no = str(row['الرقم الوظيفي']).strip()
                day = int(row['اليوم'])
                shift_code = str(row['المناوبة']).strip()
                
                # التحقق من صحة اليوم
                if day < 1 or day > calendar.monthrange(year, month)[1]:
                    failed += 1
                    errors.append(f"سطر {idx+2}: اليوم {day} غير صحيح للشهر")
                    continue
                
                # التحقق من صحة رمز المناوبة
                if shift_code not in SHIFT_TYPES and shift_code != "":
                    failed += 1
                    errors.append(f"سطر {idx+2}: رمز المناوبة {shift_code} غير معروف")
                    continue
                
                # البحث عن الموظف
                if emp_no not in emp_dict:
                    failed += 1
                    errors.append(f"سطر {idx+2}: الرقم الوظيفي {emp_no} غير موجود")
                    continue
                
                emp_id = emp_dict[emp_no]
                date_str = f"{year}-{month:02d}-{day:02d}"
                
                # حفظ المناوبة (إذا كان shift_code فارغ نرسل "off")
                save_shift = shift_code if shift_code else "off"
                batch_data.append({
                    "employee_id": str(emp_id),
                    "date": date_str,
                    "shift_type": save_shift
                })
                success += 1
                
                # ✅ تحسين: كل 200 مناوبة نرسل دفعة
                if len(batch_data) >= 200:
                    if hasattr(ss, 'batch_update_shifts'):
                        ss.batch_update_shifts(batch_data)
                    else:
                        for item in batch_data:
                            ss.update_employee_shift(item["employee_id"], item["date"], item["shift_type"])
                    batch_data = []
                    
            except Exception as e:
                failed += 1
                errors.append(f"سطر {idx+2}: {str(e)}")
            
            progress_bar.progress((idx + 1) / len(df))
        
        # ✅ تحسين: آخر دفعة
        if batch_data:
            if hasattr(ss, 'batch_update_shifts'):
                ss.batch_update_shifts(batch_data)
            else:
                for item in batch_data:
                    ss.update_employee_shift(item["employee_id"], item["date"], item["shift_type"])
        
        if errors:
            st.warning(f"⚠️ يوجد {len(errors)} خطأ")
            for err in errors[:10]:
                st.warning(err)
        
        return success, failed
        
    except Exception as e:
        st.error(f"❌ خطأ في معالجة الملف: {str(e)}")
        return 0, 0

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

# ===== دالة حساب ساعات الموظف =====
def calculate_employee_hours(employee_data, emp_shifts, days_in_month, center_name):
    """
    حساب ساعات الموظف
    """
    emp_code = employee_data.get('emp_code', '')
    
    total = 0
    for day in range(1, days_in_month + 1):
        shift_type = emp_shifts.get(day)
        if shift_type and shift_type in SHIFT_TYPES:
            if shift_type in ['D12', 'N12', 'O12']:
                total += 12
            elif shift_type == 'V':
                total += 0
            else:
                total += SHIFT_TYPES[shift_type]["hours"]
    return total

# ===== دالة عرض تقرير الطباعة =====
def show_printable_report(employee_data, shifts_data, year, month, center_name, employee_name):
    """
    عرض تقرير المناوبات بشكل مناسب للطباعة
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
    
    # حساب إجمالي الساعات
    total_hours = calculate_employee_hours(employee_data, emp_shifts, days_in_month, center_name)
    
    # بناء جدول الأيام
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
    
    # أيام الأسبوع
    weekdays_ar = ["الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]
    first_day = calendar.weekday(year, month, 1)
    
    # إنشاء شبكة الأيام
    calendar_days = []
    week = []
    for i in range(first_day):
        week.append("")
    for day in range(1, days_in_month + 1):
        week.append(day)
        if len(week) == 7:
            calendar_days.append(week)
            week = []
    if week:
        while len(week) < 7:
            week.append("")
        calendar_days.append(week)
    
    # بناء الجدول
    html_content += '<table class="shifts-table"><tr>'
    for day_name in weekdays_ar:
        html_content += f'<th>{day_name}</th>'
    html_content += '</tr>'
    
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
    html_content += f"""
        <div class="footer">
            <div>توقيع المشرف: ________________</div>
            <div>الختم: ________________</div>
            <div>تاريخ الطباعة: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
        </div>
    </div>
    """
    
    st.markdown(html_content, unsafe_allow_html=True)
    st.markdown("""
    <div class="print-button">
        <button onclick="window.print()">🖨️ طباعة التقرير</button>
    </div>
    """, unsafe_allow_html=True)
    
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
    """صفحة إدارة المناوبات - نسخة محسنة الأداء مع تشخيص"""
    
    # ===== قياس وقت التحميل =====
    start_time = time.time()
    
    # ===== 🔥 حل نهائي: التحقق من باراميتر import_success =====
    if st.query_params.get("import_success"):
        # مسح كل الكاش
        st.cache_data.clear()
        st.cache_resource.clear()
        st.session_state.shift_service = None
        
        # مسح المتغيرات المخزنة
        keys_to_clear = []
        for key in st.session_state.keys():
            if key.startswith('get_') or 'shifts' in key or 'employees' in key or 'centers' in key:
                keys_to_clear.append(key)
        for key in keys_to_clear:
            del st.session_state[key]
        
        # إزالة الباراميتر من الرابط
        st.query_params.clear()
        st.rerun()
    # ========================================================
    
    # ===== 🔍 تشخيص مشعل الحجيلي (6182) =====
    with st.sidebar:
        st.markdown("### 🔍 تشخيص")
        if st.button("🔍 تشخيص مشعل", use_container_width=True, type="primary"):
            cs, es, ss = _get_services()
            # نجيب كل الموظفين
            all_emps = es.get_employees(limit=500).get("items", [])
            mishal = next((e for e in all_emps if e.get('emp_no') == '6182'), None)
            
            if mishal:
                st.success(f"👤 {mishal['full_name']} (كود: {mishal.get('emp_no')})")
                
                # نجيب مناوباته لشهر مارس 2026
                shifts = ss.get_employee_shifts_by_month(mishal['id'], 2026, 3)
                st.write(f"📊 **عدد المناوبات في مارس:** {len(shifts)}")
                
                if shifts:
                    st.write("**أول 3 مناوبات:**")
                    for i, shift in enumerate(shifts[:3]):
                        st.write(f"{i+1}. تاريخ: {shift.get('date')} - نوع: {shift.get('shift_type')}")
                else:
                    st.error("❌ لا يوجد مناوبات لهذا الموظف في مارس!")
            else:
                st.error("❌ مشعل غير موجود في قاعدة البيانات!")
    # ====================================================
    
    # ===== حل مشكلة عدم التحديث =====
    if 'refresh_shifts_data' in st.session_state and st.session_state.refresh_shifts_data:
        st.session_state.shift_service = None
        st.session_state.refresh_shifts_data = False
        st.cache_data.clear()
        st.cache_resource.clear()
    # =================================
    
    # ===== متغير للتحكم بإعادة التحميل =====
    if 'reload_shifts' in st.session_state and st.session_state.reload_shifts:
        st.session_state.shift_service = None
        st.session_state.reload_shifts = False
        st.cache_data.clear()
    
    page_header("📅 إدارة المناوبات", "عرض، إضافة، تعديل، توليد تلقائي للمناوبات", "⏰")
    
    # ===== عرض الدوام الرسمي =====
    show_official_schedule()
    
       # أزرار التحكم - تم إضافة زر التنظيف هنا
    col1, col2, col3, col4 = st.columns([7, 1, 1, 1])
    with col2:
        if st.button("🔄 تحديث", use_container_width=True):
            st.cache_data.clear()
            st.session_state.shift_service = None
            st.rerun()
    with col3:
        if st.button("🗑️ مسح", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.session_state.clear()
            st.rerun()
    with col4:
        if st.button("🧹 تنظيف", use_container_width=True, type="secondary"):
            with st.spinner("جاري تنظيف البيانات القديمة..."):
                try:
                    # ✅ الحل: نجيب الخدمة داخل الزر
                    cs, es, ss = _get_services()
                    result = ss.cleanup_all_shifts(month=month, year=year)
                    if result and result.get("deleted_assignments", 0) > 0:
                        st.success(f"✅ تم حذف {result.get('deleted_assignments', 0)} تعيين و {result.get('deleted_shifts', 0)} مناوبة")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.info("لا توجد بيانات قديمة للحذف")
                except Exception as e:
                    st.error(f"❌ فشل التنظيف: {str(e)}")
    
    cs, es, ss = _get_services()
    centers = get_centers_cached(cs)  # ✅ استخدام الكاش
    
    if not centers:
        st.warning("❌ لا توجد مراكز متاحة")
        return
    
    # ===== اختيار المركز والشهر مع حفظ الحالة =====
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        center_names = [c["name"] for c in centers]
        
        # حفظ آخر مركز مختار
        if 'last_center' not in st.session_state:
            st.session_state.last_center = center_names[0]
        
        selected_center = st.selectbox(
            "🏥 المركز", 
            center_names,
            index=center_names.index(st.session_state.last_center) if st.session_state.last_center in center_names else 0
        )
        st.session_state.last_center = selected_center
        center_id = next(c["id"] for c in centers if c["name"] == selected_center)
    
    with col2:
        # حفظ آخر سنة مختارة
        if 'last_year' not in st.session_state:
            st.session_state.last_year = datetime.now().year
        year = st.number_input("📅 السنة", 2020, 2030, st.session_state.last_year)
        st.session_state.last_year = year
    
    with col3:
        # حفظ آخر شهر مختار
        if 'last_month' not in st.session_state:
            st.session_state.last_month = datetime.now().month
        month = st.number_input("📆 الشهر", 1, 12, st.session_state.last_month)
        st.session_state.last_month = month
    
    with col4:
        view_mode = st.radio("عرض", ["📋 الجدول", "✏️ تعديل", "➕ إضافة", "⚡ توليد تلقائي", "🔄 تكميل الفرق", "📥 استيراد Excel", "💡 مساعد ذكي"], horizontal=True)
    
    # ===== جلب الموظفين مع استخدام الكاش =====
    with st.spinner("جاري تحميل الموظفين..."):
        employees = get_employees_cached(
            es, 
            center_id, 
            cache_buster=random.randint(1, 10000) if st.session_state.get('refresh_employees', False) else None
        )
    
    if not employees:
        st.warning(f"⚠️ لا يوجد موظفون في {selected_center}")
        return
    
    # جلب المناوبات للشهر المحدد مع الكاش (ttl=60)
    with st.spinner("جاري تحميل المناوبات..."):
        shifts = get_shifts_cached(ss, center_id, year, month)
    
    # ===== تشخيص: نشوف أول 3 مناوبات من الـ API =====
    if st.checkbox("🔍 إظهار التشخيص", value=False):
        st.write("🔍 **تشخيص - أول 3 مناوبات من API:**")
        for i, shift in enumerate(shifts[:3]):
            st.write(f"مناوبة {i+1}:")
            st.json(shift)
    
    # ✅ ===== تصفية المناوبات القديمة (اللي فيها employee_id = NULL) =====
    filtered_shifts = []
    for shift in shifts:
        has_valid_assignment = False
        for assignment in shift.get("assignments", []):
            if assignment.get("employee_id"):
                has_valid_assignment = True
                break
        if has_valid_assignment:
            filtered_shifts.append(shift)
    
    if len(filtered_shifts) < len(shifts) and st.checkbox("📊 إظهار إحصائيات التصفية", value=False):
        st.info(f"📊 من أصل {len(shifts)} مناوبة، {len(filtered_shifts)} فقط فيها تعيينات صحيحة (تم تجاهل {len(shifts) - len(filtered_shifts)} مناوبة قديمة)")
    
    shifts = filtered_shifts  # نستخدم المصفاة
    # ====================================================

    # ✅ ===== الطريقة الصحيحة: جلب مناوبات كل موظف على حدة =====
    shifts_map = {}
    
    # نجيب مناوبات كل موظف لحاله
    for emp in employees:
        emp_id = str(emp["id"])
        emp_shifts_list = ss.get_employee_shifts_by_month(emp_id, year, month)
        
        # ✅ تشخيص لمشعل (6182)
        if emp.get('emp_no') == '6182':
            st.sidebar.info(f"🔍 مشعل: جلبنا {len(emp_shifts_list)} مناوبة من API")
        
        # نحول القائمة إلى قاموس {day: shift_type}
        emp_shifts_dict = {}
        for shift in emp_shifts_list:
            shift_date = shift.get("date", "").split("T")[0]
            try:
                day = int(shift_date.split("-")[2])
                shift_type = shift.get("shift_type")
                if shift_type and shift_type != "off":
                    emp_shifts_dict[day] = shift_type
            except:
                continue
        
        shifts_map[emp_id] = emp_shifts_dict
    
    days_in_month = calendar.monthrange(year, month)[1]
    
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
                    if shift_type in ['D12', 'N12', 'O12']:
                        total_hours += 12
                    elif shift_type == 'V':
                        total_hours += 0
                    else:
                        total_hours += SHIFT_TYPES[shift_type]["hours"]
            
            total_hours_all += total_hours
            
            # ✅ نسبة الإنجاز = إجمالي الساعات ÷ 192 ساعة (المطلوب شهرياً)
            required_hours = 192
            completion_rate = int((total_hours / required_hours) * 100) if required_hours > 0 else 0
            completion_rate = min(completion_rate, 100)  # ما تزيد عن 100%
            
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
            cols = st.columns(5)
            codes_to_show = ["D12", "N12", "O12", "V", "CP8"]
            for i, code in enumerate(codes_to_show):
                if code in SHIFT_TYPES:
                    info = SHIFT_TYPES[code]
                    with cols[i % 5]:
                        st.markdown(f"<div style='background:{info['color']}; color:{info['text_color']}; padding:0.5rem; border-radius:8px; text-align:center;'><strong>{code}</strong> - {info['name']}</div>", unsafe_allow_html=True)
    
    # ===== باقي الأوضاع (✏️ تعديل، ➕ إضافة، ⚡ توليد تلقائي، ...) =====
    elif view_mode == "✏️ تعديل":
        st.subheader("✏️ تعديل المناوبات")
        
        # حل مشكلة عدم التحديث
        if 'last_emp_selected' not in st.session_state:
            st.session_state.last_emp_selected = None
        
        emp_names = [f"{e['full_name']} ({e.get('emp_no', '')})" for e in employees]
        selected_emp_name = st.selectbox("👤 اختر الموظف", emp_names, key="emp_selector")
        
        if selected_emp_name != st.session_state.last_emp_selected:
            st.session_state.last_emp_selected = selected_emp_name
            keys_to_clear = ['single_day', 'single_shift', 'range_from', 'range_to', 'range_shift']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
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
                    shift_options = [""] + ["D12", "N12", "O12", "V", "CP8", "CP24", "LN8"]
                    current_shift = emp_shifts.get(day, "")
                    current_index = shift_options.index(current_shift) if current_shift in shift_options else 0
                    new_shift = st.selectbox(
                        "المناوبة",
                        options=shift_options,
                        format_func=lambda x: {
                            "": "بدون مناوبة",
                            "D12": "D12 - صباحي 12 س",
                            "N12": "N12 - ليلي 12 س",
                            "O12": "O12 - تداخلي 12 س",
                            "V": "V - إجازة",
                            "CP8": "CP8 - تكميلية 8 س",
                            "CP24": "CP24 - تكميلية 24 س",
                            "LN8": "LN8 - ليلي تكميلي 8 س"
                        }.get(x, x),
                        index=current_index,
                        key="single_shift"
                    )
                with col3:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🗑️ حذف", key="delete_single", use_container_width=True):
                        date_str = f"{year}-{month:02d}-{day:02d}"
                        if ss.update_employee_shift(emp_id, date_str, "off"):
                            st.success(f"✅ تم حذف مناوبة يوم {day}")
                            st.session_state.reload_shifts = True
                            st.session_state.refresh_shifts_data = True
                            st.rerun()
                
                if st.button("💾 حفظ التغيير", key="save_single", use_container_width=True, type="primary"):
                    if new_shift:
                        date_str = f"{year}-{month:02d}-{day:02d}"
                        if ss.update_employee_shift(emp_id, date_str, new_shift):
                            st.success(f"✅ تم تحديث يوم {day} إلى {new_shift}")
                            st.session_state.reload_shifts = True
                            st.session_state.refresh_shifts_data = True
                            st.rerun()
            
            else:  # نطاق أيام
                col1, col2 = st.columns(2)
                with col1:
                    from_day = st.number_input("من يوم", 1, days_in_month, 1, key="range_from")
                with col2:
                    to_day = st.number_input("إلى يوم", from_day, days_in_month, from_day, key="range_to")
                
                shift_options = [""] + ["D12", "N12", "O12", "V", "CP8", "CP24", "LN8"]
                new_shift = st.selectbox(
                    "المناوبة",
                    options=shift_options,
                    format_func=lambda x: {
                        "": "بدون مناوبة",
                        "D12": "D12 - صباحي 12 س",
                        "N12": "N12 - ليلي 12 س",
                        "O12": "O12 - تداخلي 12 س",
                        "V": "V - إجازة",
                        "CP8": "CP8 - تكميلية 8 س",
                        "CP24": "CP24 - تكميلية 24 س",
                        "LN8": "LN8 - ليلي تكميلي 8 س"
                    }.get(x, x),
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
                    st.session_state.reload_shifts = True
                    st.session_state.refresh_shifts_data = True
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
                    options=[""] + ["D12", "N12", "O12", "V", "CP8", "CP24", "LN8"],
                    format_func=lambda x: {
                        "": "بدون مناوبة",
                        "D12": "D12 - صباحي 12 س",
                        "N12": "N12 - ليلي 12 س",
                        "O12": "O12 - تداخلي 12 س",
                        "V": "V - إجازة",
                        "CP8": "CP8 - تكميلية 8 س",
                        "CP24": "CP24 - تكميلية 24 س",
                        "LN8": "LN8 - ليلي تكميلي 8 س"
                    }.get(x, x),
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
                    st.session_state.reload_shifts = True
                    st.session_state.refresh_shifts_data = True
                    st.rerun()
            else:
                st.info("لا توجد فرق واضحة في هذا المركز")
        
        # ===== تبويب 3: أنماط التناوب =====
        with edit_tabs[2]:
            st.markdown("#### أنماط التناوب")
            patterns = {
                "نظام 2+2+4 (صباحي/ليلي)": ["D12", "D12", "N12", "N12", "", "", "", ""],
                "نظام 3+3+3": ["D12", "D12", "D12", "N12", "N12", "N12", "", "", ""],
                "نظام تداخلي": ["O12", "O12", ""],
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
                        st.markdown(f"<div style='background:#E0E0E0; color:#4A5568; padding:0.5rem; border-radius:8px; text-align:center;'>إجازة</div>", unsafe_allow_html=True)
            
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
                st.session_state.reload_shifts = True
                st.session_state.refresh_shifts_data = True
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
                "نظام 2+2+4 (صباحي/ليلي)": {
                    "pattern": ["D12", "D12", "N12", "N12", "", "", "", ""],
                    "description": "2 صباحي، 2 ليلي، 4 إجازة"
                },
                "نظام 3+3+3": {
                    "pattern": ["D12", "D12", "D12", "N12", "N12", "N12", "", "", ""],
                    "description": "3 صباحي، 3 ليلي، 3 إجازة"
                },
                "نظام تداخلي": {
                    "pattern": ["O12", "O12", ""],
                    "description": "2 تداخلي، 1 إجازة"
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
                        if ignore_weekends:
                            current_date = datetime(year, month, day)
                            if current_date.weekday() in [4, 5]:
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
                                st.session_state.reload_shifts = True
                                st.session_state.refresh_shifts_data = True
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
                for emp in employees:
                    emp_id = str(emp["id"])
                    if shifts_map.get(emp_id, {}).get(day):
                        day_workers += 1
                
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
            st.session_state.reload_shifts = True
            st.session_state.refresh_shifts_data = True
            st.rerun()
    
    # ===== وضع الإضافة =====
    elif view_mode == "➕ إضافة":
        st.subheader("➕ إضافة مناوبة جديدة")
        
        with st.form("add_shift_form"):
            shift_date = st.date_input("📅 التاريخ", value=datetime(year, month, 1))
            shift_type = st.selectbox(
                "⏰ نوع المناوبة",
                options=["D12", "N12", "O12", "V", "CP8", "CP24", "LN8"],
                format_func=lambda x: {
                    "D12": "D12 - صباحي 12 س",
                    "N12": "N12 - ليلي 12 س",
                    "O12": "O12 - تداخلي 12 س",
                    "V": "V - إجازة",
                    "CP8": "CP8 - تكميلية 8 س",
                    "CP24": "CP24 - تكميلية 24 س",
                    "LN8": "LN8 - ليلي تكميلي 8 س"
                }.get(x, x)
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
                    st.session_state.reload_shifts = True
                    st.session_state.refresh_shifts_data = True
                    st.rerun()
    
    # ===== وضع استيراد Excel (محدث) =====
    elif view_mode == "📥 استيراد Excel":
        st.subheader("📥 استيراد مناوبات من Excel")
        
        # اختيار نوع الملف
        file_type = st.radio(
            "نوع الملف",
            ["ملف عمودي (رقم وظيفي - يوم - مناوبة)", "ملف أفقي (من ورقة بيانات ومعلومات القطاع الجنوبي)"],
            horizontal=True
        )
        
        if file_type == "ملف عمودي (رقم وظيفي - يوم - مناوبة)":
            st.markdown("""
            <div style="background: #F0F9FF; padding: 1rem; border-radius: 12px; margin-bottom: 1rem;">
                <h5 style="margin: 0 0 0.5rem 0;">📌 تعليمات الملف العمودي:</h5>
                <ul style="margin: 0; padding-right: 1.5rem; font-size: 0.9rem;">
                    <li>الأعمدة المطلوبة: <b>الرقم الوظيفي، اليوم، المناوبة</b></li>
                    <li>اليوم: رقم اليوم من 1 إلى 31</li>
                    <li>المناوبة: D12, N12, O12, V, CP8, CP24, LN8</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            uploaded_file = st.file_uploader(
                "📤 اختر ملف Excel (عمودي)",
                type=['xlsx', 'xls'],
                key="shifts_upload_vertical"
            )
            
            if uploaded_file:
                try:
                    df_preview = pd.read_excel(uploaded_file)
                    st.dataframe(df_preview.head(5), use_container_width=True)
                    st.caption(f"إجمالي {len(df_preview)} مناوبة في الملف")
                    
                    if st.button("🚀 بدء الاستيراد (عمودي)", use_container_width=True, type="primary"):
                        success, failed = import_shifts_from_excel(uploaded_file, ss, employees, year, month)
                        
                        if success > 0:
                            st.success(f"✅ تم استيراد {success} مناوبة بنجاح!")
                            st.balloons()
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("✅ نجاح", success)
                        with col2:
                            st.metric("❌ فشل", failed)
                        with col3:
                            st.metric("📦 إجمالي", len(df_preview))
                        
                        if success > 0:
                            if st.button("🔄 تحديث الجدول", use_container_width=True):
                                st.session_state.reload_shifts = True
                                st.session_state.refresh_shifts_data = True
                                st.rerun()
                                
                except Exception as e:
                    st.error(f"❌ خطأ في قراءة الملف: {str(e)}")
        
        else:  # ملف أفقي
            st.markdown("""
            <div style="background: #F0F9FF; padding: 1rem; border-radius: 12px; margin-bottom: 1rem;">
                <h5 style="margin: 0 0 0.5rem 0;">📌 تعليمات الملف الأفقي:</h5>
                <ul style="margin: 0; padding-right: 1.5rem; font-size: 0.9rem;">
                    <li>الملف يجب أن يحتوي على ورقة <b>بيانات ومعلومات القطاع الجنوبي</b></li>
                    <li>البيانات تبدأ من الصف 10 مباشرة</li>
                    <li>الأعمدة G إلى AK هي الأيام 1-31</li>
                    <li><b>⚠️ مهم: النظام يعتمد على الكود (الرقم الوظيفي) فقط لربط المناوبات</b></li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            uploaded_file = st.file_uploader(
                "📤 اختر ملف Excel (أفقي)",
                type=['xlsx', 'xls'],
                key="shifts_upload_horizontal"
            )
            
            if uploaded_file:
                try:
                    # عرض معاينة للأوراق
                    excel_file = pd.ExcelFile(uploaded_file)
                    st.info(f"📑 الأوراق الموجودة: {', '.join(excel_file.sheet_names)}")
                    
                    if st.button("🚀 بدء الاستيراد (أفقي)", use_container_width=True, type="primary"):
                        success, failed = import_shifts_from_master_sheet(uploaded_file, ss, year, month)
                        
                        if success > 0:
                            st.success(f"✅ تم استيراد {success} مناوبة بنجاح!")
                            st.balloons()
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("✅ نجاح", success)
                        with col2:
                            st.metric("❌ فشل", failed)
                        
                        if success > 0:
                            if st.button("🔄 تحديث الجدول", use_container_width=True):
                                st.session_state.reload_shifts = True
                                st.session_state.refresh_shifts_data = True
                                st.rerun()
                                
                except Exception as e:
                    st.error(f"❌ خطأ في قراءة الملف: {str(e)}")
    
    # ✅ عرض وقت التحميل
    if st.session_state.get('show_performance', False):
        st.sidebar.metric("⏱️ وقت التحميل", f"{time.time() - start_time:.2f} ث")