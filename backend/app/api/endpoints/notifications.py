# backend/app/api/endpoints/notifications.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.user import User
from app.schemas.notification import NotificationResponse
from app.services.notification_service import NotificationService
from app.api import deps
import uuid

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/", response_model=List[NotificationResponse])
def get_my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False
):
    """جلب إشعارات المستخدم الحالي"""
    service = NotificationService(db)
    return service.get_user_notifications(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        unread_only=unread_only
    )

@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """عدد الإشعارات غير المقروءة"""
    service = NotificationService(db)
    count = service.get_unread_count(current_user.id)
    return {"count": count}

@router.put("/{notification_id}/read")
def mark_notification_read(
    notification_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """تحديد إشعار كمقروء"""
    service = NotificationService(db)
    if service.mark_as_read(notification_id, current_user.id):
        return {"message": "تم تحديث الإشعار"}
    raise HTTPException(status_code=404, detail="الإشعار غير موجود")

@router.put("/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """تحديد كل الإشعارات كمقروءة"""
    service = NotificationService(db)
    count = service.mark_all_as_read(current_user.id)
    return {"message": f"تم تحديث {count} إشعار"}

@router.delete("/{notification_id}")
def delete_notification(
    notification_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """حذف إشعار"""
    service = NotificationService(db)
    notification = service.db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="الإشعار غير موجود")
    
    service.db.delete(notification)
    service.db.commit()
    return {"message": "تم حذف الإشعار"}