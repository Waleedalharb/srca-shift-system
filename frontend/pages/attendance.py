# frontend/pages/attendance.py
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from utils.helpers import page_header, section_title
from components.cards import kpi_row

def show_attendance():
    """صفحة نظام التكميل (الحضور والغياب)"""
    
    page_header("نظام التكميل", "تسجيل الحضور والغياب اليومي", "📱")
    
    auth = st.session_state.auth_service
    es = st.session_state.get("employee_service")
    ss = st.session_state.get("shift_service")
    
    if not es:
        from services.employee_service import EmployeeService
        es = EmployeeService(auth)
        st.session_state.employee_service = es
    
    if not ss:
        from services.shift_service import ShiftService
        ss = ShiftService(auth)
        st.session_state.shift_service = ss
    
    # جلب بيانات المستخدم الحالي
    current_user = st.session_state.get("username", "")
    user_role = st.session_state.get("user_role", "employee")
    
    # تبويبات حسب الصلاحية
    if user_role in ["chief_paramedic", "field_leader"]:
        tabs = st.tabs(["📝 تسجيل الحضور", "📋 تقارير الغياب", "⚙️ إدارة الطلبات"])
    else:
        tabs = st.tabs(["📝 تسجيل الحضور", "📋 سجلي الشخصي"])
    
    # ==================== تبويب تسجيل الحضور ====================
    with tabs[0]:
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
        
        # تاريخ اليوم
        today = date.today()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"""
            <div style="background: #F8FAFC; padding: 1rem; border-radius: 12px; 
                 border: 1px solid #E2E8F0; margin-bottom: 1rem;">
                <h4 style="margin: 0; color: #1A1A2E;">📅 تاريخ اليوم: {today.strftime('%Y/%m/%d')}</h4>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # زر تحديث سريع
            if st.button("🔄 تحديث", use_container_width=True):
                st.rerun()
        
        # جلب الموظفين (للمشرف) أو موظف واحد (للموظف)
        if user_role in ["chief_paramedic", "field_leader"]:
            # جلب جميع الموظفين
            centers = st.session_state.get("center_service").get_centers() if "center_service" in st.session_state else []
            center_options = {"جميع المراكز": None}
            for c in centers:
                center_options[c["name"]] = c["id"]
            
            selected_center = st.selectbox("🏥 تصفية حسب المركز", list(center_options.keys()))
            center_id = center_options[selected_center]
            
            employees = es.get_employees(center_id=center_id).get("items", [])
        else:
            # موظف عادي - نجيب بياناته فقط
            # هذا يحتاج ربط مع حساب المستخدم
            employees = []  # مؤقتاً
        
        if not employees:
            st.info("لا يوجد موظفون للتسجيل")
        else:
            # نموذج تسجيل الحضور
            st.markdown("### 📝 سجل حضورك اليومي")
            
            # عرض الموظفين في جدول تسجيل
            attendance_data = []
            
            for emp in employees[:10]:  # حد أقصى 10 موظفين للعرض
                # التحقق من وجود مناوبة اليوم
                today_shift = "صباحي"  # هذا يجلب من قاعدة البيانات
                
                attendance_data.append({
                    "الموظف": emp["full_name"],
                    "الرقم": emp.get("emp_no", ""),
                    "المناوبة": today_shift,
                    "الحضور": None,  # راح يكون اختيار
                    "ملاحظات": ""
                })
            
            # عرض جدول التعديل
            df = pd.DataFrame(attendance_data)
            
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "الموظف": st.column_config.TextColumn("الموظف", disabled=True),
                    "الرقم": st.column_config.TextColumn("الرقم", disabled=True),
                    "المناوبة": st.column_config.TextColumn("المناوبة", disabled=True),
                    "الحضور": st.column_config.SelectboxColumn(
                        "الحضور",
                        options=["✅ حاضر", "❌ غائب", "⏰ متأخر", "🏖️ إجازة", "🕐 إذن"],
                        required=True
                    ),
                    "ملاحظات": st.column_config.TextColumn("ملاحظات"),
                }
            )
            
            # زر الحفظ
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("💾 حفظ التكميل", type="primary", use_container_width=True):
                    st.success("✅ تم تسجيل الحضور بنجاح")
                    st.balloons()
    
    # ==================== تبويب تقارير الغياب ====================
    with tabs[1]:
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
        
        # فلترة التاريخ
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("من تاريخ", value=date.today() - timedelta(days=30))
        with col2:
            end_date = st.date_input("إلى تاريخ", value=date.today())
        
        # إحصائيات سريعة
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📅 أيام العمل", "22")
        with col2:
            st.metric("✅ حضور", "198")
        with col3:
            st.metric("❌ غياب", "12")
        with col4:
            st.metric("📊 نسبة الغياب", "5.7%")
        
        st.markdown("---")
        
        # جدول الغيابات
        st.subheader("📋 سجل الغيابات")
        
        # بيانات تجريبية
        leaves_data = pd.DataFrame({
            "الموظف": ["أحمد محمد", "سعد عبدالله", "فهد ناصر"],
            "التاريخ": ["2026-03-01", "2026-03-02", "2026-03-03"],
            "الحالة": ["❌ غائب", "✅ حاضر", "🏖️ إجازة"],
            "ملاحظات": ["مرض", "", "إجازة سنوية"]
        })
        
        st.dataframe(leaves_data, use_container_width=True, hide_index=True)
        
        # زر تصدير
        csv = leaves_data.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            "📥 تصدير التقرير",
            data=csv,
            file_name=f"attendance_report_{date.today()}.csv",
            mime="text/csv"
        )
    
    # ==================== تبويب إدارة الطلبات (للمشرف فقط) ====================
    if user_role in ["chief_paramedic", "field_leader"] and len(tabs) > 2:
        with tabs[2]:
            st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
            
            st.subheader("⚙️ طلبات الإجازة pending")
            
            # طلبات pending
            requests_data = pd.DataFrame({
                "الموظف": ["خالد القحطاني", "ناصر الشمري"],
                "من تاريخ": ["2026-03-10", "2026-03-15"],
                "إلى تاريخ": ["2026-03-15", "2026-03-20"],
                "الأيام": ["6", "6"],
                "النوع": ["سنوية", "مرضية"],
                "الحالة": ["🟡 قيد الانتظار", "🟡 قيد الانتظار"]
            })
            
            for i, row in requests_data.iterrows():
                with st.container():
                    col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1, 1, 1, 1, 1, 1])
                    
                    with col1:
                        st.write(row["الموظف"])
                    with col2:
                        st.write(row["من تاريخ"])
                    with col3:
                        st.write(row["إلى تاريخ"])
                    with col4:
                        st.write(row["الأيام"])
                    with col5:
                        st.write(row["النوع"])
                    with col6:
                        if st.button("✅ قبول", key=f"accept_{i}"):
                            st.success("تم القبول")
                    with col7:
                        if st.button("❌ رفض", key=f"reject_{i}"):
                            st.error("تم الرفض")
                    st.divider()