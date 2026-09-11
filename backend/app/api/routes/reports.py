from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import Bid, Document, Verification, RuleResult, CrossCheck, ReviewDecision, User
from app.services.report.pdf_generator import PDFReportGenerator
from app.core.config import settings
from app.core.security import get_current_user

router = APIRouter(prefix="/reports", tags=["PDF Reports"])

@router.get("/bids/{bid_id_or_code}")
def download_bid_report(bid_id_or_code: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    bid = db.query(Bid).filter((Bid.id == bid_id_or_code) | (Bid.bid_id == bid_id_or_code)).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")

    # Load persisted document records directly from database
    docs = []
    for d in bid.documents:
        docs.append({
            "name": d.document_type,
            "source": d.source or "Document Processing Pipeline",
            "status": d.document_status.lower(),
            "detail": d.detail or f"Filename: {d.filename} | OCR Confidence: {d.ocr_confidence}%"
        })

    # Load persisted verifications directly from database
    verifications = db.query(Verification).filter(Verification.bid_id == bid.id).all()
    ver_list = []
    for v in verifications:
        ver_list.append({
            "source": v.source,
            "status": v.status,
            "verified": v.verified,
            "ref": v.reference_id
        })

    # Load persisted decisions directly from database
    decisions = db.query(ReviewDecision).filter(ReviewDecision.bid_id == bid.id).order_by(ReviewDecision.timestamp.desc()).all()
    latest_decision = decisions[0] if decisions else None

    bid_dict = {
        "id": bid.bid_id,
        "vendorName": bid.vendor.name if bid.vendor else "Unknown Vendor",
        "category": bid.category,
        "bidAmount": bid.bid_amount,
        "submittedAt": bid.submitted_at.strftime("%Y-%m-%d %I:%M %p"),
        "status": bid.status,
        "riskLevel": bid.risk_level,
        "risk_score": bid.risk_score,
        "compliance_score": bid.compliance_score,
        "aiRecommendation": bid.ai_recommendation or "No recommendation recorded.",
        "aiSummary": bid.ai_summary or "No summary recorded.",
        "documents": docs,
        "verifications": ver_list,
        "officer": bid.reviewed_by or (latest_decision.officer_name if latest_decision else "N/A"),
        "officer_reason": latest_decision.reason if latest_decision else None
    }

    pdf_bytes = PDFReportGenerator.generate_bid_report(bid_dict)
    filename = f"BharatSetu_Compliance_Report_{bid.bid_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
