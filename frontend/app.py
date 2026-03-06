# frontend/app.py
import streamlit as st
from pathlib import Path
import sys

# إضافة المجلد الحالي للمسار
sys.path.append(str(Path(__file__).parent))

from config import config
from services.auth_service import AuthService
from utils.helpers import load_css, setup_rtl, footer

# إعداد الصفحة
st.set_page_config(
    page_title=config.APP_NAME,
    page_icon="🚑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== تحسينات PWA =====
st.markdown("""
<style>
    /* إخفاء عناصر Streamlit غير المرغوب فيها */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp header {display: none;}
    .stApp footer {display: none;}
    .stDeployButton {display: none;}
    .stApp [data-testid="stToolbar"] {display: none;}
    .stApp [data-testid="stDecoration"] {display: none;}
    .stApp [data-testid="stStatusWidget"] {display: none;}
    
    /* تحسين للجوال */
    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        .stRadio > div {
            gap: 0.25rem;
        }
        .stRadio label {
            padding: 0.3rem 0.5rem;
            font-size: 0.8rem;
        }
    }
    
    /* تنسيقات عامة */
    [data-testid="stSidebarNav"] { display: none; }
    .main > div { padding-top: 0; }
    .sidebar-logo {
        text-align: center;
        margin-bottom: 1rem;
        padding: 1rem 0;
    }
    .sidebar-logo img {
        width: 70px;
        height: auto;
    }
    .south-sector-badge {
        background: linear-gradient(135deg, #3B4A82 0%, #1A2B5C 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        text-align: center;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 0.5rem auto 1rem auto;
        width: fit-content;
    }
    .user-info {
        background: #F8FAFC;
        padding: 0.8rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        text-align: center;
        border: 1px solid #E2E8F0;
    }
    .stRadio > div {
        gap: 0.5rem;
    }
    .stRadio label {
        padding: 0.5rem 1rem;
        border-radius: 8px;
        transition: all 0.2s;
        font-size: 0.9rem;
    }
    .stRadio label:hover {
        background: #FEE7E7;
        color: #CE2E26;
    }
    .stRadio label[data-checked="true"] {
        background: #CE2E26;
        color: white !important;
    }
    hr {
        margin: 1rem 0;
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #E2E8F0, transparent);
    }
    
    /* تحسين شريط التمرير */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #F1F1F1;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb {
        background: #CE2E26;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #B71C1C;
    }
</style>
""", unsafe_allow_html=True)

# تحميل التنسيقات
load_css()

# إعداد RTL
setup_rtl()

# تهيئة حالة الجلسة
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "auth_service" not in st.session_state:
    st.session_state.auth_service = AuthService()
if "current_page" not in st.session_state:
    st.session_state.current_page = "dashboard"
if "user_role" not in st.session_state:
    st.session_state.user_role = "chief_paramedic"
if "user_center_id" not in st.session_state:
    st.session_state.user_center_id = None
if "user_employee_id" not in st.session_state:
    st.session_state.user_employee_id = None
if "show_prediction" not in st.session_state:
    st.session_state.show_prediction = False

# إذا لم يكن مسجل دخول
if not st.session_state.authenticated:
    from pages.login import show_login_page
    show_login_page()
    footer()
    st.stop()

# ===== الشريط الجانبي =====
with st.sidebar:
    # ===== شعار الهيئة =====
    st.markdown("""
    <div class="sidebar-logo">
        <img src="https://upload.wikimedia.org/wikipedia/ar/thumb/9/9e/Saudi_Red_Crescent.png/200px-Saudi_Red_Crescent.png" 
             style="width: 70px; height: auto;">
    </div>
    """, unsafe_allow_html=True)
    
    # عنوان النظام
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 0.25rem;">
        <h1 style="color: #1A2B5C; font-size: 1rem; margin: 0;">{config.APP_NAME}</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== شعار قطاع الجنوب =====
    st.markdown("""
    <div class="south-sector-badge">
        <span>📍 قطاع الجنوب - الرياض</span>
    </div>
    """, unsafe_allow_html=True)
    
    # معلومات المستخدم
    st.markdown(f"""
    <div class="user-info">
        <div style="font-size: 0.9rem; color: #1A1A2E;">👤 {st.session_state.get('username', '')}</div>
        <div style="font-size: 0.7rem; color: #64748B;">🟢 متصل</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # قائمة الصفحات - مع إضافة صفحة التنبؤ
    pages = {
        "🏠 لوحة المعلومات": "dashboard",
        "👥 الموظفين": "employees",
        "🏥 المراكز": "centers",
        "📅 المناوبات": "shifts",
        "📱 التكميل": "attendance",
        "🔮 التنبؤ": "prediction",  # ✅ صفحة التنبؤ
        "📊 التقارير": "reports",
        "⚙️ الإعدادات": "settings",
    }
    
    # تحديث الصفحة الحالية
    labels = list(pages.keys())
    current_label = next((l for l, k in pages.items() if k == st.session_state.current_page), labels[0])
    
    # عرض القائمة
    selected = st.radio(
        "",
        labels,
        index=labels.index(current_label),
        label_visibility="collapsed",
        key="sidebar_menu"
    )
    
    # تغيير الصفحة
    if pages[selected] != st.session_state.current_page:
        st.session_state.current_page = pages[selected]
        st.rerun()
    
    st.divider()
    
    # زر تسجيل الخروج
    if st.button("🚪 تسجيل خروج", use_container_width=True):
        st.session_state.auth_service.logout()
        st.session_state.authenticated = False
        # مسح البيانات المخزنة
        for key in ["employee_service", "center_service", "shift_service", "current_page", "user_role"]:
            st.session_state.pop(key, None)
        st.rerun()

# ===== توجيه الصفحات =====
page = st.session_state.get("current_page", "dashboard")

if page == "dashboard":
    from pages.dashboard import show_dashboard
    show_dashboard()
elif page == "employees":
    from pages.employees import show_employees
    show_employees()
elif page == "centers":
    from pages.centers import show_centers
    show_centers()
elif page == "shifts":
    from pages.shifts import show_shifts
    show_shifts()
elif page == "attendance":
    from pages.attendance import show_attendance
    show_attendance()
elif page == "prediction":  # ✅ صفحة التنبؤ
    from pages.prediction import show_prediction
    show_prediction()
elif page == "reports":
    from pages.reports import show_reports
    show_reports()
elif page == "settings":
    from pages.settings import show_settings
    show_settings()

# ===== تذييل الصفحة =====
footer()