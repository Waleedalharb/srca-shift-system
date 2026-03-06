# frontend/utils/api.py
import requests
import streamlit as st

API_URL = "http://localhost:8000/api"

class SRCA_API:
    def __init__(self):
        self.base_url = API_URL
        self.token = None
    
    def login(self, username: str, password: str) -> bool:
        """تسجيل الدخول والحصول على التوكن"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                data={
                    "grant_type": "password",
                    "username": username,
                    "password": password,
                    "scope": "",
                    "client_id": "",
                    "client_secret": ""
                }
            )
            
            if response.status_code == 200:
                self.token = response.json()["access_token"]
                return True
            return False
        except Exception as e:
            st.error(f"خطأ في الاتصال: {e}")
            return False
    
    def _get_headers(self):
        """إضافة التوكن للطلبات"""
        if not self.token:
            st.error("الرجاء تسجيل الدخول أولاً")
            st.stop()
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }
    
    def get_employees_stats(self):
        """إحصائيات الموظفين"""
        try:
            response = requests.get(
                f"{self.base_url}/employees/stats/overview",
                headers=self._get_headers()
            )
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def get_centers(self):
        """قائمة المراكز"""
        try:
            response = requests.get(
                f"{self.base_url}/centers/",
                headers=self._get_headers()
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("items", [])
            return []
        except:
            return []
    
    def get_employees(self, center_id=None):
        """قائمة الموظفين"""
        try:
            url = f"{self.base_url}/employees/"
            if center_id:
                url += f"?center_id={center_id}"
            
            response = requests.get(url, headers=self._get_headers())
            if response.status_code == 200:
                data = response.json()
                return data.get("items", [])
            return []
        except:
            return []
    
    def get_dashboard(self):
        """بيانات لوحة التحكم"""
        try:
            response = requests.get(
                f"{self.base_url}/reports/dashboard",
                headers=self._get_headers()
            )
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None