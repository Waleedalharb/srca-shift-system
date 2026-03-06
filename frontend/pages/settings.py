# frontend/pages/settings.py
import streamlit as st
from datetime import datetime
from utils.helpers import page_header, section_title


def show_settings():
    """صفحة الإعدادات"""

    page_header("الإعدادات", "تخصيص النظام وإدارة الحساب", "⚙️")

    user_data = st.session_state.get("user_data", {})
    username  = st.session_state.get("username", "chief")

    tabs = st.tabs(["👤 الملف الشخصي", "🔐 الأمان", "⚙️ إعدادات النظام", "ℹ️ معلومات النظام"])

    # ══════════════════════════════════════════════════════
    # تبويب 1 — الملف الشخصي
    # ══════════════════════════════════════════════════════
    with tabs[0]:
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

        # بطاقة الملف الشخصي
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

        st.markdown("""<div style="background:white;border-radius:14px;
            padding:1.5rem;border:1px solid #E2E8F0;
            box-shadow:0 4px 20px rgba(13,27,42,0.08);">""",
            unsafe_allow_html=True)
        section_title("بيانات الحساب", "👤")

        with st.form("profile_form"):
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("👤 اسم المستخدم", value=username, disabled=True)
                email = st.text_input("📧 البريد الإلكتروني",
                                      value=user_data.get("email", f"{username}@srca.gov.sa"))
                role = st.selectbox("👔 الدور الوظيفي",
                    ["كبير المسعفين","قيادة ميدانية","تحكم عملياتي","مشرف مناوبة"],
                    index=0)
            with c2:
                phone = st.text_input("📱 رقم الجوال",
                                      value=user_data.get("phone", "05xxxxxxxx"))
                dept  = st.text_input("🏢 الإدارة / القسم",
                                      value=user_data.get("dept", "قطاع الجنوب — الرياض"),
                                      disabled=True)
                lang  = st.selectbox("🌐 لغة الواجهة", ["العربية", "English"])

            bio = st.text_area("📝 نبذة مختصرة",
                               value=user_data.get("bio", ""),
                               placeholder="اكتب نبذة مختصرة عن نفسك...")

            if st.form_submit_button("💾 حفظ التغييرات", use_container_width=True, type="primary"):
                st.success("✅ تم حفظ بيانات الملف الشخصي بنجاح")

        st.markdown("</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # تبويب 2 — الأمان
    # ══════════════════════════════════════════════════════
    with tabs[1]:
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

        st.markdown("""<div style="background:white;border-radius:14px;
            padding:1.5rem;border:1px solid #E2E8F0;
            box-shadow:0 4px 20px rgba(13,27,42,0.08);margin-bottom:1rem;">""",
            unsafe_allow_html=True)
        section_title("تغيير كلمة المرور", "🔑")

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

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""<div style="background:white;border-radius:14px;
            padding:1.5rem;border:1px solid #E2E8F0;
            box-shadow:0 4px 20px rgba(13,27,42,0.08);">""",
            unsafe_allow_html=True)
        section_title("إعدادات الأمان", "🛡️")

        with st.form("security_settings"):
            tfa      = st.checkbox("🔐 تفعيل المصادقة الثنائية (2FA)")
            notif_login = st.checkbox("📧 إشعارات تسجيل الدخول على البريد", value=True)
            session_timeout = st.selectbox("⏱️ انتهاء الجلسة تلقائياً بعد",
                ["30 دقيقة","ساعة","ساعتين","4 ساعات","لا تنتهي"])
            allowed_ips = st.text_area("🌐 عناوين IP المسموح بها (اختياري)",
                                       placeholder="أدخل كل عنوان في سطر مستقل")

            if st.form_submit_button("💾 حفظ إعدادات الأمان", use_container_width=True):
                st.success("✅ تم حفظ إعدادات الأمان")

        st.markdown("</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # تبويب 3 — إعدادات النظام
    # ══════════════════════════════════════════════════════
    with tabs[2]:
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

        st.markdown("""<div style="background:white;border-radius:14px;
            padding:1.5rem;border:1px solid #E2E8F0;
            box-shadow:0 4px 20px rgba(13,27,42,0.08);margin-bottom:1rem;">""",
            unsafe_allow_html=True)
        section_title("إعدادات العرض", "🎨")

        with st.form("display_settings"):
            c1, c2 = st.columns(2)
            with c1:
                date_fmt     = st.selectbox("📅 تنسيق التاريخ",
                    ["YYYY/MM/DD","DD/MM/YYYY","MM/DD/YYYY"])
                items_per_page = st.selectbox("📊 عناصر الصفحة", [10, 20, 50, 100], index=1)
                timezone       = st.selectbox("⏰ المنطقة الزمنية",
                    ["(UTC+03:00) الرياض","(UTC+00:00) GMT"])
            with c2:
                refresh_rate = st.selectbox("🔄 تحديث البيانات تلقائياً",
                    ["كل دقيقة","كل 5 دقائق","كل 15 دقيقة","كل ساعة","يدوياً"],
                    index=1)
                notifications = st.checkbox("🔔 تفعيل الإشعارات الصوتية")
                dark_mode     = st.checkbox("🌙 الوضع الليلي (تجريبي)")

            if st.form_submit_button("💾 حفظ إعدادات العرض", use_container_width=True):
                st.success("✅ تم حفظ إعدادات العرض بنجاح")

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""<div style="background:white;border-radius:14px;
            padding:1.5rem;border:1px solid #E2E8F0;
            box-shadow:0 4px 20px rgba(13,27,42,0.08);">""",
            unsafe_allow_html=True)
        section_title("إعدادات الإشعارات", "🔔")

        with st.form("notification_settings"):
            c1, c2 = st.columns(2)
            with c1:
                st.checkbox("📧 تقارير يومية على البريد",       value=True)
                st.checkbox("🚨 تنبيه عند انخفاض التغطية",      value=True)
                st.checkbox("📅 تذكير بمواعيد المناوبات",       value=False)
            with c2:
                st.checkbox("👤 تنبيه عند إضافة موظف جديد",     value=False)
                st.checkbox("🏥 تنبيه عند تغيير حالة مركز",     value=True)
                st.checkbox("📊 تقارير أسبوعية",                value=False)

            email_notif = st.text_input("📧 بريد الإشعارات",
                                        placeholder="admin@srca.gov.sa")
            if st.form_submit_button("💾 حفظ إعدادات الإشعارات", use_container_width=True):
                st.success("✅ تم حفظ إعدادات الإشعارات")

        st.markdown("</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # تبويب 4 — معلومات النظام
    # ══════════════════════════════════════════════════════
    with tabs[3]:
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

        # بطاقة معلومات النظام
        from config import config
        st.markdown(f"""
        <div style="background:white;border-radius:14px;padding:1.5rem;
            border:1px solid #E2E8F0;box-shadow:0 4px 20px rgba(13,27,42,0.08);
            margin-bottom:1rem;direction:rtl;">
            <h3 style="font-family:Cairo,sans-serif;font-weight:700;
                color:#1A1A2E;font-size:1rem;margin:0 0 1.25rem;
                padding-bottom:0.75rem;border-bottom:1px solid #E2E8F0;">
                🖥️ معلومات النظام
            </h3>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;">
                <div style="background:#F8FAFC;border-radius:10px;padding:0.875rem;">
                    <p style="margin:0 0 0.3rem;font-size:0.75rem;color:#718096;
                        font-family:Cairo,sans-serif;">اسم النظام</p>
                    <p style="margin:0;font-weight:700;color:#1A1A2E;
                        font-family:Cairo,sans-serif;font-size:0.9rem;">
                        {config.APP_NAME}
                    </p>
                </div>
                <div style="background:#F8FAFC;border-radius:10px;padding:0.875rem;">
                    <p style="margin:0 0 0.3rem;font-size:0.75rem;color:#718096;
                        font-family:Cairo,sans-serif;">الإصدار</p>
                    <p style="margin:0;font-weight:700;color:#1A1A2E;
                        font-family:Cairo,sans-serif;font-size:0.9rem;">
                        v2.0.0 — مارس 2026
                    </p>
                </div>
                <div style="background:#F8FAFC;border-radius:10px;padding:0.875rem;">
                    <p style="margin:0 0 0.3rem;font-size:0.75rem;color:#718096;
                        font-family:Cairo,sans-serif;">عنوان API</p>
                    <p style="margin:0;font-weight:700;color:#3B4A82;
                        font-family:Cairo,sans-serif;font-size:0.9rem;">
                        {config.API_URL}
                    </p>
                </div>
                <div style="background:#E8F5E9;border-radius:10px;padding:0.875rem;">
                    <p style="margin:0 0 0.3rem;font-size:0.75rem;color:#2D6633;
                        font-family:Cairo,sans-serif;">حالة الاتصال</p>
                    <p style="margin:0;font-weight:700;color:#2D6633;
                        font-family:Cairo,sans-serif;font-size:0.9rem;">
                        🟢 السيرفر متصل
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # منطقة الخطر
        st.markdown("""
        <div style="background:#FFEBEE;border:1.5px solid #FFCDD2;border-radius:14px;
            padding:1.25rem 1.5rem;direction:rtl;">
            <h4 style="color:#C62828;font-family:Cairo,sans-serif;font-weight:700;
                margin:0 0 0.75rem;font-size:0.95rem;">⚠️ منطقة الخطر</h4>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🗑️ مسح ذاكرة التخزين المؤقت",
                         use_container_width=True):
                for key in ["employee_service","center_service","shift_service"]:
                    st.session_state.pop(key, None)
                st.success("✅ تم مسح الذاكرة المؤقتة")
        with c2:
            if st.button("🚪 تسجيل خروج من جميع الأجهزة",
                         use_container_width=True, type="primary"):
                st.session_state.auth_service.logout()
                st.session_state.authenticated = False
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
