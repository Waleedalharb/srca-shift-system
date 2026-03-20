# frontend/pages/notifications.py
import streamlit as st
from services.notification_service import NotificationService
from datetime import datetime
import time

# ❌ احذف هذا السطر
# st.set_page_config(page_title="الإشعارات", layout="wide")

def format_time_ago(created_at):
    """تحويل التاريخ إلى صيغة 'منذ ...'"""
    try:
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        now = datetime.now()
        diff = now - created_at
        
        if diff.days > 30:
            return f"منذ {diff.days // 30} شهر"
        elif diff.days > 0:
            return f"منذ {diff.days} يوم"
        elif diff.seconds > 3600:
            return f"منذ {diff.seconds // 3600} ساعة"
        elif diff.seconds > 60:
            return f"منذ {diff.seconds // 60} دقيقة"
        else:
            return "الآن"
    except:
        return ""

def show_notifications():
    """عرض إشعارات النظام (للمشرفين)"""
    
    # التحقق من الصلاحية
    if 'user_role' not in st.session_state:
        st.switch_page("pages/login.py")
        return
    
    user_role = st.session_state.user_role
    
    st.title("🔔 إدارة الإشعارات")
    st.caption("عرض وإدارة إشعارات النظام")
    
    ns = NotificationService(st.session_state.auth_service)
    
    # أزرار التحكم
    col1, col2, col3 = st.columns([3, 1, 1])
    with col2:
        if st.button("📖 تعيين الكل كمقروء", use_container_width=True):
            with st.spinner("جاري تحديث الإشعارات..."):
                ns.mark_all_as_read()
                st.success("✅ تم تعيين جميع الإشعارات كمقروءة")
                time.sleep(1)
                st.rerun()
    with col3:
        if st.button("🔄 تحديث", use_container_width=True):
            st.rerun()
    
    # جلب الإشعارات
    with st.spinner("جاري تحميل الإشعارات..."):
        notifications = ns.get_my_notifications(limit=100)
    
    if not notifications:
        st.info("📭 لا توجد إشعارات")
        return
    
    # إحصائيات
    unread_count = len([n for n in notifications if not n.get('is_read')])
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📬 إجمالي الإشعارات", len(notifications))
    with col2:
        st.metric("🔔 غير مقروء", unread_count)
    with col3:
        st.metric("📖 مقروء", len(notifications) - unread_count)
    
    st.divider()
    
    # عرض الإشعارات
    for notif in notifications:
        with st.container():
            col1, col2 = st.columns([10, 1])
            with col1:
                icon_map = {
                    "shift_change": "🔄",
                    "new_shift": "➕",
                    "shift_deleted": "🗑️",
                    "system": "📌",
                    "alert": "⚠️"
                }
                icon = icon_map.get(notif.get("type"), "🔔")
                
                bg_color = '#fef2e8' if not notif.get('is_read') else 'white'
                border_color = '#CE2E26' if not notif.get('is_read') else '#E2E8F0'
                time_ago = format_time_ago(notif.get('created_at'))
                
                st.markdown(f"""
                <div style="
                    background: {bg_color};
                    padding: 14px;
                    border-radius: 12px;
                    margin-bottom: 10px;
                    border-right: 3px solid {border_color};
                ">
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                        <span style="font-size: 22px;">{icon}</span>
                        <strong style="font-size: 16px; color: #1A2B5C;">{notif.get('title', 'إشعار')}</strong>
                        <span style="font-size: 11px; color: #888; margin-right: auto;">{time_ago}</span>
                    </div>
                    <div style="color: #444; font-size: 14px; line-height: 1.5; padding-right: 32px;">
                        {notif.get('message', '')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if not notif.get('is_read'):
                    if st.button("📖", key=f"read_{notif['id']}"):
                        ns.mark_as_read(notif['id'])
                        st.rerun()

if __name__ == "__main__":
    show_notifications()