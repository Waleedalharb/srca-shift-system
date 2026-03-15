# backend/app/services/ai_scheduler.py
import requests
import json
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIScheduler:
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "tinyllama:latest"
    
    def generate_schedule(self, prompt: str) -> str:
        """إرسال طلب للنموذج المحلي"""
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get("response", "⚠️ لا يوجد رد")
            else:
                return f"⚠️ خطأ في الاتصال: {response.status_code}"
                
        except Exception as e:
            logger.error(f"خطأ: {e}")
            return f"⚠️ تعذر الاتصال بـ Ollama: {str(e)}"