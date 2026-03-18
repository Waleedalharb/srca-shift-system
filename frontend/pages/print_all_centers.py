# frontend/pages/print_all_centers.py
import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
from utils.constants import SHIFT_TYPES
from services.center_service import CenterService
from services.employee_service import EmployeeService
from services.shift_service import ShiftService
import io
import tempfile
from fpdf import FPDF

st.set_page_config(page_title="طباعة جميع المراكز", layout="wide")

# CSS للطباعة
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
        direction: rtl;
    }
    .report-title {
        text-align: center;
        margin-bottom: 20px;
        border-bottom: 2px solid #CE2E26;
        padding-bottom: 10px;
    }
    .report-title h1 {
        color: #CE2E26;
        font-size: 24px;
        margin: 5px 0;
    }
    .report-title h2 {
        color: #1A2B5C;
        font-size: 20px;
        margin: 5px 0;
    }
    .report-title h3 {
        color: #3B4A82;
        font-size: 16px;
        margin: 5px 0;
    }
    .info-box {
        background: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        margin: 20px 0;
        display: flex;
        justify-content: space-around;
        font-size: 14px;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 20px 0;
        font-size: 11pt;
    }
    th {
        background: #1e3c72 !important;
        color: white !important;
        padding: 8px;
        text-align: center;
        border: 1px solid #2a4a8a;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }
    td {
        border: 1px solid #dee2e6;
        padding: 6px;
        text-align: center;
    }
    .center-header {
        background: #e9ecef;
        font-weight: bold;
        font-size: 14px;
    }
    .shift-D12 { background: #cfe2ff; }
    .shift-N12 { background: #d1e7dd; }
    .shift-O12 { background: #fff3cd; }
    .shift-V { background: #f8d7da; color: #721c24; }
    .footer {
        margin-top: 30px;
        display: flex;
        justify-content: space-between;
        font-size: 10pt;
    }
    .print-button {
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
    @media screen {
        .print-button {
            display: block;
        }
    }
}
</style>
""", unsafe_allow_html=True)

def get_center_data(center_id, year, month):
    """جلب بيانات مركز محدد"""
    auth = st.session_state.auth_service
    es = EmployeeService(auth)
    ss = ShiftService(auth)
    
    employees = es.get_employees(center_id=center_id).get("items", [])
    shifts_map = {}
    
    for emp in employees:
        emp_id = str(emp["id"])
        emp_shifts = ss.get_employee_shifts_by_month(emp_id, year, month)
        emp_shifts_dict = {}
        for shift in emp_shifts:
            shift_date = shift.get("date", "").split("T")[0]
            try:
                day = int(shift_date.split("-")[2])
                shift_type = shift.get("shift_type")
                if shift_type and shift_type != "off":
                    emp_shifts_dict[day] = shift_type
            except:
                continue
        shifts_map[emp_id] = emp_shifts_dict
    
    return employees, shifts_map

def generate_pdf_report(centers, year, month, total_employees_all, total_shifts_all):
    """توليد تقرير PDF"""
    pdf = FPDF()
    pdf.add_page()
    
    # عنوان التقرير
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "هيئة الهلال الأحمر السعودي", ln=1, align='C')
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"تقرير مناوبات جميع المراكز - {calendar.month_name[month]} {year}", ln=1, align='C')
    pdf.ln(10)
    
    # معلومات التقرير
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 8, f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=1, align='R')
    pdf.ln(5)
    
    # ملخص عام
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, f"📊 الملخص العام", ln=1, align='R')
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 8, f"🏥 إجمالي المراكز: {len(centers)}", ln=1, align='R')
    pdf.cell(0, 8, f"👥 إجمالي الموظفين: {total_employees_all}", ln=1, align='R')
    pdf.cell(0, 8, f"📅 إجمالي المناوبات: {total_shifts_all}", ln=1, align='R')
    pdf.ln(10)
    
    # تفاصيل المراكز
    for center in centers:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, f"🏥 {center['name']}", ln=1, align='R')
        
        employees, shifts_map = get_center_data(center["id"], year, month)
        if employees:
            # رأس الجدول
            pdf.set_font("Arial", 'B', 9)
            pdf.cell(70, 8, "الموظف", 1, 0, 'C')
            pdf.cell(30, 8, "الرقم الوظيفي", 1, 0, 'C')
            pdf.cell(30, 8, "إجمالي الساعات", 1, 1, 'C')
            
            # بيانات الموظفين
            pdf.set_font("Arial", '', 9)
            for emp in employees[:10]:  # أول 10 موظفين فقط للاختصار
                emp_id = str(emp["id"])
                emp_shifts = shifts_map.get(emp_id, {})
                
                total_hours = 0
                for day in range(1, 32):
                    shift_type = emp_shifts.get(day)
                    if shift_type and shift_type in SHIFT_TYPES:
                        if shift_type in ['D12', 'N12', 'O12']:
                            total_hours += 12
                        elif shift_type == 'V':
                            total_hours += 0
                        else:
                            total_hours += SHIFT_TYPES[shift_type]["hours"]
                
                # اختصار الاسم الطويل
                name = emp['full_name'][:20] + "..." if len(emp['full_name']) > 20 else emp['full_name']
                pdf.cell(70, 7, name, 1, 0, 'C')
                pdf.cell(30, 7, emp.get('emp_no', ''), 1, 0, 'C')
                pdf.cell(30, 7, str(total_hours), 1, 1, 'C')
            
            if len(employees) > 10:
                pdf.set_font("Arial", 'I', 8)
                pdf.cell(0, 5, f"... و {len(employees)-10} موظف آخر", ln=1, align='R')
            
            pdf.ln(5)
    
    # تذييل PDF
    pdf.set_y(-30)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 5, f"تم الإنشاء بواسطة نظام إدارة المراكز الإسعافية - هيئة الهلال الأحمر السعودي", ln=1, align='C')
    pdf.cell(0, 5, f"صفحة {pdf.page_no()}", ln=1, align='C')
    
    return pdf

def main():
    # التحقق من وجود البيانات
    if 'print_all_centers' not in st.session_state:
        st.warning("⚠️ لم يتم تحديد شهر للطباعة")
        if st.button("🔙 العودة للمناوبات"):
            st.switch_page("pages/shifts.py")
        return
    
    year = st.session_state.print_year
    month = st.session_state.print_month
    
    # عنوان التقرير
    st.markdown(f"""
    <div class="report-title">
        <h1>هيئة الهلال الأحمر السعودي</h1>
        <h2>قطاع الجنوب - تقرير مناوبات جميع المراكز</h2>
        <h3>{calendar.month_name[month]} {year}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # معلومات التقرير
    st.markdown(f"""
    <div class="info-box">
        <div><strong>تاريخ التقرير:</strong> {datetime.now().strftime('%Y-%m-%d')}</div>
        <div><strong>وقت الطباعة:</strong> {datetime.now().strftime('%H:%M')}</div>
        <div><strong>إجمالي المراكز:</strong> (سيتم احتسابها)</div>
    </div>
    """, unsafe_allow_html=True)
    
    # جلب الخدمات والمراكز
    auth = st.session_state.auth_service
    cs = CenterService(auth)
    centers = cs.get_centers() or []
    
    days_in_month = calendar.monthrange(year, month)[1]
    
    total_employees_all = 0
    total_shifts_all = 0
    
    # عرض كل مركز
    for center in centers:
        center_id = center["id"]
        center_name = center["name"]
        
        employees, shifts_map = get_center_data(center_id, year, month)
        
        if not employees:
            continue
        
        total_employees_all += len(employees)
        
        st.markdown(f"### 🏥 {center_name} - {len(employees)} موظف")
        
        # إحصائيات المركز
        center_shifts_count = sum(len(shifts) for shifts in shifts_map.values())
        total_shifts_all += center_shifts_count
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👥 الموظفين", len(employees))
        with col2:
            st.metric("📅 إجمالي المناوبات", center_shifts_count)
        with col3:
            avg_per_emp = center_shifts_count // len(employees) if employees else 0
            st.metric("📊 متوسط المناوبات", f"{avg_per_emp}/موظف")
        
        # جدول المركز
        table_data = []
        for emp in employees:
            emp_id = str(emp["id"])
            emp_shifts = shifts_map.get(emp_id, {})
            
            # حساب الساعات
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
            
            row = {
                "الموظف": emp['full_name'],
                "الرقم الوظيفي": emp.get('emp_no', ''),
                "إجمالي الساعات": total_hours
            }
            
            for day in range(1, days_in_month + 1):
                shift_type = emp_shifts.get(day)
                row[f"{day:02d}"] = shift_type if shift_type else ""
            
            table_data.append(row)
        
        if table_data:
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
    
    # ملخص عام
    st.markdown("### 📊 الملخص العام")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🏥 إجمالي المراكز", len(centers))
    with col2:
        st.metric("👥 إجمالي الموظفين", total_employees_all)
    with col3:
        st.metric("📅 إجمالي المناوبات", total_shifts_all)
    
    # أزرار التحكم
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col2:
        if st.button("🖨️ طباعة", use_container_width=True, type="secondary"):
            st.write("""
            <script>
            window.print();
            </script>
            """, unsafe_allow_html=True)
    with col3:
        if st.button("📥 PDF", use_container_width=True, type="primary"):
            with st.spinner("جاري إنشاء ملف PDF..."):
                pdf = generate_pdf_report(centers, year, month, total_employees_all, total_shifts_all)
                
                # حفظ PDF في ذاكرة مؤقتة
                pdf_output = io.BytesIO()
                pdf.output(pdf_output)
                pdf_bytes = pdf_output.getvalue()
                
                st.download_button(
                    label="📥 تحميل PDF",
                    data=pdf_bytes,
                    file_name=f"تقرير_المراكز_{month}_{year}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
    with col4:
        if st.button("🔙 عودة", use_container_width=True):
            del st.session_state.print_all_centers
            st.switch_page("pages/shifts.py")

if __name__ == "__main__":
    main()