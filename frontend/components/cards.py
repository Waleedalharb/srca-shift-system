# frontend/components/cards.py
import streamlit as st

def metric_card(value, label, icon="📊", color="red"):
    """بطاقة إحصائية"""
    
    colors = {
        "red": {"bg": "linear-gradient(135deg, #CE2E26 0%, #B71C1C 100%)"},
        "green": {"bg": "linear-gradient(135deg, #42924B 0%, #2E7D32 100%)"},
        "navy": {"bg": "linear-gradient(135deg, #3B4A82 0%, #1A2B5C 100%)"},
        "gold": {"bg": "linear-gradient(135deg, #F1B944 0%, #C49A0E 100%)"},
        "gray": {"bg": "linear-gradient(135deg, #475569 0%, #1E293B 100%)"},
    }
    
    selected = colors.get(color, colors["red"])
    
    st.markdown(f"""
    <div style="
        background: {selected['bg']};
        padding: 1.2rem 1rem;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
    ">
        <div style="font-size: 2rem;">{icon}</div>
        <div style="font-size: 1.8rem; font-weight: 800; color: white;">{value}</div>
        <div style="color: rgba(255,255,255,0.9);">{label}</div>
    </div>
    """, unsafe_allow_html=True)

def kpi_row(items):
    """صف مؤشرات الأداء"""
    cols = st.columns(len(items))
    for col, (icon, value, label, color) in zip(cols, items):
        with col:
            metric_card(value, label, icon, color)

def center_card(center, coverage=None):
    """بطاقة مركز إسعافي"""
    
    active = "🟢 نشط" if center.get('is_active') else "🔴 متوقف"
    cov_pct = coverage.get('coverage_percentage', 0) if coverage else 0
    cov_color = "#42924B" if cov_pct >= 90 else "#F1B944" if cov_pct >= 70 else "#CE2E26"
    
    st.markdown(f"""
    <div style="background: white; border-radius: 16px; padding: 1.2rem; border: 1px solid #E2E8F0; margin-bottom: 1rem; direction: rtl;">
        <div style="display: flex; align-items: center; gap: 0.8rem; margin-bottom: 1rem;">
            <div style="width: 40px; height: 40px; background: #FEF2F2; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem;">🏥</div>
            <div>
                <h4 style="margin: 0; font-size: 1rem; color: #1A1A2E;">{center.get('name', '')}</h4>
                <p style="margin: 0; color: #64748B; font-size: 0.75rem;">{center.get('code', '')} · {active}</p>
            </div>
        </div>
        <div style="margin-top: 0.8rem;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.3rem;">
                <span style="color: #475569; font-size: 0.8rem;">نسبة التغطية</span>
                <span style="color: {cov_color}; font-weight: 700; font-size: 0.9rem;">{cov_pct}%</span>
            </div>
            <div style="width: 100%; height: 6px; background: #E2E8F0; border-radius: 10px; overflow: hidden;">
                <div style="width: {cov_pct}%; height: 100%; background: {cov_color}; border-radius: 10px;"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def employee_card(employee):
    """بطاقة موظف"""
    
    type_map = {
        "paramedic": "أخصائي",
        "emt": "مسعف",
        "admin": "إداري",
        "operations": "تحكم عملياتي",
        "coordinator": "تنسيق استجابة"
    }
    emp_type = type_map.get(employee.get('employee_type'), 'إداري')
    
    status = "🟢 نشط" if employee.get('is_active', True) else "🔴 غير نشط"
    on_duty = "🚑 على رأس العمل" if employee.get('is_on_duty') else "⏸️ في الإجازة"
    
    st.markdown(f"""
    <div style="background: white; border-radius: 16px; padding: 1.2rem; border: 1px solid #E2E8F0; margin-bottom: 1rem; direction: rtl;">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div style="width: 48px; height: 48px; background: #F8FAFC; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; border: 1px solid #E2E8F0;">👤</div>
            <div style="flex: 1;">
                <h4 style="margin: 0; font-size: 1rem; color: #1A1A2E;">{employee.get('full_name', '')}</h4>
                <p style="margin: 0.3rem 0 0 0; color: #64748B; font-size: 0.8rem;">
                    #{employee.get('emp_no', '')} · {emp_type} · {status} · {on_duty}
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def info_card(title, content, icon="ℹ️"):
    """بطاقة معلومات"""
    st.markdown(f"""
    <div style="background: #F8FAFC; border-radius: 12px; padding: 1rem; border: 1px solid #E2E8F0;">
        <div style="display: flex; gap: 0.5rem;">
            <span>{icon}</span>
            <div>
                <p style="margin: 0; font-weight: 700;">{title}</p>
                <p style="margin: 0.3rem 0 0 0; color: #64748B;">{content}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)