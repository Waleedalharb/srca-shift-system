# frontend/services/auth_service.py
import requests
import streamlit as st
from config import config

class AuthService:
    def __init__(self):
        self.base_url = config.API_URL
        self.token = None
    
    def login(self, username: str, password: str) -> bool:
        """تسجيل الدخول"""
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
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                st.session_state.token = self.token
                st.session_state.username = username
                st.session_state.user_data = data.get("user", {})
                return True
            else:
                st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")
                return False
                
        except requests.exceptions.ConnectionError:
            st.error("🔌 لا يمكن الاتصال بالخادم. تأكد من تشغيل السيرفر")
            return False
        except Exception as e:
            st.error(f"❌ خطأ: {str(e)}")
            return False
    
    def logout(self):
        """تسجيل الخروج"""
        self.token = None
        st.session_state.token = None
        st.session_state.username = None
        st.session_state.user_data = None
    
    def get_headers(self):
        """الحصول على رؤوس الطلبات"""
        if not self.token and "token" in st.session_state:
            self.token = st.session_state.token
            
        if not self.token:
            st.error("الرجاء تسجيل الدخول أولاً")
            st.stop()
            
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }
    
    def is_authenticated(self):
        """التحقق من حالة المصادقة"""
        return self.token is not None or "token" in st.session_state