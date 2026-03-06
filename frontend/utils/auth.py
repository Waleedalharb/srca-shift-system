# frontend/utils/auth.py
import streamlit as st
from utils.api import SRCA_API

def init_session_state():
    """تهيئة متغيرات الجلسة"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "api" not in st.session_state:
        st.session_state.api = SRCA_API()

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
                api = st.session_state.api
                if api.login(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")
        
        st.markdown('</div>', unsafe_allow_html=True)

def logout():
    """تسجيل الخروج"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.api = SRCA_API()
    st.rerun()