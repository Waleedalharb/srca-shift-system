# frontend/utils/supabase_storage.py
import streamlit as st
import os
from supabase import create_client, Client
from datetime import datetime
import uuid
import pandas as pd
import io

class SupabaseStorage:
    def __init__(self):
        """تهيئة الاتصال مع Supabase Storage"""
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.supabase_key = os.environ.get("SUPABASE_KEY")
        self.bucket_name = "srca-reports"

        if not self.supabase_url or not self.supabase_key:
            st.error("❌ لم يتم تعيين متغيرات SUPABASE_URL و SUPABASE_KEY في Environment Variables")
            st.stop()

        try:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            print("✅ تم الاتصال بـ Supabase بنجاح")
        except Exception as e:
            st.error(f"❌ فشل الاتصال بـ Supabase: {e}")
            st.stop()

    def upload_file(self, file_bytes, file_name, folder="reports", content_type="text/csv"):
        """رفع ملف إلى Supabase Storage"""
        try:
            date_str = datetime.now().strftime("%Y/%m/%d")
            unique_id = str(uuid.uuid4())[:8]
            file_path = f"{folder}/{date_str}/{unique_id}_{file_name}"

            # محاولة رفع الملف
            self.supabase.storage.from_(self.bucket_name).upload(
                path=file_path,
                file=file_bytes,
                file_options={"content-type": content_type}
            )

            # الحصول على الرابط العام
            public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(file_path)
            print(f"✅ تم رفع الملف بنجاح: {public_url}")

            return {
                "success": True,
                "url": public_url,
                "path": file_path,
                "message": "✅ تم رفع الملف بنجاح"
            }
        except Exception as e:
            error_msg = f"❌ فشل رفع الملف: {str(e)}"
            print(error_msg)
            return {
                "success": False,
                "error": str(e),
                "message": error_msg
            }

    def upload_dataframe(self, df, report_name, folder="reports"):
        """رفع DataFrame كملف CSV"""
        try:
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
            file_bytes = csv_buffer.getvalue().encode('utf-8-sig')

            file_name = f"{report_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            return self.upload_file(file_bytes, file_name, folder, "text/csv")
        except Exception as e:
            error_msg = f"❌ فشل تحويل البيانات: {str(e)}"
            print(error_msg)
            return {"success": False, "message": error_msg}

    def upload_attendance_report(self, attendance_data, center_name, report_date):
        """رفع تقرير التكميل اليومي"""
        try:
            # تحويل بيانات التكميل إلى DataFrame
            df = pd.DataFrame(attendance_data)
            
            # ✅ إزالة المسافات من اسم المركز (سبب المشكلة)
            clean_center_name = center_name.replace(" ", "_")
            report_name = f"تكميل_{clean_center_name}_{report_date.strftime('%Y%m%d')}"
            
            print(f"📤 محاولة رفع تقرير: {report_name}")
            
            # 1. محاولة رفع الملف
            upload_result = self.upload_dataframe(df, report_name, folder="attendance")

            # 2. إذا نجح الرفع، نحاول حفظ البيانات في جدول history
            if upload_result["success"]:
                print("✅ تم رفع الملف، جاري حفظ التاريخ...")
                history_saved = self._save_attendance_history(
                    attendance_data, 
                    center_name, 
                    report_date, 
                    upload_result["url"]
                )
                
                upload_result["history_saved"] = history_saved
                if not history_saved:
                    upload_result["message"] += " (لكن فشل حفظ التاريخ)"
                    print("⚠️ فشل حفظ التاريخ في الجدول")
            else:
                print(f"❌ فشل رفع الملف: {upload_result.get('message')}")
            
            return upload_result

        except Exception as e:
            error_msg = f"❌ خطأ في رفع التقرير: {str(e)}"
            print(error_msg)
            return {"success": False, "message": error_msg}

    def _save_attendance_history(self, attendance_data, center_name, report_date, file_url):
        """حفظ تاريخ التكميل في قاعدة البيانات مع طباعة الأخطاء"""
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
            
            # محاولة الإدراج
            print(f"📤 إرسال البيانات إلى Supabase: {data}")
            result = self.supabase.table("attendance_history").insert(data).execute()
            
            print(f"✅ تم إدراج البيانات في Supabase بنجاح. النتيجة: {result}")
            return True

        except Exception as e:
            print(f"❌ فشل إدراج البيانات في Supabase:")
            print(f"   - نوع الخطأ: {type(e).__name__}")
            print(f"   - تفاصيل الخطأ: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    response_text = e.response.text if hasattr(e.response, 'text') else 'لا يوجد'
                    print(f"   - استجابة Supabase: {response_text}")
                except:
                    print("   - لا يمكن قراءة استجابة Supabase")
            return False

    def get_attendance_history(self, center_name=None):
        """جلب تاريخ التكميل"""
        try:
            print(f"📤 جلب تاريخ التكميل للمركز: {center_name if center_name else 'الكل'}")
            query = self.supabase.table("attendance_history") \
                .select("*") \
                .order("report_date", desc=True)

            if center_name and center_name != "الكل":
                query = query.eq("center_name", center_name)

            result = query.limit(100).execute()
            print(f"✅ تم جلب {len(result.data)} سجل")
            return result.data
        except Exception as e:
            print(f"❌ فشل جلب تاريخ التكميل: {e}")
            st.error(f"❌ فشل جلب تاريخ التكميل: {e}")
            return []

    def get_attendance_by_date(self, center_name, report_date):
        """جلب تكميل ليوم محدد"""
        try:
            result = self.supabase.table("attendance_history") \
                .select("*") \
                .eq("center_name", center_name) \
                .eq("report_date", report_date.isoformat()) \
                .execute()

            return result.data[0] if result.data else None
        except Exception as e:
            print(f"خطأ في جلب التكميل: {e}")
            return None

    def delete_file(self, file_path):
        """حذف ملف من التخزين"""
        try:
            self.supabase.storage.from_(self.bucket_name).remove([file_path])
            return True
        except Exception as e:
            st.error(f"❌ فشل حذف الملف: {e}")
            return False