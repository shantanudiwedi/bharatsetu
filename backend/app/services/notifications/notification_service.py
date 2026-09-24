import logging
import smtplib
import urllib.error
import urllib.parse
import urllib.request
from email.message import EmailMessage
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import Bid, Notification, User

logger = logging.getLogger(__name__)

EVENTS = {
    "BID_PLACED",
    "BID_UPDATED",
    "BID_STATUS_CHANGED",
    "CLARIFICATION_REQUESTED",
    "BID_FLAGGED",
    "BID_APPROVED",
    "BID_REJECTED",
    "TENDER_EXPIRING_48H",
    "TENDER_EXPIRING_24H",
    "TENDER_EXPIRING_4H",
    "TENDER_EXPIRED",
}


def _event_identity(event_type: str, bid: Bid, event_id: Optional[str] = None) -> str:
    return f"{event_type}:{bid.id}:{event_id or bid.status}"


def _deadline_copy(event_type: str, bid: Bid) -> tuple[str, str]:
    tender_id = bid.tender.tender_id if bid.tender else "N/A"
    deadline_date = bid.tender.bid_deadline if bid.tender else "N/A"
    remaining = {
        "TENDER_EXPIRING_48H": "48 hours",
        "TENDER_EXPIRING_24H": "24 hours",
        "TENDER_EXPIRING_4H": "4 hours",
        "TENDER_EXPIRED": "deadline reached",
    }[event_type]
    subject = {
        "TENDER_EXPIRING_48H": "BharatSetu - Tender Deadline Reminder",
        "TENDER_EXPIRING_24H": "BharatSetu - Tender Deadline Reminder",
        "TENDER_EXPIRING_4H": "BharatSetu - High Priority Tender Deadline Reminder",
        "TENDER_EXPIRED": "BharatSetu - Tender Deadline Reached",
    }[event_type]
    action = settings.NOTIFICATION_ACTION_URL or "Open BharatSetu to review your submission."
    message = (
        f"Tender ID: {tender_id}\n"
        f"Bid number: {bid.bid_id}\n"
        f"Deadline date: {deadline_date}\n"
        f"Deadline time: 00:00\n"
        f"Time zone: {settings.NOTIFICATION_TIME_ZONE}\n"
        f"Time remaining: {remaining}\n"
        f"Current status: {bid.status}\n"
        f"Action: {action}\n"
    )
    return subject, message


def _event_copy(event_type: str, bid: Bid, reason: Optional[str]) -> tuple[str, str]:
    if event_type.startswith("TENDER_"):
        return _deadline_copy(event_type, bid)
    subject = {
        "BID_PLACED": "New bid received",
        "BID_UPDATED": "Bid updated",
        "BID_STATUS_CHANGED": "Bid status changed",
        "CLARIFICATION_REQUESTED": "Clarification requested",
        "BID_FLAGGED": "Compliance issue detected",
        "BID_APPROVED": "Bid approved",
        "BID_REJECTED": "Bid rejected",
    }[event_type]
    details = {
        "BID_PLACED": f"Bid {bid.bid_id} was submitted for review.",
        "BID_UPDATED": f"Bid {bid.bid_id} was updated.",
        "BID_STATUS_CHANGED": f"Bid {bid.bid_id} status is now {bid.status}.",
        "CLARIFICATION_REQUESTED": f"Clarification is required for bid {bid.bid_id}.",
        "BID_FLAGGED": f"Compliance issue detected for bid {bid.bid_id}. Officer review required.",
        "BID_APPROVED": f"Bid {bid.bid_id} was approved by an authorized officer.",
        "BID_REJECTED": f"Bid {bid.bid_id} was rejected by an authorized officer.",
    }[event_type]
    if reason:
        details = f"{details} {reason}"
    return subject, details


def _recipients(db: Session, bid: Bid, include_staff: bool = True) -> list[User]:
    recipients = db.query(User).filter(User.vendor_id == bid.vendor_id).all()
    if include_staff:
        recipients.extend(
            db.query(User).filter(User.role.in_(["PROCUREMENT_OFFICER", "ADMIN"])).all()
        )
    unique: dict[str, User] = {}
    for user in recipients:
        unique[user.id] = user
    return list(unique.values())


def _send_email(user: User, subject: str, message: str) -> str:
    if not settings.EMAIL_NOTIFICATIONS_ENABLED:
        return "NOT_CONFIGURED"
    if not all((settings.SMTP_HOST, settings.SMTP_USERNAME, settings.SMTP_PASSWORD, settings.NOTIFICATION_FROM_EMAIL)):
        return "NOT_CONFIGURED"
    if not user.email:
        return "NOT_CONFIGURED"
    try:
        email = EmailMessage()
        email["Subject"] = subject
        email["From"] = settings.NOTIFICATION_FROM_EMAIL
        email["To"] = user.email
        email.set_content(message)
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
            smtp.starttls()
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp.send_message(email)
        return "SENT"
    except (OSError, smtplib.SMTPException) as exc:
        logger.warning("Email notification failed for registered recipient: %s", exc)
        return "FAILED"


def _send_sms(user: User, message: str) -> str:
    phone = user.vendor.contact_phone if user.vendor is not None else None
    if not phone:
        return "NO_PHONE"
    provider = settings.SMS_PROVIDER.lower()
    if not settings.SMS_NOTIFICATIONS_ENABLED or provider == "mock":
        return "NOT_CONFIGURED" if provider != "mock" else "MOCK"
    if provider != "twilio" or not all((
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN,
        settings.TWILIO_FROM_NUMBER,
    )):
        return "NOT_CONFIGURED"

    payload = urllib.parse.urlencode({
        "To": phone,
        "From": settings.TWILIO_FROM_NUMBER,
        "Body": message[:160],
    }).encode()
    request = urllib.request.Request(
        f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json",
        data=payload,
        method="POST",
    )
    credentials = f"{settings.TWILIO_ACCOUNT_SID}:{settings.TWILIO_AUTH_TOKEN}".encode()
    import base64
    request.add_header("Authorization", f"Basic {base64.b64encode(credentials).decode()}")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return "SENT" if 200 <= response.status < 300 else "FAILED"
    except (OSError, urllib.error.URLError) as exc:
        logger.warning("SMS notification failed for registered phone: %s", exc)
        return "FAILED"


def _sms_message(event_type: str, bid: Bid) -> str:
    tender_id = bid.tender.tender_id if bid.tender else "N/A"
    deadline = bid.tender.bid_deadline if bid.tender else "N/A"
    if event_type == "TENDER_EXPIRED":
        return f"BharatSetu: {tender_id} / {bid.bid_id} has reached its submission deadline."
    remaining = {
        "TENDER_EXPIRING_48H": "48 hours",
        "TENDER_EXPIRING_24H": "24 hours",
        "TENDER_EXPIRING_4H": "4 hours",
    }[event_type]
    return (
        f"BharatSetu: {tender_id} / {bid.bid_id} closes in {remaining}. "
        f"Review before {deadline} {settings.NOTIFICATION_TIME_ZONE}."
    )[:160]


def _has_channel_marker(
    db: Session,
    user_id: str,
    bid_id: str,
    identity: str,
    channel: str,
) -> bool:
    return db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.related_entity_id == bid_id,
        Notification.notification_type == identity,
        Notification.channel == channel,
    ).first() is not None


def _record_channel_marker(
    db: Session,
    user_id: str,
    bid: Bid,
    identity: str,
    title: str,
    message: str,
    channel: str,
    status: str,
) -> None:
    db.add(Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=identity,
        is_read=True,
        related_entity_id=bid.id,
        channel=channel,
        delivery_status=status,
    ))


def _aggregate_status(statuses: list[str]) -> str:
    if not statuses:
        return "NO_RECIPIENT"
    for status in ("SENT", "FAILED", "NOT_CONFIGURED", "NO_EMAIL", "NO_PHONE", "MOCK"):
        if status in statuses:
            return status
    return statuses[0]


def notify_bid_event(
    db: Session,
    bid: Bid,
    event_type: str,
    reason: Optional[str] = None,
    event_id: Optional[str] = None,
) -> dict[str, str]:
    """Best-effort notification fan-out after a bid transaction has committed."""
    if event_type not in EVENTS:
        raise ValueError(f"Unsupported bid notification event: {event_type}")

    identity = _event_identity(event_type, bid, event_id)
    title, message = _event_copy(event_type, bid, reason)
    try:
        users = _recipients(db, bid, include_staff=not event_type.startswith("TENDER_"))
    except Exception as exc:
        logger.warning("Notification recipient lookup failed: %s", exc)
        return {"in_app": "FAILED", "email": "FAILED", "sms": "FAILED"}

    try:
        for user in users:
            if not _has_channel_marker(db, user.id, bid.id, identity, "IN_APP"):
                db.add(Notification(
                    user_id=user.id,
                    title=title,
                    message=message,
                    notification_type=identity,
                    related_entity_id=bid.id,
                    channel="IN_APP",
                    delivery_status="SENT",
                ))
        db.commit()
        in_app_status = "SENT"
    except Exception as exc:
        db.rollback()
        logger.warning("In-app notification persistence failed: %s", exc)
        in_app_status = "FAILED"

    email_statuses: list[str] = []
    sms_statuses: list[str] = []
    for user in users:
        email_marker = db.query(Notification).filter(
            Notification.user_id == user.id,
            Notification.related_entity_id == bid.id,
            Notification.notification_type == identity,
            Notification.channel == "EMAIL",
        ).first()
        if email_marker:
            email_statuses.append(email_marker.delivery_status)
        else:
            email_status = _send_email(user, title, message)
            email_statuses.append(email_status)
            _record_channel_marker(
                db, user.id, bid, identity, title, message, "EMAIL", email_status,
            )
        sms_marker = db.query(Notification).filter(
            Notification.user_id == user.id,
            Notification.related_entity_id == bid.id,
            Notification.notification_type == identity,
            Notification.channel == "SMS",
        ).first()
        if sms_marker:
            sms_statuses.append(sms_marker.delivery_status)
        else:
            sms_status = _send_sms(
                user,
                _sms_message(event_type, bid) if event_type.startswith("TENDER_") else message,
            )
            sms_statuses.append(sms_status)
            _record_channel_marker(
                db, user.id, bid, identity, title, message, "SMS", sms_status,
            )
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("Notification delivery status persistence failed: %s", exc)
    return {
        "in_app": in_app_status,
        "email": _aggregate_status(email_statuses),
        "sms": _aggregate_status(sms_statuses),
    }


def process_tender_deadline_reminders(db: Session, now: Optional[datetime] = None) -> int:
    """Create each applicable deadline reminder once using persisted notifications."""
    from app.models.models import Tender

    current = now or datetime.utcnow()
    created = 0
    tenders = db.query(Tender).filter(Tender.status == "ACTIVE").all()
    for tender in tenders:
        try:
            deadline = datetime.strptime(tender.bid_deadline, "%Y-%m-%d")
        except (TypeError, ValueError):
            logger.warning("Skipping tender with invalid deadline: %s", tender.tender_id)
            continue
        remaining_hours = (deadline - current).total_seconds() / 3600
        bids = db.query(Bid).filter(Bid.tender_id == tender.id).all()
        if remaining_hours <= 0:
            event_types = ["TENDER_EXPIRED"]
        else:
            event_types = [
                event_type
                for threshold, event_type in (
                    (48, "TENDER_EXPIRING_48H"),
                    (24, "TENDER_EXPIRING_24H"),
                    (4, "TENDER_EXPIRING_4H"),
                )
                if remaining_hours <= threshold
            ]
        if not event_types:
            continue

        for bid in bids:
            for event_type in event_types:
                identity = _event_identity(event_type, bid, f"deadline:{tender.id}:{event_type}")
                exists = db.query(Notification).filter(
                    Notification.related_entity_id == bid.id,
                    Notification.notification_type == identity,
                    Notification.channel == "IN_APP",
                ).first()
                if exists:
                    continue
                notify_bid_event(
                    db,
                    bid,
                    event_type,
                    event_id=f"deadline:{tender.id}:{event_type}",
                )
                created += 1
    return created
