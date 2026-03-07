# frontend/pages/login.py
import streamlit as st
import httpx
from config import config

def show_login_page():
    """صفحة تسجيل الدخول"""
    
    # إخفاء الشريط الجانبي
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none !important; }
        .main .block-container { max-width: 100% !important; }
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
        }
        .south-sector-text {
            color: #3B4A82;
            font-weight: 600;
            margin-bottom: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # الشعار
        st.markdown("""
        <div>
            <div class="logo-circle">🚑</div>
            <div style="color: #CE2E26; font-weight: 700;">الهلال الأحمر السعودي</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"<h2>{config.APP_NAME}</h2>", unsafe_allow_html=True)
        st.markdown('<div class="south-sector-text">قطاع الجنوب - هيئة الهلال الأحمر السعودي</div>', unsafe_allow_html=True)
        
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