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
        """جلب قائمة المناوبات مع إمكانية التصفية"""
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
            else:
                return {"total": 0, "items": []}
        except Exception as e:
            print(f"خطأ في جلب المناوبات: {str(e)}")
            return {"total": 0, "items": []}
    
    def get_shifts_by_month(self, center_id, year, month):
        """جلب المناوبات الحقيقية لشهر محدد"""
        try:
            # تنسيق التاريخ
            start_date = f"{year}-{month:02d}-01"
            # حساب آخر يوم في الشهر
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
                data = response.json()
                return data.get("items", [])
            else:
                return []
        except Exception as e:
            print(f"خطأ في get_shifts_by_month: {str(e)}")
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
            else:
                return None
        except Exception as e:
            print(f"خطأ في إنشاء المناوبة: {str(e)}")
            return None
    
    def assign_employee(self, shift_id, employee_id, role="crew"):
        """تعيين موظف لمناوبة"""
        try:
            data = {
                "employee_id": employee_id,
                "role": role
            }
            response = requests.post(
                f"{self.base_url}/{shift_id}/assign",
                headers=self.auth.get_headers(),
                json=data,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"خطأ في تعيين الموظف: {str(e)}")
            return False
    
    def batch_update_shifts(self, updates):
        """تحديث مجموعة من المناوبات دفعة واحدة (تجريبي)"""
        try:
            # هذا مؤقت - يرجع نجاح دائم
            print(f"تم استلام {len(updates)} تحديث")
            return True
        except Exception as e:
            print(f"خطأ في التحديث الدفعي: {str(e)}")
            return False