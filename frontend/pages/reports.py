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
    
    if not es:
        from services.employee_service import EmployeeService
        es = EmployeeService(auth)
        st.session_state.employee_service = es
    
    if not cs:
        from services.center_service import CenterService
        cs = CenterService(auth)
        st.session_state.center_service = cs
    
    return es, cs

def show_reports():
    """صفحة التقارير والإحصائيات"""
    
    page_header("التقارير والإحصائيات", "تقارير شاملة للمراكز والموظفين", "📊")
    
    es, cs = _get_services()
    
    # تبويبات التقارير
    tabs = st.tabs([
        "📈 لوحة الأداء", 
        "👥 تقارير الموظفين", 
        "🏥 تقارير المراكز",
        "📅 تقارير المناوبات",
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
    
    # ==================== تبويب إحصائيات متقدمة ====================
    with tabs[4]:
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