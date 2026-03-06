# frontend/services/center_service.py
import requests
import streamlit as st
from config import config

class CenterService:
    def __init__(self, auth_service):
        self.base_url = f"{config.API_URL}/centers"
        self.auth = auth_service
    
    def get_centers(self, search=None):
        """قائمة المراكز"""
        try:
            params = {}
            if search:
                params["search"] = search
                
            response = requests.get(
                self.base_url,
                headers=self.auth.get_headers(),
                params=params,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("items", [])
            return []
        except Exception as e:
            st.error(f"خطأ في جلب المراكز: {str(e)}")
            return []
    
    def get_center(self, center_id):
        """بيانات مركز محدد"""
        try:
            response = requests.get(
                f"{self.base_url}/{center_id}",
                headers=self.auth.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            st.error(f"خطأ في جلب بيانات المركز: {str(e)}")
            return None
    
    def get_center_coverage(self, center_id):
        """نسبة تغطية المركز"""
        try:
            response = requests.get(
                f"{self.base_url}/{center_id}/coverage",
                headers=self.auth.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            return None
    
    def create_center(self, data):
        """إضافة مركز جديد"""
        try:
            response = requests.post(
                self.base_url,
                headers=self.auth.get_headers(),
                json=data,
                timeout=10
            )
            if response.status_code == 201:
                return response.json()
            else:
                st.error(f"خطأ في إضافة المركز: {response.text}")
                return None
        except Exception as e:
            st.error(f"خطأ: {str(e)}")
            return None
    
    def update_center(self, center_id, data):
        """تحديث بيانات مركز"""
        try:
            response = requests.put(
                f"{self.base_url}/{center_id}",
                headers=self.auth.get_headers(),
                json=data,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"خطأ في تحديث المركز: {response.text}")
                return None
        except Exception as e:
            st.error(f"خطأ: {str(e)}")
            return None
            