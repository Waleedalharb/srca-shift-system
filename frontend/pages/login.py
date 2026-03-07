# frontend/pages/login.py
import streamlit as st
from config import config

def show_login_page():
    """صفحة تسجيل الدخول - نسخة بسيطة ومتوسطة"""
    
    # إخفاء الشريط الجانبي
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none !important; }
        .main > div {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        .block-container {
            max-width: 380px !important;
            padding: 1rem !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # الشعار
    st.markdown("""
    <div style="text-align: center; margin-bottom: 0.5rem;">
        <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT6W6KLMYsA2ztLnTnKcsENtV9SOBCeYHV17g&s" 
             style="width: 90px; height: auto;">
    </div>
    """, unsafe_allow_html=True)
    
    # اسم الهيئة
    st.markdown("""
    <div style="text-align: center; color: #CE2E26; font-weight: 700; margin-bottom: 0.25rem;">
        الهلال الأحمر السعودي
    </div>
    """, unsafe_allow_html=True)
    
    # عنوان النظام
    st.markdown(f"""
    <div style="text-align: center; color: #1A2B5C; font-size: 1.3rem; font-weight: 800; margin-bottom: 0.25rem;">
        {config.APP_NAME}
    </div>
    """, unsafe_allow_html=True)
    
    # نص القطاع
    st.markdown("""
    <div style="text-align: center; color: #3B4A82; font-size: 0.85rem; margin-bottom: 1.5rem;">
        قطاع الجنوب - هيئة الهلال الأحمر السعودي
    </div>
    """, unsafe_allow_html=True)
    
    # نموذج تسجيل الدخول
    with st.form("login_form"):
        username = st.text_input("اسم المستخدم", placeholder="أدخل اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password", placeholder="أدخل كلمة المرور")
        
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