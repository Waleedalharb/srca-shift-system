import streamlit as st
import os
import pandas as pd
from datetime import datetime
import uuid

class LocalStorage:
    def __init__(self):
        # ✅ المسار الصحيح (يطابق Mount Path في Render)
        self.base_path = "/opt/render/project/src/data"
        
        # تأكد من وجود المجلدات
        os.makedirs(self.base_path, exist_ok=True)
        os.makedirs(f"{self.base_path}/attendance", exist_ok=True)
        os.makedirs(f"{self.base_path}/uploads", exist_ok=True)  # للملفات المرفوعة
    
    def save_attendance_report(self, attendance_data, center_name, report_date):
        """حفظ تقرير التكميل محلياً"""
        try:
            # تحويل البيانات إلى DataFrame
            df = pd.DataFrame(attendance_data)
            
            # تنظيف اسم المركز
            clean_center = center_name.replace(" ", "_")
            
            # إنشاء اسم الملف
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"attendance_{clean_center}_{timestamp}.csv"
            
            # المسار الكامل
            file_path = f"{self.base_path}/attendance/{filename}"
            
            # حفظ الملف
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            # إنشاء سجل في session_state (بدلاً من قاعدة البيانات)
            if "attendance_history" not in st.session_state:
                st.session_state.attendance_history = []
            
            st.session_state.attendance_history.append({
                "center_name": center_name,
                "report_date": report_date.strftime("%Y-%m-%d"),
                "file_path": file_path,
                "timestamp": timestamp
            })
            
            return {
                "success": True,
                "url": f"file://{file_path}",  # للعرض المحلي
                "message": "✅ تم حفظ التقرير محلياً"
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def get_attendance_history(self, center_name=None):
        """جلب تاريخ التكميل"""
        history = st.session_state.get("attendance_history", [])
        if center_name and center_name != "الكل":
            history = [h for h in history if h["center_name"] == center_name]
        return history