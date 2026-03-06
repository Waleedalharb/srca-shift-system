# frontend/pages/prediction.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.helpers import page_header, section_title
import calendar

def show_prediction():
    """صفحة التنبؤ بالازدحام"""
    
    page_header("نظام التنبؤ الذكي", "توقع أوقات الذروة وتحسين المناوبات", "🔮")
    
    # تبويبات
    tabs = st.tabs(["📊 تنبؤ يومي", "📅 تنبؤ شهري", "🌙 تحليل رمضان", "📈 تدريب النموذج"])
    
    # ===== تنبؤ يومي =====
    with tabs[0]:
        st.subheader("🔮 التنبؤ ليوم محدد")
        
        col1, col2 = st.columns(2)
        
        with col1:
            pred_date = st.date_input("📅 اختر التاريخ", value=datetime.now())
            staff_count = st.number_input("👥 عدد الموظفين المتاحين", 10, 50, 30)
        
        with col2:
            if st.button("🔮 توقع", type="primary", use_container_width=True):
                st.session_state.show_prediction = True
        
        if st.session_state.get("show_prediction", False):
            # بيانات تجريبية للعرض
            import random
            random.seed(pred_date.toordinal())
            
            predicted = random.randint(35, 75)
            confidence = random.randint(75, 95)
            
            # عرض النتائج
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📊 توقع البلاغات", predicted, delta=f"{predicted-45} عن المعدل")
            with col2:
                st.metric("🎯 نسبة الثقة", f"{confidence}%")
            with col3:
                status = "🔴 مرتفع" if predicted > 60 else "🟡 متوسط" if predicted > 40 else "🟢 منخفض"
                st.metric("📈 مستوى الازدحام", status)
            
            st.markdown("---")
            
            # ساعات الذروة
            st.subheader("⏰ ساعات الذروة المتوقعة")
            
            peak_hours = ["08:00-10:00", "12:00-14:00", "16:00-18:00"]
            
            cols = st.columns(len(peak_hours))
            for i, hour in enumerate(peak_hours):
                with cols[i]:
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #CE2E26 0%, #B71C1C 100%);
                        color: white;
                        padding: 1rem;
                        border-radius: 12px;
                        text-align: center;
                    ">
                        <h3 style="margin: 0;">{hour}</h3>
                        <p style="margin: 0; opacity: 0.9;">ازدحام متوقع</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # توصيات
            st.subheader("💡 التوصيات")
            
            if predicted > 60:
                st.warning("🔴 ازدحام مرتفع متوقع - يفضل زيادة المناوبات 30%")
            elif predicted > 45:
                st.info("🟡 ازدحام متوسط - تجهيز فرق احتياط")
            else:
                st.success("🟢 هدوء متوقع - يمكن منح إجازات")
    
    # ===== تنبؤ شهري =====
    with tabs[1]:
        st.subheader("📅 التنبؤ الشهري")
        
        col1, col2 = st.columns(2)
        
        with col1:
            pred_year = st.number_input("السنة", 2025, 2027, 2026)
        with col2:
            pred_month = st.selectbox("الشهر", range(1, 13), 
                                      format_func=lambda x: {
                                          1:"يناير",2:"فبراير",3:"مارس",4:"أبريل",
                                          5:"مايو",6:"يونيو",7:"يوليو",8:"أغسطس",
                                          9:"سبتمبر",10:"أكتوبر",11:"نوفمبر",12:"ديسمبر"
                                      }[x])
        
        if st.button("📊 تحليل الشهر", use_container_width=True):
            # بيانات تجريبية
            import random
            random.seed(pred_year * 100 + pred_month)
            
            days_in_month = calendar.monthrange(pred_year, pred_month)[1]
            
            data = []
            for day in range(1, days_in_month + 1):
                data.append({
                    "اليوم": day,
                    "البلاغات المتوقعة": random.randint(30, 70),
                    "الحد الأعلى": 0,
                    "الحد الأدنى": 0
                })
                data[-1]["الحد الأعلى"] = data[-1]["البلاغات المتوقعة"] + random.randint(5, 10)
                data[-1]["الحد الأدنى"] = data[-1]["البلاغات المتوقعة"] - random.randint(5, 10)
            
            df = pd.DataFrame(data)
            
            # رسم بياني
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df["اليوم"],
                y=df["البلاغات المتوقعة"],
                mode='lines+markers',
                name='المتوقع',
                line=dict(color='#CE2E26', width=3)
            ))
            
            fig.add_trace(go.Scatter(
                x=df["اليوم"],
                y=df["الحد الأعلى"],
                mode='lines',
                name='الحد الأعلى',
                line=dict(width=0),
                showlegend=False
            ))
            
            fig.add_trace(go.Scatter(
                x=df["اليوم"],
                y=df["الحد الأدنى"],
                mode='lines',
                name='الحد الأدنى',
                line=dict(width=0),
                fill='tonexty',
                fillcolor='rgba(206, 46, 38, 0.2)',
                showlegend=False
            ))
            
            fig.update_layout(
                title="توزيع البلاغات المتوقعة خلال الشهر",
                xaxis_title="اليوم",
                yaxis_title="عدد البلاغات",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # إحصائيات الشهر
            col1, col2, col3 = st.columns(3)
            
            total_calls = df["البلاغات المتوقعة"].sum()
            avg_calls = df["البلاغات المتوقعة"].mean()
            peak_days = len(df[df["البلاغات المتوقعة"] > 55])
            
            col1.metric("📊 إجمالي البلاغات", f"{total_calls}")
            col2.metric("📈 متوسط يومي", f"{avg_calls:.1f}")
            col3.metric("🔴 أيام الذروة", peak_days)
    
    # ===== تحليل رمضان =====
    with tabs[2]:
        st.subheader("🌙 تحليل شهر رمضان")
        
        ramadan_year = st.number_input("سنة رمضان", 2026, 2028, 2026)
        
        if st.button("تحليل رمضان", use_container_width=True):
            # بيانات تجريبية لرمضان
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #1A2B5C 0%, #3B4A82 100%);
                color: white;
                padding: 2rem;
                border-radius: 16px;
                text-align: center;
                margin-bottom: 2rem;
            ">
                <h2>🌙 تحليل رمضان 2026</h2>
                <p style="font-size: 1.2rem;">18 فبراير - 19 مارس (تقديري)</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            col1.metric("📊 متوسط يومي", "58 بلاغ", "30%")
            col2.metric("🔴 أيام ذروة", "12 يوم", "5 أيام")
            col3.metric("📈 زيادة متوقعة", "35%", "")
            
            st.markdown("---")
            
            # أيام الذروة
            st.subheader("🔴 أيام الذروة المتوقعة")
            
            peak_days_data = pd.DataFrame({
                "التاريخ": ["2026-02-23", "2026-02-28", "2026-03-05", "2026-03-10", "2026-03-15"],
                "البلاغات المتوقعة": [72, 75, 68, 71, 69],
                "التوصية": ["زيادة 30%", "زيادة 35%", "زيادة 25%", "زيادة 30%", "زيادة 25%"]
            })
            
            st.dataframe(peak_days_data, use_container_width=True, hide_index=True)
            
            # توصية نهائية
            st.success("""
            ✅ **التوصية النهائية:**  
            زيادة المناوبات بنسبة 25-30% في أيام الذروة  
            تجهيز 5 فرق احتياط طوال الشهر  
            تقليل الإجازات في الأسبوعين الأول والثالث
            """)
    
    # ===== تدريب النموذج =====
    with tabs[3]:
        st.subheader("📈 تدريب نموذج التنبؤ")
        
        st.warning("""
        ⚠️ **ملاحظة:** تدريب النموذج يحتاج بيانات حقيقية عن البلاغات.
        حالياً نستخدم بيانات تجريبية للعرض.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            days_back = st.number_input("أيام التدريب", 30, 365, 180)
            st.info(f"سيتم التدريب على آخر {days_back} يوم")
        
        with col2:
            if st.button("🚀 بدء التدريب", type="primary", use_container_width=True):
                with st.spinner("جاري تدريب النموذج..."):
                    import time
                    time.sleep(2)
                st.success("✅ تم تدريب النموذج بنجاح بدقة 87%")
                st.balloons()