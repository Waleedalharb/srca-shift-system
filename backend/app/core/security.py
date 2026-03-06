# backend/app/core/security.py
from datetime import datetime, timedelta
from typing import Optional, Union, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv
from enum import Enum

load_dotenv()

# ==================== الأمان الأساسي (للتوثيق) ====================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-please-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ==================== نظام الصلاحيات الجديد ====================

class Permission(str, Enum):
    # ===== الموظفين =====
    VIEW_EMPLOYEES = "view_employees"
    MANAGE_EMPLOYEES = "manage_employees"
    VIEW_ALL_EMPLOYEES = "view_all_employees"
    
    # ===== المراكز =====
    VIEW_CENTERS = "view_centers"
    MANAGE_CENTERS = "manage_centers"
    VIEW_ALL_CENTERS = "view_all_centers"
    
    # ===== المناوبات =====
    VIEW_SHIFTS = "view_shifts"
    MANAGE_SHIFTS = "manage_shifts"
    APPROVE_SHIFTS = "approve_shifts"
    
    # ===== الإجازات =====
    VIEW_LEAVES = "view_leaves"
    REQUEST_LEAVE = "request_leave"
    APPROVE_LEAVE = "approve_leave"
    VIEW_ALL_LEAVES = "view_all_leaves"
    
    # ===== التقارير =====
    VIEW_REPORTS = "view_reports"
    VIEW_STATION_REPORTS = "view_station_reports"
    VIEW_SECTOR_REPORTS = "view_sector_reports"
    
    # ===== المستخدمين =====
    MANAGE_USERS = "manage_users"
    VIEW_USERS = "view_users"

# صلاحيات كل دور
ROLE_PERMISSIONS = {
    # 👤 كبير المسعفين - كل الصلاحيات
    "chief_paramedic": [
        Permission.VIEW_ALL_EMPLOYEES,
        Permission.MANAGE_EMPLOYEES,
        Permission.VIEW_ALL_CENTERS,
        Permission.MANAGE_CENTERS,
        Permission.VIEW_SHIFTS,
        Permission.MANAGE_SHIFTS,
        Permission.APPROVE_SHIFTS,
        Permission.VIEW_ALL_LEAVES,
        Permission.APPROVE_LEAVE,
        Permission.VIEW_SECTOR_REPORTS,
        Permission.MANAGE_USERS,
    ],
    
    # 👥 مشرف مركز - يدير فريقه ومركزه
    "field_leader": [
        Permission.VIEW_EMPLOYEES,
        Permission.MANAGE_EMPLOYEES,
        Permission.VIEW_CENTERS,
        Permission.VIEW_SHIFTS,
        Permission.MANAGE_SHIFTS,
        Permission.VIEW_LEAVES,
        Permission.APPROVE_LEAVE,
        Permission.VIEW_STATION_REPORTS,
    ],
    
    # 🖥️ مشرف عمليات
    "operations_supervisor": [
        Permission.VIEW_EMPLOYEES,
        Permission.VIEW_CENTERS,
        Permission.VIEW_SHIFTS,
        Permission.MANAGE_SHIFTS,
        Permission.VIEW_LEAVES,
        Permission.VIEW_STATION_REPORTS,
    ],
    
    # 🖥️ تحكم عملياتي
    "operations_control": [
        Permission.VIEW_EMPLOYEES,
        Permission.VIEW_CENTERS,
        Permission.VIEW_SHIFTS,
        Permission.VIEW_REPORTS,
    ],
    
    # 📞 تنسيق استجابة
    "response_coordinator": [
        Permission.VIEW_EMPLOYEES,
        Permission.VIEW_CENTERS,
        Permission.VIEW_SHIFTS,
    ],
    
    # 👨‍⚕️ أخصائي/مسعف
    "paramedic": [
        Permission.VIEW_EMPLOYEES,
        Permission.VIEW_SHIFTS,
        Permission.REQUEST_LEAVE,
    ],
    "emt": [
        Permission.VIEW_EMPLOYEES,
        Permission.VIEW_SHIFTS,
        Permission.REQUEST_LEAVE,
    ],
    
    # 📋 إداري
    "admin": [
        Permission.VIEW_EMPLOYEES,
        Permission.MANAGE_EMPLOYEES,
        Permission.VIEW_CENTERS,
        Permission.VIEW_REPORTS,
    ],
}

def check_permission(user_role: str, required_permission: Permission) -> bool:
    """التحقق من صلاحية المستخدم"""
    if user_role not in ROLE_PERMISSIONS:
        return False
    return required_permission in ROLE_PERMISSIONS[user_role]

def require_permission(required_permission: Permission):
    """Decorator للتحقق من الصلاحية في APIs"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            from app.api import deps
            from app.models.user import User
            
            # هذا يحتاج تعديل حسب كيفية جلب المستخدم
            # حالياً نستخدم dependency injection
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator