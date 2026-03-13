# backend/app/core/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# إعدادات JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# إعدادات قاعدة البيانات
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////opt/render/project/src/data/srca.db")

# إعدادات المشرف
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "chief")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# إعدادات التطبيق
APP_NAME = "SRCA - نظام إدارة المراكز الإسعافية"
APP_VERSION = "1.0.0"