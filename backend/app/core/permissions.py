from enum import Enum
from functools import wraps
from fastapi import HTTPException, status
from typing import Callable

class Permission(str, Enum):
    MANAGE_EMPLOYEES = "manage_employees"
    DELETE_EMPLOYEE = "delete_employee"
    VIEW_ALL = "view_all"
    MANAGE_SHIFTS = "manage_shifts"

def require_permission(permission: Permission):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="غير مصرح"
                )
            
            # تحقق بسيط - كبير المسعفين له كل الصلاحيات
            if current_user.role.value == "chief_paramedic":
                return await func(*args, **kwargs)
            
            # باقي الصلاحيات حسب الحاجة
            if permission == Permission.DELETE_EMPLOYEE:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="فقط كبير المسعفين يمكنه الحذف"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator