from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import Bid, Document, Verification, Notification, User, Tender
from app.core.security import get_current_user
from app.core.tender_rules import MIN_TENDER_VALUE_INR
from datetime import datetime, timedelta

router = APIRouter(prefix="/bidder", tags=["Bidder Portal"])

@router.get("/dashboard")
def get_bidder_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "BIDDER":
        raise HTTPException(status_code=403, detail="Not authorized")

    if not current_user.vendor_id:
        return {"active_bids": 0, "pending_bids": 0, "approved_bids": 0, "rejected_bids": 0, "total_documents": 0, "verified_documents": 0, "failed_documents": 0, "compliance_percentage": 0}

    bids = db.query(Bid).filter(Bid.vendor_id == current_user.vendor_id).all()
    active_bids = sum(1 for b in bids if b.status not in ["APPROVED", "REJECTED", "DRAFT"])
    pending_bids = sum(1 for b in bids if b.status == "PENDING_REVIEW")
    approved_bids = sum(1 for b in bids if b.status == "APPROVED")
    rejected_bids = sum(1 for b in bids if b.status == "REJECTED")

    bid_ids = [b.id for b in bids]
    documents = db.query(Document).filter(Document.bid_id.in_(bid_ids)).all() if bid_ids else []
    
    verified_docs = sum(1 for d in documents if d.document_status == "VERIFIED")
    failed_docs = sum(1 for d in documents if d.document_status == "FAILED")
    
    compliance_rates = [b.compliance_score for b in bids if b.compliance_score > 0]
    avg_compliance = round(sum(compliance_rates) / len(compliance_rates), 1) if compliance_rates else 0.0

    action_items = []
    for d in documents:
        if d.document_status in ["FAILED", "WARNING"]:
            action_items.append({
                "issue": f"{d.document_type} Document Compliance Issue",
                "reason": d.detail or "Extracted fields or verification check did not meet required threshold",
                "requirement": d.document_type,
                "document_id": d.id,
                "document_name": d.filename,
                "action": "Re-upload Valid Document",
                "bid_id": d.bid_id
            })

    for b in bids:
        if b.risk_level in ["HIGH", "CRITICAL"]:
            action_items.append({
                "issue": f"Bid {b.bid_id} Flagged as {b.risk_level} Risk",
                "reason": b.ai_summary or "Risk score exceeds acceptable tolerance threshold",
                "requirement": "Risk Review",
                "document_id": None,
                "document_name": None,
                "action": "Review Bidding Details",
                "bid_id": b.id
            })

    vendor_name = current_user.vendor.name if current_user.vendor else current_user.full_name

    return {
        "active_bids": active_bids,
        "pending_bids": pending_bids,
        "approved_bids": approved_bids,
        "rejected_bids": rejected_bids,
        "total_documents": len(documents),
        "verified_documents": verified_docs,
        "failed_documents": failed_docs,
        "compliance_percentage": avg_compliance,
        "action_required": len(action_items),
        "action_items": action_items,
        "vendor_name": vendor_name
    }

@router.get("/alerts")
def get_bidder_alerts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "BIDDER":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    if not current_user.vendor_id:
        return []

    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.notification_type.in_(["ERROR", "WARNING"])
    ).order_by(Notification.created_at.desc()).all()
    
    alerts = []
    for notif in notifications:
        alerts.append({
            "id": notif.id,
            "type": notif.title,
            "message": notif.message,
            "severity": "high" if notif.notification_type == "ERROR" else "medium",
            "created_at": notif.created_at
        })
                
    return alerts


@router.get("/suggested-tenders")
def get_suggested_tenders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "BIDDER":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    if not current_user.vendor_id:
        return []

    # Get bidder's valid, exact-document verifications
    bids = db.query(Bid).filter(Bid.vendor_id == current_user.vendor_id).all()
    bid_ids = [b.id for b in bids]
    
    if not bid_ids:
        verifications = []
    else:
        verifications = db.query(Verification).join(Document, Verification.document_id == Document.id).filter(
            Verification.bid_id.in_(bid_ids),
            Document.bid_id.in_(bid_ids),
            Verification.verified == True,
            Verification.document_id.isnot(None),
            Document.document_status == "VERIFIED"
        ).all()
        
    verified_doc_types = set()
    for v in verifications:
        verified_doc_types.add(v.document_type.upper())

    # Evaluate active tenders with the global minimum tender value rule
    tenders = db.query(Tender).filter(
        Tender.estimated_value >= MIN_TENDER_VALUE_INR,
        Tender.status == "ACTIVE"
    ).all()
    suggestions = []
    
    for t in tenders:
        reqs = t.requirements
        if not reqs:
            continue
            
        satisfied = []
        missing = []
        failed = []
        manual_review = []
        
        mandatory_count = 0
        satisfied_mandatory_count = 0
        
        for r in reqs:
            rtype = r.document_type.upper()
            if r.is_mandatory:
                mandatory_count += 1
                
            if rtype in verified_doc_types:
                satisfied.append(f"{rtype} Verification")
                if r.is_mandatory:
                    satisfied_mandatory_count += 1
            else:
                if r.is_mandatory:
                    missing.append(f"{rtype} Document")
                    
        # Calculate score deterministically
        if mandatory_count == 0:
            score = 100
        else:
            score = int((satisfied_mandatory_count / mandatory_count) * 100)
            
        readiness = "Strong Match" if score >= 80 else ("Good Match" if score >= 50 else "Requirements Need Review")

        suggestions.append({
            "tender_id": t.id,
            "tender_reference": t.tender_id,
            "tender_name": t.title,
            "department": t.department,
            "tender_value": t.estimated_value,
            "closing_date": t.bid_deadline,
            "match_score": score,
            "readiness": readiness,
            "satisfied_requirements": satisfied,
            "missing_requirements": missing,
            "failed_requirements": failed,
            "manual_review_requirements": manual_review,
            "reasons": [
                f"Satisfied ({len(satisfied)}): {', '.join(satisfied)}" if satisfied else "No verified documents match this tender yet",
                f"Action needed ({len(missing)}): {', '.join(missing)}" if missing else "All mandatory requirements verified"
            ],
            "explanation": f"Based on currently verified documents, you match {score}% of the mandatory requirements."
        })
        
    # Sort by highest score first
    suggestions.sort(key=lambda x: x["match_score"], reverse=True)
    return suggestions
