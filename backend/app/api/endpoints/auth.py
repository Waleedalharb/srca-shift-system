# backend/app/api/endpoints/auth.py
from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import User as UserSchema

router = APIRouter()

@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    تسجيل دخول المستخدمين
    """
    # البحث عن المستخدم
    user = db.query(User).filter(User.username == form_data.username).first()
    
    # التحقق من كلمة المرور
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="اسم المستخدم أو كلمة المرور غير صحيحة",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # التحقق من أن المستخدم نشط
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="المستخدم غير نشط"
        )
    
    # إنشاء التوكن
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "username": user.username,
            "role": user.role.value,
            "employee_name": user.employee.full_name if user.employee else None
        }
    }

@router.get("/me", response_model=UserSchema)
def read_current_user(
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    جلب بيانات المستخدم الحالي
    """
    return current_user
    