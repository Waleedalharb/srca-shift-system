# frontend/pages/login.py
import streamlit as st
from config import config

def show_login_page():
    """صفحة تسجيل الدخول"""
    
    # إخفاء الشريط الجانبي بالكامل
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            display: none !important;
        }
        [data-testid="stSidebarContent"] {
            display: none !important;
        }
        .main .block-container {
            max-width: 100% !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }
        .stApp { background: #F8FAFC; }
        .login-container {
            max-width: 400px;
            margin: 100px auto;
            background: white;
            padding: 2.5rem;
            border-radius: 16px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.1);
            text-align: center;
            border-top: 4px solid #CE2E26;
        }
        .logo-container {
            margin-bottom: 1.5rem;
        }
        .logo-circle {
            width: 120px;
            height: 120px;
            background: linear-gradient(135deg, #CE2E26 0%, #B71C1C 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1rem auto;
            font-size: 3rem;
            color: white;
            box-shadow: 0 4px 12px rgba(206,46,38,0.3);
        }
        .south-sector-text {
            color: #3B4A82;
            font-weight: 600;
            margin-top: -0.5rem;
            margin-bottom: 2rem;
            font-size: 0.9rem;
        }
        .login-title {
            color: #1A1A2E;
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        .stTextInput > div > div > input {
            text-align: right;
            padding: 0.75rem;
            border-radius: 8px;
            border: 1px solid #E2E8F0;
        }
        .stButton > button {
            background: linear-gradient(135deg, #CE2E26 0%, #B71C1C 100%);
            color: white;
            font-weight: 700;
            padding: 0.75rem;
            border-radius: 8px;
            border: none;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # الشعار
        st.markdown("""
        <div class="logo-container">
            <div class="logo-circle">🚑</div>
            <div style="color: #CE2E26; font-weight: 700;">الهلال الأحمر السعودي</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="login-title">{config.APP_NAME}</div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="south-sector-text">
            قطاع الجنوب - هيئة الهلال الأحمر السعودي
        </div>
        """, unsafe_allow_html=True)
        
        # نموذج تسجيل الدخول
        with st.form("login_form"):
            username = st.text_input("👤 اسم المستخدم", placeholder="أدخل اسم المستخدم")
            password = st.text_input("🔐 كلمة المرور", type="password", placeholder="أدخل كلمة المرور")
            
            if st.form_submit_button("دخول", use_container_width=True, type="primary"):
                if not username or not password:
                    st.error("❌ الرجاء إدخال اسم المستخدم وكلمة المرور")
                else:
                    with st.spinner("جاري تسجيل الدخول..."):
                        if st.session_state.auth_service.login(username, password):
                            st.session_state.authenticated = True
                            st.rerun()
                        else:
                            st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")
        
        st.markdown('</div>', unsafe_allow_html=True)