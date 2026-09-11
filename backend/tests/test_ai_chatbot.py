import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.models import Bid, Vendor, Tender, Document, Verification, TenderRequirement, User, Notification
from app.core.security import create_access_token
import uuid
from app.db.database import SessionLocal

client = TestClient(app)

@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()

def setup_bidder_env(db: Session):
    uid = str(uuid.uuid4())[:8]
    tender = Tender(title=f"Test Tender {uid}", tender_id=f"TEND-{uid}", department="IT", category="Software", bid_deadline="2026-12-31")
    db.add(tender)
    db.commit()
    db.refresh(tender)
    
    req_gst = TenderRequirement(tender_id=tender.id, document_type="GST", is_mandatory=True)
    req_pan = TenderRequirement(tender_id=tender.id, document_type="PAN", is_mandatory=True)
    db.add_all([req_gst, req_pan])
    
    vendor = Vendor(name=f"Vendor {uid}", gstin="TESTGST123", pan="TESTPAN123")
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    
    bidder = User(email=f"bidder_{uid}@test.com", hashed_password="pwd", full_name="Test Bidder", role="BIDDER", vendor_id=vendor.id)
    db.add(bidder)
    db.commit()
    db.refresh(bidder)
    
    bid = Bid(bid_id=f"BID-{uid}", tender_id=tender.id, vendor_id=vendor.id, category="Software", bid_amount="₹1,00,000", status="PROCESSING", risk_level="HIGH")
    db.add(bid)
    db.commit()
    db.refresh(bid)
    
    token = create_access_token(subject=bidder.id)
    return bidder, bid, {"Authorization": f"Bearer {token}"}

def test_ai_chatbot_missing_documents(db: Session):
    bidder, bid, headers = setup_bidder_env(db)
    
    # Upload GST, leave PAN missing
    doc = Document(bid_id=bid.id, document_type="GST", filename="gst.pdf", file_path="gst.pdf", file_hash="hash1", document_status="UPLOADED")
    db.add(doc)
    db.commit()
    
    res = client.post("/api/support/chat", json={"query": "what documents am i missing"}, headers=headers)
    assert res.status_code == 200
    reply = res.json()["reply"]
    
    assert "[MOCK AI]" in reply
    assert "PAN" in reply
    assert "GST" not in reply

def test_ai_chatbot_compliance_status(db: Session):
    bidder, bid, headers = setup_bidder_env(db)
    
    res = client.post("/api/support/chat", json={"query": "what is my compliance status"}, headers=headers)
    assert res.status_code == 200
    reply = res.json()["reply"]
    
    assert "[MOCK AI]" in reply
    assert "PROCESSING" in reply
    assert "HIGH" in reply

def test_ai_chatbot_flagged_bid(db: Session):
    bidder, bid, headers = setup_bidder_env(db)
    
    ver = Verification(bid_id=bid.id, document_type="GST", source="TEST", verified=False, status="FAILED")
    db.add(ver)
    db.commit()
    
    res = client.post("/api/support/chat", json={"query": "why is my bid flagged"}, headers=headers)
    assert res.status_code == 200
    reply = res.json()["reply"]
    
    assert "[MOCK AI]" in reply
    assert bid.bid_id in reply
    assert "Failed Verifications" in reply
    assert "GST from TEST" in reply

def test_ai_chatbot_alerts(db: Session):
    bidder, bid, headers = setup_bidder_env(db)
    
    alert = Notification(user_id=bidder.id, title="Test Alert", message="Your document failed", notification_type="ERROR")
    db.add(alert)
    db.commit()
    
    res = client.post("/api/support/chat", json={"query": "do i have any alerts"}, headers=headers)
    assert res.status_code == 200
    reply = res.json()["reply"]
    
    assert "[MOCK AI]" in reply
    assert "Test Alert" in reply
    assert "Your document failed" in reply

def test_ai_chatbot_document_failure_and_refusal(db: Session):
    bidder, bid, headers = setup_bidder_env(db)

    failed_doc = Document(
        bid_id=bid.id,
        document_type="GST",
        filename="gst_failed.pdf",
        file_path="gst_failed.pdf",
        file_hash="hash-failed",
        document_status="FAILED",
        detail="GST identity mismatch and PAN mismatch detected."
    )
    db.add(failed_doc)
    db.commit()

    res = client.post("/api/support/chat", json={"query": "which documents failed"}, headers=headers)
    assert res.status_code == 200
    reply = res.json()["reply"]
    assert "[MOCK AI]" in reply
    assert "GST" in reply
    assert "FAILED" in reply

    res = client.post("/api/support/chat", json={"query": "approve my bid"}, headers=headers)
    assert res.status_code == 200
    reply = res.json()["reply"]
    assert "cannot approve or reject" in reply.lower()


def test_ai_chatbot_officer_rbac(db: Session):
    # Setup officer
    uid = str(uuid.uuid4())[:8]
    officer = User(email=f"officer_{uid}@test.com", hashed_password="pwd", full_name="Test Officer", role="OFFICER")
    db.add(officer)
    db.commit()
    db.refresh(officer)
    
    token = create_access_token(subject=officer.id)
    headers = {"Authorization": f"Bearer {token}"}
    
    res = client.post("/api/support/chat", json={"query": "what documents am i missing"}, headers=headers)
    assert res.status_code == 200
    reply = res.json()["reply"]
    
    assert "[MOCK AI]" in reply
    assert "I can only assist bidders" in reply
