# frontend/utils/api.py
import requests
import streamlit as st
import os

# تحديد الرابط حسب البيئة
if os.path.exists('/opt/render/project/src'):
    # نحن في Render - الرابط الصحيح لتطبيقك
    API_BASE_URL = "https://srca-shift-system.onrender.com/api"  # 👈 رابط Render
else:
    # نحن في الجهاز المحلي
    API_BASE_URL = "http://localhost:8000/api"  # 👈 رابط محلي

class SRCA_API:
    def __init__(self):
        self.base_url = API_BASE_URL  # 👈 استخدم API_BASE_URL مو API_URL
        self.token = None