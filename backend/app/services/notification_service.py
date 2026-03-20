# backend/app/services/notification_service.py
from sqlalchemy.orm import Session
from app.models.notification import Notification, NotificationType
from app.models.user import User
import uuid

class NotificationService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_notification(
        self,
        user_id: uuid.UUID,
        title: str,
        message: str,
        type: NotificationType = NotificationType.SYSTEM
    ) -> Notification:
        """إنشاء إشعار جديد"""
        notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            title=title,
            message=message,
            type=type
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification
    
    def create_shift_change_notification(
        self,
        employee_id: uuid.UUID,
        date: str,
        old_shift: str,
        new_shift: str,
        changed_by: str
    ) -> Notification | None:
        """إنشاء إشعار تغيير مناوبة"""
        # البحث عن المستخدم المرتبط بالموظف
        user = self.db.query(User).filter(User.employee_id == employee_id).first()
        if not user:
            return None
        
        # ترجمة أنواع المناوبات
        shift_names = {
            "D12": "صباحي 12 ساعة",
            "N12": "ليلي 12 ساعة",
            "O12": "تداخلي 12 ساعة",
            "V": "إجازة",
            "off": "بدون مناوبة",
            "CP8": "تكميلية 8 ساعات",
            "CP24": "تكميلية 24 ساعة",
            "LN8": "ليلي تكميلي 8 ساعات"
        }
        
        old_name = shift_names.get(old_shift, old_shift or "بدون")
        new_name = shift_names.get(new_shift, new_shift)
        
        title = "🔄 تحديث في جدول المناوبات"
        message = f"تم تعديل مناوبتك ليوم {date} من {old_name} إلى {new_name} بواسطة {changed_by}"
        
        return self.create_notification(
            user_id=user.id,
            title=title,
            message=message,
            type=NotificationType.SHIFT_CHANGE
        )
    
    def create_new_shift_notification(
        self,
        employee_id: uuid.UUID,
        date: str,
        shift_type: str,
        created_by: str
    ) -> Notification | None:
        """إنشاء إشعار إضافة مناوبة جديدة"""
        user = self.db.query(User).filter(User.employee_id == employee_id).first()
        if not user:
            return None
        
        shift_names = {
            "D12": "صباحي 12 ساعة",
            "N12": "ليلي 12 ساعة",
            "O12": "تداخلي 12 ساعة",
            "V": "إجازة",
            "CP8": "تكميلية 8 ساعات",
            "CP24": "تكميلية 24 ساعة",
            "LN8": "ليلي تكميلي 8 ساعات"
        }
        
        shift_name = shift_names.get(shift_type, shift_type)
        title = "➕ مناوبة جديدة"
        message = f"تم إضافة مناوبة {shift_name} لك يوم {date} بواسطة {created_by}"
        
        return self.create_notification(
            user_id=user.id,
            title=title,
            message=message,
            type=NotificationType.NEW_SHIFT
        )
    
    def get_user_notifications(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False
    ):
        """جلب إشعارات المستخدم"""
        query = self.db.query(Notification).filter(Notification.user_id == user_id)
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        return query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_unread_count(self, user_id: uuid.UUID) -> int:
        """عدد الإشعارات غير المقروءة"""
        return self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).count()
    
    def mark_as_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """تحديد إشعار كمقروء"""
        notification = self.db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        
        if notification:
            notification.is_read = True
            self.db.commit()
            return True
        return False
    
    def mark_all_as_read(self, user_id: uuid.UUID) -> int:
        """تحديد كل إشعارات المستخدم كمقروءة"""
        count = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({"is_read": True})
        self.db.commit()
        return count