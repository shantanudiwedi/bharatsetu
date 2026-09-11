from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import AuditEvent, User
from app.schemas.schemas import AuditEntrySchema
from app.core.security import get_current_user

router = APIRouter(prefix="/audit", tags=["Audit Trail"])

@router.get("", response_model=List[AuditEntrySchema])
def get_audit_trail(
    bid_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(AuditEvent)
    if bid_id:
        query = query.filter(AuditEvent.bid_id == bid_id)
    events = query.order_by(AuditEvent.timestamp.desc()).limit(limit).all()

    results = []
    for e in events:
        results.append({
            "id": e.id,
            "source": e.source,
            "label": e.action_label,
            "vendor": e.vendor_name or "System",
            "status": e.status,
            "timestamp": e.timestamp.strftime("%H:%M:%S"),
            "action": e.action_label
        })
    return results
