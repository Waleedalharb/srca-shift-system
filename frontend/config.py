# frontend/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ── API ─────────────────────────────────────────────
    API_URL = os.getenv("API_URL", "http://localhost:8000/api")

    # ── App ─────────────────────────────────────────────
    APP_NAME   = "نظام إدارة المراكز الإسعافية"
    APP_ICON   = "🚑"
    APP_LAYOUT = "wide"

    # ── الهوية البصرية للهلال الأحمر السعودي ────────────
    # الألوان الأساسية
    PRIMARY_COLOR   = "#CE2E26"   # أحمر رئيسي
    PRIMARY_DARK    = "#B71C1C"   # أحمر غامق
    SECONDARY_COLOR = "#42924B"   # أخضر
    NAVY_COLOR      = "#3B4A82"   # كحلي
    NAVY_DARK       = "#1A2B5C"   # كحلي غامق
    GOLD_COLOR      = "#F1B944"   # ذهبي
    
    # ألوان ثانوية
    ORANGE_COLOR    = "#FF7C10"
    TEAL_COLOR      = "#3A8478"
    BLUE_COLOR      = "#45CFEF"
    PURPLE_COLOR    = "#513A87"
    
    # ألوان محايدة
    DARK_BG         = "#1A1A2E"
    GRAY_600        = "#475569"
    GRAY_300        = "#CBD5E1"
    GRAY_100        = "#F1F5F9"

    # ── Pagination ──────────────────────────────────────
    ITEMS_PER_PAGE = 20

    # ── Formats ─────────────────────────────────────────
    DATE_FORMAT     = "%Y/%m/%d"
    DATETIME_FORMAT = "%Y/%m/%d %H:%M"

    # ── RTL ─────────────────────────────────────────────
    RTL_LANGUAGES = ["ar"]

config = Config()