# frontend/pages/reports.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.helpers import page_header, section_title
from components.cards import kpi_row
import calendar

def _get_services():
    """تهيئة الخدمات المطلوبة"""
    auth = st.session_state.auth_service
    
    es = st.session_state.get("employee_service")
    cs = st.session_state.get("center_service")
    ss = st.session_state.get("shift_service")
    ins = st.session_state.get("incident_service")
    
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
    
    if not ins:
        from services.incident_service import IncidentService
        ins = IncidentService(auth)
        st.session_state.incident_service = ins
    
    return es, cs, ss, ins

def show_reports():
    """صفحة التقارير والإحصائيات"""
    
    page_header("التقارير والإحصائيات", "تقارير شاملة للمراكز والموظفين والبلاغات", "📊")
    
    es, cs, ss, ins = _get_services()
    
    # تبويبات التقارير (6 تبويبات)
    tabs = st.tabs([
        "📈 لوحة الأداء", 
        "👥 تقارير الموظفين", 
        "🏥 تقارير المراكز",
        "📅 تقارير المناوبات",
        "🚨 تقارير البلاغات",  # 👈 تبويب جديد
        "📊 إحصائيات متقدمة"
    ])
    
    # ==================== تبويب لوحة الأداء ====================
    with tabs[0]:
        st.subheader("📈 لوحة أداء قطاع الجنوب")
        
        with st.spinner("جاري تحميل البيانات..."):
            stats = es.get_stats()
            centers = cs.get_centers()
        
        if stats and centers:
            # مؤشرات رئيسية
            col1, col2, col3, col4 = st.columns(4)
            
            total_employees = stats.get("total", 0)
            on_duty = stats.get("on_duty", 0)
            available = stats.get("available", 0)
            
            with col1:
                st.metric(
                    "👥 إجمالي الموظفين", 
                    total_employees,
                    help="إجمالي عدد الموظفين في القطاع"
                )
            with col2:
                st.metric(
                    "🚑 على رأس العمل", 
                    on_duty,
                    delta=f"{on_duty/total_employees*100:.1f}%" if total_employees > 0 else "0%",
                    delta_color="normal"
                )
            with col3:
                st.metric(
                    "✅ متاحون", 
                    available,
                    delta=f"{available/total_employees*100:.1f}%" if total_employees > 0 else "0%"
                )
            with col4:
                st.metric(
                    "🏥 عدد المراكز", 
                    len(centers)
                )
            
            st.markdown("---")
            
            # صف البطاقات التفصيلية
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 👥 توزيع الموظفين حسب الفئة")
                by_type = stats.get("by_type", {})
                type_df = pd.DataFrame({
                    "الفئة": ["أخصائيين", "مسعفين", "إداريين"],
                    "العدد": [
                        by_type.get("paramedics", 0),
                        by_type.get("emts", 0),
                        by_type.get("admins", 0)
                    ]
                })
                
                fig = px.pie(
                    type_df, 
                    values='العدد', 
                    names='الفئة',
                    color_discrete_sequence=["#42924B", "#3B4A82", "#F1B944"],
                    hole=0.4
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("### 🏥 توزيع الموظفين حسب المركز")
                top_centers = stats.get("top_centers", [])
                if top_centers:
                    centers_df = pd.DataFrame(top_centers)
                    centers_df.columns = ["المركز", "العدد"]
                    
                    fig = px.bar(
                        centers_df,
                        x="المركز",
                        y="العدد",
                        color="العدد",
                        color_continuous_scale=["#FFB74D", "#4A6FA5", "#42924B"],
                        text="العدد"
                    )
                    fig.update_layout(height=350)
                    fig.update_traces(textposition='outside')
                    st.plotly_chart(fig, use_container_width=True)
    
    # ==================== تبويب تقارير الموظفين ====================
    with tabs[1]:
        st.subheader("👥 تقارير الموظفين")
        
        with st.spinner("جاري تحميل بيانات الموظفين..."):
            employees_data = es.get_employees(limit=500)
            employees = employees_data.get("items", [])
        
        if employees:
            # إحصائيات سريعة
            total = len(employees)
            paramedics = sum(1 for e in employees if e.get("employee_type") == "paramedic")
            emts = sum(1 for e in employees if e.get("employee_type") == "emt")
            admins = sum(1 for e in employees if e.get("employee_type") == "admin")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("👥 إجمالي", total)
            col2.metric("👨‍⚕️ أخصائيين", paramedics, f"{paramedics/total*100:.1f}%")
            col3.metric("🚑 مسعفين", emts, f"{emts/total*100:.1f}%")
            col4.metric("📋 إداريين", admins, f"{admins/total*100:.1f}%")
            
            st.markdown("---")
            
            # جدول الموظفين
            st.markdown("### 📋 قائمة الموظفين")
            
            # تجهيز البيانات للجدول
            emp_table = []
            for emp in employees[:100]:  # أول 100 موظف
                emp_type = {
                    "paramedic": "أخصائي",
                    "emt": "مسعف",
                    "admin": "إداري"
                }.get(emp.get("employee_type"), emp.get("employee_type"))
                
                emp_table.append({
                    "الرقم الوظيفي": emp.get("emp_no", ""),
                    "الاسم": emp.get("full_name", ""),
                    "الفئة": emp_type,
                    "الحالة": "🟢 نشط" if emp.get("is_active", True) else "🔴 غير نشط",
                    "على رأس العمل": "✅" if emp.get("is_on_duty") else "❌"
                })
            
            df_emp = pd.DataFrame(emp_table)
            st.dataframe(df_emp, use_container_width=True, hide_index=True)
            
            # زر تصدير - مع دعم العربية في Excel
            csv = df_emp.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                "📥 تصدير بيانات الموظفين CSV",
                data=csv.encode('utf-8-sig'),
                file_name=f"employees_report_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                help="ملص بصيغة CSV متوافقة مع Excel"
            )
    
    # ==================== تبويب تقارير المراكز ====================
    with tabs[2]:
        st.subheader("🏥 تقارير المراكز الإسعافية")
        
        with st.spinner("جاري تحميل بيانات المراكز..."):
            centers = cs.get_centers()
        
        if centers:
            # إحصائيات المراكز
            active_centers = sum(1 for c in centers if c.get("is_active"))
            
            col1, col2, col3 = st.columns(3)
            col1.metric("🏥 إجمالي المراكز", len(centers))
            col2.metric("✅ مراكز نشطة", active_centers)
            col3.metric("❌ مراكز متوقفة", len(centers) - active_centers)
            
            st.markdown("---")
            
            # بيانات التغطية للمراكز
            coverage_data = []
            for center in centers:
                coverage = cs.get_center_coverage(center["id"])
                if coverage:
                    coverage_data.append({
                        "المركز": center["name"],
                        "الكود": center["code"],
                        "نسبة التغطية": coverage.get("coverage_percentage", 0),
                        "الحالة": coverage.get("status", "—"),
                        "نشط": "✅" if center.get("is_active") else "❌"
                    })
            
            if coverage_data:
                df_coverage = pd.DataFrame(coverage_data)
                df_coverage = df_coverage.sort_values("نسبة التغطية", ascending=False)
                
                # رسم بياني للتغطية
                fig = px.bar(
                    df_coverage,
                    x="المركز",
                    y="نسبة التغطية",
                    color="نسبة التغطية",
                    color_continuous_scale=["#CE2E26", "#F1B944", "#42924B"],
                    text="نسبة التغطية",
                    title="نسبة تغطية المراكز"
                )
                fig.update_traces(texttemplate='%{text}%', textposition='outside')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("---")
                st.markdown("### 📋 تفاصيل المراكز")
                st.dataframe(df_coverage, use_container_width=True, hide_index=True)
                
                # زر تصدير - مع دعم العربية في Excel
                csv = df_coverage.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    "📥 تصدير تقرير المراكز CSV",
                    data=csv.encode('utf-8-sig'),
                    file_name=f"centers_report_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    help="ملف بصيغة CSV متوافقة مع Excel"
                )
    
    # ==================== تبويب تقارير المناوبات ====================
    with tabs[3]:
        st.subheader("📅 تقارير المناوبات")
        
        # اختيار الشهر والسنة
        col1, col2, col3 = st.columns(3)
        with col1:
            report_year = st.number_input("السنة", 2024, 2026, 2026)
        with col2:
            report_month = st.number_input("الشهر", 1, 12, datetime.now().month)
        with col3:
            if st.button("🔄 تحديث", use_container_width=True):
                st.rerun()
        
        st.info("📊 قريباً: إحصائيات المناوبات الفعلية")
        
        # بيانات تجريبية للعرض
        days_in_month = calendar.monthrange(report_year, report_month)[1]
        
        # توليد بيانات تجريبية
        import random
        random.seed(42)
        
        daily_shifts = []
        for day in range(1, days_in_month + 1):
            daily_shifts.append({
                "اليوم": day,
                "صباحية": random.randint(4, 8),
                "مسائية": random.randint(3, 7),
                "ليلية": random.randint(2, 5),
                "إجمالي": 0
            })
            daily_shifts[-1]["إجمالي"] = (
                daily_shifts[-1]["صباحية"] + 
                daily_shifts[-1]["مسائية"] + 
                daily_shifts[-1]["ليلية"]
            )
        
        df_shifts = pd.DataFrame(daily_shifts)
        
        # إحصائيات المناوبات
        total_shifts = df_shifts["إجمالي"].sum()
        avg_daily = total_shifts / days_in_month
        
        col1, col2, col3 = st.columns(3)
        col1.metric("📊 إجمالي المناوبات", total_shifts)
        col2.metric("📈 متوسط يومي", f"{avg_daily:.1f}")
        col3.metric("📅 أيام الشهر", days_in_month)
        
        # رسم بياني للمناوبات اليومية
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_shifts["اليوم"],
            y=df_shifts["صباحية"],
            mode='lines+markers',
            name='صباحية',
            line=dict(color='#FFB74D', width=3)
        ))
        fig.add_trace(go.Scatter(
            x=df_shifts["اليوم"],
            y=df_shifts["مسائية"],
            mode='lines+markers',
            name='مسائية',
            line=dict(color='#4A6FA5', width=3)
        ))
        fig.add_trace(go.Scatter(
            x=df_shifts["اليوم"],
            y=df_shifts["ليلية"],
            mode='lines+markers',
            name='ليلية',
            line=dict(color='#2D4A6E', width=3)
        ))
        
        fig.update_layout(
            title="توزيع المناوبات اليومية",
            xaxis_title="اليوم",
            yaxis_title="عدد المناوبات",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # تصدير تقرير المناوبات
        csv_shifts = df_shifts.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            "📥 تصدير تقرير المناوبات CSV",
            data=csv_shifts.encode('utf-8-sig'),
            file_name=f"shifts_report_{report_year}{report_month:02d}.csv",
            mime="text/csv"
        )
    
    # ==================== تبويب تقارير البلاغات (جديد) ====================
    with tabs[4]:
        st.subheader("🚨 تقارير البلاغات")
        
        # اختيار الفترة
        col1, col2, col3 = st.columns(3)
        with col1:
            report_start = st.date_input("من تاريخ", value=datetime.now().replace(day=1))
        with col2:
            report_end = st.date_input("إلى تاريخ", value=datetime.now())
        with col3:
            if st.button("🔄 عرض التقرير", use_container_width=True):
                st.rerun()
        
        # جلب إحصائيات البلاغات
        with st.spinner("جاري تحميل تقرير البلاغات..."):
            team_stats = ins.get_incidents_stats_by_team(
                report_start.strftime("%Y-%m-%d"),
                report_end.strftime("%Y-%m-%d")
            )
            center_stats = ins.get_incidents_stats_by_center(
                report_start.strftime("%Y-%m-%d"),
                report_end.strftime("%Y-%m-%d")
            )
            avg_response = ins.get_avg_response_time(
                report_start.strftime("%Y-%m-%d"),
                report_end.strftime("%Y-%m-%d")
            )
        
        # ملخص التقرير
        total_incidents = sum([t.get("count", 0) for t in team_stats]) if team_stats else 0
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e3c72, #2a5298); padding: 1.5rem; border-radius: 16px; color: white; margin-bottom: 1.5rem;">
            <h3 style="margin: 0;">📊 تقرير البلاغات</h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">{report_start.strftime('%Y/%m/%d')} - {report_end.strftime('%Y/%m/%d')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🚨 إجمالي البلاغات", total_incidents)
        with col2:
            st.metric("⏱️ متوسط الاستجابة", f"{avg_response.get('avg_minutes', 0):.1f} دقيقة")
        with col3:
            st.metric("🏥 عدد المراكز", len(center_stats))
        
        st.markdown("---")
        
        # عرض إحصائيات الفرق
        if team_stats:
            st.markdown("### 👥 إحصائيات الفرق")
            df_team_report = pd.DataFrame(team_stats)
            df_team_report.columns = ["الفريق", "عدد البلاغات"]
            
            col1, col2 = st.columns(2)
            
            with col1:
                # رسم بياني
                fig = px.bar(
                    df_team_report,
                    x="الفريق",
                    y="عدد البلاغات",
                    color="عدد البلاغات",
                    color_continuous_scale="Reds",
                    text="عدد البلاغات"
                )
                fig.update_traces(textposition='outside')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # جدول
                st.dataframe(df_team_report, use_container_width=True, hide_index=True)
            
            # إحصائيات حسب المركز
            if center_stats:
                st.markdown("### 🏥 إحصائيات المراكز")
                df_center_report = pd.DataFrame(center_stats)
                df_center_report.columns = ["المركز", "عدد البلاغات"]
                
                fig = px.pie(
                    df_center_report,
                    values="عدد البلاغات",
                    names="المركز",
                    title="توزيع البلاغات حسب المركز"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # زر طباعة التقرير
        if st.button("🖨️ طباعة التقرير", use_container_width=True):
            html_content = f"""
            <html dir="rtl">
            <head>
                <meta charset="UTF-8">
                <title>تقرير البلاغات</title>
                <style>
                    body {{ font-family: 'Arial', sans-serif; margin: 20px; direction: rtl; }}
                    .header {{ text-align: center; border-bottom: 2px solid #CE2E26; padding-bottom: 10px; margin-bottom: 20px; }}
                    .header h1 {{ color: #CE2E26; margin: 5px; }}
                    .header h2 {{ color: #1A2B5C; margin: 5px; }}
                    .stats {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin: 20px 0; }}
                    .stat-box {{ background: #f5f5f5; padding: 15px; border-radius: 8px; text-align: center; }}
                    .stat-box strong {{ display: block; font-size: 14px; color: #666; margin-bottom: 5px; }}
                    .stat-box .value {{ font-size: 24px; font-weight: bold; color: #1A2B5C; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                    th {{ background: #1e3c72; color: white; padding: 10px; text-align: center; }}
                    td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
                    .footer {{ margin-top: 30px; display: flex; justify-content: space-between; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>هيئة الهلال الأحمر السعودي</h1>
                    <h2>تقرير البلاغات - قطاع الجنوب</h2>
                    <h3>{report_start.strftime('%Y/%m/%d')} - {report_end.strftime('%Y/%m/%d')}</h3>
                </div>
                
                <div class="stats">
                    <div class="stat-box">
                        <strong>إجمالي البلاغات</strong>
                        <div class="value">{total_incidents}</div>
                    </div>
                    <div class="stat-box">
                        <strong>متوسط الاستجابة</strong>
                        <div class="value">{avg_response.get('avg_minutes', 0):.1f} دقيقة</div>
                    </div>
                    <div class="stat-box">
                        <strong>عدد المراكز</strong>
                        <div class="value">{len(center_stats)}</div>
                    </div>
                </div>
                
                <h3>إحصائيات الفرق</h3>
                <table>
                    <tr><th>الفريق</th><th>عدد البلاغات</th></tr>
            """
            
            for team in team_stats:
                html_content += f"<tr><td>{team[0]}</td><td>{team[1]}</td></tr>"
            
            html_content += f"""
                </table>
                
                <div class="footer">
                    <div>توقيع المشرف: ________________</div>
                    <div>تاريخ الطباعة: {datetime.now().strftime('%Y/%m/%d %H:%M')}</div>
                </div>
            </body>
            </html>
            """
            
            st.markdown(html_content, unsafe_allow_html=True)
            st.markdown("""
            <div style="text-align: center; margin: 20px;">
                <button onclick="window.print()" style="
                    background: #CE2E26;
                    color: white;
                    padding: 10px 30px;
                    border: none;
                    border-radius: 5px;
                    font-size: 16px;
                    cursor: pointer;
                ">🖨️ طباعة</button>
            </div>
            """, unsafe_allow_html=True)
    
    # ==================== تبويب إحصائيات متقدمة ====================
    with tabs[5]:
        st.subheader("📊 إحصائيات متقدمة")
        
        with st.spinner("جاري تحميل البيانات..."):
            stats = es.get_stats()
        
        if stats:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📈 نسب التشغيل")
                
                total = stats.get("total", 1)
                on_duty = stats.get("on_duty", 0)
                available = stats.get("available", 0)
                
                # مؤشرات دائرية
                fig = go.Figure()
                
                fig.add_trace(go.Indicator(
                    mode="gauge+number",
                    value=on_duty/total*100,
                    title={"text": "نسبة التشغيل"},
                    domain={'x': [0, 0.5], 'y': [0, 1]},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "#42924B"},
                        'steps': [
                            {'range': [0, 50], 'color': "#FFEBEE"},
                            {'range': [50, 75], 'color': "#FFF8E1"},
                            {'range': [75, 100], 'color': "#E8F5E9"}
                        ]
                    }
                ))
                
                fig.add_trace(go.Indicator(
                    mode="gauge+number",
                    value=available/total*100,
                    title={"text": "نسبة الإتاحة"},
                    domain={'x': [0.5, 1], 'y': [0, 1]},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "#3B4A82"},
                        'steps': [
                            {'range': [0, 50], 'color': "#FFEBEE"},
                            {'range': [50, 75], 'color': "#FFF8E1"},
                            {'range': [75, 100], 'color': "#E8F5E9"}
                        ]
                    }
                ))
                
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("### 📊 مؤشرات الأداء")
                
                # جدول مؤشرات
                kpi_data = pd.DataFrame({
                    "المؤشر": [
                        "إجمالي الموظفين",
                        "أخصائيين", 
                        "مسعفين",
                        "إداريين",
                        "على رأس العمل",
                        "متاحون"
                    ],
                    "القيمة": [
                        total,
                        stats.get("by_type", {}).get("paramedics", 0),
                        stats.get("by_type", {}).get("emts", 0),
                        stats.get("by_type", {}).get("admins", 0),
                        on_duty,
                        available
                    ]
                })
                
                st.dataframe(kpi_data, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # تحليل المراكز
            st.markdown("### 🏥 تحليل أداء المراكز")
            
            centers = cs.get_centers()
            if centers:
                center_analysis = []
                for center in centers:
                    coverage = cs.get_center_coverage(center["id"])
                    if coverage:
                        center_analysis.append({
                            "المركز": center["name"],
                            "التغطية": coverage.get("coverage_percentage", 0),
                            "التقييم": coverage.get("status", "—")
                        })
                
                if center_analysis:
                    df_analysis = pd.DataFrame(center_analysis)
                    
                    # توزيع المراكز حسب التقييم
                    eval_counts = df_analysis["التقييم"].value_counts().reset_index()
                    eval_counts.columns = ["التقييم", "العدد"]
                    
                    fig = px.pie(
                        eval_counts,
                        values='العدد',
                        names='التقييم',
                        color_discrete_sequence=["#42924B", "#F1B944", "#CE2E26"],
                        title="توزيع المراكز حسب التقييم"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # تصدير التحليل
                    csv_analysis = df_analysis.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        "📥 تصدير تحليل المراكز CSV",
                        data=csv_analysis.encode('utf-8-sig'),
                        file_name=f"centers_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )