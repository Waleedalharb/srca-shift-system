# frontend/services/incident_service.py
import requests
import streamlit as st
from config import config
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

class IncidentService:
    def __init__(self, auth_service):
        self.base_url = f"{config.API_URL}/incidents"
        self.auth = auth_service
    
    def get_incidents(self, skip=0, limit=100) -> Dict[str, Any]:
        """جلب قائمة البلاغات"""
        try:
            params = {"skip": skip, "limit": limit}
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
            print(f"خطأ في جلب البلاغات: {e}")
            return {"total": 0, "items": []}
    
    def get_incidents_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """جلب البلاغات في نطاق تاريخي"""
        try:
            response = requests.get(
                f"{self.base_url}/by_date_range",
                headers=self.auth.get_headers(),
                params={
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
            print(f"خطأ في جلب البلاغات حسب التاريخ: {e}")
            return []
    
    def get_incidents_by_shift(self, shift_id: str) -> List[Dict]:
        """جلب البلاغات لمناوبة محددة"""
        try:
            response = requests.get(
                f"{self.base_url}/by_shift/{shift_id}",
                headers=self.auth.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("items", [])
            return []
        except Exception as e:
            print(f"خطأ في جلب بلاغات المناوبة: {e}")
            return []
    
    def create_incident(self, data: Dict) -> Optional[Dict]:
        """تسجيل بلاغ جديد"""
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
                st.error(f"❌ خطأ في تسجيل البلاغ: {response.text}")
                return None
        except Exception as e:
            st.error(f"❌ فشل الاتصال: {str(e)}")
            return None
    
    def update_response_time(self, incident_id: str, arrival_time: str) -> bool:
        """تحديث وقت الاستجابة للبلاغ"""
        try:
            data = {"arrival_time": arrival_time}
            response = requests.put(
                f"{self.base_url}/{incident_id}/response",
                headers=self.auth.get_headers(),
                json=data,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"خطأ في تحديث وقت الاستجابة: {e}")
            return False
    
    def get_incidents_stats_by_team(self, start_date: str, end_date: str) -> List[Dict]:
        """إحصائيات البلاغات حسب الفرق"""
        try:
            response = requests.get(
                f"{self.base_url}/stats/by_team",
                headers=self.auth.get_headers(),
                params={
                    "start_date": start_date,
                    "end_date": end_date
                },
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"خطأ في إحصائيات البلاغات: {e}")
            return []
    
    def get_incidents_stats_by_center(self, start_date: str, end_date: str) -> List[Dict]:
        """إحصائيات البلاغات حسب المراكز"""
        try:
            response = requests.get(
                f"{self.base_url}/stats/by_center",
                headers=self.auth.get_headers(),
                params={
                    "start_date": start_date,
                    "end_date": end_date
                },
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"خطأ في إحصائيات البلاغات: {e}")
            return []
    
    def get_avg_response_time(self, start_date: str, end_date: str) -> Dict:
        """متوسط وقت الاستجابة"""
        try:
            response = requests.get(
                f"{self.base_url}/stats/avg_response",
                headers=self.auth.get_headers(),
                params={
                    "start_date": start_date,
                    "end_date": end_date
                },
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return {"avg_seconds": 0, "avg_minutes": 0}
        except Exception as e:
            print(f"خطأ في متوسط وقت الاستجابة: {e}")
            return {"avg_seconds": 0, "avg_minutes": 0}