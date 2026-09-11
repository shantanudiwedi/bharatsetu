import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.database import get_db, SessionLocal, engine, Base
from app.db.seed_data import seed_db
from app.models.models import Bid, Document, Verification, RuleResult, Notification, CrossCheck, User, Vendor, Tender

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    from app.db.database import run_migrations
    run_migrations()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_db()

@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()

def get_bidder_auth(email="bidder@bharatsetu.gov.in"):
    res = client.post("/api/auth/login", json={"email": email, "password": "bidder123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}

def get_officer_auth():
    res = client.post("/api/auth/login", json={"email": "officer@bharatsetu.gov.in", "password": "officer123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}

def test_valid_document_verification(db: Session):
    bidder_headers = get_bidder_auth()
    
    tender = db.query(Tender).filter(Tender.tender_id == "CPCL-2026-IND-09").first()
    
    # Create bid
    res = client.post("/api/bids", json={
        "tender_id": tender.id,
        "vendor_name": "TechCorp India Pvt Ltd",
        "category": "Industrial Machinery",
        "bid_amount": "1000",
        "gstin": "27ABCDE1234F1Z5",
        "pan": "ABCDE1234F",
        "udyam": "UDYAM-MH-00-1234567"
    }, headers=bidder_headers)
    bid_id = res.json()["id"]

    # Test 1: Upload valid document
    with patch("app.api.routes.bids.OCRService.process_file") as mock_ocr, \
         patch("app.api.routes.bids.DocumentClassifier.classify") as mock_clf:
        
        # Valid GST text
        mock_ocr.return_value = ("27ABCDE1234F1Z5 Status: ACTIVE Legal Name: TechCorp India Pvt Ltd Address: Pune", 95.0)
        mock_clf.return_value = ("GST", 98.0)
        
        file_content = b"%PDF-1.4\ndummy pdf content"
        res_upload = client.post(
            f"/api/bids/{bid_id}/documents",
            headers=bidder_headers,
            files={"file": ("valid_gst.pdf", file_content, "application/pdf")}
        )
        assert res_upload.status_code == 200
        doc = res_upload.json()
        assert doc["document_status"] == "UPLOADED"

    # Trigger verification
    res_verify = client.post(f"/api/bids/{bid_id}/verify", headers=bidder_headers)
    assert res_verify.status_code == 200

    # Check status
    res_list = client.get("/api/bids", headers=bidder_headers)
    bid = next(b for b in res_list.json() if b["id"] == bid_id)
    assert any(d["name"] == "GST" and d["status"] == "verified" for d in bid["documents"])


def test_bid_created_from_tender_reference_is_returned_for_selected_tender(db: Session):
    bidder_headers = get_bidder_auth()
    tender = db.query(Tender).filter(Tender.tender_id == "CPCL-2026-IND-09").first()

    response = client.post("/api/bids", json={
        "tender_id": tender.tender_id,
        "vendor_name": "TechCorp India Pvt Ltd",
        "category": "Industrial Machinery",
        "bid_amount": "₹12,34,567",
    }, headers=bidder_headers)

    assert response.status_code == 200
    bid_code = response.json()["id"]
    db.expire_all()
    created = db.query(Bid).filter(Bid.bid_id == bid_code).first()
    assert created is not None
    assert created.tender_id == tender.id
    assert created.vendor_id == db.query(User).filter(User.email == "bidder@bharatsetu.gov.in").first().vendor_id

    listed = client.get("/api/bids", headers=bidder_headers)
    assert listed.status_code == 200
    result = next(item for item in listed.json() if item["id"] == bid_code)
    assert result["tender_title"] == tender.title


def test_invalid_document_no_fallback(db: Session):
    bidder_headers = get_bidder_auth("biddera@bharatsetu.gov.in")
    
    tender = db.query(Tender).filter(Tender.tender_id == "CPCL-2026-IND-09").first()
    
    res = client.post("/api/bids", json={
        "tender_id": tender.id,
        "vendor_name": "TechCorp India Pvt Ltd",
        "category": "Industrial Machinery",
        "bid_amount": "1000",
        "gstin": "27ABCDE1234F1Z5",
        "pan": "ABCDE1234F",
        "udyam": "UDYAM-MH-00-1234567"
    }, headers=bidder_headers)
    bid_id = res.json()["id"]

    # Test 2: Unrelated document - should NOT verify through fallback
    with patch("app.api.routes.bids.OCRService.process_file") as mock_ocr, \
         patch("app.api.routes.bids.DocumentClassifier.classify") as mock_clf:
        
        # Classified as GST but doesn't contain a valid GSTIN
        mock_ocr.return_value = ("Some unrelated text with no GSTIN", 80.0)
        mock_clf.return_value = ("GST", 85.0)
        
        file_content = b"%PDF-1.4\ninvalid pdf content"
        client.post(
            f"/api/bids/{bid_id}/documents",
            headers=bidder_headers,
            files={"file": ("invalid_gst.pdf", file_content, "application/pdf")}
        )

    # Trigger verification
    client.post(f"/api/bids/{bid_id}/verify", headers=bidder_headers)

    # Verify it failed
    res_list = client.get("/api/bids", headers=bidder_headers)
    bid = next(b for b in res_list.json() if b["id"] == bid_id)
    doc = next(d for d in bid["documents"] if d["name"] == "GST")
    assert doc["status"] == "failed"

    # Test 6: Persistent Alert created
    res_alerts = client.get("/api/bidder/alerts", headers=bidder_headers)
    alerts = res_alerts.json()
    assert any("GST" in a["type"] or "GST" in a["message"] for a in alerts)


def test_mismatched_identity_verification(db: Session):
    bidder_headers = get_bidder_auth("bidderb@bharatsetu.gov.in")
    
    tender = db.query(Tender).filter(Tender.tender_id == "CPCL-2026-IND-09").first()
    
    res = client.post("/api/bids", json={
        "tender_id": tender.id,
        "vendor_name": "Global Heavy Industries",
        "category": "Industrial Machinery",
        "bid_amount": "1000",
        "gstin": "33VWXYZ5678G2ZP",
        "pan": "VWXYZ5678G",
        "udyam": "UDYAM-DL-11-7654321"
    }, headers=bidder_headers)
    bid_id = res.json()["id"]

    # Test 4: Mismatched identity field
    with patch("app.api.routes.bids.OCRService.process_file") as mock_ocr, \
         patch("app.api.routes.bids.DocumentClassifier.classify") as mock_clf:
        
        # Different PAN in document
        mock_ocr.return_value = ("ABCDE1234F Name: Global Heavy Industries", 95.0)
        mock_clf.return_value = ("PAN", 98.0)
        
        client.post(
            f"/api/bids/{bid_id}/documents",
            headers=bidder_headers,
            files={"file": ("wrong_pan.pdf", b"%PDF-1.4\npdf content", "application/pdf")}
        )

    client.post(f"/api/bids/{bid_id}/verify", headers=bidder_headers)

    res_list = client.get("/api/bids", headers=bidder_headers)
    bid = next(b for b in res_list.json() if b["id"] == bid_id)
    doc = next(d for d in bid["documents"] if d["name"] == "PAN")
    assert doc["status"] == "failed"


def test_missing_mandatory_document_alert(db: Session):
    bidder_headers = get_bidder_auth()
    
    tender = db.query(Tender).filter(Tender.tender_id == "CPCL-2026-IND-09").first()
    
    res = client.post("/api/bids", json={
        "tender_id": tender.id,
        "vendor_name": "TechCorp India Pvt Ltd",
        "category": "Industrial Machinery",
        "bid_amount": "1000"
    }, headers=bidder_headers)
    bid_id = res.json()["id"]

    # We don't upload GST. It's mandatory.
    client.post(f"/api/bids/{bid_id}/verify", headers=bidder_headers)

    # Test 5 & 7: Check alerts
    res_alerts = client.get("/api/bidder/alerts", headers=bidder_headers)
    alerts = res_alerts.json()
    assert any("GST" in a["message"] and "missing" in a["message"].lower() for a in alerts)

    # Trigger verify again to test deduplication
    client.post(f"/api/bids/{bid_id}/verify", headers=bidder_headers)
    res_alerts2 = client.get("/api/bidder/alerts", headers=bidder_headers)
    assert len(res_alerts2.json()) == len(alerts) # No new duplicates


def test_officer_sees_same_failure(db: Session):
    officer_headers = get_officer_auth()
    
    run_migrations()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_db()

@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()

def get_bidder_auth(email="bidder@bharatsetu.gov.in"):
    res = client.post("/api/auth/login", json={"email": email, "password": "bidder123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}

def get_officer_auth():
    res = client.post("/api/auth/login", json={"email": "officer@bharatsetu.gov.in", "password": "officer123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}

def test_valid_document_verification(db: Session):
    bidder_headers = get_bidder_auth()
    
    tender = db.query(Tender).filter(Tender.tender_id == "CPCL-2026-IND-09").first()
    
    # Create bid
    res = client.post("/api/bids", json={
        "tender_id": tender.id,
        "vendor_name": "TechCorp India Pvt Ltd",
        "category": "Industrial Machinery",
        "bid_amount": "1000",
        "gstin": "27ABCDE1234F1Z5",
        "pan": "ABCDE1234F",
        "udyam": "UDYAM-MH-00-1234567"
    }, headers=bidder_headers)
    bid_id = res.json()["id"]

    # Test 1: Upload valid document
    with patch("app.api.routes.bids.OCRService.process_file") as mock_ocr, \
         patch("app.api.routes.bids.DocumentClassifier.classify") as mock_clf:
        
        # Valid GST text
        mock_ocr.return_value = ("27ABCDE1234F1Z5 Status: ACTIVE Legal Name: TechCorp India Pvt Ltd Address: Pune", 95.0)
        mock_clf.return_value = ("GST", 98.0)
        
        file_content = b"%PDF-1.4\ndummy pdf content"
        res_upload = client.post(
            f"/api/bids/{bid_id}/documents",
            headers=bidder_headers,
            files={"file": ("valid_gst.pdf", file_content, "application/pdf")}
        )
        assert res_upload.status_code == 200
        doc = res_upload.json()
        assert doc["document_status"] == "UPLOADED"

    # Trigger verification
    res_verify = client.post(f"/api/bids/{bid_id}/verify", headers=bidder_headers)
    assert res_verify.status_code == 200

    # Check status
    res_list = client.get("/api/bids", headers=bidder_headers)
    bid = next(b for b in res_list.json() if b["id"] == bid_id)
    assert any(d["name"] == "GST" and d["status"] == "verified" for d in bid["documents"])


def test_invalid_document_no_fallback(db: Session):
    bidder_headers = get_bidder_auth("biddera@bharatsetu.gov.in")
    
    tender = db.query(Tender).filter(Tender.tender_id == "CPCL-2026-IND-09").first()
    
    res = client.post("/api/bids", json={
        "tender_id": tender.id,
        "vendor_name": "TechCorp India Pvt Ltd",
        "category": "Industrial Machinery",
        "bid_amount": "1000",
        "gstin": "27ABCDE1234F1Z5",
        "pan": "ABCDE1234F",
        "udyam": "UDYAM-MH-00-1234567"
    }, headers=bidder_headers)
    bid_id = res.json()["id"]

    # Test 2: Unrelated document - should NOT verify through fallback
    with patch("app.api.routes.bids.OCRService.process_file") as mock_ocr, \
         patch("app.api.routes.bids.DocumentClassifier.classify") as mock_clf:
        
        # Classified as GST but doesn't contain a valid GSTIN
        mock_ocr.return_value = ("Some unrelated text with no GSTIN", 80.0)
        mock_clf.return_value = ("GST", 85.0)
        
        file_content = b"%PDF-1.4\ninvalid pdf content"
        client.post(
            f"/api/bids/{bid_id}/documents",
            headers=bidder_headers,
            files={"file": ("invalid_gst.pdf", file_content, "application/pdf")}
        )

    # Trigger verification
    client.post(f"/api/bids/{bid_id}/verify", headers=bidder_headers)

    # Verify it failed
    res_list = client.get("/api/bids", headers=bidder_headers)
    bid = next(b for b in res_list.json() if b["id"] == bid_id)
    doc = next(d for d in bid["documents"] if d["name"] == "GST")
    assert doc["status"] == "failed"

    # Test 6: Persistent Alert created
    res_alerts = client.get("/api/bidder/alerts", headers=bidder_headers)
    alerts = res_alerts.json()
    assert any("GST" in a["type"] or "GST" in a["message"] for a in alerts)


def test_mismatched_identity_verification(db: Session):
    bidder_headers = get_bidder_auth("bidderb@bharatsetu.gov.in")
    
    tender = db.query(Tender).filter(Tender.tender_id == "CPCL-2026-IND-09").first()
    
    res = client.post("/api/bids", json={
        "tender_id": tender.id,
        "vendor_name": "Global Heavy Industries",
        "category": "Industrial Machinery",
        "bid_amount": "1000",
        "gstin": "33VWXYZ5678G2ZP",
        "pan": "VWXYZ5678G",
        "udyam": "UDYAM-DL-11-7654321"
    }, headers=bidder_headers)
    bid_id = res.json()["id"]

    # Test 4: Mismatched identity field
    with patch("app.api.routes.bids.OCRService.process_file") as mock_ocr, \
         patch("app.api.routes.bids.DocumentClassifier.classify") as mock_clf:
        
        # Different PAN in document
        mock_ocr.return_value = ("ABCDE1234F Name: Global Heavy Industries", 95.0)
        mock_clf.return_value = ("PAN", 98.0)
        
        client.post(
            f"/api/bids/{bid_id}/documents",
            headers=bidder_headers,
            files={"file": ("wrong_pan.pdf", b"%PDF-1.4\npdf content", "application/pdf")}
        )

    client.post(f"/api/bids/{bid_id}/verify", headers=bidder_headers)

    res_list = client.get("/api/bids", headers=bidder_headers)
    bid = next(b for b in res_list.json() if b["id"] == bid_id)
    doc = next(d for d in bid["documents"] if d["name"] == "PAN")
    assert doc["status"] == "failed"


def test_missing_mandatory_document_alert(db: Session):
    bidder_headers = get_bidder_auth()
    
    tender = db.query(Tender).filter(Tender.tender_id == "CPCL-2026-IND-09").first()
    
    res = client.post("/api/bids", json={
        "tender_id": tender.id,
        "vendor_name": "TechCorp India Pvt Ltd",
        "category": "Industrial Machinery",
        "bid_amount": "1000"
    }, headers=bidder_headers)
    bid_id = res.json()["id"]

    # We don't upload GST. It's mandatory.
    client.post(f"/api/bids/{bid_id}/verify", headers=bidder_headers)

    # Test 5 & 7: Check alerts
    res_alerts = client.get("/api/bidder/alerts", headers=bidder_headers)
    alerts = res_alerts.json()
    assert any("GST" in a["message"] and "missing" in a["message"].lower() for a in alerts)

    # Trigger verify again to test deduplication
    client.post(f"/api/bids/{bid_id}/verify", headers=bidder_headers)
    res_alerts2 = client.get("/api/bidder/alerts", headers=bidder_headers)
    assert len(res_alerts2.json()) == len(alerts) # No new duplicates


def test_officer_sees_same_failure(db: Session):
    officer_headers = get_officer_auth()
    
    # List bids as officer
    res_list = client.get("/api/bids", headers=officer_headers)
    bids = res_list.json()
    # Check that any flagged/pending_review bid shows the documents correctly
    # If the previous test left a missing mandatory doc, officer should see it
    bid = next((b for b in bids if b["compliance_score"] < 100 and b["status"] != "draft"), None)
    if bid:
        assert bid["status"] in ["pending_review", "flagged"]

def test_multiple_documents_same_type(db: Session):
    # Tests that if a bidder uploads two documents of the same type (e.g., two GST certificates),
    # the pipeline processes BOTH and produces separate Verification records linked to exact document IDs.
    vendor = db.query(Vendor).filter(Vendor.name == "TechCorp India Pvt Ltd").first()
    tender = db.query(Tender).first()
    bid = Bid(bid_id="MULTIPLE-DOC-BID", tender_id=tender.id, vendor_id=vendor.id, category="Test", bid_amount=1000, status="draft")
    db.add(bid)
    db.commit()
    db.refresh(bid)

    user = db.query(User).filter(User.vendor_id == vendor.id).first()
    headers = get_bidder_auth(user.email)

    with patch("app.api.routes.bids.OCRService.process_file") as mock_ocr, \
         patch("app.api.routes.bids.DocumentClassifier.classify") as mock_clf:
         
        # Upload first GST doc
        mock_ocr.return_value = ("GSTIN: 27AABCDE1234F1Z5", 95.0)
        mock_clf.return_value = ("GST", 98.0)
        res1 = client.post(
            f"/api/bids/{bid.id}/documents",
            headers=headers,
            files={"file": ("gst_1.pdf", b"%PDF-1.4\ndummy 1", "application/pdf")}
        )
        assert res1.status_code == 200
        doc1_id = res1.json()["id"]

        # Upload second GST doc
        mock_ocr.return_value = ("GSTIN: 27AABCDE1234F1Z5", 96.0)
        mock_clf.return_value = ("GST", 99.0)
        res2 = client.post(
            f"/api/bids/{bid.id}/documents",
            headers=headers,
            files={"file": ("gst_2.pdf", b"%PDF-1.4\ndummy 2", "application/pdf")}
        )
        assert res2.status_code == 200
        doc2_id = res2.json()["id"]

    # Verify bid
    res_verify = client.post(f"/api/bids/{bid.id}/verify", headers=headers)
    assert res_verify.status_code == 200

    # Assert database state
    verifications = db.query(Verification).filter(Verification.bid_id == bid.id, Verification.document_type == "GST").all()
    assert len(verifications) == 2, "Should have created exactly 2 Verification records for GST"
    
    doc_ids_in_verifications = {v.document_id for v in verifications}
    assert doc1_id in doc_ids_in_verifications
    assert doc2_id in doc_ids_in_verifications
