# backend/app/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: UUID
    is_active: bool
    employee_id: Optional[UUID] = None
    
    class Config:
        from_attributes = True  # تغيير من orm_mode إلى from_attributes