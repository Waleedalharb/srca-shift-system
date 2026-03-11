# frontend/utils/auth.py
import streamlit as st
from services.auth_service import AuthService
import streamlit.components.v1 as components

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
    
    # استرجاع التوكن من localStorage إذا كان موجود
    token = st.session_state.get("token")
    if not token:
        components.html("""
        <script>
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
        max-width: 400px;
        margin: 100px auto;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
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
                </script>
                """, height=0)
                
                st.rerun()
            else:
                st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")

def logout():
    """تسجيل الخروج"""
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