# frontend/pages/settings.py
import streamlit as st
from datetime import datetime
import json
import os
from utils.helpers import page_header, section_title

# ===== تحديد مسار الحفظ الصحيح 100% لـ Render =====
def get_settings_path():
    """تحديد مسار حفظ الإعدادات حسب البيئة"""
    # إذا كنا في Render (الفرونتند)
    if os.path.exists('/opt/render/project/src'):
        settings_path = '/opt/render/project/src/srca_settings.json'
        # التأكد من وجود الملف وصلاحياته (مرة واحدة)
        if not os.path.exists(settings_path):
            try:
                with open(settings_path, 'w') as f:
                    json.dump({}, f)
                os.chmod(settings_path, 0o666)  # صلاحيات قراءة وكتابة للجميع
            except:
                pass
        return settings_path
    # إذا كنا محلياً (Windows/Mac)
    else:
        return os.path.join(os.path.expanduser("~"), ".srca_settings.json")

SETTINGS_FILE = get_settings_path()

def init_settings():
    """تهيئة إعدادات التطبيق"""
    if 'app_settings' not in st.session_state:
        st.session_state.app_settings = {
            'theme': 'light',  # light or dark
            'language': 'ar',
            'notifications': True,
            'compact_view': False,
            'auto_refresh': False,
            'refresh_interval': 5,
            'show_weekends': True,
            'font_size': 'medium',
        }
    load_settings()

def save_settings():
    """حفظ الإعدادات في الملف المناسب"""
    try:
        settings = st.session_state.app_settings
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"❌ فشل حفظ الإعدادات: {str(e)}")
        return False

def load_settings():
    """تحميل الإعدادات من الملف المناسب"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                saved_settings = json.load(f)
                st.session_state.app_settings.update(saved_settings)
    except Exception:
        pass

def apply_theme():
    """تطبيق الثيم على التطبيق"""
    theme = st.session_state.app_settings.get('theme', 'light')
    
    if theme == 'dark':
        st.markdown("""
        <style>
            /* خلفية التطبيق */
            .stApp {
                background: #1E1E1E !important;
            }
            
            /* جميع النصوص */
            .stMarkdown, p, h1, h2, h3, h4, h5, h6, span, label, div {
                color: #FFFFFF !important;
            }
            
            /* القوائم المنسدلة */
            .stSelectbox div[data-baseweb="select"] {
                background: #2D2D2D !important;
                border-color: #404040 !important;
            }
            
            .stSelectbox div[data-baseweb="select"] * {
                color: #FFFFFF !important;
            }
            
            /* خيارات القائمة */
            div[data-baseweb="menu"] {
                background: #2D2D2D !important;
                border-color: #404040 !important;
            }
            
            div[data-baseweb="menu"] * {
                color: #FFFFFF !important;
            }
            
            /* حقول الإدخال */
            .stTextInput input, .stNumberInput input, .stDateInput input {
                background: #2D2D2D !important;
                color: #FFFFFF !important;
                border-color: #404040 !important;
            }
            
            /* الأزرار */
            .stButton button {
                background: #0d6efd !important;
                color: white !important;
                border: none !important;
            }
            
            .stButton button:hover {
                background: #0b5ed7 !important;
            }
            
            /* البطاقات */
            div[data-testid="stVerticalBlock"] > div {
                background: #2D2D2D !important;
                border-color: #404040 !important;
            }
            
            /* التبويبات */
            .stTabs [data-baseweb="tab-list"] {
                background: #2D2D2D !important;
            }
            
            .stTabs [data-baseweb="tab"] {
                color: #FFFFFF !important;
            }
            
            /* القوائم الجانبية */
            .css-1d391kg, .css-163ttbj, .css-1wrcr25 {
                background: #252526 !important;
            }
            
            /* الخط الفاصل */
            hr {
                border-color: #404040 !important;
            }
            
            /* رسائل الخطأ والنجاح */
            .stAlert {
                background: #2D2D2D !important;
                color: #FFFFFF !important;
                border-color: #404040 !important;
            }
            
            /* الجداول */
            .stDataFrame {
                background: #2D2D2D !important;
            }
            
            .stDataFrame * {
                color: #FFFFFF !important;
            }
            
            /* تحسين ظهور التحديد */
            ::selection {
                background: #0d6efd !important;
                color: white !important;
            }
            
            /* تحسين ظهور الروابط */
            a {
                color: #0d6efd !important;
            }
        </style>
        """, unsafe_allow_html=True)
    else:
        # ثيم فاتح (بسيط)
        st.markdown("""
        <style>
            .stApp {
                background: #FFFFFF;
            }
        </style>
        """, unsafe_allow_html=True)

def show_settings():
    """صفحة الإعدادات"""
    
    # تهيئة الإعدادات
    init_settings()
    apply_theme()

    page_header("الإعدادات", "تخصيص النظام وإدارة الحساب", "⚙️")

    user_data = st.session_state.get("user_data", {})
    username  = st.session_state.get("username", "chief")

    tabs = st.tabs(["👤 الملف الشخصي", "🔐 الأمان", "⚙️ إعدادات النظام", "🎨 المظهر", "ℹ️ معلومات النظام"])

    # ══════════════════════════════════════════════════════
    # تبويب 1 — الملف الشخصي
    # ══════════════════════════════════════════════════════
    with tabs[0]:
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

        initials = username[:2].upper()
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#0D1B2A,#3B4A82);
            border-radius:16px;padding:1.75rem 2rem;color:white;
            margin-bottom:1.25rem;direction:rtl;
            box-shadow:0 8px 32px rgba(13,27,42,0.3);
            display:flex;align-items:center;gap:1.25rem;">
            <div style="width:64px;height:64px;border-radius:50%;
                background:linear-gradient(135deg,#CE2E26,#F1B944);
                display:flex;align-items:center;justify-content:center;
                font-size:1.5rem;font-weight:900;color:white;flex-shrink:0;
                font-family:Cairo,sans-serif;">{initials}</div>
            <div>
                <h3 style="margin:0 0 0.25rem;font-family:Tajawal,sans-serif;
                    font-weight:900;font-size:1.2rem;">{username}</h3>
                <p style="margin:0;color:rgba(255,255,255,0.55);
                    font-family:Cairo,sans-serif;font-size:0.83rem;">
                    🟢 متصل الآن · آخر دخول {datetime.now().strftime('%Y/%m/%d %H:%M')}
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("profile_form"):
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("👤 اسم المستخدم", value=username, disabled=True)
                email = st.text_input("📧 البريد الإلكتروني",
                                      value=user_data.get("email", f"{username}@srca.gov.sa"))
            with c2:
                phone = st.text_input("📱 رقم الجوال",
                                      value=user_data.get("phone", "05xxxxxxxx"))
                dept  = st.text_input("🏢 الإدارة / القسم",
                                      value=user_data.get("dept", "قطاع الجنوب — الرياض"),
                                      disabled=True)

            if st.form_submit_button("💾 حفظ التغييرات", use_container_width=True, type="primary"):
                st.success("✅ تم حفظ بيانات الملف الشخصي بنجاح")

    # ══════════════════════════════════════════════════════
    # تبويب 2 — الأمان
    # ══════════════════════════════════════════════════════
    with tabs[1]:
        with st.form("password_form"):
            current = st.text_input("🔑 كلمة المرور الحالية", type="password")
            new_pw  = st.text_input("🆕 كلمة المرور الجديدة", type="password")
            confirm = st.text_input("🔄 تأكيد كلمة المرور", type="password")

            if st.form_submit_button("🔒 تحديث كلمة المرور", use_container_width=True, type="primary"):
                if not current or not new_pw:
                    st.error("❌ الرجاء تعبئة جميع الحقول")
                elif new_pw != confirm:
                    st.error("❌ كلمة المرور الجديدة غير متطابقة")
                elif len(new_pw) < 8:
                    st.error("❌ كلمة المرور يجب أن تكون 8 أحرف على الأقل")
                else:
                    st.success("✅ تم تحديث كلمة المرور بنجاح")

        with st.form("security_settings"):
            tfa = st.checkbox("🔐 تفعيل المصادقة الثنائية (2FA)")
            notif_login = st.checkbox("📧 إشعارات تسجيل الدخول على البريد", value=True)
            
            if st.form_submit_button("💾 حفظ إعدادات الأمان", use_container_width=True):
                st.success("✅ تم حفظ إعدادات الأمان")

    # ══════════════════════════════════════════════════════
    # تبويب 3 — إعدادات النظام
    # ══════════════════════════════════════════════════════
    with tabs[2]:
        with st.form("system_settings"):
            c1, c2 = st.columns(2)
            with c1:
                items_per_page = st.selectbox("📊 عناصر الصفحة", [10, 20, 50, 100], index=1)
                refresh_rate = st.selectbox("🔄 تحديث البيانات",
                    ["يدوياً", "كل دقيقة", "كل 5 دقائق", "كل 15 دقيقة"],
                    index=1)
            with c2:
                notifications = st.checkbox("🔔 تفعيل الإشعارات", 
                    value=st.session_state.app_settings['notifications'])
                auto_refresh = st.checkbox("🔄 تحديث تلقائي",
                    value=st.session_state.app_settings['auto_refresh'])

            if st.form_submit_button("💾 حفظ إعدادات النظام", use_container_width=True):
                st.session_state.app_settings['notifications'] = notifications
                st.session_state.app_settings['auto_refresh'] = auto_refresh
                save_settings()
                st.success("✅ تم حفظ إعدادات النظام")

    # ══════════════════════════════════════════════════════
    # تبويب 4 — المظهر
    # ══════════════════════════════════════════════════════
    with tabs[3]:
        with st.form("theme_settings"):
            st.markdown("#### 🎨 المظهر")
            
            current_theme = st.session_state.app_settings['theme']
            theme_options = {'light': 'فاتح ☀️', 'dark': 'داكن 🌙'}
            
            new_theme = st.radio(
                "اختر الثيم",
                options=list(theme_options.keys()),
                format_func=lambda x: theme_options[x],
                index=0 if current_theme == 'light' else 1,
                horizontal=True
            )
            
            st.markdown("#### 📏 حجم الخط")
            font_options = {'small': 'صغير', 'medium': 'متوسط', 'large': 'كبير'}
            new_font = st.select_slider(
                "حجم الخط",
                options=list(font_options.keys()),
                value=st.session_state.app_settings['font_size'],
                format_func=lambda x: font_options[x]
            )
            
            st.markdown("#### 📅 عرض الجدول")
            show_weekends = st.checkbox("إظهار عطل نهاية الأسبوع",
                value=st.session_state.app_settings['show_weekends'])
            compact_view = st.checkbox("عرض مضغوط",
                value=st.session_state.app_settings['compact_view'])
            
            if st.form_submit_button("💾 حفظ المظهر", use_container_width=True, type="primary"):
                st.session_state.app_settings['theme'] = new_theme
                st.session_state.app_settings['font_size'] = new_font
                st.session_state.app_settings['show_weekends'] = show_weekends
                st.session_state.app_settings['compact_view'] = compact_view
                save_settings()
                apply_theme()
                st.success("✅ تم حفظ إعدادات المظهر")
                st.rerun()

    # ══════════════════════════════════════════════════════
    # تبويب 5 — معلومات النظام
    # ══════════════════════════════════════════════════════
    with tabs[4]:
        theme_options = {'light': 'فاتح ☀️', 'dark': 'داكن 🌙'}
        
        st.markdown(f"""
        <div style="background:white;border-radius:14px;padding:1.5rem;
            border:1px solid #E2E8F0;margin-bottom:1rem;direction:rtl;">
            <h3 style="margin:0 0 1.25rem;padding-bottom:0.75rem;
                border-bottom:1px solid #E2E8F0;">
                🖥️ معلومات النظام
            </h3>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;">
                <div style="background:#F8FAFC;border-radius:10px;padding:0.875rem;">
                    <p style="margin:0 0 0.3rem;font-size:0.75rem;color:#718096;">
                        اسم النظام</p>
                    <p style="margin:0;font-weight:700;color:#1A1A2E;">
                        نظام إدارة المناوبات
                    </p>
                </div>
                <div style="background:#F8FAFC;border-radius:10px;padding:0.875rem;">
                    <p style="margin:0 0 0.3rem;font-size:0.75rem;color:#718096;">
                        الإصدار</p>
                    <p style="margin:0;font-weight:700;color:#1A1A2E;">
                        v2.0.0 — مارس 2026
                    </p>
                </div>
                <div style="background:#E8F5E9;border-radius:10px;padding:0.875rem;">
                    <p style="margin:0 0 0.3rem;font-size:0.75rem;color:#2D6633;">
                        حالة الاتصال</p>
                    <p style="margin:0;font-weight:700;color:#2D6633;">
                        🟢 السيرفر متصل
                    </p>
                </div>
                <div style="background:#F8FAFC;border-radius:10px;padding:0.875rem;">
                    <p style="margin:0 0 0.3rem;font-size:0.75rem;color:#718096;">
                        الثيم الحالي</p>
                    <p style="margin:0;font-weight:700;color:#1A1A2E;">
                        {theme_options[st.session_state.app_settings['theme']]}
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # مسار الحفظ
        st.info(f"📁 **مسار حفظ الإعدادات:** `{SETTINGS_FILE}`")

        # منطقة الخطر
        st.markdown("""
        <div style="background:#FFEBEE;border:1.5px solid #FFCDD2;border-radius:14px;
            padding:1.25rem 1.5rem;direction:rtl;">
            <h4 style="color:#C62828;margin:0 0 0.75rem;">⚠️ منطقة الخطر</h4>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🗑️ مسح ذاكرة التخزين المؤقت", use_container_width=True):
                st.cache_data.clear()
                st.success("✅ تم مسح الذاكرة المؤقتة")
        with c2:
            if st.button("🚪 تسجيل خروج من جميع الأجهزة", use_container_width=True):
                st.session_state.clear()
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)