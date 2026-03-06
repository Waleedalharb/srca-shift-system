# frontend/utils/helpers.py
import streamlit as st
from pathlib import Path
from datetime import datetime

def load_css():
    """تحميل ملف CSS المخصص"""
    css_file = Path(__file__).parent.parent / "assets" / "styles.css"
    if css_file.exists():
        with open(css_file, 'r', encoding='utf-8') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ ملف CSS غير موجود")

def setup_rtl():
    """إعداد الاتجاه من اليمين لليسار"""
    st.markdown("""
    <style>
        .stApp { direction: rtl; }
        .stTextInput > div > div > input { text-align: right; }
        .stSelectbox > div > div > div { text-align: right; }
    </style>
    """, unsafe_allow_html=True)

def page_header(title, subtitle="", icon=""):
    """عنوان الصفحة بتنسيق موحد"""
    st.markdown(f"""
    <div style="margin-bottom: 1.5rem;">
        <h1 style="display: flex; align-items: center; gap: 0.5rem;">
            {icon} {title}
        </h1>
        {f'<p style="color: #64748B; margin-top: -0.5rem;">{subtitle}</p>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)

def section_title(title, icon=""):
    """عنوان قسم فرعي"""
    st.markdown(f"""
    <h3 style="
        color: #1E293B;
        font-weight: 700;
        font-size: 1.1rem;
        margin: 1.5rem 0 1rem 0;
        padding-right: 0.5rem;
        border-right: 3px solid #CE2E26;
    ">{icon} {title}</h3>
    """, unsafe_allow_html=True)

def format_date(date_str):
    """تنسيق التاريخ"""
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime("%Y/%m/%d")
    except:
        return date_str

def format_datetime(datetime_str):
    """تنسيق التاريخ والوقت"""
    if not datetime_str:
        return ""
    try:
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        return dt.strftime("%Y/%m/%d %H:%M")
    except:
        return datetime_str

def get_status_text(status):
    """ترجمة الحالة إلى العربية"""
    status_map = {
        "active": "نشط",
        "inactive": "غير نشط",
        "on_duty": "على رأس العمل",
        "off_duty": "في إجازة",
        "pending": "قيد الانتظار",
        "approved": "مقبول",
        "rejected": "مرفوض",
        "scheduled": "مجدول",
        "completed": "مكتمل",
        "cancelled": "ملغي",
    }
    return status_map.get(status, status)

def get_status_color(status):
    """لون الحالة"""
    color_map = {
        "active": "#42924B",
        "inactive": "#CE2E26",
        "on_duty": "#3B4A82",
        "off_duty": "#F1B944",
        "pending": "#F1B944",
        "approved": "#42924B",
        "rejected": "#CE2E26",
    }
    return color_map.get(status, "#64748B")

def south_sector_badge():
    """شعار قطاع الجنوب"""
    st.markdown("""
    <div class="south-sector-badge">
        <span>📍</span>
        <span>قطاع الجنوب - مدينة الرياض</span>
    </div>
    """, unsafe_allow_html=True)

def footer():
    """تذييل الصفحة"""
    current_year = datetime.now().year
    st.markdown(f"""
    <div class="footer">
        © {current_year} هيئة الهلال الأحمر السعودي - قطاع الجنوب<br>
        جميع الحقوق محفوظة
    </div>
    """, unsafe_allow_html=True)