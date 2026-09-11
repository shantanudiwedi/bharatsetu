from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import Tender, TenderRequirement, User
from app.schemas.schemas import TenderCreate, TenderResponse, TenderDeadlineUpdate
from app.core.security import get_current_user, require_roles
from app.core.tender_rules import MIN_TENDER_VALUE_INR, format_inr, tender_value_is_eligible

router = APIRouter(prefix="/tenders", tags=["Tenders"])

@router.get("", response_model=List[TenderResponse])
def list_tenders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Tender).filter(
        Tender.status == "ACTIVE",
        Tender.estimated_value >= MIN_TENDER_VALUE_INR
    ).all()

@router.post("", response_model=TenderResponse)
def create_tender(payload: TenderCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(["ADMIN", "PROCUREMENT_OFFICER"]))):
    existing = db.query(Tender).filter(Tender.tender_id == payload.tender_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tender ID already exists")
    if payload.estimated_value <= 0:
        raise HTTPException(status_code=400, detail="Tender estimated value must be greater than zero")
    if not tender_value_is_eligible(payload.estimated_value):
        raise HTTPException(status_code=400, detail=f"Tender estimated value must be at least {format_inr(MIN_TENDER_VALUE_INR)}.")

    tender = Tender(
        tender_id=payload.tender_id,
        title=payload.title,
        department=payload.department,
        category=payload.category,
        bid_deadline=payload.bid_deadline,
        minimum_turnover_inr=payload.minimum_turnover_inr,
        minimum_experience_years=payload.minimum_experience_years,
        msme_exemption_allowed=payload.msme_exemption_allowed,
        startup_exemption_allowed=payload.startup_exemption_allowed,
        local_content_percentage=payload.local_content_percentage,
        estimated_value=payload.estimated_value
    )
    db.add(tender)
    db.commit()
    db.refresh(tender)

    for req in payload.requirements:
        t_req = TenderRequirement(
            tender_id=tender.id,
            document_type=req.document_type,
            is_mandatory=req.is_mandatory,
            description=req.description
        )
        db.add(t_req)
    db.commit()

    return tender

@router.patch("/{tender_id_or_id}/deadline", response_model=TenderResponse)
def update_tender_deadline(
    tender_id_or_id: str,
    payload: TenderDeadlineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "PROCUREMENT_OFFICER"])),
):
    try:
        deadline = datetime.strptime(payload.bid_deadline, "%Y-%m-%d").date()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Deadline must be a valid date in YYYY-MM-DD format") from exc

    tender = db.query(Tender).filter(
        (Tender.id == tender_id_or_id) | (Tender.tender_id == tender_id_or_id)
    ).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    tender.bid_deadline = deadline.isoformat()
    db.commit()
    db.refresh(tender)
    return tender

@router.get("/{tender_id_or_id}", response_model=TenderResponse)
def get_tender(tender_id_or_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tender = db.query(Tender).filter((Tender.id == tender_id_or_id) | (Tender.tender_id == tender_id_or_id)).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    if tender.status.upper() == "ACTIVE" and not tender_value_is_eligible(tender.estimated_value):
        raise HTTPException(status_code=404, detail="Tender is not eligible for live listing")
    return tender
