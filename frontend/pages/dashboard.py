import streamlit as st
import pandas as pd
from datetime import datetime

def show_dashboard():
    st.title("🏠 لوحة المعلومات")
    st.caption(f"آخر تحديث: {datetime.now().strftime('%Y/%m/%d %H:%M')}")
    st.divider()

    auth = st.session_state.auth_service
    if not st.session_state.get('employee_service'):
        from services.employee_service import EmployeeService
        from services.center_service import CenterService
        st.session_state.employee_service = EmployeeService(auth)
        st.session_state.center_service   = CenterService(auth)

    es = st.session_state.employee_service
    cs = st.session_state.center_service

    with st.spinner("جاري التحميل..."):
        stats   = es.get_stats()
        centers = cs.get_centers() or []

    if not stats:
        st.error("تعذر الاتصال بالخادم")
        return

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("👥 إجمالي الموظفين", stats.get("total",0))
    c2.metric("🚑 على رأس العمل",   stats.get("on_duty",0))
    c3.metric("✅ متاحون",           stats.get("available",0))
    c4.metric("🏥 المراكز",          len(centers))
    st.divider()

    from components.charts import create_bar_chart, create_pie_chart, display_chart
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("توزيع الموظفين حسب الفئة")
        bt = stats.get("by_type",{})
        df = pd.DataFrame({"الفئة":["أخصائيون","مسعفون","إداريون"],
            "العدد":[bt.get("paramedics",0),bt.get("emts",0),bt.get("admins",0)]})
        display_chart(create_bar_chart(df,"الفئة","العدد"))
    with col2:
        st.subheader("توزيع الموظفين على المراكز")
        top = stats.get("top_centers",[])
        if top:
            df2 = pd.DataFrame(top); df2.columns=["المركز","العدد"]
            display_chart(create_pie_chart(df2,"المركز","العدد"))

    st.divider()
    st.subheader("🏥 المراكز الإسعافية")
    if centers:
        rows = []
        for c in centers:
            cov = cs.get_center_coverage(c['id'])
            rows.append({"المركز":c['name'],"الكود":c['code'],"المدينة":c.get('city','الرياض'),
                "الحالة":"✅ نشط" if c.get('is_active') else "❌ متوقف",
                "التغطية":f"{cov.get('coverage_percentage',0)}%" if cov else "—"})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
