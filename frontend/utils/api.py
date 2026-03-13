# frontend/utils/api.py
import requests
import streamlit as st
import os

# تحديد الرابط حسب البيئة
if os.path.exists('/opt/render/project/src'):
    # نحن في Render - الرابط الصحيح لتطبيقك
    API_URL = "https://srca-shift-system.onrender.com/api"
else:
    # نحن في الجهاز المحلي
    API_URL = "http://localhost:8000/api"

class SRCA_API:
    def __init__(self):
        self.base_url = API_URL
        self.token = None
    
    def login(self, username: str, password: str) -> bool:
        """تسجيل الدخول والحصول على التوكن"""
        try:
            print(f"🔐 محاولة تسجيل الدخول إلى: {self.base_url}/auth/login")
            response = requests.post(
                f"{self.base_url}/auth/login",
                data={
                    "grant_type": "password",
                    "username": username,
                    "password": password,
                    "scope": "",
                    "client_id": "",
                    "client_secret": ""
                },
                timeout=10
            )
            
            if response.status_code == 200:
                self.token = response.json()["access_token"]
                return True
            else:
                st.error(f"❌ خطأ في تسجيل الدخول: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            st.error(f"❌ لا يمكن الاتصال بالخادم: {self.base_url}")
            return False
        except Exception as e:
            st.error(f"❌ خطأ في الاتصال: {str(e)}")
            return False
    
    def _get_headers(self):
        """إضافة التوكن للطلبات"""
        if not self.token:
            st.error("الرجاء تسجيل الدخول أولاً")
            st.stop()
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def get_employees_stats(self):
        """إحصائيات الموظفين"""
        try:
            response = requests.get(
                f"{self.base_url}/employees/stats/overview",
                headers=self._get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"خطأ في get_employees_stats: {e}")
            return None
    
    def get_centers(self):
        """قائمة المراكز"""
        try:
            response = requests.get(
                f"{self.base_url}/centers/",
                headers=self._get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("items", [])
            return []
        except Exception as e:
            print(f"خطأ في get_centers: {e}")
            return []
    
    def get_employees(self, center_id=None):
        """قائمة الموظفين"""
        try:
            url = f"{self.base_url}/employees/"
            if center_id:
                url += f"?center_id={center_id}"
            
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("items", [])
            return []
        except Exception as e:
            print(f"خطأ في get_employees: {e}")
            return []
    
    def get_dashboard(self):
        """بيانات لوحة التحكم"""
        try:
            response = requests.get(
                f"{self.base_url}/reports/dashboard",
                headers=self._get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"خطأ في get_dashboard: {e}")
            return None
    
    def update_shift(self, employee_id, date, shift_type):
        """تحديث مناوبة"""
        try:
            data = {
                "employee_id": employee_id,
                "date": date,
                "shift_type": shift_type
            }
            response = requests.put(
                f"{self.base_url}/shifts/update",
                headers=self._get_headers(),
                json=data,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"خطأ في update_shift: {e}")
            return False
    
    # ===== دوال البلاغات الجديدة =====
    def get_incidents(self, skip=0, limit=100):
        """جلب قائمة البلاغات"""
        try:
            response = requests.get(
                f"{self.base_url}/incidents/",
                headers=self._get_headers(),
                params={"skip": skip, "limit": limit},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return {"total": 0, "items": []}
        except Exception as e:
            print(f"خطأ في get_incidents: {e}")
            return {"total": 0, "items": []}
    
    def create_incident(self, data):
        """تسجيل بلاغ جديد"""
        try:
            response = requests.post(
                f"{self.base_url}/incidents/",
                headers=self._get_headers(),
                json=data,
                timeout=10
            )
            return response.status_code == 201
        except Exception as e:
            print(f"خطأ في create_incident: {e}")
            return False
    
    def get_incidents_by_date_range(self, start_date, end_date):
        """جلب البلاغات في نطاق تاريخي"""
        try:
            response = requests.get(
                f"{self.base_url}/incidents/by_date_range",
                headers=self._get_headers(),
                params={"start_date": start_date, "end_date": end_date},
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("items", [])
            return []
        except Exception as e:
            print(f"خطأ في get_incidents_by_date_range: {e}")
            return []
    
    def get_incidents_stats_by_team(self, start_date, end_date):
        """إحصائيات البلاغات حسب الفرق"""
        try:
            response = requests.get(
                f"{self.base_url}/incidents/stats/by_team",
                headers=self._get_headers(),
                params={"start_date": start_date, "end_date": end_date},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"خطأ في get_incidents_stats_by_team: {e}")
            return []
    
    def get_incidents_stats_by_center(self, start_date, end_date):
        """إحصائيات البلاغات حسب المراكز"""
        try:
            response = requests.get(
                f"{self.base_url}/incidents/stats/by_center",
                headers=self._get_headers(),
                params={"start_date": start_date, "end_date": end_date},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"خطأ في get_incidents_stats_by_center: {e}")
            return []
    
    def get_avg_response_time(self, start_date, end_date):
        """متوسط وقت الاستجابة"""
        try:
            response = requests.get(
                f"{self.base_url}/incidents/stats/avg_response",
                headers=self._get_headers(),
                params={"start_date": start_date, "end_date": end_date},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return {"avg_seconds": 0, "avg_minutes": 0}
        except Exception as e:
            print(f"خطأ في get_avg_response_time: {e}")
            return {"avg_seconds": 0, "avg_minutes": 0}