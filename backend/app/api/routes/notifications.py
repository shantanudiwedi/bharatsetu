from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.models import Notification, User
from app.schemas.schemas import NotificationSchema
from app.core.security import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("", response_model=List[NotificationSchema])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.channel == "IN_APP",
    ).order_by(Notification.created_at.desc()).all()
    return notifications

@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.channel == "IN_APP",
        Notification.is_read == False,
    ).count()
    return {"unread_count": count}

@router.post("/{notification_id}/read")
def mark_as_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
        Notification.channel == "IN_APP",
    ).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    db.commit()
    return {"message": "Marked as read"}

@router.post("/read-all")
def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.channel == "IN_APP",
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"message": "All marked as read"}
