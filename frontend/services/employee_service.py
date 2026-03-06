# frontend/services/employee_service.py
import requests
import streamlit as st
from config import config

class EmployeeService:
    def __init__(self, auth_service):
        self.base_url = f"{config.API_URL}/employees"
        self.auth = auth_service
    
    def get_stats(self):
        """إحصائيات الموظفين"""
        try:
            response = requests.get(
                f"{self.base_url}/stats/overview",
                headers=self.auth.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            st.error(f"خطأ: {str(e)}")
            return None
    
    def get_employees(self, center_id=None, search=None, employee_type=None, skip=0, limit=100):
        """قائمة الموظفين"""
        try:
            params = {"skip": skip, "limit": limit}
            if center_id:
                params["center_id"] = center_id
            if search:
                params["search"] = search
            if employee_type:
                params["employee_type"] = employee_type
            
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
            st.error(f"خطأ: {str(e)}")
            return {"total": 0, "items": []}
    
    def get_employee(self, employee_id):
        """بيانات موظف محدد"""
        try:
            response = requests.get(
                f"{self.base_url}/{employee_id}",
                headers=self.auth.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            st.error(f"خطأ: {str(e)}")
            return None
    
    def create_employee(self, data):
        """إضافة موظف جديد"""
        try:
            response = requests.post(
                self.base_url,
                headers=self.auth.get_headers(),
                json=data,
                timeout=10
            )
            if response.status_code == 201:
                return response.json()
            st.error(f"خطأ: {response.status_code}")
            return None
        except Exception as e:
            st.error(f"خطأ: {str(e)}")
            return None
    
    def update_employee(self, employee_id, data):
        """تحديث بيانات موظف"""
        try:
            response = requests.put(
                f"{self.base_url}/{employee_id}",
                headers=self.auth.get_headers(),
                json=data,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            st.error(f"خطأ: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            st.error(f"خطأ: {str(e)}")
            return None
    
    def delete_employee(self, employee_id):
        """حذف موظف"""
        try:
            response = requests.delete(
                f"{self.base_url}/{employee_id}",
                headers=self.auth.get_headers(),
                timeout=10
            )
            return response.status_code == 204
        except Exception as e:
            st.error(f"خطأ: {str(e)}")
            return False