# frontend/pages/print_attendance.py
import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

def show_print_attendance(attendance_data, center_name, report_date):
    """صفحة طباعة تقرير التكميل - نسخة مبسطة"""
    
    st.set_page_config(layout="wide")
    
    # إخفاء كل شيء عدا التقرير
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="stToolbar"] { display: none !important; }
        [data-testid="stDecoration"] { display: none !important; }
        footer { display: none !important; }
        header { display: none !important; }
        .main > div { padding: 0 !important; }
        body { background: white; }
        @media print {
            @page { size: landscape; margin: 1cm; }
            body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
        }
    </style>
    """, unsafe_allow_html=True)
    
    # تنسيق التاريخ بشكل مباشر
    try:
        if isinstance(report_date, str):
            date_obj = datetime.strptime(report_date, '%Y-%m-%d')
        else:
            date_obj = report_date
        formatted_date = date_obj.strftime('%Y/%m/%d')
        day_name = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"][date_obj.weekday()]
    except:
        formatted_date = str(report_date)
        day_name = "الخميس"
    
    # بناء HTML
    html = f"""
    <!DOCTYPE html>
    <html dir="rtl">
    <head><meta charset="UTF-8"><title>تقرير التكميل</title>
    <style>
        body {{ font-family: Arial; margin: 20px; }}
        .header {{ text-align: center; border-bottom: 2px solid #CE2E26; padding-bottom: 10px; }}
        .header h1 {{ color: #CE2E26; margin: 5px; }}
        .header h2 {{ color: #1A2B5C; margin: 5px; }}
        .info {{ background: #f5f5f5; padding: 10px; margin: 20px 0; display: flex; justify-content: space-around; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #3B4A82; color: white; padding: 8px; }}
        td {{ border: 1px solid #ccc; padding: 6px; text-align: center; }}
        .present {{ color: green; font-weight: bold; }}
        .absent {{ color: red; font-weight: bold; }}
        .footer {{ margin-top: 20px; display: flex; justify-content: space-between; }}
    </style>
    </head>
    <body>
        <div class="header">
            <h1>هيئة الهلال الأحمر السعودي</h1>
            <h2>قطاع الجنوب - {center_name}</h2>
        </div>
        
        <div class="info">
            <div><strong>التاريخ:</strong> {formatted_date}</div>
            <div><strong>اليوم:</strong> {day_name}</div>
            <div><strong>الطباعة:</strong> {datetime.now().strftime('%Y/%m/%d %H:%M')}</div>
        </div>
    """
    
    if attendance_data:
        html += """
        <table>
            <tr>
                <th>م</th><th>الرقم</th><th>الاسم</th><th>المناوبة</th><th>الحالة</th>
            </tr>
        """
        for i, emp in enumerate(attendance_data, 1):
            status = emp.get('status', '')
            status_class = 'present' if status == 'حاضر' else 'absent' if status == 'غائب' else ''
            html += f"""
            <tr>
                <td>{i}</td>
                <td>{emp.get('emp_no', '')}</td>
                <td>{emp.get('employee_name', '')}</td>
                <td>{emp.get('planned_shift', '')}</td>
                <td class="{status_class}">{status}</td>
            </tr>
            """
        html += "</table>"
        
        # إحصائيات
        total = len(attendance_data)
        present = sum(1 for e in attendance_data if e.get('status') == 'حاضر')
        html += f"<p style='margin-top:20px'><strong>ملخص:</strong> إجمالي: {total} | ✅ حاضر: {present}</p>"
    
    html += """
        <div class="footer">
            <div>توقيع المشرف: ________</div>
            <div>الختم: ________</div>
        </div>
    </body></html>
    """
    
    components.html(html, height=800, scrolling=True)
    st.button("🖨️ طباعة", on_click="window.print()")