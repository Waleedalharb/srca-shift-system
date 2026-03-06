# backend/app/api/deps.py
from typing import Optional, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import os

from app.core.database import SessionLocal
from app.models.user import User
from app.models.employee import Employee
from app.core.security import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_db() -> Generator:
    """جلب جلسة قاعدة البيانات"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """الحصول على المستخدم الحالي من التوكن"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="صلاحية غير صالحة",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """التحقق من أن المستخدم نشط"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="المستخدم غير نشط")
    return current_user

def check_center_access(center_id: Optional[str] = None):
    """التحقق من صلاحية الوصول للمركز"""
    def decorator(current_user: User = Depends(get_current_active_user)):
        # كبير المسعفين يشوف كل المراكز
        if current_user.role == "chief_paramedic":
            return True
        
        # قيادة ميدانية تشوف مركزها فقط
        if current_user.role == "field_leader":
            if not center_id:
                return True
            if str(current_user.employee.center_id) != center_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="لا تملك صلاحية لهذا المركز"
                )
        
        # باقي الصلاحيات
        return True
    
    return decorator