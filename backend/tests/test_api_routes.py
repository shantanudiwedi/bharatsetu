import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.database import get_db, SessionLocal, engine, Base
from app.db.seed_data import seed_db
from app.models.models import User, Tender, Vendor, Bid, Document, ExtractedField, Verification, RuleResult, CrossCheck, RiskAssessment, AuditEvent, ReviewDecision
from app.core.security import get_password_hash, create_access_token

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

def test_jwt_login_and_auth_routes(db: Session):
    # Test valid officer login
    res = client.post("/api/auth/login", json={"email": "officer@bharatsetu.gov.in", "password": "officer123"})
    assert res.status_code == 200
    token_data = res.json()
    assert "access_token" in token_data

    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Test GET /me with token
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "officer@bharatsetu.gov.in"

    # Test invalid JWT
    bad_res = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid_token_123"})
    assert bad_res.status_code == 401

def test_rbac_authorization(db: Session):
    import uuid
    uid = str(uuid.uuid4())[:8]
    from app.models.models import User
    from app.core.security import get_password_hash
    # Create auditor user with unique email
    auditor = User(
        email=f"auditor_{uid}@bharatsetu.gov.in",
        hashed_password=get_password_hash("auditor123"),
        full_name="Audit Specialist",
        role="AUDITOR"
    )
    db.add(auditor)
    db.commit()

    from app.core.security import create_access_token
    token = create_access_token(subject=auditor.id)
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to approve a bid with AUDITOR role (should be forbidden 403)
    res = client.post("/api/bids/GEM-2026-04827/approve", json={"action": "APPROVE"}, headers=headers)
    assert res.status_code == 403

    # Bidder specific RBAC checks
    res_login = client.post("/api/auth/login", json={"email": "bidder@bharatsetu.gov.in", "password": "bidder123"})
    bidder_token = res_login.json().get("access_token")
    if bidder_token:
        bidder_headers = {"Authorization": f"Bearer {bidder_token}"}
        
        res_approve = client.post("/api/bids/GEM-2026-04827/approve", json={"action": "APPROVE"}, headers=bidder_headers)
        assert res_approve.status_code == 403

        res_reject = client.post("/api/bids/GEM-2026-04827/reject", json={"action": "REJECT", "reason": "Testing"}, headers=bidder_headers)
        assert res_reject.status_code == 403

        res_escalate = client.post("/api/bids/GEM-2026-04827/escalate", json={"action": "ESCALATE", "reason": "Testing"}, headers=bidder_headers)
        assert res_escalate.status_code == 403

def test_sensitive_endpoints_require_auth(db: Session):
    unauth_tenders = client.get("/api/tenders")
    assert unauth_tenders.status_code == 401

    unauth_report = client.get("/api/reports/bids/GEM-2026-04827")
    assert unauth_report.status_code == 401

def test_dashboard_metrics_api(db: Session):
    res_login = client.post("/api/auth/login", json={"email": "officer@bharatsetu.gov.in", "password": "officer123"})
    token = res_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get("/api/dashboard/metrics", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "pending_review_count" in data
    assert "approved_today_count" in data
    assert "compliance_rate_percent" in data

def test_tenders_and_vendors_api(db: Session):
    # Get tenders after login
    res_login = client.post("/api/auth/login", json={"email": "officer@bharatsetu.gov.in", "password": "officer123"})
    token = res_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    t_res = client.get("/api/tenders", headers=headers)
    assert t_res.status_code == 200
    assert isinstance(t_res.json(), list)

    # Get vendors
    v_res = client.get("/api/vendors", headers=headers)
    assert v_res.status_code == 200
    assert isinstance(v_res.json(), list)

def test_pdf_report_download(db: Session):
    res_login = client.post("/api/auth/login", json={"email": "officer@bharatsetu.gov.in", "password": "officer123"})
    token = res_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    bids_res = client.get("/api/bids", headers=headers)
    bids = bids_res.json()
    if len(bids) == 0:
        from app.models.models import Bid, Tender, Vendor
        tender = db.query(Tender).first()
        vendor = db.query(Vendor).first()
        new_bid = Bid(bid_id="DUMMY-BID", tender_id=tender.id, vendor_id=vendor.id, status="approved", risk_score=0, category="General", bid_amount="₹1,00,000")
        db.add(new_bid)
        db.commit()
        db.refresh(new_bid)
        bids_res = client.get("/api/bids", headers=headers)
        bids = bids_res.json()
        
    assert len(bids) > 0
    bid_code = bids[0]["id"]

    report_res = client.get(f"/api/reports/bids/{bid_code}", headers=headers)
    assert report_res.status_code == 200
    assert report_res.headers["content-type"] == "application/pdf"
    assert len(report_res.content) > 500

def test_bidder_isolation_and_security(db: Session, tmp_path):
    uid1 = str(uuid.uuid4())[:8]
    uid2 = str(uuid.uuid4())[:8]

    # Vendor A
    vendor_a = Vendor(name=f"Vendor A {uid1}", gstin=f"GSTA{uid1}")
    db.add(vendor_a)
    db.commit()
    db.refresh(vendor_a)

    # Vendor B
    vendor_b = Vendor(name=f"Vendor B {uid2}", gstin=f"GSTB{uid2}")
    db.add(vendor_b)
    db.commit()
    db.refresh(vendor_b)

    # Bidder A
    bidder_a = User(
        email=f"biddera_{uid1}@bharatsetu.gov.in",
        hashed_password=get_password_hash("bidder123"),
        full_name="Bidder A",
        role="BIDDER",
        vendor_id=vendor_a.id
    )
    db.add(bidder_a)

    # Bidder B
    bidder_b = User(
        email=f"bidderb_{uid2}@bharatsetu.gov.in",
        hashed_password=get_password_hash("bidder123"),
        full_name="Bidder B",
        role="BIDDER",
        vendor_id=vendor_b.id
    )
    db.add(bidder_b)
    db.commit()
    db.refresh(bidder_a)
    db.refresh(bidder_b)

    # Setup Bids
    tender = db.query(Tender).first()
    
    # Bid A (Owned by Vendor A)
    bid_a = Bid(
        bid_id=f"BIDA-{uid1}", tender_id=tender.id, vendor_id=vendor_a.id,
        category="Test", bid_amount="₹1,00,000", status="DRAFT"
    )
    db.add(bid_a)
    
    # Bid B (Owned by Vendor B)
    bid_b = Bid(
        bid_id=f"BIDB-{uid2}", tender_id=tender.id, vendor_id=vendor_b.id,
        category="Test", bid_amount="₹1,10,000", status="DRAFT"
    )
    db.add(bid_b)
    db.commit()
    db.refresh(bid_a)
    db.refresh(bid_b)

    # Document A (Owned by Bid A)
    doc_a = Document(
        bid_id=bid_a.id, document_type="PAN", filename="pan_a.pdf",
        file_path="dummy", file_hash=f"hashA{uid1}"
    )
    db.add(doc_a)

    # Document B (Owned by Bid B)
    doc_b = Document(
        bid_id=bid_b.id, document_type="GST", filename="gst_b.pdf",
        file_path="dummy", file_hash=f"hashB{uid2}"
    )
    db.add(doc_b)
    db.commit()
    db.refresh(doc_a)
    db.refresh(doc_b)

    token_a = create_access_token(subject=bidder_a.id)
    token_b = create_access_token(subject=bidder_b.id)
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Fetch Bids - A should see A but not B
    bids_a = client.get("/api/bids", headers=headers_a).json()
    assert any(b["id"] == bid_a.bid_id for b in bids_a)
    assert not any(b["id"] == bid_b.bid_id for b in bids_a)

    bids_b = client.get("/api/bids", headers=headers_b).json()
    assert any(b["id"] == bid_b.bid_id for b in bids_b)
    assert not any(b["id"] == bid_a.bid_id for b in bids_b)

    # Upload Document - A to A
    test_pdf = tmp_path / "test_dummy.pdf"
    test_pdf.write_bytes(b"%PDF-1.4\ndummy")
    with test_pdf.open("rb") as f:
        res = client.post(f"/api/bids/{bid_a.id}/documents", headers=headers_a, files={"file": ("test_dummy.pdf", f, "application/pdf")})
    assert res.status_code == 200

    # Upload Document - A to B (Forbidden)
    with test_pdf.open("rb") as f:
        res = client.post(f"/api/bids/{bid_b.id}/documents", headers=headers_a, files={"file": ("test_dummy.pdf", f, "application/pdf")})
    assert res.status_code == 403

    # View Document - A views A
    # Since file_path is dummy, it will fail finding it, but it should pass the DB auth check and return 404 instead of 403.
    res_view_aa = client.get(f"/api/bids/documents/{doc_a.id}/view", headers=headers_a)
    assert res_view_aa.status_code == 404  # Passes auth, fails at file read

    # View Document - A views B (Forbidden)
    res_view_ab = client.get(f"/api/bids/documents/{doc_b.id}/view", headers=headers_a)
    assert res_view_ab.status_code == 403

    # View Document - B views B
    res_view_bb = client.get(f"/api/bids/documents/{doc_b.id}/view", headers=headers_b)
    assert res_view_bb.status_code == 404  # Passes auth, fails at file read

    # View Document - B views A (Forbidden)
    res_view_ba = client.get(f"/api/bids/documents/{doc_a.id}/view", headers=headers_b)
    assert res_view_ba.status_code == 403

