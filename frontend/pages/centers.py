# frontend/pages/centers.py
import streamlit as st
import pandas as pd
from components.cards import center_card, kpi_row
from components.charts import create_bar_chart, create_gauge, display_chart
from utils.helpers import page_header, section_title
from utils.constants import CENTER_CODES, HQ_CENTER

st.cache_data.clear()

def _get_service():
    auth = st.session_state.auth_service
    cs = st.session_state.get("center_service")
    if not cs:
        from services.center_service import CenterService
        cs = CenterService(auth)
        st.session_state.center_service = cs
    return cs

def show_centers():
    """صفحة إدارة المراكز الإسعافية والتمركزات"""

    page_header("إدارة المراكز والتمركزات", "عرض وإضافة وتعديل المراكز والتمركزات التابعة", "🏥")

    cs = _get_service()
    tabs = st.tabs(["📋 قائمة المراكز", "➕ إضافة مركز/تمركز", "✏️ تعديل", "📊 التغطية"])

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
                <p style="font-size:0.95rem;margin:0;">لا توجد مراكز أو تمركزات مسجلة</p>
                <p style="font-size:0.8rem;color:#9CA3AF;margin-top:0.5rem;">أضف المركز الرئيسي أولاً</p>
            </div>""", unsafe_allow_html=True)
            return

        # تصنيف المراكز
        hq_centers = [c for c in centers if c.get('is_hq')]
        regular_centers = [c for c in centers if not c.get('is_hq') and not c.get('is_virtual')]
        deployments = [c for c in centers if c.get('is_virtual')]

        # إحصائيات سريعة
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🏢 المركز الرئيسي", len(hq_centers))
        with col2:
            st.metric("🏥 مراكز ثابتة", len(regular_centers))
        with col3:
            st.metric("🚚 تمركزات", len(deployments))
        with col4:
            active = sum(1 for c in centers if c.get("is_active"))
            st.metric("✅ نشط", active)
        
        st.markdown("<div style='margin:1rem 0;'></div>", unsafe_allow_html=True)

        # عرض المركز الرئيسي أولاً
        if hq_centers:
            st.markdown("### 🏢 المركز الرئيسي للقطاع")
            for center in hq_centers:
                cov = cs.get_center_coverage(center["id"])
                center_card(center, cov, is_hq=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏️ تعديل", key=f"cedit_{center['id']}", use_container_width=True):
                        st.session_state.editing_center = center
                        st.rerun()
                with col2:
                    lbl = "🔴 إيقاف" if center.get("is_active") else "🟢 تفعيل"
                    if st.button(lbl, key=f"ctoggle_{center['id']}", use_container_width=True):
                        cs.update_center(center["id"], {"is_active": not center.get("is_active")})
                        st.rerun()
                st.markdown("---")

        # عرض المراكز الثابتة
        if regular_centers:
            st.markdown("### 🏥 المراكز الثابتة")
            for i in range(0, len(regular_centers), 2):
                cols = st.columns(2)
                for j, col in enumerate(cols):
                    if i + j < len(regular_centers):
                        center = regular_centers[i + j]
                        cov = cs.get_center_coverage(center["id"])
                        with col:
                            center_card(center, cov)
                            bc1, bc2 = st.columns(2)
                            with bc1:
                                if st.button("✏️ تعديل", key=f"cedit_{center['id']}", use_container_width=True):
                                    st.session_state.editing_center = center
                                    st.rerun()
                            with bc2:
                                lbl = "🔴 إيقاف" if center.get("is_active") else "🟢 تفعيل"
                                if st.button(lbl, key=f"ctoggle_{center['id']}", use_container_width=True):
                                    cs.update_center(center["id"], {"is_active": not center.get("is_active")})
                                    st.rerun()
                            st.markdown("<div style='margin-bottom:0.5rem;'></div>", unsafe_allow_html=True)

        # عرض التمركزات
        if deployments:
            st.markdown("### 🚚 التمركزات (قوى دعم متنقلة)")
            for center in deployments:
                cov = cs.get_center_coverage(center["id"])
                st.markdown(f"""
                <div style="background: #F0F9FF; border-radius: 12px; padding: 1rem; margin-bottom: 1rem; border-right: 4px solid #45CFEF;">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="font-size: 2rem;">🚚</div>
                        <div>
                            <h4 style="margin: 0;">{center['name']}</h4>
                            <p style="margin: 0; color: #666;">كود: {center.get('code', '—')}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏️ تعديل", key=f"cedit_{center['id']}", use_container_width=True):
                        st.session_state.editing_center = center
                        st.rerun()
                with col2:
                    lbl = "🔴 إيقاف" if center.get("is_active") else "🟢 تفعيل"
                    if st.button(lbl, key=f"ctoggle_{center['id']}", use_container_width=True):
                        cs.update_center(center["id"], {"is_active": not center.get("is_active")})
                        st.rerun()
                st.markdown("---")

    # ══════════════════════════════════════════════════════
    # تبويب 2 — إضافة مركز/تمركز
    # ══════════════════════════════════════════════════════
    with tabs[1]:
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

        center_type = st.radio(
            "نوع الموقع",
            ["🏢 مركز رئيسي", "🏥 مركز ثابت", "🚚 تمركز"],
            horizontal=True
        )

        st.markdown(f"""
        <div style="background:white;border-radius:14px;padding:1.5rem;
            box-shadow:0 4px 20px rgba(13,27,42,0.08);border:1px solid #E2E8F0;
            border-top:3px solid #CE2E26;">
            <h3 style="font-family:Cairo,sans-serif;font-weight:700;
                color:#1A1A2E;font-size:1rem;margin:0 0 1.25rem;">
                ➕ إضافة {center_type}
            </h3>
        """, unsafe_allow_html=True)

        with st.form("add_center_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                code = st.text_input("🔤 كود المركز *", placeholder="مثال: HQ, C001, DEP1")
                name = st.text_input("🏥 الاسم *", placeholder="مثال: المركز الرئيسي, مركز الحائر")
                city = st.text_input("🏙️ المدينة", value="الرياض")
                
            with c2:
                if center_type != "🚚 تمركز":
                    coverage_area = st.number_input("📏 مساحة التغطية (كم²)", min_value=0, value=50)
                    latitude = st.text_input("🌍 خط العرض", placeholder="24.5667")
                    longitude = st.text_input("🌐 خط الطول", placeholder="46.7333")
                else:
                    st.info("📍 التمركزات متنقلة - لا تحتاج إحداثيات ثابتة")
                    coverage_area = 0
                    latitude = longitude = None

            address = st.text_area("📍 العنوان التفصيلي", placeholder="الحي، الشارع، الرقم...")

            submitted = st.form_submit_button("✅ إضافة", use_container_width=True, type="primary")
            if submitted:
                if not code or not name:
                    st.error("❌ الكود والاسم مطلوبان")
                else:
                    data = dict(
                        code=code,
                        name=name,
                        city=city,
                        latitude=latitude or None,
                        longitude=longitude or None,
                        coverage_area=coverage_area or None,
                        address=address or None,
                        is_active=True,
                        is_hq=(center_type == "🏢 مركز رئيسي"),
                        is_virtual=(center_type == "🚚 تمركز"),
                        center_type="قيادة" if center_type == "🏢 مركز رئيسي" else ("تمركز" if center_type == "🚚 تمركز" else "مركز ثابت")
                    )
                    res = cs.create_center(data)
                    if res:
                        st.success(f"✅ تم إضافة {name} بنجاح!")
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
                <p>اختر مركزاً أو تمركزاً من التبويب الأول ثم اضغط «تعديل»</p>
            </div>""", unsafe_allow_html=True)
        else:
            center = st.session_state.editing_center
            icon = "🏢" if center.get('is_hq') else ("🚚" if center.get('is_virtual') else "🏥")
            
            st.markdown(f"""
            <div style="background:white;border-radius:14px;padding:1.5rem;
                box-shadow:0 4px 20px rgba(13,27,42,0.08);border:1px solid #E2E8F0;
                border-top:3px solid #3B4A82;margin-bottom:1rem;">
                <h3 style="font-family:Cairo,sans-serif;font-weight:700;
                    color:#1A1A2E;font-size:1rem;margin:0 0 1.25rem;">
                    ✏️ تعديل: {icon} {center.get('name','')}
                </h3>
            """, unsafe_allow_html=True)

            with st.form("edit_center_form"):
                c1, c2 = st.columns(2)
                with c1:
                    name = st.text_input("🏥 الاسم", value=center.get("name",""))
                    city = st.text_input("🏙️ المدينة", value=center.get("city","الرياض"))
                    cov = st.number_input("📏 مساحة التغطية (كم²)",
                                          value=center.get("coverage_area", 50))
                with c2:
                    lat = st.text_input("🌍 خط العرض", value=str(center.get("latitude","")))
                    lng = st.text_input("🌐 خط الطول", value=str(center.get("longitude","")))
                    addr = st.text_area("📍 العنوان", value=center.get("address",""))

                is_active = st.checkbox("✅ نشط", value=center.get("is_active", True))

                bc1, bc2 = st.columns(2)
                with bc1:
                    save = st.form_submit_button("💾 حفظ", use_container_width=True, type="primary")
                with bc2:
                    cancel = st.form_submit_button("❌ إلغاء", use_container_width=True)

                if save:
                    data = dict(
                        name=name,
                        city=city,
                        coverage_area=cov or None,
                        latitude=lat or None,
                        longitude=lng or None,
                        address=addr or None,
                        is_active=is_active
                    )
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
    # تبويب 4 — التغطية
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
            if center.get('is_virtual'):
                continue  # التمركزات ما لها تغطية ثابتة
            cov = cs.get_center_coverage(center["id"])
            cov_data.append({
                "المركز": center["name"],
                "الكود": center["code"],
                "النوع": "رئيسي" if center.get('is_hq') else "ثابت",
                "التغطية": cov.get("coverage_percentage", 0) if cov else 0,
                "الحالة": cov.get("status", "—") if cov else "—",
            })

        if cov_data:
            df_cov = pd.DataFrame(cov_data).sort_values("التغطية", ascending=False)

            st.markdown("""<div style="background:white;border-radius:14px;
                padding:1.25rem 1.5rem;border:1px solid #E2E8F0;
                box-shadow:0 4px 16px rgba(13,27,42,0.07);margin-bottom:1rem;">""",
                unsafe_allow_html=True)
            section_title("نسبة التغطية لكل مركز", "📊")
            display_chart(create_bar_chart(df_cov, "المركز", "التغطية",
                                           "", "#42924B", horizontal=True))
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("""<div style="background:white;border-radius:14px;
                padding:1.25rem 1.5rem;border:1px solid #E2E8F0;
                box-shadow:0 4px 16px rgba(13,27,42,0.07);">""",
                unsafe_allow_html=True)
            section_title("جدول التغطية", "📋")
            st.dataframe(df_cov, use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("لا توجد مراكز ثابتة لعرض التغطية")