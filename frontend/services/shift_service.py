# frontend/services/shift_service.py
import requests
import streamlit as st
from config import config
from datetime import datetime, timedelta

class ShiftService:
    def __init__(self, auth_service):
        self.base_url = f"{config.API_URL}/shifts"
        self.auth = auth_service
    
    def get_shifts(self, center_id=None, shift_date=None, skip=0, limit=100):
        """جلب قائمة المناوبات"""
        try:
            params = {"skip": skip, "limit": limit}
            if center_id:
                params["center_id"] = center_id
            if shift_date:
                params["shift_date"] = shift_date
            
            response = requests.get(
                self.base_url,
                headers=self.auth.get_headers(),
                params=params,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return {"total": 0, "items": []}
        except Exception as e:
            print(f"خطأ في جلب المناوبات: {e}")
            return {"total": 0, "items": []}
    
    def get_shifts_by_date(self, center_id, target_date):
        """جلب المناوبات ليوم محدد"""
        try:
            date_str = target_date.strftime("%Y-%m-%d")
            next_day = (target_date + timedelta(days=1)).strftime("%Y-%m-%d")
            
            response = requests.get(
                f"{self.base_url}/by_month",
                headers=self.auth.get_headers(),
                params={
                    "center_id": center_id,
                    "start_date": date_str,
                    "end_date": next_day,
                    "limit": 100
                },
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("items", [])
            return []
        except Exception as e:
            print(f"خطأ في جلب المناوبات لليوم: {e}")
            return []
    
    def get_shifts_by_month(self, center_id, year, month):
        """جلب المناوبات لشهر كامل (طريقة قديمة)"""
        try:
            start_date = f"{year}-{month:02d}-01"
            if month == 12:
                end_date = f"{year+1}-01-01"
            else:
                end_date = f"{year}-{month+1:02d}-01"
            
            response = requests.get(
                f"{self.base_url}/by_month",
                headers=self.auth.get_headers(),
                params={
                    "center_id": center_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "limit": 500
                },
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("items", [])
            return []
        except Exception as e:
            print(f"خطأ في get_shifts_by_month: {e}")
            return []
    
    def get_employee_shifts_by_month(self, employee_id, year, month):
        """جلب مناوبات موظف محدد لشهر كامل"""
        try:
            start_date = f"{year}-{month:02d}-01"
            if month == 12:
                end_date = f"{year+1}-01-01"
            else:
                end_date = f"{year}-{month+1:02d}-01"
            
            response = requests.get(
                f"{self.base_url}/by_employee",
                headers=self.auth.get_headers(),
                params={
                    "employee_id": employee_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "limit": 40
                },
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("items", [])
            return []
        except Exception as e:
            print(f"خطأ في get_employee_shifts_by_month: {e}")
            return []
    
    # ===== دالة جديدة: تجلب كل التعيينات للشهر =====
    def get_assignments_by_month(self, center_id, year, month):
        """جلب جميع تعيينات المناوبات لشهر كامل"""
        try:
            start_date = f"{year}-{month:02d}-01"
            if month == 12:
                end_date = f"{year+1}-01-01"
            else:
                end_date = f"{year}-{month+1:02d}-01"
            
            response = requests.get(
                f"{self.base_url}/assignments/by_month",
                headers=self.auth.get_headers(),
                params={
                    "center_id": center_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "limit": 1000
                },
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("items", [])
            return []
        except Exception as e:
            print(f"خطأ في get_assignments_by_month: {e}")
            return []
    
    # ===== دالة جديدة: تجلب تفاصيل مناوبة معينة =====
    def get_shift(self, shift_id):
        """جلب تفاصيل مناوبة محددة"""
        try:
            response = requests.get(
                f"{self.base_url}/{shift_id}",
                headers=self.auth.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"خطأ في get_shift: {e}")
            return None
    
    def create_shift(self, data):
        """إنشاء مناوبة جديدة"""
        try:
            response = requests.post(
                self.base_url,
                headers=self.auth.get_headers(),
                json=data,
                timeout=10
            )
            if response.status_code == 201:
                return response.json()
            return None
        except Exception as e:
            print(f"خطأ في create_shift: {e}")
            return None
    
    def assign_employee(self, shift_id, employee_id, role="crew"):
        """تعيين موظف لمناوبة"""
        try:
            data = {"employee_id": employee_id, "role": role}
            response = requests.post(
                f"{self.base_url}/{shift_id}/assign",
                headers=self.auth.get_headers(),
                json=data,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"خطأ في assign_employee: {e}")
            return False
    
    def save_shift(self, employee_id, date, shift_type):
        """حفظ مناوبة (إنشاء أو تحديث)"""
        try:
            data = {
                "employee_id": employee_id,
                "date": date,
                "shift_type": shift_type
            }
            
            print(f"\n📤 إرسال تحديث مناوبة:")
            print(f"   - الرابط: {self.base_url}/update")
            print(f"   - البيانات: {data}")
            
            response = requests.put(
                f"{self.base_url}/update",
                headers=self.auth.get_headers(),
                json=data,
                timeout=10
            )
            
            print(f"📥 الرد: {response.status_code} - {response.text}")
            
            if response.status_code == 200:
                return True
            else:
                st.error(f"❌ خطأ: {response.text}")
                return False
        except Exception as e:
            st.error(f"❌ فشل الاتصال: {str(e)}")
            return False
    
    def update_employee_shift(self, employee_id, date, shift_type):
        """تحديث مناوبة موظف ليوم محدد"""
        return self.save_shift(employee_id, date, shift_type)
    
    # ===== 🚀 دالة جديدة: Batch Update (تحديث دفعة واحدة) =====
    def batch_update_shifts(self, shifts_data):
        """
        تحديث مجموعة من المناوبات دفعة واحدة
        - shifts_data: قائمة من العناصر، كل عنصر فيه employee_id, date, shift_type
        - أسرع 20 مرة من التحديث المفرد
        """
        try:
            if not shifts_data:
                print("⚠️ لا توجد بيانات للتحديث")
                return 0
            
            print(f"📦 إرسال {len(shifts_data)} مناوبة دفعة واحدة")
            
            response = requests.post(
                f"{self.base_url}/batch-update",
                headers=self.auth.get_headers(),
                json=shifts_data,
                timeout=60  # وقت أطول للدفعة
            )
            
            if response.status_code == 200:
                result = response.json()
                success = result.get("success", 0)
                failed = result.get("failed", 0)
                print(f"✅ نجاح: {success} مناوبة")
                if failed > 0:
                    print(f"⚠️ فشل: {failed} مناوبة")
                return success
            else:
                print(f"❌ فشل batch update: {response.status_code}")
                print(f"   الرد: {response.text[:200]}")
                
                # fallback: استخدام التحديث المفرد إذا فشلت الدفعة
                print("⚠️ استخدام التحديث المفرد كبديل...")
                success = 0
                for item in shifts_data:
                    if self.update_employee_shift(item["employee_id"], item["date"], item["shift_type"]):
                        success += 1
                return success
                
        except requests.exceptions.Timeout:
            print("❌ Timeout في batch update")
            st.warning("⚠️ استغرقت العملية وقتاً طويلاً، جاري المحاولة بشكل منفرد...")
            
            # fallback: استخدام التحديث المفرد
            success = 0
            for item in shifts_data:
                if self.update_employee_shift(item["employee_id"], item["date"], item["shift_type"]):
                    success += 1
            return success
            
        except Exception as e:
            print(f"❌ خطأ في batch_update_shifts: {str(e)}")
            st.error(f"❌ فشل التحديث الدفعي: {str(e)}")
            return 0