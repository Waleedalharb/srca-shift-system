# frontend/pages/print_attendance.py
import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components
import calendar

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
    
    # تحويل التاريخ الميلادي إلى هجري (تقريبي)
    def gregorian_to_hijri(date_str):
        """تحويل التاريخ الميلادي إلى هجري (تقريبي)"""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            # تقريب بسيط: السنة الهجرية = السنة الميلادية - 622 + (شهر/12)
            year_hijri = date_obj.year - 622 + (date_obj.month / 33)
            month_hijri = date_obj.month
            day_hijri = date_obj.day
            return f"{int(year_hijri):04d}/{month_hijri:02d}/{day_hijri:02d}"
        except:
            return "1447/09/18"  # fallback
    
    # اسم اليوم بالعربية
    def get_arabic_weekday(date_str):
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            weekdays = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
            return weekdays[date_obj.weekday()]
        except:
            return "الخميس"
    
    hijri_date = gregorian_to_hijri(report_date)
    weekday_ar = get_arabic_weekday(report_date)
    
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
            <div class="info-item"><strong>اليوم:</strong> {weekday_ar}</div>
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
        status_map = {
            "حاضر": ("present", "حاضر"),
            "غائب": ("absent", "غائب"),
            "متأخر": ("late", "متأخر")
        }
        status_class, status_text = status_map.get(emp['status'], ("", emp['status']))
        
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