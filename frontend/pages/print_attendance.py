# frontend/pages/print_attendance.py
import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

def show_print_attendance(attendance_data, center_name, report_date):
    """صفحة طباعة تقرير التكميل - تصميم مثل القديم"""
    
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
    
    # تحويل التاريخ الهجري (تقريبي)
    hijri_date = "1447/09/18"
    
    # تجهيز البيانات للجدول
    html_content = f"""
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>تقرير التكميل - {center_name}</title>
        <style>
            body {{
                font-family: 'Arial', sans-serif;
                margin: 20px;
                direction: rtl;
            }}
            .report-header {{
                text-align: center;
                margin-bottom: 30px;
                border-bottom: 2px solid #CE2E26;
                padding-bottom: 10px;
            }}
            .report-header h1 {{
                color: #CE2E26;
                font-size: 24px;
                margin: 5px 0;
            }}
            .report-header h2 {{
                color: #1A2B5C;
                font-size: 18px;
                margin: 5px 0;
            }}
            .report-header h3 {{
                color: #3B4A82;
                font-size: 16px;
                margin: 5px 0;
            }}
            .report-info {{
                display: flex;
                justify-content: space-between;
                margin: 20px 0;
                padding: 10px;
                background: #f5f5f5;
                border-radius: 5px;
            }}
            .info-item {{
                font-size: 14px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                font-size: 13px;
            }}
            th {{
                background: #3B4A82;
                color: white;
                padding: 10px;
                text-align: center;
                font-weight: bold;
                border: 1px solid #2A3A6A;
            }}
            td {{
                border: 1px solid #CCCCCC;
                padding: 8px;
                text-align: center;
            }}
            tr:nth-child(even) {{
                background: #F8F9FA;
            }}
            .present {{ color: #28A745; font-weight: bold; }}
            .absent {{ color: #DC3545; font-weight: bold; }}
            .late {{ color: #FFC107; font-weight: bold; }}
            .footer {{
                margin-top: 30px;
                display: flex;
                justify-content: space-between;
                font-size: 12px;
            }}
            .signature {{
                text-align: center;
                width: 200px;
                border-top: 1px solid #000;
                padding-top: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="report-header">
            <h1>هيئة الهلال الأحمر السعودي</h1>
            <h2>قطاع الجنوب - تقرير التكميل اليومي</h2>
            <h3>{center_name}</h3>
        </div>
        
        <div class="report-info">
            <div class="info-item"><strong>التاريخ الهجري:</strong> {hijri_date}</div>
            <div class="info-item"><strong>التاريخ الميلادي:</strong> {report_date}</div>
            <div class="info-item"><strong>اليوم:</strong> {datetime.strptime(report_date, '%Y-%m-%d').strftime('%A')}</div>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>م</th>
                    <th>الرقم الوظيفي</th>
                    <th>الاسم</th>
                    <th>المناوبة</th>
                    <th>من</th>
                    <th>إلى</th>
                    <th>الحالة</th>
                    <th>وقت الحضور</th>
                    <th>وقت الانصراف</th>
                    <th>التأخير</th>
                    <th>ملاحظات</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for idx, emp in enumerate(attendance_data, 1):
        # تحديد لون الحالة
        if emp['status'] == "حاضر":
            status_class = "present"
            status_text = "حاضر"
        elif emp['status'] == "غائب":
            status_class = "absent"
            status_text = "غائب"
        elif emp['status'] == "متأخر":
            status_class = "late"
            status_text = "متأخر"
        else:
            status_class = ""
            status_text = emp['status']
        
        html_content += f"""
                <tr>
                    <td>{idx}</td>
                    <td>{emp.get('emp_no', '')}</td>
                    <td>{emp['employee_name']}</td>
                    <td>{emp.get('actual_shift_name', emp.get('planned_shift', ''))}</td>
                    <td>{emp.get('planned_start', '')}</td>
                    <td>{emp.get('planned_end', '')}</td>
                    <td class="{status_class}">{status_text}</td>
                    <td>{emp.get('actual_start', '')}</td>
                    <td>{emp.get('actual_end', '')}</td>
                    <td>{emp.get('late_time', '')}</td>
                    <td>{emp.get('notes', '')}</td>
                </tr>
        """
    
    # إحصائيات سريعة
    total = len(attendance_data)
    present = sum(1 for e in attendance_data if e['status'] == "حاضر")
    absent = sum(1 for e in attendance_data if e['status'] == "غائب")
    late = sum(1 for e in attendance_data if e['status'] == "متأخر")
    
    html_content += f"""
            </tbody>
        </table>
        
        <div style="margin: 20px 0; padding: 10px; background: #F0F0F0; border-radius: 5px;">
            <p><strong>ملخص اليوم:</strong></p>
            <p>إجمالي الموظفين: {total} | ✅ حاضر: {present} | ❌ غائب: {absent} | ⏰ متأخر: {late}</p>
        </div>
        
        <div class="footer">
            <div class="signature">توقيع المشرف</div>
            <div class="signature">الختم</div>
            <div class="signature">تاريخ الطباعة: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
        </div>
    </body>
    </html>
    """
    
    # عرض الصفحة
    components.html(html_content, height=800, scrolling=True)
    
    # زر الطباعة
    st.markdown("""
    <div style="text-align: center; margin: 20px;">
        <button onclick="window.print()" style="
            background: #CE2E26;
            color: white;
            padding: 10px 30px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
        ">🖨️ طباعة التقرير</button>
    </div>
    """, unsafe_allow_html=True)