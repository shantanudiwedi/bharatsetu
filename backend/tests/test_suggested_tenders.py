import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.models import Bid, Vendor, Tender, Document, Verification, TenderRequirement, User
from app.core.security import create_access_token
import uuid

client = TestClient(app)

from app.db.database import SessionLocal, engine, Base

@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()



def setup_bidder_and_tender(db: Session):
    uid = str(uuid.uuid4())[:8]
    
    # 1. Create a Tender with GST and PAN requirements
    tender = Tender(title=f"Test Tender {uid}", tender_id=f"TEND-{uid}", department="IT", category="Software", bid_deadline="2026-12-31")
    db.add(tender)
    db.commit()
    db.refresh(tender)
    
    req_gst = TenderRequirement(tender_id=tender.id, document_type="GST", is_mandatory=True)
    req_pan = TenderRequirement(tender_id=tender.id, document_type="PAN", is_mandatory=True)
    req_exp = TenderRequirement(tender_id=tender.id, document_type="EXPERIENCE", is_mandatory=False)
    db.add_all([req_gst, req_pan, req_exp])
    
    # 2. Create Vendor
    vendor = Vendor(name=f"Vendor {uid}", gstin="TESTGST123", pan="TESTPAN123")
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    
    # 3. Create Bidder User
    bidder = User(email=f"bidder_{uid}@test.com", hashed_password="pwd", full_name="Test Bidder", role="BIDDER", vendor_id=vendor.id)
    db.add(bidder)
    db.commit()
    db.refresh(bidder)
    
    # 4. Create Bid
    bid = Bid(bid_id=f"BID-{uid}", tender_id=tender.id, vendor_id=vendor.id, category="Software", bid_amount="₹1,00,000")
    db.add(bid)
    db.commit()
    db.refresh(bid)
    
    token = create_access_token(subject=bidder.id)
    return tender, vendor, bidder, bid, {"Authorization": f"Bearer {token}"}

def test_suggested_tenders_verified_document_satisfies(db: Session):
    tender, vendor, bidder, bid, headers = setup_bidder_and_tender(db)
    
    # Add a fully verified document
    doc = Document(bid_id=bid.id, document_type="GST", filename="gst.pdf", file_hash="hash123", file_path="gst.pdf", document_status="VERIFIED")
    db.add(doc)
    db.commit()
    
    ver = Verification(bid_id=bid.id, document_id=doc.id, document_type="GST", source="TEST", verified=True, status="SUCCESS")
    db.add(ver)
    db.commit()
    
    res = client.get("/api/bidder/suggested-tenders", headers=headers)
    assert res.status_code == 200
    suggestions = res.json()
    my_tender = next(s for s in suggestions if s["tender_id"] == tender.id)
    
    # We have 2 mandatory reqs (GST, PAN). We satisfied GST. Score should be 50%.
    assert my_tender["match_score"] == 50
    assert "GST Verification" in my_tender["satisfied_requirements"]
    assert "PAN Document" in my_tender["missing_requirements"]

def test_suggested_tenders_uploaded_processing_failed_do_not_satisfy(db: Session):
    tender, vendor, bidder, bid, headers = setup_bidder_and_tender(db)
    
    # UPLOADED only (no verification)
    doc_pan = Document(bid_id=bid.id, document_type="PAN", filename="pan.pdf", file_hash="hash456", file_path="pan.pdf", document_status="UPLOADED")
    db.add(doc_pan)
    
    # FAILED verification
    doc_gst = Document(bid_id=bid.id, document_type="GST", filename="gst.pdf", file_hash="hash123", file_path="gst.pdf", document_status="FAILED")
    db.add(doc_gst)
    db.commit()
    ver_gst = Verification(bid_id=bid.id, document_id=doc_gst.id, document_type="GST", source="TEST", verified=False, status="FAILED")
    db.add(ver_gst)
    db.commit()
    
    res = client.get("/api/bidder/suggested-tenders", headers=headers)
    assert res.status_code == 200
    suggestions = res.json()
    my_tender = next(s for s in suggestions if s["tender_id"] == tender.id)
    
    assert my_tender["match_score"] == 0
    assert "PAN Document" in my_tender["missing_requirements"]
    assert "GST Document" in my_tender["missing_requirements"]

def test_verification_without_document_does_not_satisfy(db: Session):
    tender, vendor, bidder, bid, headers = setup_bidder_and_tender(db)
    
    # verified=True but document_id is NULL
    ver_gst = Verification(bid_id=bid.id, document_id=None, document_type="GST", source="TEST", verified=True, status="SUCCESS")
    db.add(ver_gst)
    db.commit()
    
    res = client.get("/api/bidder/suggested-tenders", headers=headers)
    suggestions = res.json()
    my_tender = next(s for s in suggestions if s["tender_id"] == tender.id)
    
    assert my_tender["match_score"] == 0
    assert "GST Verification" not in my_tender["satisfied_requirements"]

def test_bidder_only_receives_suggestions_based_on_own_evidence(db: Session):
    tender, vendor, bidder, bid, headers = setup_bidder_and_tender(db)
    
    # Create another vendor and their bid with verified document
    vendor2 = Vendor(name="Other Vendor")
    db.add(vendor2)
    db.commit()
    db.refresh(vendor2)
    import uuid
    uid = str(uuid.uuid4())[:8]
    bid2 = Bid(bid_id=f"OTHER-BID-{uid}", tender_id=tender.id, vendor_id=vendor2.id, category="Software", bid_amount="₹1,00,000")
    db.add(bid2)
    db.commit()
    
    doc2 = Document(bid_id=bid2.id, document_type="GST", filename="gst.pdf", file_hash="hash123", file_path="gst.pdf", document_status="VERIFIED")
    db.add(doc2)
    db.commit()
    ver2 = Verification(bid_id=bid2.id, document_id=doc2.id, document_type="GST", source="TEST", verified=True, status="SUCCESS")
    db.add(ver2)
    db.commit()
    
    # Current bidder should still have 0% score because vendor2's evidence doesn't count for them
    res = client.get("/api/bidder/suggested-tenders", headers=headers)
    suggestions = res.json()
    my_tender = next(s for s in suggestions if s["tender_id"] == tender.id)
    
    assert my_tender["match_score"] == 0
