# frontend/app.py
import streamlit as st
from pathlib import Path
import sys
import hashlib
import base64
from datetime import datetime

# إضافة المجلد الحالي للمسار
sys.path.append(str(Path(__file__).parent))

from config import config
from services.auth_service import AuthService
from utils.helpers import load_css, setup_rtl, footer
from utils.auth import init_session_state  # ✅ استيراد دالة تهيئة الجلسة

# ===== مدير الجلسات لحل مشكلة تعدد المستخدمين =====
class SessionManager:
    def __init__(self):
        self.sessions = {}
    
    def create_session(self, username):
        """إنشاء جلسة فريدة لكل مستخدم وجهاز"""
        session_id = base64.b64encode(hashlib.sha256(
            f"{username}_{datetime.now().timestamp()}".encode()
        ).digest()).decode()[:16]
        self.sessions[session_id] = {
            "username": username,
            "created_at": datetime.now()
        }
        return session_id
    
    def validate_session(self, session_id):
        """التحقق من صحة الجلسة"""
        if session_id in self.sessions:
            self.sessions[session_id]["created_at"] = datetime.now()
            return True
        return False

# ✅ تهيئة الجلسة مع localStorage (هذا السطر مهم جداً)
init_session_state()

# إعداد الصفحة
st.set_page_config(
    page_title=config.APP_NAME,
    page_icon="🚑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تنسيقات محسنة (سيتم استبدالها بملف CSS)
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
    
    /* تنسيقات الشريط الجانبي */
    [data-testid="stSidebarNav"] { display: none; }
    section[data-testid="stSidebar"] {
        background: white;
        border-left: 1px solid #E2E8F0;
        padding: 1rem 0.5rem;
        box-shadow: -4px 0 12px rgba(0,0,0,0.02);
    }
    
    /* الشعار في الشريط الجانبي */
    .sidebar-logo {
        text-align: center;
        margin-bottom: 1rem;
        padding: 1rem;
        border-bottom: 1px solid #F1F5F9;
    }
    .sidebar-logo img {
        width: 60px;
        height: auto;
        display: block;
        margin: 0 auto;
    }
    .sidebar-title {
        text-align: center;
        color: #1A2B5C;
        font-weight: 700;
        font-size: 0.9rem;
        margin: 0.5rem 0 0 0;
    }
    
    /* شعار قطاع الجنوب */
    .south-sector-badge {
        background: linear-gradient(135deg, #3B4A82 0%, #1A2B5C 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 30px;
        text-align: center;
        font-size: 0.75rem;
        font-weight: 600;
        margin: 1rem auto;
        width: fit-content;
        letter-spacing: 0.3px;
    }
    
    /* معلومات المستخدم */
    .user-info {
        background: #F8FAFC;
        padding: 1rem;
        border-radius: 16px;
        margin: 1rem 0;
        text-align: center;
        border: 1px solid #E2E8F0;
    }
    .user-name {
        font-weight: 700;
        color: #1A1A2E;
        margin-bottom: 0.25rem;
    }
    .user-status {
        font-size: 0.7rem;
        color: #42924B;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.25rem;
    }
    
    /* قائمة التنقل */
    .stRadio > div {
        gap: 0.25rem;
    }
    .stRadio label {
        padding: 0.6rem 1rem;
        border-radius: 12px;
        transition: all 0.2s;
        font-size: 0.9rem;
        color: #475569 !important;
    }
    .stRadio label:hover {
        background: #FEE7E7;
        color: #CE2E26 !important;
    }
    .stRadio label[data-checked="true"] {
        background: linear-gradient(135deg, #CE2E26 0%, #B71C1C 100%);
        color: white !important;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(206,46,38,0.2);
    }
    
    /* زر الخروج */
    .stButton > button {
        background: #F1F5F9;
        color: #475569;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: #FEE7E7;
        color: #CE2E26;
        border-color: #CE2E26;
    }
    
    /* فواصل */
    hr {
        margin: 1rem 0;
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #E2E8F0, transparent);
    }
    
    /* تحسين للآيباد والأجهزة اللوحية */
    @media (max-width: 1024px) {
        /* تكبير الأزرار */
        .stButton > button, .stDownloadButton > button {
            min-height: 44px !important;
            min-width: 44px !important;
            padding: 12px 20px !important;
            font-size: 16px !important;
        }
        
        /* تكبير القوائم */
        .stRadio label, .stSelectbox label, .stCheckbox label {
            padding: 12px !important;
            font-size: 16px !important;
        }
        
        /* تكبير حقول الإدخال */
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select,
        .stTextArea > div > textarea {
            padding: 12px !important;
            font-size: 16px !important;
            min-height: 44px !important;
        }
        
        /* تحسين اللمس */
        .stRadio > div, .stSelectbox > div {
            touch-action: manipulation;
        }
    }
    
    /* تحسين للجوال */
    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        .stRadio label {
            padding: 0.4rem 0.5rem;
            font-size: 0.9rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# تحميل التنسيقات
load_css()

# إعداد RTL
setup_rtl()

# تهيئة مدير الجلسات
if "session_manager" not in st.session_state:
    st.session_state.session_manager = SessionManager()

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
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "is_mobile" not in st.session_state:
    st.session_state.is_mobile = False
if "token" not in st.session_state:
    st.session_state.token = None

# إذا لم يكن مسجل دخول
if not st.session_state.authenticated:
    from pages.login import show_login_page
    show_login_page()
    footer()
    st.stop()

# إنشاء جلسة فريدة للمستخدم
if st.session_state.session_id is None:
    st.session_state.session_id = st.session_state.session_manager.create_session(
        st.session_state.get("username", "guest")
    )

# ===== الشريط الجانبي =====
with st.sidebar:
    # الشعار
    st.markdown("""
    <div class="sidebar-logo">
        <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT6W6KLMYsA2ztLnTnKcsENtV9SOBCeYHV17g&s" 
             style="width: 60px; height: auto;">
        <div class="sidebar-title">الهلال الأحمر السعودي</div>
    </div>
    """, unsafe_allow_html=True)
    
    # معلومات المستخدم
    st.markdown(f"""
    <div class="user-info">
        <div class="user-name">{st.session_state.get('username', '')}</div>
        <div class="user-status">
            <span>🟢</span> متصل
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # شعار قطاع الجنوب
    st.markdown("""
    <div class="south-sector-badge">
        قطاع الجنوب - الرياض
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # قائمة الصفحات
    pages = {
        "🏠 لوحة المعلومات": "dashboard",
        "👥 الموظفين": "employees",
        "🏥 المراكز": "centers",
        "📅 المناوبات": "shifts",
        "📱 التكميل": "attendance",
        "🔮 التنبؤ": "prediction",
        "📊 التقارير": "reports",
        "⚙️ الإعدادات": "settings",
    }
    
    labels = list(pages.keys())
    current_label = next((l for l, k in pages.items() if k == st.session_state.current_page), labels[0])
    
    selected = st.radio(
        "",
        labels,
        index=labels.index(current_label),
        label_visibility="collapsed",
        key="sidebar_menu"
    )
    
    if pages[selected] != st.session_state.current_page:
        st.session_state.current_page = pages[selected]
        st.rerun()
    
    st.divider()
    
    if st.button("🚪 تسجيل خروج", use_container_width=True):
        st.session_state.auth_service.logout()
        st.session_state.authenticated = False
        st.session_state.session_id = None
        st.session_state.token = None
        for key in ["employee_service", "center_service", "shift_service", "current_page", "user_role"]:
            st.session_state.pop(key, None)
        st.rerun()

# توجيه الصفحات
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
elif page == "prediction":
    from pages.prediction import show_prediction
    show_prediction()
elif page == "reports":
    from pages.reports import show_reports
    show_reports()
elif page == "settings":
    from pages.settings import show_settings
    show_settings()

footer()