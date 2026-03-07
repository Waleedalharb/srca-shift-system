# frontend/pages/login.py
import streamlit as st
from config import config

def show_login_page():
    """صفحة تسجيل الدخول"""
    
    st.markdown("""
    <style>
        /* إخفاء الشريط الجانبي */
        [data-testid="stSidebar"] { display: none !important; }
        
        /* الخلفية */
        .stApp {
            background: linear-gradient(135deg, #F8FAFC 0%, #FFFFFF 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        /* إزالة المسافات الزائدة */
        .main .block-container {
            max-width: 100% !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        
        /* الحاوية الرئيسية */
        .login-wrapper {
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 1rem;
        }
        
        /* بطاقة تسجيل الدخول */
        .login-card {
            max-width: 400px;
            width: 100%;
            background: white;
            padding: 2.5rem 2rem;
            border-radius: 32px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.15);
            border: 1px solid #E2E8F0;
            text-align: center;
        }
        
        /* الشعار */
        .logo-section {
            margin-bottom: 1.5rem;
        }
        .logo-section img {
            width: 100px;
            height: auto;
            display: block;
            margin: 0 auto 1rem auto;
        }
        .logo-section .srca-title {
            color: #CE2E26;
            font-size: 1rem;
            font-weight: 600;
            margin: 0.5rem 0 0.25rem 0;
        }
        
        /* عنوان النظام */
        .system-title {
            color: #1A2B5C;
            font-size: 1.6rem;
            font-weight: 800;
            margin: 0.25rem 0;
            line-height: 1.3;
        }
        
        /* نص القطاع */
        .sector-text {
            color: #3B4A82;
            font-weight: 500;
            font-size: 0.95rem;
            margin: 0.75rem 0 1.5rem 0;
            padding-bottom: 1.5rem;
            border-bottom: 2px solid #F1F5F9;
        }
        
        /* تنسيق حقول الإدخال */
        .stTextInput {
            margin-bottom: 0.5rem;
        }
        .stTextInput > label {
            color: #1E293B !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            margin-bottom: 0.3rem !important;
        }
        .stTextInput > div > div > input {
            text-align: right;
            padding: 0.8rem 1rem;
            border-radius: 14px;
            border: 1.5px solid #E2E8F0;
            font-size: 1rem;
            transition: all 0.2s;
            background: #F8FAFC;
        }
        .stTextInput > div > div > input:focus {
            border-color: #CE2E26;
            box-shadow: 0 0 0 3px rgba(206,46,38,0.1);
            background: white;
        }
        
        /* زر الدخول */
        .stButton > button {
            background: linear-gradient(135deg, #CE2E26 0%, #B71C1C 100%);
            color: white;
            font-weight: 700;
            padding: 0.8rem;
            border-radius: 14px;
            border: none;
            font-size: 1.1rem;
            transition: all 0.3s;
            margin-top: 1.5rem;
            letter-spacing: 0.5px;
            box-shadow: 0 8px 16px rgba(206,46,38,0.15);
        }
        .stButton > button:hover {
            opacity: 0.9;
            transform: translateY(-2px);
            box-shadow: 0 12px 24px rgba(206,46,38,0.25);
        }
        
        /* تذييل الصفحة */
        .login-footer {
            color: #94A3B8;
            font-size: 0.7rem;
            margin-top: 2rem;
            text-align: center;
            padding-top: 1rem;
            border-top: 1px solid #F1F5F9;
        }
        
        /* تنسيق رسائل الخطأ */
        .stAlert {
            border-radius: 12px;
            border-right: 4px solid #CE2E26;
            background: #FEF2F2;
            padding: 1rem;
            margin: 1rem 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # حاوية خارجية للتوسيط
    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    
    # الشعار
    st.markdown("""
    <div class="logo-section">
        <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT6W6KLMYsA2ztLnTnKcsENtV9SOBCeYHV17g&s" 
             style="width: 100px; height: auto;">
        <div class="srca-title">الهلال الأحمر السعودي</div>
    </div>
    """, unsafe_allow_html=True)
    
    # عنوان النظام
    st.markdown(f"""
    <div class="system-title">{config.APP_NAME}</div>
    """, unsafe_allow_html=True)
    
    # نص القطاع
    st.markdown("""
    <div class="sector-text">قطاع الجنوب - هيئة الهلال الأحمر السعودي</div>
    """, unsafe_allow_html=True)
    
    # نموذج تسجيل الدخول
    with st.form("login_form"):
        username = st.text_input("👤 اسم المستخدم", placeholder="أدخل اسم المستخدم")
        password = st.text_input("🔐 كلمة المرور", type="password", placeholder="أدخل كلمة المرور")
        
        submitted = st.form_submit_button("دخول", use_container_width=True)
        
        if submitted:
            if not username or not password:
                st.error("❌ الرجاء إدخال اسم المستخدم وكلمة المرور")
            else:
                with st.spinner("جاري تسجيل الدخول..."):
                    if st.session_state.auth_service.login(username, password):
                        st.session_state.authenticated = True
                        st.rerun()
                    else:
                        st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")
    
    # تذييل
    st.markdown("""
    <div class="login-footer">
        جميع الحقوق محفوظة © 2026 هيئة الهلال الأحمر السعودي
    </div>
    """, unsafe_allow_html=True)
    
    # إغلاق الحاويات
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)