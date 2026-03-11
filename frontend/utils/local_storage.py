# frontend/utils/local_storage.py
import streamlit as st
import os
import pandas as pd
from datetime import datetime
import uuid
import json  # ✅ أضفنا json للتاريخ

class LocalStorage:
    def __init__(self):
        # ✅ المسار الصحيح (يطابق Mount Path في Render)
        self.base_path = "/opt/render/project/src/data"
        
        # تأكد من وجود المجلدات
        os.makedirs(self.base_path, exist_ok=True)
        os.makedirs(f"{self.base_path}/attendance", exist_ok=True)
        os.makedirs(f"{self.base_path}/uploads", exist_ok=True)
        os.makedirs(f"{self.base_path}/backup", exist_ok=True)  # ✅ للملفات الاحتياطية
    
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
            
            # سجل في ملف JSON منفصل (أضفناه)
            self._add_to_history({
                "center_name": center_name,
                "report_date": report_date.strftime("%Y-%m-%d"),
                "file_path": file_path,
                "filename": filename,
                "timestamp": timestamp,
                "type": "attendance"
            })
            
            return {
                "success": True,
                "url": f"file://{file_path}",
                "message": "✅ تم حفظ التقرير محلياً"
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def save_uploaded_file(self, uploaded_file):
        """حفظ ملف Excel مرفوع"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{uploaded_file.name}"
            file_path = f"{self.base_path}/uploads/{filename}"
            
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            return {
                "success": True,
                "file_path": file_path,
                "filename": filename
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _add_to_history(self, record):
        """إضافة سجل للتاريخ (في ملف JSON)"""
        try:
            history_file = f"{self.base_path}/history.json"
            
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            else:
                history = []
            
            history.append(record)
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def get_attendance_history(self, center_name=None):
        """جلب تاريخ التكميل"""
        try:
            history_file = f"{self.base_path}/history.json"
            if not os.path.exists(history_file):
                return []
            
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            attendance_records = [h for h in history if h.get('type') == 'attendance']
            
            if center_name and center_name != "الكل":
                attendance_records = [h for h in attendance_records if h.get('center_name') == center_name]
            
            return attendance_records
        except:
            return []
    
    def backup_data(self):
        """عمل نسخة احتياطية"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{self.base_path}/backup/backup_{timestamp}.json"
            
            data = {
                "timestamp": timestamp,
                "history": self.get_all_history(),
                "attendance_files": os.listdir(f"{self.base_path}/attendance") if os.path.exists(f"{self.base_path}/attendance") else []
            }
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return {"success": True, "file": backup_file}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_all_history(self):
        """جلب كل التاريخ"""
        try:
            history_file = f"{self.base_path}/history.json"
            if not os.path.exists(history_file):
                return []
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []