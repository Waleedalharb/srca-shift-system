# frontend/utils/constants.py
"""
ملف الثوابت المشتركة للنظام
نظام إدارة المراكز الإسعافية - قطاع الجنوب
"""

# ============================================================================
# 1. رموز المناوبات والفرق (Shift Types)
# ============================================================================
SHIFT_TYPES = {
    'A': {
        'name': 'الفريق الأول',
        'icon': '👥', 
        'color': '#FFB74D',
        'description': 'الفريق الأساسي - يغطي الفترة الصباحية'
    },
    'B': {
        'name': 'الفريق الثاني',
        'icon': '👥',
        'color': '#4A6FA5',
        'description': 'الفريق الأساسي - يغطي الفترة المسائية'
    },
    'C': {
        'name': 'الفريق الثالث',
        'icon': '👥',
        'color': '#2D4A6E',
        'description': 'الفريق الأساسي - يغطي الفترة الليلية'
    },
    'D': {
        'name': 'الفريق الرابع',
        'icon': '👥',
        'color': '#FFB74D',
        'description': 'الفريق الأساسي - يغطي الفترات المتغيرة'
    },
    'O': {
        'name': 'فريق التداخلية',
        'icon': '🔄',
        'color': '#45CFEF',
        'description': 'Overlap - فريق دعم وتغطية الفترات الحرجة'
    },
    'RR': {
        'name': 'فريق التدخل السريع',
        'icon': '⚡',
        'color': '#CE2E26',
        'description': 'Rapid Response - فرق استجابة سريعة'
    },
    'XW': {
        'name': 'فريق العمليات',
        'icon': '🖥️',
        'color': '#513A87',
        'description': 'غرفة التحكم والعمليات'
    },
    'C00': {
        'name': 'العمليات الموحدة',
        'icon': '💻',
        'color': '#3B4A82',
        'description': 'نظام العمليات المستقبلي'
    }
}

# ============================================================================
# 2. رموز المراكز والتمركزات (Center & Deployment Codes)
# ============================================================================
CENTER_CODES = {
    # المراكز الحقيقية (1-10)
    1: {'name': 'المنصور', 'type': 'مركز ثابت', 'city': 'الرياض', 'is_virtual': False},
    2: {'name': 'الخالدية', 'type': 'مركز ثابت', 'city': 'الرياض', 'is_virtual': False},
    3: {'name': 'منفوحة', 'type': 'مركز ثابت', 'city': 'الرياض', 'is_virtual': False},
    4: {'name': 'طريق الخرج', 'type': 'مركز ثابت', 'city': 'الرياض', 'is_virtual': False},
    5: {'name': 'العزيزية/الدار البيضاء', 'type': 'مركز ثابت', 'city': 'الرياض', 'is_virtual': False},
    6: {'name': 'الإسكان', 'type': 'مركز ثابت', 'city': 'الرياض', 'is_virtual': False},
    7: {'name': 'الحائر', 'type': 'مركز ثابت', 'city': 'الرياض', 'is_virtual': False},
    8: {'name': 'الشفاء', 'type': 'مركز ثابت', 'city': 'الرياض', 'is_virtual': False},
    9: {'name': 'عكاظ', 'type': 'مركز ثابت', 'city': 'الرياض', 'is_virtual': False},
    10: {'name': 'ديراب', 'type': 'مركز ثابت', 'city': 'الرياض', 'is_virtual': False},
    
    # التمركزات (مراكز دعم متنقلة)
    12: {'name': 'التمركز الأول', 'type': 'تمركز', 'city': 'متنقل', 'is_virtual': True},
    14: {'name': 'التمركز الثاني', 'type': 'تمركز', 'city': 'متنقل', 'is_virtual': True},
}

# ============================================================================
# 3. المركز الرئيسي للقطاع (HQ)
# ============================================================================
HQ_CENTER = {
    'id': 'HQ',
    'name': 'المركز الرئيسي للقطاع',
    'type': 'قيادة',
    'city': 'الرياض',
    'is_hq': True
}

# ============================================================================
# 4. رموز الوحدات الخاصة (Special Units)
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
# 5. أنواع الموظفين (Employee Types)
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
# 6. دوال مساعدة
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
    """الحصول على معلومات الفريق من رمزه"""
    return SHIFT_TYPES.get(shift_code, {
        'name': shift_code,
        'icon': '❓',
        'color': '#9CA3AF',
        'description': 'غير معروف'
    })

def get_special_unit_info(unit_code: str) -> dict:
    """الحصول على معلومات الوحدة الخاصة"""
    return SPECIAL_UNITS.get(unit_code, {
        'name': unit_code,
        'icon': '❓',
        'color': '#9CA3AF',
        'category': 'غير معروف'
    })