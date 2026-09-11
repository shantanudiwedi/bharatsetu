import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.database import SessionLocal, engine, Base
from app.db.seed_data import seed_db
from app.models.models import User, Vendor, Tender, Bid, Document, Verification
from app.core.security import get_password_hash, create_access_token
from app.core.config import settings

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    from app.db.database import run_migrations
    run_migrations()
    Base.metadata.create_all(bind=engine)
    seed_db()

@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()

def test_four_document_traceability(db: Session):
    # Setup test Bidder
    uid = str(uuid.uuid4())[:8]
    vendor = Vendor(name=f"Vendor Trace {uid}", gstin=f"GST{uid}", pan=f"PAN{uid}", udyam=f"UDYAM{uid}", epfo_code=f"EPFO{uid}")
    db.add(vendor)
    db.commit()
    db.refresh(vendor)

    bidder = User(
        email=f"trace_{uid}@bharatsetu.gov.in",
        hashed_password=get_password_hash("trace123"),
        full_name="Trace Bidder",
        role="BIDDER",
        vendor_id=vendor.id
    )
    db.add(bidder)
    db.commit()
    db.refresh(bidder)

    tender = db.query(Tender).first()
    bid = Bid(
        bid_id=f"TRACE-{uid}", tender_id=tender.id, vendor_id=vendor.id,
        category="Traceability", bid_amount="₹1,00,000", status="DRAFT"
    )
    db.add(bid)
    db.commit()
    db.refresh(bid)

    bidder_token = create_access_token(subject=bidder.id)
    bidder_headers = {"Authorization": f"Bearer {bidder_token}"}

    # Create 4 fake PDFs
    doc_types = ["UDYAM", "PAN", "GST", "EPFO"]
    doc_ids = {}

    for dt in doc_types:
        filename = f"{dt.lower()}_{uid}.pdf"
        with open(filename, "wb") as f:
            f.write(b"%PDF-1.4\n%Dummy PDF for " + dt.encode() + b"\n")
        
        with open(filename, "rb") as f:
            res = client.post(f"/api/bids/{bid.id}/documents", headers=bidder_headers, files={"file": (filename, f, "application/pdf")})
        assert res.status_code == 200
        doc_ids[dt] = res.json()["id"]
        os.remove(filename)

    # Trigger Verification Pipeline
    res_verify = client.post(f"/api/bids/{bid.id}/verify", headers=bidder_headers)
    assert res_verify.status_code == 200

    # Assert Verification records exactly map to Document.id
    verifications = db.query(Verification).filter(Verification.bid_id == bid.id).all()
    
    # Exclude global DEBARMENT verification which doesn't map to a specific document
    doc_verifications = [v for v in verifications if v.document_type != "DEBARMENT"]
    
    assert len(doc_verifications) == 4, f"Expected 4 verifications, got {len(doc_verifications)}"

    for v in doc_verifications:
        dt = v.document_type.upper()
        assert dt in doc_ids, f"Unexpected document type verified: {dt}"
        assert v.document_id == doc_ids[dt], f"Traceability Failure: Verification {v.id} for {dt} mapped to Document {v.document_id}, expected {doc_ids[dt]}"

    # Test Document View Endpoint (Bidder)
    for dt, doc_id in doc_ids.items():
        res_view = client.get(f"/api/bids/documents/{doc_id}/view", headers=bidder_headers)
        assert res_view.status_code == 200, f"Bidder could not view {dt} document"
        assert b"%PDF-1.4" in res_view.content

    # Test Document View Endpoint (Officer)
    officer_res = client.post("/api/auth/login", json={"email": "officer@bharatsetu.gov.in", "password": "officer123"})
    officer_token = officer_res.json()["access_token"]
    officer_headers = {"Authorization": f"Bearer {officer_token}"}

    for dt, doc_id in doc_ids.items():
        res_view = client.get(f"/api/bids/documents/{doc_id}/view", headers=officer_headers)
        assert res_view.status_code == 200, f"Officer could not view {dt} document"
        assert b"%PDF-1.4" in res_view.content

    # Clean up uploaded files
    for doc_id in doc_ids.values():
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc and os.path.exists(doc.file_path):
            os.remove(doc.file_path)
