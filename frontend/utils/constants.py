# frontend/utils/constants.py
"""
ملف الثوابت المشتركة للنظام
نظام إدارة المراكز الإسعافية - قطاع الجنوب
"""

from typing import Dict, Any

# ============================================================================
# 1. رموز المناوبات (Shift Types) - النظام الجديد بالكامل
# ============================================================================
SHIFT_TYPES: Dict[str, Dict[str, Any]] = {
    # ===== صباحي (Day) =====
    "D6": {
        "name": "صباحي 6 س",
        "code": "D6",
        "icon": "D6",
        "display": "D6",
        "type": "صباحي",
        "category": "day",
        "hours": 6,
        "start": "08:00",
        "end": "14:00",
        "color": "#FFB74D",
        "text_color": "#7A5800",
        "description": "فترة صباحية 6 ساعات"
    },
    "D8": {
        "name": "صباحي 8 س",
        "code": "D8",
        "icon": "D8",
        "display": "D8",
        "type": "صباحي",
        "category": "day",
        "hours": 8,
        "start": "08:00",
        "end": "16:00",
        "color": "#FFB74D",
        "text_color": "#7A5800",
        "description": "فترة صباحية 8 ساعات"
    },
    "D10": {
        "name": "صباحي 10 س",
        "code": "D10",
        "icon": "D10",
        "display": "D10",
        "type": "صباحي",
        "category": "day",
        "hours": 10,
        "start": "08:00",
        "end": "18:00",
        "color": "#FFB74D",
        "text_color": "#7A5800",
        "description": "فترة صباحية 10 ساعات"
    },
    "D11": {
        "name": "صباحي 11 س",
        "code": "D11",
        "icon": "D11",
        "display": "D11",
        "type": "صباحي",
        "category": "day",
        "hours": 11,
        "start": "08:00",
        "end": "19:00",
        "color": "#FFB74D",
        "text_color": "#7A5800",
        "description": "فترة صباحية 11 ساعة"
    },
    "D12": {
        "name": "صباحي 12 س",
        "code": "D12",
        "icon": "D12",
        "display": "D12",
        "type": "صباحي",
        "category": "day",
        "hours": 12,
        "start": "08:00",
        "end": "20:00",
        "color": "#FFB74D",
        "text_color": "#7A5800",
        "description": "فترة صباحية 12 ساعة"
    },
    
    # ===== ليلي (Night) =====
    "N6": {
        "name": "ليلي 6 س",
        "code": "N6",
        "icon": "N6",
        "display": "N6",
        "type": "ليلي",
        "category": "night",
        "hours": 6,
        "start": "00:00",
        "end": "06:00",
        "color": "#4A6FA5",
        "text_color": "#FFFFFF",
        "description": "فترة ليلية 6 ساعات"
    },
    "N8": {
        "name": "ليلي 8 س",
        "code": "N8",
        "icon": "N8",
        "display": "N8",
        "type": "ليلي",
        "category": "night",
        "hours": 8,
        "start": "22:00",
        "end": "06:00",
        "color": "#4A6FA5",
        "text_color": "#FFFFFF",
        "description": "فترة ليلية 8 ساعات"
    },
    "N10": {
        "name": "ليلي 10 س",
        "code": "N10",
        "icon": "N10",
        "display": "N10",
        "type": "ليلي",
        "category": "night",
        "hours": 10,
        "start": "22:00",
        "end": "08:00",
        "color": "#4A6FA5",
        "text_color": "#FFFFFF",
        "description": "فترة ليلية 10 ساعات"
    },
    "N11": {
        "name": "ليلي 11 س",
        "code": "N11",
        "icon": "N11",
        "display": "N11",
        "type": "ليلي",
        "category": "night",
        "hours": 11,
        "start": "21:00",
        "end": "08:00",
        "color": "#4A6FA5",
        "text_color": "#FFFFFF",
        "description": "فترة ليلية 11 ساعة"
    },
    "N12": {
        "name": "ليلي 12 س",
        "code": "N12",
        "icon": "N12",
        "display": "N12",
        "type": "ليلي",
        "category": "night",
        "hours": 12,
        "start": "20:00",
        "end": "08:00",
        "color": "#4A6FA5",
        "text_color": "#FFFFFF",
        "description": "فترة ليلية 12 ساعة"
    },
    
    # ===== تداخلي (Overlap) =====
    "O6": {
        "name": "تداخلي 6 س",
        "code": "O6",
        "icon": "O6",
        "display": "O6",
        "type": "تداخلي",
        "category": "overlap",
        "hours": 6,
        "start": "14:00",
        "end": "20:00",
        "color": "#45CFEF",
        "text_color": "#1A1A2E",
        "description": "فترة تداخلية 6 ساعات"
    },
    "O8": {
        "name": "تداخلي 8 س",
        "code": "O8",
        "icon": "O8",
        "display": "O8",
        "type": "تداخلي",
        "category": "overlap",
        "hours": 8,
        "start": "12:00",
        "end": "20:00",
        "color": "#45CFEF",
        "text_color": "#1A1A2E",
        "description": "فترة تداخلية 8 ساعات"
    },
    "O10": {
        "name": "تداخلي 10 س",
        "code": "O10",
        "icon": "O10",
        "display": "O10",
        "type": "تداخلي",
        "category": "overlap",
        "hours": 10,
        "start": "10:00",
        "end": "20:00",
        "color": "#45CFEF",
        "text_color": "#1A1A2E",
        "description": "فترة تداخلية 10 ساعات"
    },
    "O12": {
        "name": "تداخلي 12 س",
        "code": "O12",
        "icon": "O12",
        "display": "O12",
        "type": "تداخلي",
        "category": "overlap",
        "hours": 12,
        "start": "08:00",
        "end": "20:00",
        "color": "#45CFEF",
        "text_color": "#1A1A2E",
        "description": "فترة تداخلية 12 ساعة"
    },
    
    # ===== تكميلية (Tkmilia) =====
    "CP8": {
        "name": "تكميلية صباحية 8 س",
        "code": "CP8",
        "icon": "CP8",
        "display": "CP8",
        "type": "تكميلية",
        "category": "tkmilia",
        "hours": 8,
        "start": "08:00",
        "end": "16:00",
        "color": "#E57373",
        "text_color": "#7A1212",
        "description": "فترة تكميلية صباحية 8 ساعات"
    },
    "CP12": {
        "name": "تكميلية صباحية 12 س",
        "code": "CP12",
        "icon": "CP12",
        "display": "CP12",
        "type": "تكميلية",
        "category": "tkmilia",
        "hours": 12,
        "start": "08:00",
        "end": "20:00",
        "color": "#E57373",
        "text_color": "#7A1212",
        "description": "فترة تكميلية صباحية 12 ساعة"
    },
    "CP24": {
        "name": "تكميلية كامل اليوم",
        "code": "CP24",
        "icon": "CP24",
        "display": "CP24",
        "type": "تكميلية",
        "category": "tkmilia",
        "hours": 24,
        "start": "08:00",
        "end": "08:00",
        "color": "#E57373",
        "text_color": "#7A1212",
        "description": "فترة تكميلية 24 ساعة"
    },
    
    # ===== ليلي تكميلي =====
    "LN8": {
        "name": "ليلي تكميلي 8 س",
        "code": "LN8",
        "icon": "LN8",
        "display": "LN8",
        "type": "ليلي تكميلي",
        "category": "night",
        "hours": 8,
        "start": "22:00",
        "end": "06:00",
        "color": "#2D4A6E",
        "text_color": "#FFFFFF",
        "description": "فترة ليلية تكميلية 8 ساعات"
    },
    "LN10": {
        "name": "ليلي تكميلي 10 س",
        "code": "LN10",
        "icon": "LN10",
        "display": "LN10",
        "type": "ليلي تكميلي",
        "category": "night",
        "hours": 10,
        "start": "22:00",
        "end": "08:00",
        "color": "#2D4A6E",
        "text_color": "#FFFFFF",
        "description": "فترة ليلية تكميلية 10 ساعات"
    },
    
    # ===== إجازات وحالات خاصة =====
    "V": {
        "name": "إجازة",
        "code": "V",
        "icon": "V",
        "display": "V",
        "type": "إجازة",
        "category": "off",
        "hours": 0,
        "start": "--:--",
        "end": "--:--",
        "color": "#E0E0E0",
        "text_color": "#4A5568",
        "description": "إجازة عادية"
    },
    "E": {
        "name": "إجازة اختبارات",
        "code": "E",
        "icon": "E",
        "display": "E",
        "type": "إجازة اختبارات",
        "category": "off",
        "hours": 0,
        "start": "--:--",
        "end": "--:--",
        "color": "#9CA3AF",
        "text_color": "#1F2937",
        "description": "إجازة لأداء الاختبارات"
    },
    "EV": {
        "name": "إجازة استثنائية",
        "code": "EV",
        "icon": "EV",
        "display": "EV",
        "type": "إجازة استثنائية",
        "category": "off",
        "hours": 0,
        "start": "--:--",
        "end": "--:--",
        "color": "#9CA3AF",
        "text_color": "#1F2937",
        "description": "إجازة استثنائية"
    },
    "M": {
        "name": "مهمة رسمية",
        "code": "M",
        "icon": "M",
        "display": "M",
        "type": "مهمة رسمية",
        "category": "mission",
        "hours": 8,
        "start": "08:00",
        "end": "16:00",
        "color": "#64748B",
        "text_color": "#FFFFFF",
        "description": "مهمة رسمية خارج المركز"
    },
    "ME": {
        "name": "مكلف",
        "code": "ME",
        "icon": "ME",
        "display": "ME",
        "type": "مكلف",
        "category": "mission",
        "hours": 8,
        "start": "08:00",
        "end": "16:00",
        "color": "#64748B",
        "text_color": "#FFFFFF",
        "description": "مكلف بمهام إضافية"
    },
}

# ============================================================================
# 2. رموز الفرق القديمة (للتوسع - للتوافق مع الإصدارات السابقة)
# ============================================================================
TEAM_CODES = {
    'A': {
        'name': 'الفريق الأول',
        'icon': '👥',
        'color': '#FFB74D',
        'description': 'الفريق الأساسي'
    },
    'B': {
        'name': 'الفريق الثاني',
        'icon': '👥',
        'color': '#4A6FA5',
        'description': 'الفريق الأساسي'
    },
    'C': {
        'name': 'الفريق الثالث',
        'icon': '👥',
        'color': '#2D4A6E',
        'description': 'الفريق الأساسي'
    },
    'D': {
        'name': 'الفريق الرابع',
        'icon': '👥',
        'color': '#FFB74D',
        'description': 'الفريق الأساسي'
    },
    'O': {
        'name': 'فريق التداخلية',
        'icon': '🔄',
        'color': '#45CFEF',
        'description': 'فريق دعم'
    },
    'RR': {
        'name': 'فريق التدخل السريع',
        'icon': '⚡',
        'color': '#CE2E26',
        'description': 'Rapid Response'
    },
    'XW': {
        'name': 'فريق العمليات',
        'icon': '🖥️',
        'color': '#513A87',
        'description': 'غرفة التحكم'
    },
    'C00': {
        'name': 'العمليات الموحدة',
        'icon': '💻',
        'color': '#3B4A82',
        'description': 'نظام العمليات'
    }
}

# ============================================================================
# 3. رموز المراكز والتمركزات (Center & Deployment Codes) - محدث
# ============================================================================
CENTER_CODES = {
    # المراكز الحقيقية (1-10)
    1: {'name': 'المنصورة', 'type': 'مركز ثابت', 'city': 'الرياض', 'is_virtual': False},
    2: {'name': 'الخالدية', 'type': 'مركز ثابت', 'city': 'الرياض', 'is_virtual': False},
    3: {'name': 'منفوحة', 'type': 'مركز ثابت', 'city': 'الرياض', 'is_virtual': False},
    4: {'name': 'الدار البيضاء', 'type': 'مركز ثابت', 'city': 'الرياض', 'is_virtual': False},
    5: {'name': 'العزيزية', 'type': 'مركز ثابت', 'city': 'الرياض', 'is_virtual': False},
    6: {'name': 'الإسكان', 'type': 'مركز ثابت', 'city': 'الرياض', 'is_virtual': False},
    7: {'name': 'الحائر', 'type': 'مركز ثابت', 'city': 'الرياض', 'is_virtual': False},
    8: {'name': 'الشفاء', 'type': 'مركز ثابت', 'city': 'الرياض', 'is_virtual': False},
    9: {'name': 'عكاظ', 'type': 'مركز ثابت', 'city': 'الرياض', 'is_virtual': False},
    10: {'name': 'ديراب', 'type': 'مركز ثابت', 'city': 'الرياض', 'is_virtual': False},
    
    # التمركز
    12: {'name': 'التمركز', 'type': 'تمركز', 'city': 'متنقل', 'is_virtual': True},
}

# ============================================================================
# 4. المركز الرئيسي للقطاع (HQ)
# ============================================================================
HQ_CENTER = {
    'id': 'HQ',
    'name': 'المركز الرئيسي للقطاع',
    'type': 'قيادة',
    'city': 'الرياض',
    'is_hq': True
}

# ============================================================================
# 5. رموز الوحدات الخاصة (Special Units)
# ============================================================================
SPECIAL_UNITS = {
    'ST': {'name': 'وحدة نقل', 'icon': '🚛', 'color': '#64748B', 'category': 'لوجستي'},
    'TT': {'name': 'باص استجابة', 'icon': '🚑', 'color': '#CE2E26', 'category': 'إسعافي'},
    'XX': {'name': 'إجازة', 'icon': '🏖️', 'color': '#9CA3AF', 'category': 'حالة خاصة'},
    'Y': {'name': 'إداري', 'icon': '📋', 'color': '#475569', 'category': 'دعم'},
    'YY': {'name': 'صيانة مركبات', 'icon': '🔧', 'color': '#6B7280', 'category': 'صيانة'},
    'YYY': {'name': 'تموين طبي', 'icon': '💊', 'color': '#42924B', 'category': 'تموين'},
    'YYYY': {'name': 'أوكسجين', 'icon': '💨', 'color': '#45CFEF', 'category': 'تموين'},
    'Z': {'name': 'صيانة أجهزة', 'icon': '⚙️', 'color': '#F1B944', 'category': 'صيانة'},
}

# ============================================================================
# 6. أنواع الموظفين (Employee Types)
# ============================================================================
EMP_TYPE_LABELS = {
    "chief_paramedic": "كبير مسعفين",
    "assistant_chief": "مساعد كبير مسعفين",
    "field_leader": "قيادة ميدانية",
    "operations_control": "تحكم عملياتي",
    "response_coordinator": "تنسيق استجابة",
    "paramedic": "أخصائي اسعاف",
    "emt": "فني اسعاف",
    "health_assistant": "مساعد صحي",
    "logistic_support": "دعم لوجستي",
    "admin": "إداري"
}

EMP_TYPE_COLORS = {
    "chief_paramedic": "#CE2E26",
    "assistant_chief": "#B71C1C",
    "field_leader": "#3B4A82",
    "operations_control": "#45CFEF",
    "response_coordinator": "#513A87",
    "paramedic": "#42924B",
    "emt": "#F1B944",
    "health_assistant": "#FF7C10",
    "logistic_support": "#64748B",
    "admin": "#475569"
}

# ============================================================================
# 7. دوال مساعدة
# ============================================================================

def get_center_name(center_num: int) -> str:
    """الحصول على اسم المركز من رقمه"""
    if center_num in CENTER_CODES:
        return CENTER_CODES[center_num]['name']
    return f'مركز {center_num}'

def is_virtual_center(center_num: int) -> bool:
    """التحقق إذا كان المركز وهمياً (تمركز)"""
    if center_num in CENTER_CODES:
        return CENTER_CODES[center_num].get('is_virtual', False)
    return False

def get_shift_info(shift_code: str) -> dict:
    """الحصول على معلومات المناوبة من رمزها"""
    if shift_code in SHIFT_TYPES:
        return SHIFT_TYPES[shift_code]
    if shift_code in TEAM_CODES:
        return TEAM_CODES[shift_code]
    return {
        'name': shift_code,
        'icon': shift_code,
        'display': shift_code,
        'color': '#9CA3AF',
        'text_color': '#1F2937',
        'hours': 0,
        'description': 'غير معروف'
    }

def get_special_unit_info(unit_code: str) -> dict:
    """الحصول على معلومات الوحدة الخاصة"""
    return SPECIAL_UNITS.get(unit_code, {
        'name': unit_code,
        'icon': '❓',
        'color': '#9CA3AF',
        'category': 'غير معروف'
    })

def get_all_shift_codes() -> list:
    """الحصول على جميع رموز المناوبات"""
    return list(SHIFT_TYPES.keys())

def get_shift_codes_by_category(category: str) -> list:
    """الحصول على رموز المناوبات حسب التصنيف"""
    return [code for code, info in SHIFT_TYPES.items() if info.get('category') == category]