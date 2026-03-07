# frontend/pages/login.py
import streamlit as st
from config import config

def show_login_page():
    """صفحة تسجيل الدخول"""
    
    # إخفاء الشريط الجانبي وتنسيق الصفحة
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none !important; }
        .main .block-container {
            max-width: 100% !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        .stApp {
            background: linear-gradient(135deg, #F8FAFC 0%, #FFFFFF 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            max-width: 400px;
            width: 90%;
            margin: 2rem auto;
            background: white;
            padding: 2.5rem 2rem;
            border-radius: 24px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.08);
            text-align: center;
            border: 1px solid #E2E8F0;
        }
        .logo-container {
            margin-bottom: 1.5rem;
        }
        .logo-container img {
            width: 100px;
            height: auto;
            display: block;
            margin: 0 auto;
            filter: drop-shadow(0 4px 8px rgba(206,46,38,0.1));
        }
        .sector-title {
            color: #CE2E26;
            font-size: 1rem;
            font-weight: 600;
            margin: 0.5rem 0 0.25rem 0;
        }
        .app-name {
            color: #1A2B5C;
            font-size: 1.4rem;
            font-weight: 800;
            margin: 0.25rem 0;
            line-height: 1.3;
        }
        .south-sector-text {
            color: #3B4A82;
            font-weight: 500;
            margin: 0.5rem 0 2rem 0;
            font-size: 0.9rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid #F1F5F9;
        }
        .stTextInput > div > div > input {
            text-align: right;
            padding: 0.75rem 1rem;
            border-radius: 12px;
            border: 1.5px solid #E2E8F0;
            font-size: 0.95rem;
            transition: all 0.2s;
        }
        .stTextInput > div > div > input:focus {
            border-color: #CE2E26;
            box-shadow: 0 0 0 3px rgba(206,46,38,0.1);
        }
        .stButton > button {
            background: linear-gradient(135deg, #CE2E26 0%, #B71C1C 100%);
            color: white;
            font-weight: 700;
            padding: 0.75rem;
            border-radius: 12px;
            border: none;
            font-size: 1rem;
            transition: all 0.3s;
            margin-top: 1rem;
        }
        .stButton > button:hover {
            opacity: 0.9;
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(206,46,38,0.2);
        }
        .footer-text {
            color: #94A3B8;
            font-size: 0.75rem;
            margin-top: 2rem;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # حاوية تسجيل الدخول
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # الشعار
    st.markdown("""
    <div class="logo-container">
        <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT6W6KLMYsA2ztLnTnKcsENtV9SOBCeYHV17g&s" 
             style="width: 100px; height: auto;">
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="sector-title">الهلال الأحمر السعودي</div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="app-name">{config.APP_NAME}</div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="south-sector-text">قطاع الجنوب - هيئة الهلال الأحمر السعودي</div>
    """, unsafe_allow_html=True)
    
    # نموذج تسجيل الدخول
    with st.form("login_form"):
        username = st.text_input("👤 اسم المستخدم", placeholder="أدخل اسم المستخدم")
        password = st.text_input("🔐 كلمة المرور", type="password", placeholder="أدخل كلمة المرور")
        
        if st.form_submit_button("دخول", use_container_width=True):
            if not username or not password:
                st.error("❌ الرجاء إدخال اسم المستخدم وكلمة المرور")
            else:
                with st.spinner("جاري تسجيل الدخول..."):
                    if st.session_state.auth_service.login(username, password):
                        st.session_state.authenticated = True
                        st.rerun()
                    else:
                        st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")
    
    st.markdown("""
    <div class="footer-text">
        جميع الحقوق محفوظة © 2026 هيئة الهلال الأحمر السعودي
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)