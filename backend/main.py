# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router
from app.core.database import engine
from app.models import Base

# إنشاء جداول قاعدة البيانات
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SRCA - نظام إدارة المراكز الإسعافية",
    description="نظام متكامل لإدارة المناوبات والموظفين والبلاغات",
    version="1.0.0"
)

# إعداد CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # في الإنتاج حدد النطاقات المسموحة
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# تضمين الـ routes
app.include_router(api_router)

@app.get("/")
def root():
    return {
        "message": "مرحباً في نظام SRCA",
        "version": "1.0.0",
        "status": "active"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}