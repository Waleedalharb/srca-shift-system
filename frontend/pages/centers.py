# frontend/pages/centers.py
import streamlit as st
import pandas as pd
from components.cards import center_card, kpi_row
from components.charts import create_bar_chart, create_gauge, display_chart
from utils.helpers import page_header, section_title


def _get_service():
    auth = st.session_state.auth_service
    cs = st.session_state.get("center_service")
    if not cs:
        from services.center_service import CenterService
        cs = CenterService(auth)
        st.session_state.center_service = cs
    return cs


def show_centers():
    """صفحة إدارة المراكز الإسعافية"""

    page_header("إدارة المراكز الإسعافية", "عرض وإضافة وتعديل المراكز التابعة", "🏥")

    cs = _get_service()
    tabs = st.tabs(["📋 قائمة المراكز", "➕ إضافة مركز", "✏️ تعديل مركز", "📊 مقارنة التغطية"])

    # ══════════════════════════════════════════════════════
    # تبويب 1 — القائمة
    # ══════════════════════════════════════════════════════
    with tabs[0]:
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

        search = st.text_input("🔍 بحث باسم المركز أو الكود",
                               placeholder="اكتب للبحث...", key="center_search")

        with st.spinner("جاري التحميل..."):
            centers = cs.get_centers(search or None) or []

        if not centers:
            st.markdown("""
            <div style="text-align:center;padding:3rem 1rem;
                background:white;border-radius:14px;border:1px solid #E2E8F0;
                color:#718096;font-family:Cairo,sans-serif;">
                <div style="font-size:2.5rem;margin-bottom:0.75rem;">🏥</div>
                <p style="font-size:0.95rem;margin:0;">لا توجد مراكز مسجلة</p>
            </div>""", unsafe_allow_html=True)
            return

        active   = sum(1 for c in centers if c.get("is_active"))
        inactive = len(centers) - active

        kpi_row([
            ("🏥", len(centers), "إجمالي المراكز",    "red"),
            ("✅", active,       "مراكز نشطة",        "green"),
            ("❌", inactive,     "مراكز متوقفة",      "navy"),
        ])
        st.markdown("<div style='margin:1rem 0;'></div>", unsafe_allow_html=True)

        # عرض البطاقات
        for i in range(0, len(centers), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                if i + j < len(centers):
                    center = centers[i + j]
                    cov    = cs.get_center_coverage(center["id"])
                    with col:
                        center_card(center, cov)
                        bc1, bc2 = st.columns(2)
                        with bc1:
                            if st.button("✏️ تعديل", key=f"cedit_{center['id']}",
                                         use_container_width=True):
                                st.session_state.editing_center = center
                                st.rerun()
                        with bc2:
                            lbl = "🔴 إيقاف" if center.get("is_active") else "🟢 تفعيل"
                            if st.button(lbl, key=f"ctoggle_{center['id']}",
                                         use_container_width=True):
                                cs.update_center(center["id"],
                                    {"is_active": not center.get("is_active")})
                                st.rerun()
                        st.markdown("<div style='margin-bottom:0.5rem;'></div>",
                                    unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # تبويب 2 — إضافة مركز
    # ══════════════════════════════════════════════════════
    with tabs[1]:
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:white;border-radius:14px;padding:1.5rem;
            box-shadow:0 4px 20px rgba(13,27,42,0.08);border:1px solid #E2E8F0;
            border-top:3px solid #CE2E26;">
            <h3 style="font-family:Cairo,sans-serif;font-weight:700;
                color:#1A1A2E;font-size:1rem;margin:0 0 1.25rem;">
                ➕ بيانات المركز الجديد
            </h3>
        """, unsafe_allow_html=True)

        with st.form("add_center_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                code          = st.text_input("🔤 كود المركز *",      placeholder="مثال: HAER")
                name          = st.text_input("🏥 اسم المركز *",      placeholder="مثال: مركز الحائر")
                city          = st.text_input("🏙️ المدينة",           value="جازان")
                coverage_area = st.number_input("📏 مساحة التغطية (كم²)", min_value=0, value=50)
            with c2:
                latitude  = st.text_input("🌍 خط العرض",  placeholder="24.5667")
                longitude = st.text_input("🌐 خط الطول",  placeholder="46.7333")
                manager   = st.text_input("👤 مدير المركز", placeholder="الاسم الكامل")
                phone     = st.text_input("📱 هاتف المركز", placeholder="01xxxxxxxx")

            address = st.text_area("📍 العنوان التفصيلي", placeholder="الحي، الشارع، الرقم...")

            submitted = st.form_submit_button("✅ إضافة المركز", use_container_width=True,
                                              type="primary")
            if submitted:
                if not code or not name:
                    st.error("❌ الكود والاسم مطلوبان")
                else:
                    data = dict(
                        code=code, name=name, city=city,
                        latitude=latitude or None,
                        longitude=longitude or None,
                        coverage_area=coverage_area or None,
                        address=address or None,
                        manager=manager or None,
                        phone=phone or None,
                        is_active=True,
                    )
                    res = cs.create_center(data)
                    if res:
                        st.success(f"✅ تم إضافة مركز **{name}** بنجاح!")
                        st.balloons()
                        st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # تبويب 3 — تعديل
    # ══════════════════════════════════════════════════════
    with tabs[2]:
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

        if "editing_center" not in st.session_state:
            st.markdown("""
            <div style="text-align:center;padding:3rem;background:white;
                border-radius:14px;border:1px solid #E2E8F0;
                color:#718096;font-family:Cairo,sans-serif;">
                <div style="font-size:2.5rem;margin-bottom:0.75rem;">✏️</div>
                <p>اختر مركزاً من التبويب الأول ثم اضغط «تعديل»</p>
            </div>""", unsafe_allow_html=True)
        else:
            center = st.session_state.editing_center
            st.markdown(f"""
            <div style="background:white;border-radius:14px;padding:1.5rem;
                box-shadow:0 4px 20px rgba(13,27,42,0.08);border:1px solid #E2E8F0;
                border-top:3px solid #3B4A82;margin-bottom:1rem;">
                <h3 style="font-family:Cairo,sans-serif;font-weight:700;
                    color:#1A1A2E;font-size:1rem;margin:0 0 1.25rem;">
                    ✏️ تعديل: {center.get('name','')}
                </h3>
            """, unsafe_allow_html=True)

            with st.form("edit_center_form"):
                c1, c2 = st.columns(2)
                with c1:
                    name = st.text_input("🏥 الاسم",    value=center.get("name",""))
                    city = st.text_input("🏙️ المدينة", value=center.get("city","جازان"))
                    cov  = st.number_input("📏 مساحة التغطية (كم²)",
                                           value=center.get("coverage_area", 50))
                with c2:
                    lat  = st.text_input("🌍 خط العرض", value=str(center.get("latitude","")))
                    lng  = st.text_input("🌐 خط الطول", value=str(center.get("longitude","")))
                    addr = st.text_area("📍 العنوان",   value=center.get("address",""))

                is_active = st.checkbox("✅ المركز نشط", value=center.get("is_active", True))

                bc1, bc2 = st.columns(2)
                with bc1:
                    save = st.form_submit_button("💾 حفظ", use_container_width=True, type="primary")
                with bc2:
                    cancel = st.form_submit_button("❌ إلغاء", use_container_width=True)

                if save:
                    data = dict(name=name, city=city,
                                coverage_area=cov or None,
                                latitude=lat or None,
                                longitude=lng or None,
                                address=addr or None,
                                is_active=is_active)
                    res = cs.update_center(center["id"], data)
                    if res:
                        st.success("✅ تم التحديث بنجاح")
                        del st.session_state.editing_center
                        st.rerun()
                if cancel:
                    del st.session_state.editing_center
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # تبويب 4 — مقارنة التغطية
    # ══════════════════════════════════════════════════════
    with tabs[3]:
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

        with st.spinner("جاري تحميل بيانات التغطية..."):
            centers_all = cs.get_centers() or []

        if not centers_all:
            st.info("لا توجد مراكز")
            return

        cov_data = []
        for center in centers_all:
            cov = cs.get_center_coverage(center["id"])
            cov_data.append({
                "المركز":   center["name"],
                "الكود":    center["code"],
                "التغطية":  cov.get("coverage_percentage", 0) if cov else 0,
                "الحالة":   cov.get("status", "—") if cov else "—",
            })

        df_cov = pd.DataFrame(cov_data).sort_values("التغطية", ascending=False)

        # رسم بياني
        st.markdown("""<div style="background:white;border-radius:14px;
            padding:1.25rem 1.5rem;border:1px solid #E2E8F0;
            box-shadow:0 4px 16px rgba(13,27,42,0.07);margin-bottom:1rem;">""",
            unsafe_allow_html=True)
        section_title("نسبة التغطية لكل مركز", "📊")
        display_chart(create_bar_chart(df_cov, "المركز", "التغطية",
                                       "", "#42924B", horizontal=True))
        st.markdown("</div>", unsafe_allow_html=True)

        # جدول مفصل
        st.markdown("""<div style="background:white;border-radius:14px;
            padding:1.25rem 1.5rem;border:1px solid #E2E8F0;
            box-shadow:0 4px 16px rgba(13,27,42,0.07);">""",
            unsafe_allow_html=True)
        section_title("جدول مقارنة التغطية", "📋")
        st.dataframe(df_cov, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)