# frontend/pages/incidents.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from utils.helpers import page_header, section_title
from components.cards import kpi_row
import calendar

def _get_services():
    """تهيئة خدمات البلاغات"""
    auth = st.session_state.auth_service
    
    is = st.session_state.get("incident_service")
    es = st.session_state.get("employee_service")
    cs = st.session_state.get("center_service")
    ss = st.session_state.get("shift_service")
    
    if not is:
        from services.incident_service import IncidentService
        is = IncidentService(auth)
        st.session_state.incident_service = is
    
    if not es:
        from services.employee_service import EmployeeService
        es = EmployeeService(auth)
        st.session_state.employee_service = es
    
    if not cs:
        from services.center_service import CenterService
        cs = CenterService(auth)
        st.session_state.center_service = cs
    
    if not ss:
        from services.shift_service import ShiftService
        ss = ShiftService(auth)
        st.session_state.shift_service = ss
    
    return is, es, cs, ss

def show_incidents():
    """صفحة إدارة البلاغات والإحصائيات"""
    
    page_header("🚨 إدارة البلاغات", "تسجيل وإحصاءات البلاغات لكل فريق", "🚑")
    
    is_, es, cs, ss = _get_services()
    
    # تبويبات البلاغات
    tabs = st.tabs([
        "📊 لوحة البلاغات",
        "➕ تسجيل بلاغ جديد",
        "📈 إحصائيات الفرق",
        "📋 قائمة البلاغات"
    ])
    
    # ==================== لوحة البلاغات ====================
    with tabs[0]:
        st.subheader("📊 لوحة معلومات البلاغات")
        
        # اختيار الفترة
        col1, col2, col3 = st.columns(3)
        with col1:
            period = st.selectbox(
                "الفترة",
                ["اليوم", "آخر 7 أيام", "آخر 30 يوم", "شهر محدد"],
                index=1
            )
        
        end_date = datetime.now()
        if period == "اليوم":
            start_date = end_date.replace(hour=0, minute=0, second=0)
            date_range = f"{start_date.strftime('%Y-%m-%d')}"
        elif period == "آخر 7 أيام":
            start_date = end_date - timedelta(days=7)
            date_range = f"{start_date.strftime('%Y-%m-%d')} إلى {end_date.strftime('%Y-%m-%d')}"
        elif period == "آخر 30 يوم":
            start_date = end_date - timedelta(days=30)
            date_range = f"{start_date.strftime('%Y-%m-%d')} إلى {end_date.strftime('%Y-%m-%d')}"
        else:
            with col2:
                selected_month = st.selectbox("الشهر", range(1, 13), index=datetime.now().month-1)
            with col3:
                selected_year = st.number_input("السنة", 2024, 2026, datetime.now().year)
            start_date = datetime(selected_year, selected_month, 1)
            if selected_month == 12:
                end_date = datetime(selected_year+1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(selected_year, selected_month+1, 1) - timedelta(days=1)
            date_range = f"{start_date.strftime('%Y-%m-%d')} إلى {end_date.strftime('%Y-%m-%d')}"
        
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        st.caption(f"📅 الفترة: {date_range}")
        
        # جلب إحصائيات البلاغات
        with st.spinner("جاري تحميل الإحصائيات..."):
            team_stats = is_.get_incidents_stats_by_team(start_date_str, end_date_str)
            center_stats = is_.get_incidents_stats_by_center(start_date_str, end_date_str)
            avg_response = is_.get_avg_response_time(start_date_str, end_date_str)
        
        # مؤشرات رئيسية
        total_incidents = sum([t.get("count", 0) for t in team_stats]) if team_stats else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🚨 إجمالي البلاغات", total_incidents, help="إجمالي البلاغات في الفترة المحددة")
        with col2:
            st.metric("⏱️ متوسط الاستجابة", f"{avg_response.get('avg_minutes', 0):.1f} دقيقة", help="متوسط وقت الاستجابة")
        with col3:
            st.metric("🏥 عدد المراكز", len(center_stats))
        with col4:
            st.metric("👥 عدد الفرق", len(team_stats))
        
        st.markdown("---")
        
        # رسم بياني للبلاغات حسب الفرق
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 البلاغات حسب الفرق")
            if team_stats:
                df_teams = pd.DataFrame(team_stats)
                df_teams.columns = ["الفريق", "عدد البلاغات"]
                
                fig = px.bar(
                    df_teams,
                    x="الفريق",
                    y="عدد البلاغات",
                    color="عدد البلاغات",
                    color_continuous_scale=["#45CFEF", "#3B4A82", "#CE2E26"],
                    text="عدد البلاغات"
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("لا توجد بيانات للعرض")
        
        with col2:
            st.markdown("### 📈 البلاغات حسب المراكز")
            if center_stats:
                df_centers = pd.DataFrame(center_stats)
                df_centers.columns = ["المركز", "عدد البلاغات"]
                
                fig = px.pie(
                    df_centers,
                    values="عدد البلاغات",
                    names="المركز",
                    color_discrete_sequence=px.colors.sequential.RdBu,
                    hole=0.4
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("لا توجد بيانات للعرض")
    
    # ==================== تسجيل بلاغ جديد ====================
    with tabs[1]:
        st.subheader("➕ تسجيل بلاغ جديد")
        
        # جلب المناوبات النشطة
        centers = cs.get_centers()
        
        with st.form("incident_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                incident_number = st.text_input("📋 رقم البلاغ", placeholder="INC-2025-001")
                location = st.text_input("📍 الموقع", placeholder="الموقع التفصيلي")
                priority = st.selectbox(
                    "⚡ الأولوية",
                    ["high", "medium", "low"],
                    format_func=lambda x: {
                        "high": "عالية 🔴",
                        "medium": "متوسطة 🟡",
                        "low": "منخفضة 🟢"
                    }.get(x, x)
                )
                
                if centers:
                    center_names = [c["name"] for c in centers]
                    selected_center = st.selectbox("🏥 المركز", center_names)
                    center_id = next(c["id"] for c in centers if c["name"] == selected_center)
                else:
                    center_id = None
                    st.warning("لا توجد مراكز متاحة")
            
            with col2:
                call_time = st.datetime_input("⏰ وقت البلاغ", value=datetime.now())
                dispatch_time = st.datetime_input("🚑 وقت التوجيه", value=None)
                arrival_time = st.datetime_input("✅ وقت الوصول", value=None)
                
                # اختيار الفريق
                if center_id:
                    employees = es.get_employees(center_id=center_id)
                    emp_names = [f"{e['full_name']} ({e.get('emp_no', '')})" for e in employees]
                    selected_emp = st.selectbox("👥 الفريق المسؤول", [""] + emp_names)
                    if selected_emp:
                        assigned_crew = employees[emp_names.index(selected_emp)-1]["id"] if selected_emp != "" else None
                    else:
                        assigned_crew = None
                else:
                    assigned_crew = None
            
            notes = st.text_area("📝 ملاحظات إضافية")
            
            if st.form_submit_button("✅ تسجيل البلاغ", use_container_width=True, type="primary"):
                if not incident_number or not location:
                    st.error("❌ رقم البلاغ والموقع مطلوبان")
                else:
                    # تحضير البيانات
                    incident_data = {
                        "incident_number": incident_number,
                        "location": location,
                        "priority": priority,
                        "call_time": call_time.isoformat(),
                        "shift_id": None,  # يمكن ربطه بالمناوبة لاحقاً
                    }
                    
                    if dispatch_time:
                        incident_data["dispatch_time"] = dispatch_time.isoformat()
                    if arrival_time:
                        incident_data["arrival_time"] = arrival_time.isoformat()
                    if assigned_crew:
                        incident_data["assigned_crew"] = str(assigned_crew)
                    
                    # إرسال البيانات
                    result = is_.create_incident(incident_data)
                    if result:
                        st.success(f"✅ تم تسجيل البلاغ {incident_number} بنجاح")
                        st.balloons()
                        st.rerun()
    
    # ==================== إحصائيات الفرق ====================
    with tabs[2]:
        st.subheader("📈 إحصائيات الفرق")
        
        # اختيار الفترة
        col1, col2, col3 = st.columns(3)
        with col1:
            stats_month = st.selectbox("الشهر", range(1, 13), index=datetime.now().month-1, key="stats_month")
        with col2:
            stats_year = st.number_input("السنة", 2024, 2026, datetime.now().year, key="stats_year")
        with col3:
            if st.button("🔄 تحديث", use_container_width=True):
                st.rerun()
        
        # تحديد نطاق التاريخ
        stats_start = datetime(stats_year, stats_month, 1)
        if stats_month == 12:
            stats_end = datetime(stats_year+1, 1, 1) - timedelta(days=1)
        else:
            stats_end = datetime(stats_year, stats_month+1, 1) - timedelta(days=1)
        
        # جلب الإحصائيات
        with st.spinner("جاري تحميل إحصائيات الفرق..."):
            team_stats_detail = is_.get_incidents_stats_by_team(
                stats_start.strftime("%Y-%m-%d"),
                stats_end.strftime("%Y-%m-%d")
            )
            avg_response_time = is_.get_avg_response_time(
                stats_start.strftime("%Y-%m-%d"),
                stats_end.strftime("%Y-%m-%d")
            )
        
        st.markdown(f"### 📅 إحصائيات {stats_start.strftime('%B %Y')}")
        
        if team_stats_detail:
            # تحويل إلى DataFrame
            df_stats = pd.DataFrame(team_stats_detail)
            df_stats.columns = ["الفريق", "عدد البلاغات"]
            
            # إضافة متوسط وقت الاستجابة
            if avg_response_time:
                df_stats["متوسط وقت الاستجابة (دقيقة)"] = round(avg_response_time.get('avg_minutes', 0), 1)
            
            # عرض الجدول
            st.dataframe(df_stats, use_container_width=True, hide_index=True)
            
            # رسم بياني
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(
                    df_stats,
                    x="الفريق",
                    y="عدد البلاغات",
                    color="عدد البلاغات",
                    color_continuous_scale="Viridis",
                    title="عدد البلاغات لكل فريق"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # حساب الكفاءة (افتراضي - يمكن تعديله حسب المعايير)
                df_stats["الكفاءة"] = df_stats["عدد البلاغات"] / df_stats["عدد البلاغات"].max() * 100
                
                fig = px.line(
                    df_stats,
                    x="الفريق",
                    y="الكفاءة",
                    markers=True,
                    title="مؤشر كفاءة الفرق"
                )
                fig.update_traces(line=dict(color="#CE2E26", width=3))
                st.plotly_chart(fig, use_container_width=True)
            
            # تصدير
            csv_stats = df_stats.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                "📥 تصدير إحصائيات الفرق",
                data=csv_stats.encode('utf-8-sig'),
                file_name=f"team_stats_{stats_year}{stats_month:02d}.csv",
                mime="text/csv"
            )
        else:
            st.info("لا توجد بيانات للعرض في هذه الفترة")
    
    # ==================== قائمة البلاغات ====================
    with tabs[3]:
        st.subheader("📋 قائمة البلاغات")
        
        # جلب البلاغات
        with st.spinner("جاري تحميل البلاغات..."):
            incidents_data = is_.get_incidents(limit=500)
            incidents = incidents_data.get("items", [])
        
        if incidents:
            # تحويل البيانات للعرض
            incidents_table = []
            for inc in incidents:
                # تحويل الأولوية
                priority_icon = {
                    "high": "🔴 عالية",
                    "medium": "🟡 متوسطة",
                    "low": "🟢 منخفضة"
                }.get(inc.get("priority"), inc.get("priority"))
                
                # حساب وقت الاستجابة
                if inc.get("response_time"):
                    response_min = inc["response_time"] / 60
                    response_display = f"{response_min:.1f} د"
                else:
                    response_display = "—"
                
                incidents_table.append({
                    "رقم البلاغ": inc.get("incident_number", ""),
                    "الموقع": inc.get("location", ""),
                    "الأولوية": priority_icon,
                    "وقت البلاغ": inc.get("call_time", "")[:16].replace("T", " "),
                    "وقت الاستجابة": response_display,
                    "الحالة": "✅ مكتمل" if inc.get("end_time") else "🔄 قيد التنفيذ"
                })
            
            df_incidents = pd.DataFrame(incidents_table)
            st.dataframe(df_incidents, use_container_width=True, hide_index=True)
            
            # إحصائيات سريعة
            total = len(incidents)
            completed = sum(1 for i in incidents if i.get("end_time"))
            in_progress = total - completed
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 إجمالي البلاغات", total)
            with col2:
                st.metric("✅ مكتملة", completed, f"{completed/total*100:.1f}%" if total > 0 else "0%")
            with col3:
                st.metric("🔄 قيد التنفيذ", in_progress, f"{in_progress/total*100:.1f}%" if total > 0 else "0%")
            with col4:
                # حساب متوسط الاستجابة
                response_times = [i.get("response_time", 0) for i in incidents if i.get("response_time")]
                avg_response = sum(response_times) / len(response_times) / 60 if response_times else 0
                st.metric("⏱️ متوسط الاستجابة", f"{avg_response:.1f} دقيقة")
            
            # تصدير
            csv_incidents = df_incidents.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                "📥 تصدير قائمة البلاغات CSV",
                data=csv_incidents.encode('utf-8-sig'),
                file_name=f"incidents_list_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("لا توجد بلاغات مسجلة")