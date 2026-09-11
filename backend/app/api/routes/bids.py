import os
import random
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import (
    Bid, Vendor, Tender, Document, ExtractedField, Verification,
    RuleResult, CrossCheck, RiskAssessment, AuditEvent, User, Notification
)
from app.schemas.schemas import BidCreate, BidResponse, DocumentResponse, DocumentListResponse
from app.core.config import settings, BASE_DIR
from app.core.security import get_current_user
from app.core.tender_rules import MIN_TENDER_VALUE_INR, format_inr, tender_value_is_eligible
from app.services.ocr.ocr_service import OCRService
from app.services.classification.classifier import DocumentClassifier
from app.services.extraction.extractor import FieldExtractor
from app.services.cross_check.cross_check_engine import CrossCheckEngine
from app.services.compliance.rule_engine import ComplianceRuleEngine
from app.services.risk.risk_engine import RiskEngine
from app.services.ai.explanation_engine import AIExplanationEngine
from app.services.audit.audit_logger import AuditLogger
from app.services.validation.validators import (
    compare_names,
    parse_bid_amount,
    validate_entity_name,
    validate_gstin,
    validate_pan,
    validate_udyam,
    validate_epfo,
)
from app.providers.government.base import (
    MockGSTProvider, MockUdyamProvider, MockPANProvider, MockEPFOProvider,
    MockESICProvider, MockMCAProvider, MockStartupProvider, MockNSICProvider,
    MockDigiLockerProvider, MockDebarmentProvider
)

router = APIRouter(prefix="/bids", tags=["Bids"])

def execute_bid_verification_pipeline(bid_id: str, db: Session):
    bid = db.query(Bid).filter(Bid.id == bid_id).first()
    if not bid:
        return

    # Update processing state
    bid.status = "PROCESSING"
    db.commit()

    AuditLogger.log_event(db, "VERIFICATION_STARTED", "Verification Engine", "Started automated verification pipeline", bid_id=bid.id, vendor_name=bid.vendor.name if bid.vendor else "", status="checking")

    # 1. Load Tender and Requirements from DB
    tender = db.query(Tender).filter(Tender.id == bid.tender_id).first()
    tender_reqs = tender.requirements if tender else []
    required_doc_types = [r.document_type.upper() for r in tender_reqs if r.is_mandatory]

    # 2. Gather Extracted Fields from database and build document map
    extracted_fields_map = {}
    uploaded_doc_types = []
    docs_by_type = {}
    for doc in bid.documents:
        doc_type_upper = doc.document_type.upper()
        if doc_type_upper not in uploaded_doc_types:
            uploaded_doc_types.append(doc_type_upper)
            
        if doc_type_upper not in docs_by_type:
            docs_by_type[doc_type_upper] = []
        docs_by_type[doc_type_upper].append(doc)
        
        for ef in doc.extracted_fields:
            extracted_fields_map[ef.field_name] = ef.field_value

    # 3. Call Government Verification Providers and persist Verification DB records
    doc_verifications = []
    doc_checks = []
    verification_ids_by_type = {}

    vendor = bid.vendor
    vendor_name = extracted_fields_map.get("legal_name") or extracted_fields_map.get("enterprise_name") or (vendor.name if vendor else "")

    # Clean old verifications for re-run
    db.query(Verification).filter(Verification.bid_id == bid.id).delete()
    db.query(RuleResult).filter(RuleResult.bid_id == bid.id).delete()
    db.query(CrossCheck).filter(CrossCheck.bid_id == bid.id).delete()
    db.query(RiskAssessment).filter(RiskAssessment.bid_id == bid.id).delete()
    db.commit()

    # Mark every document as PROCESSING before providers run.
    # This ensures that if the pipeline is interrupted, documents do not remain
    # in UPLOADED state indefinitely — they will be in PROCESSING, which signals
    # an incomplete verification run that can be retried.
    for doc in bid.documents:
        doc.document_status = "PROCESSING"
        doc.verification_status = "IN_PROGRESS"
    db.commit()

    pan_res, gst_res = {}, {}

    # Provider 1: GST
    for doc in docs_by_type.get("GST", []):
        doc_fields = {ef.field_name: ef.field_value for ef in doc.extracted_fields}
        doc_gstin = doc_fields.get("gstin")
        doc_id = doc.id
        
        if not doc_gstin:
            current_gst_res = {"verified": False, "status": "INVALID_DOCUMENT", "source": "OCR Extraction", "detail": "GSTIN could not be extracted from the uploaded document."}
        elif vendor and vendor.gstin and doc_gstin != vendor.gstin:
            current_gst_res = {"verified": False, "status": "IDENTITY_MISMATCH", "source": "System Cross-Check", "detail": f"Uploaded GSTIN ({doc_gstin}) does not match vendor profile."}
        else:
            current_gst_res = MockGSTProvider().verify(doc_gstin, {"vendor_name": vendor_name, "address": vendor.address if vendor else ""})
            
        v_gst = Verification(bid_id=bid.id, document_id=doc_id, document_type="GST", source=current_gst_res["source"], is_simulated=True, provider_mode=current_gst_res.get("provider_mode", "MOCK"), verified=current_gst_res["verified"], status=current_gst_res["status"], reference_id=current_gst_res.get("reference_id"), raw_response=current_gst_res)
        db.add(v_gst)
        db.flush()
        verification_ids_by_type.setdefault("GST", []).append(v_gst.id)
        doc_verifications.append(current_gst_res)
        doc_checks.append({"name": "GST", "status": "verified" if current_gst_res["verified"] else "failed", "source": current_gst_res["source"], "detail": current_gst_res["detail"]})
        
        if not current_gst_res["verified"]:
            doc.document_status = "FAILED"
        elif doc.document_status != "FAILED":
            doc.document_status = "VERIFIED"
        doc.detail = current_gst_res["detail"]
        doc.source = current_gst_res["source"]
        doc.verification_status = "COMPLETED"
        gst_res = current_gst_res  # save last for cross checks

    # Provider 2: PAN
    for doc in docs_by_type.get("PAN", []):
        doc_fields = {ef.field_name: ef.field_value for ef in doc.extracted_fields}
        doc_pan = doc_fields.get("pan")
        doc_id = doc.id
        
        if not doc_pan:
            current_pan_res = {"verified": False, "status": "INVALID_DOCUMENT", "source": "OCR Extraction", "detail": "PAN could not be extracted from the uploaded document."}
        elif vendor and vendor.pan and doc_pan != vendor.pan:
            current_pan_res = {"verified": False, "status": "IDENTITY_MISMATCH", "source": "System Cross-Check", "detail": f"Uploaded PAN ({doc_pan}) does not match vendor profile."}
        else:
            current_pan_res = MockPANProvider().verify(doc_pan, {"vendor_name": vendor_name})
            
        v_pan = Verification(bid_id=bid.id, document_id=doc_id, document_type="PAN", source=current_pan_res["source"], is_simulated=True, provider_mode=current_pan_res.get("provider_mode", "MOCK"), verified=current_pan_res["verified"], status=current_pan_res["status"], reference_id=current_pan_res.get("reference_id"), raw_response=current_pan_res)
        db.add(v_pan)
        db.flush()
        verification_ids_by_type.setdefault("PAN", []).append(v_pan.id)
        doc_verifications.append(current_pan_res)
        doc_checks.append({"name": "PAN", "status": "verified" if current_pan_res["verified"] else "failed", "source": current_pan_res["source"], "detail": current_pan_res["detail"]})
        
        if not current_pan_res["verified"]:
            doc.document_status = "FAILED"
        elif doc.document_status != "FAILED":
            doc.document_status = "VERIFIED"
        doc.detail = current_pan_res["detail"]
        doc.source = current_pan_res["source"]
        doc.verification_status = "COMPLETED"
        pan_res = current_pan_res

    # Provider 3: Udyam
    for doc in docs_by_type.get("UDYAM", []):
        doc_fields = {ef.field_name: ef.field_value for ef in doc.extracted_fields}
        doc_udyam = doc_fields.get("udyam_number")
        doc_id = doc.id
        
        if not doc_udyam:
            udyam_res = {"verified": False, "status": "INVALID_DOCUMENT", "source": "OCR Extraction", "detail": "Udyam Number could not be extracted from the uploaded document."}
        elif vendor and vendor.udyam and doc_udyam != vendor.udyam:
            udyam_res = {"verified": False, "status": "IDENTITY_MISMATCH", "source": "System Cross-Check", "detail": f"Uploaded Udyam ({doc_udyam}) does not match vendor profile."}
        else:
            udyam_res = MockUdyamProvider().verify(doc_udyam, {"vendor_name": vendor_name})
            
        v_udyam = Verification(bid_id=bid.id, document_id=doc_id, document_type="UDYAM", source=udyam_res["source"], is_simulated=True, provider_mode=udyam_res.get("provider_mode", "MOCK"), verified=udyam_res["verified"], status=udyam_res["status"], reference_id=udyam_res.get("reference_id"), raw_response=udyam_res)
        db.add(v_udyam)
        db.flush()
        verification_ids_by_type.setdefault("UDYAM", []).append(v_udyam.id)
        doc_verifications.append(udyam_res)
        doc_checks.append({"name": "Udyam", "status": "verified" if udyam_res["verified"] else "failed", "source": udyam_res["source"], "detail": udyam_res["detail"]})
        
        if not udyam_res["verified"]:
            doc.document_status = "FAILED"
        elif doc.document_status != "FAILED":
            doc.document_status = "VERIFIED"
        doc.detail = udyam_res["detail"]
        doc.source = udyam_res["source"]
        doc.verification_status = "COMPLETED"

    # Provider 4: EPFO
    for doc in docs_by_type.get("EPFO", []):
        doc_fields = {ef.field_name: ef.field_value for ef in doc.extracted_fields}
        doc_epfo = doc_fields.get("establishment_code")
        doc_id = doc.id
        
        if not doc_epfo:
            epfo_res = {"verified": False, "status": "INVALID_DOCUMENT", "source": "OCR Extraction", "detail": "EPFO Establishment Code could not be extracted from the uploaded document."}
        elif vendor and vendor.epfo_code and doc_epfo != vendor.epfo_code:
            epfo_res = {"verified": False, "status": "IDENTITY_MISMATCH", "source": "System Cross-Check", "detail": f"Uploaded EPFO Code ({doc_epfo}) does not match vendor profile."}
        else:
            epfo_res = MockEPFOProvider().verify(doc_epfo, {"vendor_name": vendor_name})
            
        v_epfo = Verification(bid_id=bid.id, document_id=doc_id, document_type="EPFO", source=epfo_res["source"], is_simulated=True, provider_mode=epfo_res.get("provider_mode", "MOCK"), verified=epfo_res["verified"], status=epfo_res["status"], reference_id=epfo_res.get("reference_id"), raw_response=epfo_res)
        db.add(v_epfo)
        db.flush()
        verification_ids_by_type.setdefault("EPFO", []).append(v_epfo.id)
        doc_verifications.append(epfo_res)
        doc_checks.append({"name": "EPFO", "status": "verified" if epfo_res["verified"] else "failed", "source": epfo_res["source"], "detail": epfo_res["detail"]})
        
        if not epfo_res["verified"]:
            doc.document_status = "FAILED"
        elif doc.document_status != "FAILED":
            doc.document_status = "VERIFIED"
        doc.detail = epfo_res["detail"]
        doc.source = epfo_res["source"]
        doc.verification_status = "COMPLETED"

    # Provider 5: Debarment (always run as a global compliance check)
    debar_res = MockDebarmentProvider().verify(vendor_name)
    v_debar = Verification(bid_id=bid.id, document_id=None, document_type="DEBARMENT", source=debar_res["source"], is_simulated=True, provider_mode=debar_res.get("provider_mode", "MOCK"), verified=debar_res["verified"], status=debar_res["status"], reference_id=debar_res.get("reference_id"), raw_response=debar_res)
    db.add(v_debar)
    doc_verifications.append(debar_res)

    # Every uploaded document must end in an explicit terminal outcome. A
    # content-unknown document is never verified by filename or OCR confidence.
    for doc in bid.documents:
        if doc.document_type.upper() == "OTHER":
            review = Verification(
                bid_id=bid.id,
                document_id=doc.id,
                document_type="OTHER",
                source="Document Classifier",
                is_simulated=True,
                provider_mode="MOCK",
                verified=False,
                status="MANUAL_REVIEW_REQUIRED",
                raw_response={"detail": "Document content did not match a supported compliance category."},
            )
            db.add(review)
            db.flush()
            verification_ids_by_type.setdefault("OTHER", []).append(review.id)
            doc.document_status = "MANUAL_REVIEW_REQUIRED"
            doc.verification_status = "COMPLETED"
            doc.detail = "Content did not identify a supported compliance document; manual review required."
            doc.source = "Document Classifier"

    # 4. Perform Cross-Document Comparisons and persist CrossCheck records
    cross_checks = []
    
    # Name match (Only if PAN provider ran)
    if "PAN" in uploaded_doc_types and pan_res:
        pan_name = pan_res.get("pan_holder_name", vendor_name)
        name_score, name_status = CrossCheckEngine.compare_names(vendor_name, pan_name)
        cc_name = CrossCheck(bid_id=bid.id, check_type="NAME_MATCH", field_a="vendor_name", value_a=vendor_name, field_b="pan_holder_name", value_b=pan_name, match_score=name_score, status=name_status, explanation=f"Comparison: '{vendor_name}' vs '{pan_name}'")
        db.add(cc_name)
        if name_status != "MATCH":
            cross_checks.append({"check_type": "NAME_MATCH", "status": name_status, "explanation": f"Submitted name '{vendor_name}' vs PAN name '{pan_name}'"})

    # Address match (Only if GST provider ran)
    if "GST" in uploaded_doc_types and gst_res:
        gst_addr = gst_res.get("registered_address", "")
        udyam_addr = extracted_fields_map.get("address") or (vendor.address if vendor else "")
        if gst_addr and udyam_addr:
            addr_score, addr_status = CrossCheckEngine.compare_addresses(gst_addr, udyam_addr)
            cc_addr = CrossCheck(bid_id=bid.id, check_type="ADDRESS_MATCH", field_a="gst_address", value_a=gst_addr, field_b="udyam_address", value_b=udyam_addr, match_score=addr_score, status=addr_status, explanation=f"Comparison: '{gst_addr}' vs '{udyam_addr}'")
            db.add(cc_addr)
            if addr_status != "MATCH":
                cross_checks.append({"check_type": "ADDRESS_MATCH", "status": addr_status, "explanation": f"GST address '{gst_addr}' vs Udyam address '{udyam_addr}'"})

    # 5. Evaluate Rules against Tender Requirements and persist RuleResult records
    tender_data_dict = {
        "required_documents": required_doc_types,
        "minimum_turnover_inr": tender.minimum_turnover_inr if tender else 0.0,
        "minimum_experience_years": tender.minimum_experience_years if tender else 0
    }

    rule_results_list = ComplianceRuleEngine.evaluate_tender_rules(
        tender_data_dict, extracted_fields_map, doc_verifications, cross_checks, uploaded_doc_types
    )

    for rr in rule_results_list:
        db_rr = RuleResult(
            bid_id=bid.id,
            verification_id=(
                verification_ids_by_type.get(rr["document_type"].upper(), [None])[0]
                if rr.get("document_type")
                else None
            ),
            rule_id=rr["rule_id"],
            document_type=rr["document_type"],
            result=rr["result"],
            finding=rr["finding"],
            impact=rr.get("impact", "HIGH"),
            recommended_action=rr.get("recommended_action")
        )
        db.add(db_rr)

    # 6. Calculate Risk and Compliance Scores
    risk_score, risk_level, compliance_score, risk_factors = RiskEngine.calculate_scores(
        rule_results_list, doc_checks, cross_checks
    )

    # 7. Generate Explainable AI Summary (strictly fact-grounded)
    rec, summary, confidence = AIExplanationEngine.generate_explanation(
        vendor_name, risk_level, risk_score, compliance_score, risk_factors, doc_checks
    )

    # Persist RiskAssessment
    risk_assess = RiskAssessment(
        bid_id=bid.id,
        risk_score=risk_score,
        risk_level=risk_level,
        compliance_score=compliance_score,
        risk_factors=risk_factors
    )
    db.add(risk_assess)

    # Update Bid status
    bid.risk_score = risk_score
    bid.risk_level = risk_level
    bid.compliance_score = compliance_score
    bid.ai_confidence = confidence
    bid.ai_recommendation = rec
    bid.ai_summary = summary
    bid.status = "FLAGGED" if risk_level == "HIGH" else "PENDING_REVIEW"

    db.commit()

    AuditLogger.log_event(
        db, "RISK_CALCULATED", "AI Engine",
        f"Verification complete: Risk Score {risk_score} ({risk_level}), Compliance {compliance_score}%",
        bid_id=bid.id, vendor_name=vendor_name, status="pass" if risk_level != "HIGH" else "fail"
    )

    # Get the users who own this bid to generate persistent alerts
    bidder_users = db.query(User).filter(User.vendor_id == bid.vendor_id).all()
    for bidder_user in bidder_users:
        for rr in rule_results_list:
            if rr["result"] == "FAIL":
                title = f"Compliance Failure: {rr['rule_id']}"
                message = rr["finding"]
                existing = db.query(Notification).filter(
                    Notification.user_id == bidder_user.id,
                    Notification.related_entity_id == bid.id,
                    Notification.title == title
                ).first()
                if not existing:
                    notif = Notification(user_id=bidder_user.id, title=title, message=message, notification_type="ERROR", related_entity_id=bid.id)
                    db.add(notif)
                    
        for chk in doc_checks:
            if chk["status"] == "failed":
                title = f"Verification Failed: {chk['name']}"
                message = chk["detail"]
                existing = db.query(Notification).filter(
                    Notification.user_id == bidder_user.id,
                    Notification.related_entity_id == bid.id,
                    Notification.title == title
                ).first()
                if not existing:
                    notif = Notification(user_id=bidder_user.id, title=title, message=message, notification_type="ERROR", related_entity_id=bid.id)
                    db.add(notif)
                    
    db.commit()

@router.get("", response_model=List[BidResponse])
def list_bids(
    search: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    risk_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Bid).join(Tender, Bid.tender_id == Tender.id)
    if current_user.role == "BIDDER":
        if not current_user.vendor_id:
            return []
        query = query.filter(Bid.vendor_id == current_user.vendor_id)

    query = query.filter(Tender.estimated_value >= MIN_TENDER_VALUE_INR)

    if status_filter:
        query = query.filter(Bid.status == status_filter.upper())
    if risk_filter:
        query = query.filter(Bid.risk_level == risk_filter.upper())

    bids = query.order_by(Bid.submitted_at.desc()).all()
    results = []

    for b in bids:
        # Search filter
        if search:
            s_lower = search.lower().strip()
            if s_lower:
                v_name = (b.vendor.name if b.vendor and b.vendor.name else "").lower()
                b_id = (b.bid_id if b.bid_id else "").lower()
                v_gstin = (b.vendor.gstin if b.vendor and b.vendor.gstin else "").lower()
                v_pan = (b.vendor.pan if b.vendor and b.vendor.pan else "").lower()
                v_udyam = (b.vendor.udyam if b.vendor and b.vendor.udyam else "").lower()
                
                if (s_lower not in v_name and 
                    s_lower not in b_id and 
                    s_lower not in v_gstin and 
                    s_lower not in v_pan and 
                    s_lower not in v_udyam):
                    continue

        # Load persisted documents
        docs = []
        for d in b.documents:
            docs.append({
                "id": d.id,
                "name": d.document_type,
                "status": d.document_status.lower(),
                "source": d.source or "Uploaded Document",
                "detail": d.detail or f"{d.filename} processed."
            })

        # Load persisted audit entries
        audit_entries = []
        for a in b.audit_events:
            audit_entries.append({
                "id": a.id,
                "source": a.source,
                "label": a.action_label,
                "status": a.status,
                "timestamp": a.timestamp.strftime("%H:%M:%S")
            })

        results.append({
            "id": b.bid_id,
            "vendorName": b.vendor.name if b.vendor else "Unknown Vendor",
            "vendor_id_code": b.vendor.udyam or b.vendor.gstin or b.vendor.pan or "N/A",
            "category": b.category,
            "bidAmount": b.bid_amount,
            "submittedAt": b.submitted_at.strftime("%Y-%m-%d %I:%M %p"),
            "riskLevel": b.risk_level.lower(),
            "risk_score": b.risk_score,
            "compliance_score": b.compliance_score,
            "status": b.status.lower(),
            "aiConfidence": b.ai_confidence,
            "aiRecommendation": b.ai_recommendation or "Awaiting verification pipeline execution.",
            "aiSummary": b.ai_summary or "New bid submission registered.",
            "documents": docs,
            "audit_trail": audit_entries,
            "officer": b.reviewed_by,
            "tender_title": b.tender.title if b.tender else ""
        })

    return results

@router.post("", response_model=BidResponse)
def create_bid(
    payload: BidCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tender = db.query(Tender).filter((Tender.id == payload.tender_id) | (Tender.tender_id == payload.tender_id)).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    if tender.status.upper() != "ACTIVE":
        raise HTTPException(status_code=400, detail="Tender is not active")
    if not tender_value_is_eligible(tender.estimated_value):
        raise HTTPException(status_code=400, detail=f"Tender value is below the minimum {format_inr(MIN_TENDER_VALUE_INR)} threshold")
    try:
        deadline = datetime.strptime(tender.bid_deadline, "%Y-%m-%d")
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Tender deadline is invalid")
    if deadline.date() < datetime.utcnow().date():
        raise HTTPException(status_code=400, detail="Tender deadline has passed")

    try:
        vendor_name = validate_entity_name(payload.vendor_name)
        bid_amount = parse_bid_amount(payload.bid_amount)
        pan = validate_pan(payload.pan) if payload.pan else None
        gstin = validate_gstin(payload.gstin, pan) if payload.gstin else None
        udyam = validate_udyam(payload.udyam) if payload.udyam else None
    except ValueError as exc:
        field = "bid_amount"
        message = str(exc)
        if "PAN" in message:
            field = "pan"
        elif "GSTIN" in message:
            field = "gstin"
        elif "Udyam" in message:
            field = "udyam"
        elif "entity" in message.lower():
            field = "vendor_name"
        raise HTTPException(
            status_code=422,
            detail={"field": field, "code": "INVALID_INPUT", "message": message},
        )

    if not payload.category or payload.category.strip().casefold() != tender.category.strip().casefold():
        raise HTTPException(
            status_code=422,
            detail={
                "field": "category",
                "code": "CATEGORY_NOT_ALLOWED",
                "message": "Select the category configured for the selected tender.",
            },
        )

    if current_user.role == "BIDDER":
        if not current_user.vendor_id:
            raise HTTPException(status_code=400, detail="Bidder has no associated vendor profile.")
        vendor_id = current_user.vendor_id
        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            raise HTTPException(status_code=422, detail={"field": "vendor", "code": "VENDOR_NOT_FOUND", "message": "Bidder vendor profile was not found."})
        if vendor_name.casefold() != vendor.name.strip().casefold():
            raise HTTPException(status_code=422, detail={"field": "vendor_name", "code": "VENDOR_MISMATCH", "message": "Vendor name does not match the authenticated vendor profile."})
        for field_name, submitted, stored in (
            ("pan", pan, vendor.pan),
            ("gstin", gstin, vendor.gstin),
            ("udyam", udyam, vendor.udyam),
        ):
            if submitted and stored and submitted != stored.upper():
                raise HTTPException(
                    status_code=422,
                    detail={"field": field_name, "code": "VENDOR_MISMATCH", "message": f"{field_name.upper()} does not match the authenticated vendor profile."},
                )
    else:
        # Find or create vendor for manual entry by officer
        vendor = db.query(Vendor).filter(Vendor.name == vendor_name).first()
        if not vendor:
            vendor = Vendor(
                name=vendor_name,
                gstin=gstin,
                pan=pan,
                cin=payload.cin,
                udyam=udyam
            )
            db.add(vendor)
            db.commit()
            db.refresh(vendor)
        vendor_id = vendor.id

    bid_num = random.randint(48000, 49999)
    bid_code = f"GEM-2026-{bid_num}"

    # AUDIT ITEM 5: Starts as DRAFT with 0 scores until verification runs
    bid = Bid(
        bid_id=bid_code,
        # The request may identify a tender by its public reference. Persist
        # the database primary key so relationship joins and queue queries
        # return the newly created bid.
        tender_id=tender.id,
        vendor_id=vendor_id,
        category=tender.category,
        bid_amount=bid_amount,
        status="DRAFT",
        risk_level="MEDIUM",
        risk_score=0,
        compliance_score=0.0,
        ai_confidence=0,
        ai_recommendation="New bid created in DRAFT state. Upload documents and run verification.",
        ai_summary="Draft bid registered."
    )
    db.add(bid)
    db.commit()
    db.refresh(bid)

    AuditLogger.log_event(
        db, "BID_CREATED", "Bidder Console", f"Created new draft bid {bid_code}",
        bid_id=bid.id, user_id=current_user.id, vendor_name=vendor.name, status="pass"
    )

    # Notification Trigger
    notification = Notification(
        user_id=current_user.id,
        title="Bid Submitted",
        message=f"Bid {bid_code} has been successfully submitted.",
        notification_type="INFO",
        related_entity_id=bid.id
    )
    db.add(notification)
    db.commit()

    return {
        "id": bid.bid_id,
        "vendorName": vendor.name,
        "vendor_id_code": vendor.udyam or vendor.gstin or "N/A",
        "category": bid.category,
        "bidAmount": bid.bid_amount,
        "submittedAt": bid.submitted_at.strftime("%Y-%m-%d %I:%M %p"),
        "riskLevel": "medium",
        "risk_score": 0,
        "compliance_score": 0.0,
        "status": "draft",
        "aiConfidence": 0,
        "aiRecommendation": bid.ai_recommendation,
        "aiSummary": bid.ai_summary,
        "documents": [],
        "audit_trail": []
    }

@router.post("/{bid_id_or_code}/documents", response_model=DocumentResponse)
def upload_document(
    bid_id_or_code: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bid = db.query(Bid).filter((Bid.id == bid_id_or_code) | (Bid.bid_id == bid_id_or_code)).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
        
    if current_user.role != "BIDDER":
        raise HTTPException(status_code=403, detail="Only bidders can upload documents")

    if bid.vendor_id != current_user.vendor_id:
        raise HTTPException(status_code=403, detail="Not authorized to upload to this bid")

    # AUDIT ITEM 13: File validation (extension and size)
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File extension '{ext}' not allowed. Permitted: {settings.ALLOWED_EXTENSIONS}")

    file_bytes = file.file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded document is empty.")
    if len(file_bytes) > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail=f"File size exceeds limit ({settings.MAX_FILE_SIZE_BYTES / (1024*1024):.1f}MB)")

    # MIME magic-bytes validation: reject files whose binary header does not
    # match their declared extension. Prevents extension-spoofing attacks.
    _MAGIC_BYTES = {
        ".pdf": [(0, b"%PDF")],
        ".png": [(0, b"\x89PNG")],
        ".jpg": [(0, b"\xff\xd8\xff")],
        ".jpeg": [(0, b"\xff\xd8\xff")],
    }
    expected_mime_types = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }
    if file.content_type and file.content_type.lower() != expected_mime_types[ext]:
        raise HTTPException(status_code=400, detail="Declared MIME type does not match the file extension.")
    if ext in _MAGIC_BYTES:
        header_checks = _MAGIC_BYTES[ext]
        mime_ok = any(
            file_bytes[offset:offset + len(magic)] == magic
            for offset, magic in header_checks
        )
        if not mime_ok:
            raise HTTPException(
                status_code=400,
                detail=f"File content does not match declared extension '{ext}'. Upload rejected."
            )

    file_hash = OCRService.calculate_sha256(file_bytes)

    # AUDIT ITEM 14: Prevent duplicate uploads using SHA-256
    existing_doc = db.query(Document).filter(Document.bid_id == bid.id, Document.file_hash == file_hash).first()
    if existing_doc:
        raise HTTPException(status_code=400, detail="Duplicate document upload detected (matching SHA-256 file hash)")

    safe_filename = os.path.basename(file.filename)
    save_filename = f"{bid.bid_id}_{safe_filename}"
    save_path = os.path.join(settings.UPLOAD_DIR, save_filename)
    with open(save_path, "wb") as f:
        f.write(file_bytes)

    # Run OCR & Extraction
    extracted_text, ocr_conf = OCRService.process_file(save_path)
    doc_type, class_conf = DocumentClassifier.classify(safe_filename, extracted_text)
    extracted_fields = FieldExtractor.extract_fields(doc_type, extracted_text)
    extracted_map = {field["field_name"]: field["field_value"] for field in extracted_fields}
    consistency_issues = []
    vendor = bid.vendor
    if doc_type == "PAN":
        extracted_pan = extracted_map.get("pan")
        if extracted_pan:
            try:
                validate_pan(extracted_pan)
            except ValueError:
                consistency_issues.append("MANUAL_REVIEW_REQUIRED: extracted PAN has an invalid format.")
        if extracted_pan and vendor.pan and extracted_pan.upper() != vendor.pan.upper():
            consistency_issues.append("IDENTITY_MISMATCH: extracted PAN does not match vendor PAN.")
        name_result = compare_names(extracted_map.get("entity_name"), vendor.name if vendor else None)
        if name_result == "MISMATCH":
            consistency_issues.append("IDENTITY_MISMATCH: PAN document name does not match vendor entity name.")
    elif doc_type == "GST":
        extracted_gstin = extracted_map.get("gstin")
        if extracted_gstin:
            try:
                validate_gstin(extracted_gstin, vendor.pan if vendor else None)
            except ValueError:
                consistency_issues.append("MANUAL_REVIEW_REQUIRED: extracted GSTIN failed structural validation.")
        if extracted_gstin and vendor.gstin and extracted_gstin.upper() != vendor.gstin.upper():
            consistency_issues.append("IDENTITY_MISMATCH: extracted GSTIN does not match vendor GSTIN.")
        if extracted_gstin and vendor.pan and extracted_gstin[2:12] != vendor.pan.upper():
            consistency_issues.append("IDENTITY_MISMATCH: GSTIN embedded PAN does not match vendor PAN.")
        name_result = compare_names(extracted_map.get("legal_name"), vendor.name if vendor else None)
        if name_result == "MISMATCH":
            consistency_issues.append("IDENTITY_MISMATCH: GST legal name does not match vendor entity name.")
    elif doc_type == "UDYAM":
        extracted_udyam = extracted_map.get("udyam_number")
        if extracted_udyam:
            try:
                validate_udyam(extracted_udyam)
            except ValueError:
                consistency_issues.append("MANUAL_REVIEW_REQUIRED: extracted Udyam number has an invalid format.")
        if extracted_udyam and vendor.udyam and extracted_udyam.upper() != vendor.udyam.upper():
            consistency_issues.append("IDENTITY_MISMATCH: extracted Udyam number does not match vendor Udyam number.")
        name_result = compare_names(extracted_map.get("enterprise_name"), vendor.name if vendor else None)
        if name_result == "MISMATCH":
            consistency_issues.append("IDENTITY_MISMATCH: Udyam enterprise name does not match vendor entity name.")
    elif doc_type == "EPFO":
        establishment_code = extracted_map.get("establishment_code")
        if establishment_code:
            try:
                validate_epfo(establishment_code)
            except ValueError:
                consistency_issues.append("MANUAL_REVIEW_REQUIRED: extracted EPFO identifier has an invalid format.")
        if vendor and vendor.epfo_code and establishment_code and establishment_code.upper() != vendor.epfo_code.upper():
            consistency_issues.append("IDENTITY_MISMATCH: extracted EPFO identifier does not match vendor EPFO identifier.")
    if ext == ".pdf":
        if extracted_text.strip():
            extraction_state = "PDF_TEXT_EXTRACTED"
        elif ocr_conf <= 50:
            extraction_state = "PDF_OCR_FAILED"
        else:
            extraction_state = "PDF_EMPTY_CONTENT"
    else:
        extraction_state = "IMAGE_TEXT_EXTRACTED" if extracted_text.strip() else "IMAGE_OCR_FAILED"

    doc = Document(
        bid_id=bid.id,
        document_type=doc_type,
        filename=safe_filename,
        file_path=save_path,
        file_hash=file_hash,
        extracted_text=extracted_text,
        ocr_confidence=ocr_conf,
        document_status="FAILED" if consistency_issues else "UPLOADED",
        verification_status="MANUAL_REVIEW_REQUIRED" if consistency_issues else "PENDING",
        source="OCR Engine",
        detail=f"{extraction_state}; classified as {doc_type} ({class_conf:.0f}% confidence)."
        + (f" {' '.join(consistency_issues)}" if consistency_issues else "")
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # AUDIT ITEM 2: Persist every ExtractedField into DB
    for ef in extracted_fields:
        db_field = ExtractedField(
            document_id=doc.id,
            field_name=ef["field_name"],
            field_value=ef["field_value"],
            confidence=ef["confidence"],
            validation_status=ef["validation_status"]
        )
        db.add(db_field)
    db.commit()

    AuditLogger.log_event(
        db, "DOCUMENT_UPLOADED", "Document Pipeline", f"Uploaded & classified document '{safe_filename}' as {doc_type}",
        bid_id=bid.id, user_id=current_user.id, vendor_name=bid.vendor.name if bid.vendor else "", status="pass"
    )

    return doc

@router.get("/documents", response_model=List[DocumentListResponse])
def list_bidder_documents(
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "BIDDER":
        raise HTTPException(status_code=403, detail="Only bidders can access bidder documents")
    if not current_user.vendor_id:
        return []

    documents = (
        db.query(Document)
        .join(Bid, Document.bid_id == Bid.id)
        .join(Tender, Bid.tender_id == Tender.id)
        .filter(Bid.vendor_id == current_user.vendor_id)
        .order_by(Document.upload_timestamp.desc())
        .all()
    )
    results = []
    for document in documents:
        if search:
            term = search.strip().lower()
            searchable = " ".join([
                document.filename or "",
                document.document_type or "",
                document.bid.bid_id if document.bid else "",
                document.bid.tender.title if document.bid and document.bid.tender else "",
            ]).lower()
            if term not in searchable:
                continue

        extracted_statuses = [field.validation_status.upper() for field in document.extracted_fields]
        if not extracted_statuses:
            extracted_fields_status = "NOT_EXTRACTED"
        elif "INVALID" in extracted_statuses:
            extracted_fields_status = "INVALID"
        elif "UNCERTAIN" in extracted_statuses:
            extracted_fields_status = "UNCERTAIN"
        else:
            extracted_fields_status = "VALID"

        latest_verification = max(
            document.verifications,
            key=lambda verification: verification.timestamp or datetime.min,
            default=None,
        )
        verification_result = (
            f"{latest_verification.status}{' (verified)' if latest_verification.verified else ''}"
            if latest_verification
            else "PENDING"
        )
        document_path = Path(document.file_path)
        if not document_path.is_absolute():
            document_path = Path(BASE_DIR) / document_path
        document_path = document_path.resolve()
        upload_root = Path(settings.UPLOAD_DIR).resolve()
        samples_root = (Path(BASE_DIR) / "samples").resolve()
        file_available = (
            document_path.exists()
            and document_path.is_file()
            and (
                upload_root in document_path.parents
                or samples_root in document_path.parents
            )
        )
        results.append({
            "id": document.id,
            "bid_id": document.bid_id,
            "bid_reference": document.bid.bid_id,
            "tender_id": document.bid.tender.tender_id,
            "tender_title": document.bid.tender.title,
            "filename": document.filename,
            "document_type": document.document_type,
            "upload_timestamp": document.upload_timestamp,
            "document_status": document.document_status,
            "verification_status": document.verification_status,
            "verification_result": verification_result,
            "extracted_fields_status": extracted_fields_status,
            "detail": document.detail,
            "source": document.source,
            "file_available": file_available,
        })
    return results

@router.post("/{bid_id_or_code}/verify")
def verify_bid(
    bid_id_or_code: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bid = db.query(Bid).filter((Bid.id == bid_id_or_code) | (Bid.bid_id == bid_id_or_code)).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")

    if current_user.role == "BIDDER" and bid.vendor_id != current_user.vendor_id:
        raise HTTPException(status_code=403, detail="Not authorized to verify this bid")

    # Execute synchronously for SIH demo reliability
    execute_bid_verification_pipeline(bid.id, db)
    
    # Reload bid to get updated status
    db.refresh(bid)

    # Generate Alert for Bidder
    notif_title = f"Bid Verification: {bid.bid_id}"
    existing_notif = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.related_entity_id == bid.id,
        Notification.title == notif_title
    ).first()
    if not existing_notif:
        notif = Notification(
            user_id=current_user.id,
            title=notif_title,
            message=f"Verification completed for Bid {bid.bid_id}. Risk Level: {bid.risk_level}",
            notification_type="WARNING" if bid.risk_level == "HIGH" else "INFO",
            related_entity_id=bid.id
        )
        db.add(notif)
        db.commit()

    return {"message": "Verification pipeline completed", "bid_id": bid.bid_id, "status": bid.status}

@router.get("/documents/{doc_id}/view")
def view_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if current_user.role == "BIDDER" and doc.bid.vendor_id != current_user.vendor_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this document")

    requested_path = Path(doc.file_path)
    if not requested_path.is_absolute():
        requested_path = Path(BASE_DIR) / requested_path
    
    requested_path = requested_path.resolve()
    upload_root = Path(settings.UPLOAD_DIR).resolve()
    samples_root = (Path(BASE_DIR) / "samples").resolve()

    if not requested_path.exists() or not requested_path.is_file():
        raise HTTPException(status_code=404, detail="File not found on server")
        
    is_in_uploads = upload_root in requested_path.parents or requested_path == upload_root
    is_in_samples = samples_root in requested_path.parents or requested_path == samples_root
    
    if not is_in_uploads and not is_in_samples:
        raise HTTPException(status_code=403, detail="Access to this file is not allowed")

    safe_filename = Path(doc.filename).name.replace('"', '').replace("'", "")
    is_pdf = safe_filename.lower().endswith(".pdf")

    # Read binary header to validate magic bytes
    try:
        with open(requested_path, "rb") as f:
            header = f.read(1024)
    except Exception:
        raise HTTPException(status_code=500, detail="Unable to read document file")

    if is_pdf:
        if not header.startswith(b"%PDF-"):
            raise HTTPException(status_code=400, detail="Invalid PDF file: Missing %PDF- signature")
        media_type = "application/pdf"
    elif header.startswith(b"\x89PNG"):
        media_type = "image/png"
    elif header.startswith(b"\xff\xd8\xff"):
        media_type = "image/jpeg"
    else:
        media_type = "application/octet-stream"

    headers = {
        "Content-Disposition": f'inline; filename="{safe_filename}"'
    }

    return FileResponse(path=str(requested_path), media_type=media_type, headers=headers)
