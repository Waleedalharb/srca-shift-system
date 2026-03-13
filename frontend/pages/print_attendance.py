# frontend/pages/print_attendance.py
import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

def convert_shift_code(shift_name):
    """تحويل أسماء المناوبات القديمة إلى الرموز الجديدة"""
    shift_map = {
        "صباحية 8 س": "D8",
        "صباحية 12 س": "D12",
        "مسائية 8 س": "N8",
        "ليلية 10 س": "N10",
        "ليلية 12 س": "N12",
        "تداخلية 8 س": "O8",
        "تداخلية 12 س": "O12",
        "إجازة": "V",
        "نوبة 24 س": "CP24",
        "morning_8": "D8",
        "morning_12": "D12",
        "evening_8": "N8",
        "night_10": "N10",
        "night_12": "N12",
        "overlap_8": "O8",
        "overlap_12": "O12",
        "off": "V",
        "fullday_24": "CP24"
    }
    return shift_map.get(shift_name, shift_name)

def show_print_attendance(attendance_data, center_name, report_date):
    """صفحة طباعة تقرير التكميل"""
    
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
    
    # تنسيق التاريخ
    try:
        if isinstance(report_date, str):
            date_obj = datetime.strptime(report_date, '%Y-%m-%d')
        else:
            date_obj = report_date
        formatted_date = date_obj.strftime('%Y/%m/%d')
        day_name = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"][date_obj.weekday()]
        year_hijri = date_obj.year - 622
        hijri_date = f"{year_hijri}/{date_obj.month:02d}/{date_obj.day:02d}"
    except:
        formatted_date = str(report_date)
        day_name = "الخميس"
        hijri_date = "1447/09/18"
    
    # بناء HTML
    html = f"""
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
            .header {{
                text-align: center;
                border-bottom: 2px solid #CE2E26;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }}
            .header h1 {{
                color: #CE2E26;
                font-size: 24px;
                margin: 5px 0;
            }}
            .header h2 {{
                color: #1A2B5C;
                font-size: 18px;
                margin: 5px 0;
            }}
            .header h3 {{
                color: #3B4A82;
                font-size: 16px;
                margin: 5px 0;
            }}
            .info {{
                background: #f5f5f5;
                padding: 15px;
                margin: 20px 0;
                border-radius: 5px;
                display: flex;
                justify-content: space-around;
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
                border: 1px solid #2A3A6A;
            }}
            td {{
                border: 1px solid #ccc;
                padding: 8px;
                text-align: center;
            }}
            .present {{ color: #28A745; font-weight: bold; }}
            .absent {{ color: #DC3545; font-weight: bold; }}
            .summary {{
                background: #F0F0F0;
                padding: 10px;
                border-radius: 5px;
                margin: 20px 0;
            }}
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
        <div class="header">
            <h1>هيئة الهلال الأحمر السعودي</h1>
            <h2>قطاع الجنوب - تقرير التكميل اليومي</h2>
            <h3>{center_name}</h3>
        </div>
        
        <div class="info">
            <div><strong>التاريخ الهجري:</strong> {hijri_date}</div>
            <div><strong>التاريخ الميلادي:</strong> {formatted_date}</div>
            <div><strong>اليوم:</strong> {day_name}</div>
        </div>
    """
    
    if attendance_data:
        # تحويل البيانات
        converted_data = []
        for emp in attendance_data:
            emp_copy = emp.copy()
            # تحويل اسم المناوبة
            if 'planned_shift' in emp_copy:
                emp_copy['planned_shift_display'] = convert_shift_code(emp_copy['planned_shift'])
            if 'actual_shift_name' in emp_copy:
                emp_copy['actual_shift_display'] = convert_shift_code(emp_copy['actual_shift_name'])
            converted_data.append(emp_copy)
        
        html += """
        <table>
            <thead>
                <tr>
                    <th>م</th>
                    <th>الرقم الوظيفي</th>
                    <th>الاسم</th>
                    <th>المناوبة</th>
                    <th>الحالة</th>
                    <th>وقت الحضور</th>
                    <th>وقت الانصراف</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for idx, emp in enumerate(converted_data, 1):
            status = emp.get('status', '')
            status_class = 'present' if status == 'حاضر' else 'absent' if status == 'غائب' else ''
            
            # استخدام الرمز المحول
            shift_display = emp.get('actual_shift_display', emp.get('planned_shift_display', emp.get('planned_shift', '')))
            
            html += f"""
                <tr>
                    <td>{idx}</td>
                    <td>{emp.get('emp_no', '')}</td>
                    <td>{emp.get('employee_name', '')}</td>
                    <td><strong>{shift_display}</strong></td>
                    <td class="{status_class}">{status}</td>
                    <td>{emp.get('actual_start', '')}</td>
                    <td>{emp.get('actual_end', '')}</td>
                </tr>
            """
        
        html += "</tbody></table>"
        
        # إحصائيات
        total = len(attendance_data)
        present = sum(1 for e in attendance_data if e.get('status') == 'حاضر')
        absent = sum(1 for e in attendance_data if e.get('status') == 'غائب')
        
        html += f"""
        <div class="summary">
            <p><strong>ملخص اليوم:</strong></p>
            <p>إجمالي الموظفين: {total} | ✅ حاضر: {present} | ❌ غائب: {absent}</p>
        </div>
        """
    else:
        html += "<p style='text-align: center; color: #666;'>لا توجد بيانات للتكميل في هذا التاريخ</p>"
    
    html += f"""
        <div class="footer">
            <div class="signature">توقيع المشرف</div>
            <div class="signature">الختم</div>
            <div class="signature">تاريخ الطباعة: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
        </div>
    </body>
    </html>
    """
    
    # عرض الصفحة
    components.html(html, height=800, scrolling=True)
    
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