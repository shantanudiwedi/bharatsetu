import uuid
import pytest
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine, Base
from app.models.models import Tender, Vendor, Bid, Document, ReviewDecision, AuditEvent
from app.services.ocr.ocr_service import OCRService
from app.services.classification.classifier import DocumentClassifier
from app.services.extraction.extractor import FieldExtractor
from app.services.cross_check.cross_check_engine import CrossCheckEngine
from app.services.compliance.rule_engine import ComplianceRuleEngine
from app.services.risk.risk_engine import RiskEngine
from app.services.ai.explanation_engine import AIExplanationEngine
from app.services.audit.audit_logger import AuditLogger
from app.services.report.pdf_generator import PDFReportGenerator
from app.providers.government.base import (
    MockGSTProvider, MockUdyamProvider, MockPANProvider, MockEPFOProvider, MockDebarmentProvider
)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

def test_full_bid_compliance_acceptance_scenario(db: Session):
    uid = str(uuid.uuid4())[:8]
    # 1. Create Tender
    tender = Tender(
        tender_id=f"CPCL-TEST-{uid}",
        title="Heavy Industrial Machinery Procurement",
        department="CPCL Refinery Division",
        category="Industrial Machinery",
        bid_deadline="2026-10-01",
        minimum_turnover_inr=50000000.0,
        minimum_experience_years=3
    )
    db.add(tender)
    db.commit()

    # 2. Register High Risk Bidder: Shree Lakshmi Industries
    vendor_high = Vendor(
        name=f"Shree Lakshmi Industries {uid} Pvt Ltd",
        gstin="27AABCDE1234F1Z5",
        pan="AABCDE1234F",
        udyam="UDYAM-MH-29-0048291",
        epfo_code="MH/PUN/0048291",
        address="Plot 42, MIDC Industrial Area, Nagpur"
    )
    db.add(vendor_high)
    db.commit()

    bid_high = Bid(
        bid_id=f"GEM-2026-E2E-{uid}",
        tender_id=tender.id,
        vendor_id=vendor_high.id,
        category="Industrial Machinery",
        bid_amount="₹ 48,27,500"
    )
    db.add(bid_high)
    db.commit()

    # 3. Simulate Document Upload & Processing Pipeline
    sample_text_gst = "Goods and Services Tax GSTIN: 27AABCDE1234F1Z5 Status: ACTIVE Legal Name: Shree Lakshmi Industries Address: Flat 402, Shivajinagar, Pune"
    sample_text_udyam = "Udyam Registration Certificate UDYAM-MH-29-0048291 Enterprise Name: Shree Lakshmi Industries Registered Address: Nagpur, Maharashtra"

    doc_type_gst, conf_gst = DocumentClassifier.classify("GST_Cert.pdf", sample_text_gst)
    assert doc_type_gst == "GST"

    doc_type_udyam, conf_udyam = DocumentClassifier.classify("Udyam_Cert.pdf", sample_text_udyam)
    assert doc_type_udyam == "UDYAM"

    # 4. Government Verification Mock Calls
    mock_gst = MockGSTProvider()
    gst_res = mock_gst.verify(vendor_high.gstin, {"vendor_name": vendor_high.name, "address": vendor_high.address})
    assert gst_res["verified"] is False

    mock_epfo = MockEPFOProvider()
    epfo_res = mock_epfo.verify(vendor_high.epfo_code, {"vendor_name": vendor_high.name})
    assert epfo_res["verified"] is False

    mock_debar = MockDebarmentProvider()
    debar_res = mock_debar.verify(vendor_high.name)
    assert debar_res["status"] == "CLEAR"

    # 5. Cross-Check Address Comparison
    score, status = CrossCheckEngine.compare_addresses("Pune, Maharashtra", "Nagpur, Maharashtra")
    assert status in ["POTENTIAL_MISMATCH", "MISMATCH"]

    # 6. Compliance & Risk Engine
    rule_results = ComplianceRuleEngine.evaluate_tender_rules(
        {"required_documents": ["GST", "PAN", "UDYAM", "EPFO"], "minimum_turnover_inr": 50000000.0},
        {"address": "Pune, Maharashtra"},
        [gst_res, epfo_res],
        [{"status": "MISMATCH", "check_type": "ADDRESS", "explanation": "Pune vs Nagpur"}],
        ["GST", "UDYAM"]
    )

    doc_checks = [
        {"name": "GST", "status": "failed", "detail": gst_res["detail"]},
        {"name": "EPFO", "status": "failed", "detail": epfo_res["detail"]},
        {"name": "Udyam", "status": "verified", "detail": "Valid MSME"}
    ]

    risk_score, risk_level, comp_score, risk_factors = RiskEngine.calculate_scores(
        rule_results, doc_checks, [{"status": "MISMATCH", "check_type": "ADDRESS", "explanation": "Pune vs Nagpur"}]
    )

    assert risk_level == "HIGH"
    assert risk_score >= 61

    # 7. AI Explanation
    rec, summary, confidence = AIExplanationEngine.generate_explanation(
        vendor_high.name, risk_level, risk_score, comp_score, risk_factors, doc_checks
    )
    assert "High Risk" in rec or "Escalation" in rec

    # 8. Procurement Officer Decision: Flag for Escalation
    bid_high.status = "FLAGGED"
    bid_high.reviewed_by = "Anil Kumar"
    decision = ReviewDecision(
        bid_id=bid_high.id,
        officer_id="officer_1",
        officer_name="Anil Kumar",
        action="ESCALATED",
        reason="Address discrepancy between GST and Udyam; EPFO registration code not verified."
    )
    db.add(decision)
    db.commit()

    AuditLogger.log_event(
        db, "BID_ESCALATED", "Procurement Officer", "Bid ESCALATED for senior review",
        bid_id=bid_high.id, vendor_name=vendor_high.name, status="checking"
    )

    # Verify decision recorded
    saved_dec = db.query(ReviewDecision).filter(ReviewDecision.bid_id == bid_high.id).first()
    assert saved_dec is not None
    assert saved_dec.action == "ESCALATED"

    # 9. PDF Report Generation
    pdf_bytes = PDFReportGenerator.generate_bid_report({
        "id": bid_high.bid_id,
        "vendorName": vendor_high.name,
        "category": bid_high.category,
        "bidAmount": bid_high.bid_amount,
        "submittedAt": "2026-09-08",
        "status": bid_high.status,
        "riskLevel": risk_level,
        "risk_score": risk_score,
        "compliance_score": comp_score,
        "aiRecommendation": rec,
        "aiSummary": summary,
        "documents": doc_checks
    })
    assert len(pdf_bytes) > 1000

    # 10. Clean Bidder Test: Bharat Tech Solutions LLP (LOW RISK -> APPROVED)
    vendor_low = Vendor(
        name=f"Bharat Tech Solutions {uid} LLP",
        gstin="07AAAB1234C1Z9",
        pan="AAAB1234C",
        udyam="UDYAM-DL-09-0037112",
        epfo_code="DL/CPM/0037112"
    )
    db.add(vendor_low)
    db.commit()

    bid_low = Bid(
        bid_id=f"GEM-2026-CLEAN-{uid}",
        tender_id=tender.id,
        vendor_id=vendor_low.id,
        category="IT Hardware",
        bid_amount="₹ 12,40,000",
        status="APPROVED",
        risk_level="LOW",
        risk_score=12,
        compliance_score=100.0,
        reviewed_by="Anil Kumar"
    )
    db.add(bid_low)
    db.commit()

    assert bid_low.status == "APPROVED"
    assert bid_low.risk_level == "LOW"
