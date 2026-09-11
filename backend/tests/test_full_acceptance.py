import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.db.database import get_db, SessionLocal, engine, Base
from app.db.seed_data import seed_db
from app.models.models import (
    User, Tender, TenderRequirement, Vendor, Bid, Document, ExtractedField,
    Verification, RuleResult, CrossCheck, RiskAssessment, AuditEvent, ReviewDecision
)

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    seed_db()

def test_complete_sih_acceptance_flow():
    # 1. Procurement Officer logs in via JWT
    login_res = client.post("/api/auth/login", json={"email": "officer@bharatsetu.gov.in", "password": "officer123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    uid = str(uuid.uuid4())[:8]

    # 2. Store Tender with dynamic rules in Database
    create_tender_payload = {
        "tender_id": f"CPCL-ACCEPT-{uid}",
        "title": "Industrial High Pressure Machinery Procurement",
        "department": "CPCL Refinery Wing",
        "category": "Industrial Machinery",
        "bid_deadline": "2026-11-30",
        "minimum_turnover_inr": 50000000.0,
        "estimated_value": 60000000.0,
        "minimum_experience_years": 3,
        "requirements": [
            {"document_type": "GST", "is_mandatory": True, "description": "Active GSTIN Certificate"},
            {"document_type": "PAN", "is_mandatory": True, "description": "PAN Card"},
            {"document_type": "UDYAM", "is_mandatory": True, "description": "Udyam Registration Certificate"},
            {"document_type": "EPFO", "is_mandatory": True, "description": "EPFO Registration Proof"}
        ]
    }
    t_res = client.post("/api/tenders", json=create_tender_payload, headers=headers)
    assert t_res.status_code == 200
    tender_id_db = t_res.json()["id"]

    # 3. Create Bidder & New Bid Submission (Starts in DRAFT status)
    bid_payload = {
        "tender_id": tender_id_db,
        "vendor_name": f"Shree Lakshmi Heavy Industries {uid} Pvt Ltd",
        "category": "Industrial Machinery",
        "bid_amount": "₹ 48,27,500",
        "gstin": "27ABCDE1234F1Z5",
        "pan": "ABCDE1234F",
        "udyam": "UDYAM-MH-29-0048291"
    }
    b_res = client.post("/api/bids", json=bid_payload, headers=headers)
    assert b_res.status_code == 200
    bid_data = b_res.json()
    bid_code = bid_data["id"]
    assert bid_data["status"] == "draft"
    assert bid_data["risk_score"] == 0

    # Create Bidder User
    bidder = User(
        email=f"bidder_{uid}@bharatsetu.gov.in",
        hashed_password="password",
        full_name="Test Bidder",
        role="BIDDER",
        vendor_id=None # We will fetch the dynamically created vendor
    )
    db = SessionLocal()
    vendor = db.query(Vendor).filter(Vendor.name == f"Shree Lakshmi Heavy Industries {uid} Pvt Ltd").first()
    bidder.vendor_id = vendor.id
    db.add(bidder)
    db.commit()
    db.refresh(bidder)

    from app.core.security import create_access_token
    bidder_token = create_access_token(subject=bidder.id)
    bidder_headers = {"Authorization": f"Bearer {bidder_token}"}

    # 4. Upload Document (GST Certificate containing address) (Must be done by Bidder)
    gst_content = b"%PDF-1.4\nGoods and Services Tax Registration Certificate. GSTIN: 27AABCDE1234F1Z5. Legal Name: Shree Lakshmi Heavy Industries. Registered Address: Flat 402, Shivajinagar, Pune, Maharashtra."
    file_obj = ("GST_Cert_2026.pdf", gst_content, "application/pdf")
    doc_res = client.post(f"/api/bids/{bid_code}/documents", files={"file": file_obj}, headers=bidder_headers)
    assert doc_res.status_code == 200
    doc_id = doc_res.json()["id"]

    # Test SHA-256 duplicate document detection (Audit Item 14)
    dup_res = client.post(f"/api/bids/{bid_code}/documents", files={"file": file_obj}, headers=bidder_headers)
    assert dup_res.status_code == 400
    assert "Duplicate document" in dup_res.json()["detail"]

    # 5. Run Verification Pipeline
    ver_res = client.post(f"/api/bids/{bid_code}/verify", headers=headers)
    assert ver_res.status_code == 200

    # 6. Verify ExtractedFields, Verifications, CrossChecks, and RiskAssessments persisted in DB
    db: Session = SessionLocal()
    db_bid = db.query(Bid).filter(Bid.bid_id == bid_code).first()
    assert db_bid is not None
    assert db_bid.status in ["FLAGGED", "PENDING_REVIEW"]
    assert db_bid.risk_score >= 60

    # Verify ExtractedField persisted
    db_ef = db.query(ExtractedField).filter(ExtractedField.document_id == doc_id).all()
    assert len(db_ef) > 0

    # Verify Verification records persisted
    db_ver = db.query(Verification).filter(Verification.bid_id == db_bid.id).all()
    assert len(db_ver) >= 2

    # Verify RuleResult persisted
    db_rr = db.query(RuleResult).filter(RuleResult.bid_id == db_bid.id).all()
    assert len(db_rr) > 0

    # Verify RiskAssessment persisted
    db_ra = db.query(RiskAssessment).filter(RiskAssessment.bid_id == db_bid.id).first()
    assert db_ra is not None

    # Verify AI language does NOT contain autonomous approve/reject decisions
    assert "No automated compliance blockers" in db_bid.ai_recommendation or "Escalation" in db_bid.ai_recommendation or "Review" in db_bid.ai_recommendation

    db.close()

    # 7. Procurement Officer Escalates the Bid (Authenticated officer identity persisted)
    esc_res = client.post(f"/api/bids/{bid_code}/escalate", json={"action": "ESCALATE", "reason": "Address mismatch detected between Pune GST certificate and Nagpur Udyam certificate."}, headers=headers)
    assert esc_res.status_code == 200
    assert esc_res.json()["officer"] == "Anil Kumar"

    # 8. Verify PDF report generates directly from persisted DB records
    pdf_res = client.get(f"/api/reports/bids/{bid_code}", headers=headers)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 1000

    # 9. RESTART DB SESSION & VERIFY EVERYTHING STILL EXISTS INTACT
    db_check: Session = SessionLocal()
    check_bid = db_check.query(Bid).filter(Bid.bid_id == bid_code).first()
    assert check_bid.status == "FLAGGED"
    assert check_bid.reviewed_by == "Anil Kumar"

    check_decision = db_check.query(ReviewDecision).filter(ReviewDecision.bid_id == check_bid.id).first()
    assert check_decision is not None
    assert check_decision.action == "ESCALATED"
    assert check_decision.officer_name == "Anil Kumar"

    check_audit = db_check.query(AuditEvent).filter(AuditEvent.bid_id == check_bid.id, AuditEvent.event_type == "BID_ESCALATED").first()
    assert check_audit is not None
    db_check.close()
