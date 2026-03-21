# frontend/pages/login.py
import streamlit as st
from config import config
import requests

def show_login_page():
    """صفحة تسجيل الدخول - مع تشخيص"""
    
    # ===== تشخيص الاتصال بالـ API =====
    st.sidebar.markdown("### 🔧 Debug Info")
    st.sidebar.write(f"**API URL:** `{config.API_URL}`")
    
    try:
        r = requests.get(f"{config.API_URL}/health", timeout=2)
        if r.status_code == 200:
            st.sidebar.success(f"✅ API متصل (الحالة: {r.status_code})")
            st.sidebar.json(r.json())
        else:
            st.sidebar.error(f"❌ API غير متصل: {r.status_code}")
    except Exception as e:
        st.sidebar.error(f"❌ API غير متصل: {str(e)}")
    
    try:
        r2 = requests.get(f"{config.API_URL}/", timeout=2)
        if r2.status_code == 200:
            st.sidebar.info(f"✅ API root: {r2.status_code}")
    except:
        pass
    # ====================================
    
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
                    # محاولة تسجيل الدخول
                    login_success = st.session_state.auth_service.login(username, password)
                    
                    if login_success:
                        # ✅ تبسيط: تعيين البيانات مباشرة بدون جلب من API
                        if username == "8736":
                            st.session_state.user_role = "PARAMEDIC"
                            st.session_state.user_employee_id = st.session_state.get("user_employee_id")
                            st.session_state.user_full_name = "زياد عبدالله ابراهيم الرشيد"
                            st.session_state.username = username
                            st.session_state.authenticated = True
                            st.session_state.current_page = "my_shifts"
                            st.query_params.clear()
                            st.success("✅ تم تسجيل الدخول بنجاح (كموظف)")
                            st.rerun()
                        elif username == "chief":
                            st.session_state.user_role = "ADMIN"
                            st.session_state.user_full_name = "المشرف العام"
                            st.session_state.username = username
                            st.session_state.authenticated = True
                            st.session_state.current_page = "dashboard"
                            st.query_params.clear()
                            st.success("✅ تم تسجيل الدخول بنجاح (كمشرف)")
                            st.rerun()
                        else:
                            # أي مستخدم آخر
                            st.session_state.user_role = "USER"
                            st.session_state.user_full_name = username
                            st.session_state.username = username
                            st.session_state.authenticated = True
                            st.session_state.current_page = "shifts"
                            st.query_params.clear()
                            st.success("✅ تم تسجيل الدخول بنجاح")
                            st.rerun()
                    else:
                        st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")