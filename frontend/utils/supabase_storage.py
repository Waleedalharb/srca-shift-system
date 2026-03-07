# frontend/utils/supabase_storage.py
import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import uuid
import pandas as pd
import io

class SupabaseStorage:
    def __init__(self):
        """تهيئة الاتصال مع Supabase Storage"""
        self.supabase_url = st.secrets["SUPABASE_URL"]
        self.supabase_key = st.secrets["SUPABASE_KEY"]
        self.bucket_name = "srca-reports"
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
    
    def upload_file(self, file_bytes, file_name, folder="reports", content_type="text/csv"):
        """رفع ملف إلى Supabase Storage"""
        try:
            # إنشاء مسار فريد للملف
            date_str = datetime.now().strftime("%Y/%m/%d")
            unique_id = str(uuid.uuid4())[:8]
            file_path = f"{folder}/{date_str}/{unique_id}_{file_name}"
            
            # رفع الملف
            result = self.supabase.storage.from_(self.bucket_name).upload(
                path=file_path,
                file=file_bytes,
                file_options={"content-type": content_type}
            )
            
            # الحصول على الرابط العام
            public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(file_path)
            
            # حفظ معلومات الملف في قاعدة البيانات
            self._save_file_metadata(file_path, file_name, public_url)
            
            return {
                "success": True,
                "url": public_url,
                "path": file_path,
                "message": "✅ تم رفع الملف بنجاح"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"❌ فشل رفع الملف: {e}"
            }
    
    def upload_dataframe(self, df, report_name, folder="reports"):
        """رفع DataFrame كملف CSV"""
        try:
            # تحويل DataFrame إلى CSV
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
            file_bytes = csv_buffer.getvalue().encode('utf-8-sig')
            
            file_name = f"{report_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            return self.upload_file(file_bytes, file_name, folder, "text/csv")
        except Exception as e:
            return {"success": False, "message": f"❌ {str(e)}"}
    
    def upload_attendance_report(self, attendance_data, center_name, report_date):
        """رفع تقرير التكميل اليومي"""
        try:
            # تحويل بيانات التكميل إلى DataFrame
            df = pd.DataFrame(attendance_data)
            
            # اسم التقرير
            report_name = f"تكميل_{center_name}_{report_date.strftime('%Y%m%d')}"
            
            # رفع الملف
            result = self.upload_dataframe(df, report_name, folder="attendance")
            
            # حفظ في جدول attendance_history
            self._save_attendance_history(attendance_data, center_name, report_date, result.get("url"))
            
            return result
        except Exception as e:
            return {"success": False, "message": f"❌ {str(e)}"}
    
    def _save_file_metadata(self, file_path, file_name, public_url):
        """حفظ معلومات الملف في قاعدة البيانات"""
        try:
            data = {
                "file_path": file_path,
                "file_name": file_name,
                "public_url": public_url,
                "uploaded_by": st.session_state.get("username", "unknown"),
                "uploaded_at": datetime.now().isoformat()
            }
            self.supabase.table("uploaded_files").insert(data).execute()
        except Exception as e:
            print(f"خطأ في حفظ معلومات الملف: {e}")
    
    def _save_attendance_history(self, attendance_data, center_name, report_date, file_url):
        """حفظ تاريخ التكميل في قاعدة البيانات"""
        try:
            # حساب الإحصائيات
            total = len(attendance_data)
            present = sum(1 for r in attendance_data if r.get("status") == "حاضر")
            absent = sum(1 for r in attendance_data if r.get("status") == "غائب")
            late = sum(1 for r in attendance_data if r.get("status") == "متأخر")
            
            data = {
                "center_name": center_name,
                "report_date": report_date.isoformat(),
                "total_employees": total,
                "present": present,
                "absent": absent,
                "late": late,
                "file_url": file_url,
                "created_by": st.session_state.get("username", "unknown"),
                "created_at": datetime.now().isoformat()
            }
            self.supabase.table("attendance_history").insert(data).execute()
        except Exception as e:
            print(f"خطأ في حفظ تاريخ التكميل: {e}")
    
    def list_files(self, folder="reports", limit=50):
        """عرض الملفات المرفوعة"""
        try:
            # جلب من قاعدة البيانات
            result = self.supabase.table("uploaded_files") \
                .select("*") \
                .order("uploaded_at", desc=True) \
                .limit(limit) \
                .execute()
            
            return result.data
        except Exception as e:
            st.error(f"❌ فشل جلب الملفات: {e}")
            return []
    
    def get_attendance_history(self, center_name=None, days_back=30):
        """جلب تاريخ التكميل"""
        try:
            query = self.supabase.table("attendance_history") \
                .select("*") \
                .order("report_date", desc=True)
            
            if center_name:
                query = query.eq("center_name", center_name)
            
            result = query.limit(100).execute()
            return result.data
        except Exception as e:
            st.error(f"❌ فشل جلب تاريخ التكميل: {e}")
            return []
    
    def delete_file(self, file_path):
        """حذف ملف من التخزين"""
        try:
            self.supabase.storage.from_(self.bucket_name).remove([file_path])
            
            # حذف من قاعدة البيانات
            self.supabase.table("uploaded_files").delete().eq("file_path", file_path).execute()
            
            return True
        except Exception as e:
            st.error(f"❌ فشل حذف الملف: {e}")
            return False