from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import Bid, ReviewDecision, User
from app.schemas.schemas import ReviewDecisionCreate
from app.services.audit.audit_logger import AuditLogger
from app.core.security import get_current_user, require_roles
from app.services.notifications.notification_service import notify_bid_event

router = APIRouter(prefix="/bids", tags=["Review Decisions"])

@router.post("/{bid_id_or_code}/approve")
def approve_bid(
    bid_id_or_code: str,
    payload: ReviewDecisionCreate,
    current_user: User = Depends(require_roles(["ADMIN", "PROCUREMENT_OFFICER"])),
    db: Session = Depends(get_db)
):
    bid = db.query(Bid).filter((Bid.id == bid_id_or_code) | (Bid.bid_id == bid_id_or_code)).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")

    bid.status = "APPROVED"
    bid.reviewed_by = current_user.full_name

    decision = ReviewDecision(
        bid_id=bid.id,
        officer_id=current_user.id,
        officer_name=current_user.full_name,
        action="APPROVED",
        reason=payload.reason or f"Compliance verified. Approved by officer {current_user.full_name}."
    )
    db.add(decision)
    
    db.commit()
    notify_bid_event(db, bid, "BID_APPROVED", reason=payload.reason)

    AuditLogger.log_event(
        db, "BID_APPROVED", "Procurement Officer", f"Bid APPROVED by officer {current_user.full_name}",
        bid_id=bid.id, user_id=current_user.id, vendor_name=bid.vendor.name if bid.vendor else "", status="pass"
    )

    return {"message": f"Bid {bid.bid_id} APPROVED by {current_user.full_name}", "status": "APPROVED", "officer": current_user.full_name}

@router.post("/{bid_id_or_code}/reject")
def reject_bid(
    bid_id_or_code: str,
    payload: ReviewDecisionCreate,
    current_user: User = Depends(require_roles(["ADMIN", "PROCUREMENT_OFFICER"])),
    db: Session = Depends(get_db)
):
    if not payload.reason or len(payload.reason.strip()) < 5:
        raise HTTPException(status_code=400, detail="Rejection reason comment is mandatory")

    bid = db.query(Bid).filter((Bid.id == bid_id_or_code) | (Bid.bid_id == bid_id_or_code)).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")

    bid.status = "REJECTED"
    bid.reviewed_by = current_user.full_name

    decision = ReviewDecision(
        bid_id=bid.id,
        officer_id=current_user.id,
        officer_name=current_user.full_name,
        action="REJECTED",
        reason=payload.reason
    )
    db.add(decision)

    db.commit()
    notify_bid_event(db, bid, "BID_REJECTED", reason=payload.reason)

    AuditLogger.log_event(
        db, "BID_REJECTED", "Procurement Officer", f"Bid REJECTED by officer {current_user.full_name}: {payload.reason}",
        bid_id=bid.id, user_id=current_user.id, vendor_name=bid.vendor.name if bid.vendor else "", status="fail"
    )

    return {"message": f"Bid {bid.bid_id} REJECTED by {current_user.full_name}", "status": "REJECTED", "officer": current_user.full_name}

@router.post("/{bid_id_or_code}/escalate")
def escalate_bid(
    bid_id_or_code: str,
    payload: ReviewDecisionCreate,
    current_user: User = Depends(require_roles(["ADMIN", "PROCUREMENT_OFFICER", "REVIEWER"])),
    db: Session = Depends(get_db)
):
    if not payload.reason or len(payload.reason.strip()) < 5:
        raise HTTPException(status_code=400, detail="Escalation reason comment is mandatory")

    bid = db.query(Bid).filter((Bid.id == bid_id_or_code) | (Bid.bid_id == bid_id_or_code)).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")

    bid.status = "FLAGGED"
    bid.reviewed_by = current_user.full_name

    decision = ReviewDecision(
        bid_id=bid.id,
        officer_id=current_user.id,
        officer_name=current_user.full_name,
        action="ESCALATED",
        reason=payload.reason
    )
    db.add(decision)

    db.commit()
    notify_bid_event(db, bid, "BID_FLAGGED", reason=payload.reason, event_id=f"escalation:{bid.id}")

    AuditLogger.log_event(
        db, "BID_ESCALATED", "Procurement Officer", f"Bid ESCALATED for senior review by {current_user.full_name}: {payload.reason}",
        bid_id=bid.id, user_id=current_user.id, vendor_name=bid.vendor.name if bid.vendor else "", status="checking"
    )

    return {"message": f"Bid {bid.bid_id} ESCALATED by {current_user.full_name}", "status": "FLAGGED", "officer": current_user.full_name}
