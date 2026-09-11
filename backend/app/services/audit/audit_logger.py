from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.models import AuditEvent, utc_now

class AuditLogger:
    @staticmethod
    def log_event(
        db: Session,
        event_type: str,
        source: str,
        action_label: str,
        bid_id: Optional[str] = None,
        user_id: Optional[str] = None,
        vendor_name: Optional[str] = None,
        status: str = "pass",
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """
        Creates an immutable AuditEvent record in the database.
        """
        event = AuditEvent(
            bid_id=bid_id,
            user_id=user_id,
            event_type=event_type,
            source=source,
            action_label=action_label,
            vendor_name=vendor_name,
            status=status,
            details_json=details,
            timestamp=utc_now()
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
