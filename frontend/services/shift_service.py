# frontend/services/shift_service.py
import requests
import streamlit as st
from config import config
from datetime import datetime

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
    
    def get_shifts_by_date(self, center_id, date):
        """جلب المناوبات ليوم محدد (للتكميل الذكي)"""
        try:
            date_str = date.strftime("%Y-%m-%d")
            params = {
                "center_id": center_id,
                "date": date_str
            }
            response = requests.get(
                f"{self.base_url}/by_date",
                headers=self.auth.get_headers(),
                params=params,
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("items", [])
            return []
        except Exception as e:
            print(f"خطأ في جلب المناوبات لليوم: {e}")
            return []
    
    def get_shifts_by_month(self, center_id, year, month):
        """جلب المناوبات لشهر كامل"""
        try:
            start_date = f"{year}-{month:02d}-01"
            if month == 12:
                end_date = f"{year+1}-01-01"
            else:
                end_date = f"{year}-{month+1:02d}-01"
            
            params = {
                "center_id": center_id,
                "start_date": start_date,
                "end_date": end_date,
                "limit": 500
            }
            response = requests.get(
                f"{self.base_url}/by_month",
                headers=self.auth.get_headers(),
                params=params,
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("items", [])
            return []
        except Exception as e:
            print(f"خطأ في get_shifts_by_month: {e}")
            return []
    
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