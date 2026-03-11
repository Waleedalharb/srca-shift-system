# frontend/utils/auth.py
import streamlit as st
from services.auth_service import AuthService
import streamlit.components.v1 as components
import time

def init_session_state():
    """تهيئة متغيرات الجلسة مع دعم localStorage"""
    
    # أولاً: تهيئة المتغيرات الأساسية
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "auth_service" not in st.session_state:
        st.session_state.auth_service = AuthService()
    if "token" not in st.session_state:
        st.session_state.token = None
    if "user_role" not in st.session_state:
        st.session_state.user_role = "chief_paramedic"
    if "user_center_id" not in st.session_state:
        st.session_state.user_center_id = None
    if "user_employee_id" not in st.session_state:
        st.session_state.user_employee_id = None
    
    # استرجاع التوكن من localStorage إذا كان موجود
    token = st.session_state.get("token")
    if not token:
        # نحاول نجيب التوكن من localStorage
        components.html("""
        <script>
        // استرجاع التوكن من localStorage
        const token = localStorage.getItem('srca_token');
        const username = localStorage.getItem('srca_username');
        
        if (token && username) {
            window.parent.postMessage({
                type: 'streamlit:setSessionState',
                data: {
                    token: token,
                    username: username,
                    authenticated: true
                }
            }, '*');
        }
        </script>
        """, height=0)

def login_page():
    """صفحة تسجيل الدخول"""
    # إذا كان مسجل دخول بالفعل، نوجهه للصفحة الرئيسية
    if st.session_state.get("authenticated", False):
        st.switch_page("app.py")
        return
    
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        direction: rtl;
    }
    .login-box {
        background: white;
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        max-width: 400px;
        margin: 100px auto;
        text-align: center;
    }
    .stTextInput > div > div > input {
        text-align: right;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.image("https://upload.wikimedia.org/wikipedia/ar/thumb/9/9e/Saudi_Red_Crescent.png/200px-Saudi_Red_Crescent.png")
        st.title("نظام إدارة المراكز الإسعافية")
        st.markdown("---")
        
        with st.form("login_form"):
            username = st.text_input("👤 اسم المستخدم")
            password = st.text_input("🔐 كلمة المرور", type="password")
            
            if st.form_submit_button("🚀 دخول", use_container_width=True):
                auth_service = st.session_state.auth_service
                if auth_service.login(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.token = auth_service.token
                    
                    # حفظ التوكن في localStorage
                    components.html(f"""
                    <script>
                    localStorage.setItem('srca_token', '{auth_service.token}');
                    localStorage.setItem('srca_username', '{username}');
                    window.parent.postMessage({{
                        type: 'streamlit:setSessionState',
                        data: {{
                            token: '{auth_service.token}',
                            username: '{username}',
                            authenticated: true
                        }}
                    }}, '*');
                    </script>
                    """, height=0)
                    
                    st.rerun()
                else:
                    st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")
        
        st.markdown('</div>', unsafe_allow_html=True)

def logout():
    """تسجيل الخروج"""
    # حذف التوكن من localStorage
    components.html("""
    <script>
    localStorage.removeItem('srca_token');
    localStorage.removeItem('srca_username');
    </script>
    """, height=0)
    
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.token = None
    st.session_state.auth_service = AuthService()
    st.rerun()