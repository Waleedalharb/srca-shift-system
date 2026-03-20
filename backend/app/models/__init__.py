# backend/app/models/__init__.py
from ..core.database import Base
from .user import User, UserRole
from .employee import Employee
from .center import EmergencyCenter
from .role import Role
from .shift import Shift, ShiftAssignment
from .incident import Incident
from .leave import Leave
from .ambulance import Ambulance
from .notification import Notification, NotificationType  # 👈 أضف هذا السطر

__all__ = [
    "Base",
    "User",
    "UserRole",
    "Employee", 
    "EmergencyCenter",
    "Role",
    "Shift",
    "ShiftAssignment",
    "Incident",
    "Leave",
    "Ambulance",
    "Notification",      # 👈 أضف
    "NotificationType"   # 👈 أضف
]