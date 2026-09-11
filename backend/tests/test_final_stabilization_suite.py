import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.models import Bid, Vendor, Tender, Document, Verification, TenderRequirement, User
from app.core.security import create_access_token
from app.core.config import settings
from app.db.database import SessionLocal
import uuid

import tempfile

client = TestClient(app)


def read_chat_reply(res):
    data = res.json() if res.status_code == 200 else {}
    return data.get("response", data.get("reply", ""))


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


# ===================================================================== #
# 1. CHATBOT REGRESSION TESTS                                           #
# ===================================================================== #

def test_chatbot_empty_query_400(db: Session):
    uid = str(uuid.uuid4())[:8]
    user = User(email=f"b_{uid}@test.com", hashed_password="pwd", full_name="Bidder", role="BIDDER")
    db.add(user)
    db.commit()
    token = create_access_token(subject=user.id)
    headers = {"Authorization": f"Bearer {token}"}

    # Empty query -> 400
    res = client.post("/api/support/chat", json={"query": ""}, headers=headers)
    assert res.status_code == 400

    # Whitespace-only query -> 400
    res_ws = client.post("/api/support/chat", json={"query": "   \t \n  "}, headers=headers)
    assert res_ws.status_code == 400


def test_chatbot_dynamic_compliance_score(db: Session):
    uid = str(uuid.uuid4())[:8]
    vendor = Vendor(name=f"Vendor {uid}")
    db.add(vendor)
    db.commit()

    bidder = User(email=f"bidder_{uid}@test.com", hashed_password="pwd", full_name="Dynamic Bidder", role="BIDDER", vendor_id=vendor.id)
    db.add(bidder)
    db.commit()

    tender = Tender(title=f"Tender {uid}", tender_id=f"T-{uid}", department="CPCL", category="Engineering", bid_deadline="2026-12-31", estimated_value=200000.0)
    db.add(tender)
    db.commit()

    test_score = 83.5
    bid = Bid(bid_id=f"GEM-{uid}", tender_id=tender.id, vendor_id=vendor.id, category="Engineering", bid_amount="₹1,50,000", status="PENDING_REVIEW", risk_level="LOW", compliance_score=test_score)
    db.add(bid)
    db.commit()

    token = create_access_token(subject=bidder.id)
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post("/api/support/chat", json={"query": "what is my compliance status"}, headers=headers)
    assert res.status_code == 200
    reply = read_chat_reply(res)
    assert f"Compliance Score is **{test_score:.1f}%**" in reply
    assert "[MOCK AI]" in reply


def test_chatbot_bidder_isolation(db: Session):
    uid1 = str(uuid.uuid4())[:8]
    uid2 = str(uuid.uuid4())[:8]
    
    v1 = Vendor(name=f"V1 {uid1}")
    v2 = Vendor(name=f"V2 {uid2}")
    db.add_all([v1, v2])
    db.commit()

    b1 = User(email=f"b1_{uid1}@test.com", hashed_password="pwd", full_name="Bidder 1", role="BIDDER", vendor_id=v1.id)
    b2 = User(email=f"b2_{uid2}@test.com", hashed_password="pwd", full_name="Bidder 2", role="BIDDER", vendor_id=v2.id)
    db.add_all([b1, b2])
    db.commit()

    t = Tender(title=f"Tender {uid1}", tender_id=f"T-{uid1}", department="CPCL", category="Engineering", bid_deadline="2026-12-31", estimated_value=200000.0)
    db.add(t)
    db.commit()

    bid1 = Bid(bid_id=f"BID1-{uid1}", tender_id=t.id, vendor_id=v1.id, category="Eng", bid_amount="₹1,00,000", status="PROCESSING", risk_level="HIGH")
    bid2 = Bid(bid_id=f"BID2-{uid2}", tender_id=t.id, vendor_id=v2.id, category="Eng", bid_amount="₹1,10,000", status="PROCESSING", risk_level="HIGH")
    db.add_all([bid1, bid2])
    db.commit()

    token1 = create_access_token(subject=b1.id)
    res = client.post("/api/support/chat", json={"query": "what is my compliance status"}, headers={"Authorization": f"Bearer {token1}"})
    assert res.status_code == 200
    reply = read_chat_reply(res)
    assert bid1.bid_id in reply
    assert bid2.bid_id not in reply


def test_chatbot_flagged_bid_does_not_crash_when_rule_result_has_no_passed_flag(db: Session):
    uid = str(uuid.uuid4())[:8]
    vendor = Vendor(name=f"Vendor {uid}")
    db.add(vendor)
    db.commit()

    bidder = User(email=f"bidder_{uid}@test.com", hashed_password="pwd", full_name="Bidder", role="BIDDER", vendor_id=vendor.id)
    db.add(bidder)
    db.commit()

    tender = Tender(
        title=f"Tender {uid}",
        tender_id=f"T-{uid}",
        department="CPCL",
        category="Engineering",
        bid_deadline="2026-12-31",
        estimated_value=200000.0,
        status="ACTIVE"
    )
    db.add(tender)
    db.commit()

    bid = Bid(
        bid_id=f"GEM-{uid}",
        tender_id=tender.id,
        vendor_id=vendor.id,
        category="Engineering",
        bid_amount="₹1,50,000",
        status="FLAGGED",
        risk_level="HIGH",
        compliance_score=30.0
    )
    db.add(bid)
    db.commit()
    db.add_all([
        __import__('app.models.models', fromlist=['RuleResult']).RuleResult(
            bid_id=bid.id,
            rule_id="FINANCIAL_MIN",
            document_type="FINANCIAL",
            result="FAIL",
            finding="Annual turnover below threshold.",
            impact="HIGH",
            recommended_action="Upload audited statements."
        )
    ])
    db.commit()

    token = create_access_token(subject=bidder.id)
    res = client.post("/api/support/chat", json={"query": "why is my bid flagged"}, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    reply = read_chat_reply(res)
    assert "flagged" in reply.lower()
    assert "Annual turnover below threshold" in reply


def test_create_bid_rejects_invalid_or_inactive_tender(db: Session):
    uid = str(uuid.uuid4())[:8]
    vendor = Vendor(name=f"Vendor {uid}")
    db.add(vendor)
    db.commit()

    bidder = User(email=f"bidder_{uid}@test.com", hashed_password="pwd", full_name="Bidder", role="BIDDER", vendor_id=vendor.id)
    db.add(bidder)
    db.commit()

    tender = Tender(
        title=f"Closed Tender {uid}",
        tender_id=f"T-CLOSED-{uid}",
        department="CPCL",
        category="Engineering",
        bid_deadline="2024-12-31",
        estimated_value=50000.0,
        status="CLOSED"
    )
    db.add(tender)
    db.commit()

    token = create_access_token(subject=bidder.id)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "tender_id": tender.tender_id,
        "vendor_name": vendor.name,
        "category": "Engineering",
        "bid_amount": "75000",
        "gstin": "27AAABC1234F1Z5",
        "pan": "AAABC1234F",
        "udyam": "UDYAM-MH-29-0000001"
    }

    res = client.post("/api/bids", json=payload, headers=headers)
    assert res.status_code == 400


# ===================================================================== #
# 2. TENDER ₹1 LAKH (100,000 INR) FILTER REGRESSION TESTS               #
# ===================================================================== #

def test_tender_estimated_value_filter_thresholds(db: Session):
    uid = str(uuid.uuid4())[:8]
    
    # Below ₹1 Lakh: 99,999 -> EXCLUDE
    t_below = Tender(
        title=f"Below Threshold {uid}",
        tender_id=f"T-LOW-{uid}",
        department="Test Dept",
        category="Supplies",
        bid_deadline="2026-12-31",
        estimated_value=99999.0
    )
    # Exactly ₹1 Lakh: 100,000 -> INCLUDE
    t_exact = Tender(
        title=f"Exact Threshold {uid}",
        tender_id=f"T-EXACT-{uid}",
        department="Test Dept",
        category="Supplies",
        bid_deadline="2026-12-31",
        estimated_value=100000.0
    )
    # Above ₹1 Lakh: 100,001 -> INCLUDE
    t_above = Tender(
        title=f"Above Threshold {uid}",
        tender_id=f"T-HIGH-{uid}",
        department="Test Dept",
        category="Supplies",
        bid_deadline="2026-12-31",
        estimated_value=100001.0
    )
    db.add_all([t_below, t_exact, t_above])
    db.commit()

    user = User(email=f"user_{uid}@test.com", hashed_password="pwd", full_name="User", role="BIDDER")
    db.add(user)
    db.commit()
    token = create_access_token(subject=user.id)
    headers = {"Authorization": f"Bearer {token}"}

    # GET /api/tenders
    res = client.get("/api/tenders", headers=headers)
    assert res.status_code == 200
    listed_ids = [t["tender_id"] for t in res.json()]

    assert t_below.tender_id not in listed_ids
    assert t_exact.tender_id in listed_ids
    assert t_above.tender_id in listed_ids


def test_suggested_tenders_excludes_below_100k(db: Session):
    uid = str(uuid.uuid4())[:8]
    vendor = Vendor(name=f"Vendor {uid}", pan="ABCDE1234F")
    db.add(vendor)
    db.commit()

    bidder = User(email=f"bidder_sug_{uid}@test.com", hashed_password="pwd", full_name="Bidder", role="BIDDER", vendor_id=vendor.id)
    db.add(bidder)
    db.commit()

    # Tender with value < 100,000
    t_low = Tender(
        title=f"Cheap Tender {uid}",
        tender_id=f"T-CHEAP-{uid}",
        department="CPCL",
        category="Hardware",
        bid_deadline="2026-12-31",
        estimated_value=50000.0
    )
    # Tender with value >= 100,000
    t_high = Tender(
        title=f"Standard Tender {uid}",
        tender_id=f"T-STD-{uid}",
        department="CPCL",
        category="Hardware",
        bid_deadline="2026-12-31",
        estimated_value=1500000.0
    )
    db.add_all([t_low, t_high])
    db.commit()

    req_low = TenderRequirement(tender_id=t_low.id, document_type="PAN", is_mandatory=True)
    req_high = TenderRequirement(tender_id=t_high.id, document_type="PAN", is_mandatory=True)
    db.add_all([req_low, req_high])
    db.commit()

    token = create_access_token(subject=bidder.id)
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/bidder/suggested-tenders", headers=headers)
    assert res.status_code == 200
    suggestions = res.json()
    suggested_tender_ids = [s["tender_id"] for s in suggestions]

    assert t_low.id not in suggested_tender_ids
    assert t_high.id in suggested_tender_ids


def test_cancelled_tenders_are_excluded_from_public_lists(db: Session):
    uid = str(uuid.uuid4())[:8]

    cancelled = Tender(
        title=f"Cancelled Tender {uid}",
        tender_id=f"T-CANCEL-{uid}",
        department="Test Dept",
        category="Supplies",
        bid_deadline="2026-12-31",
        estimated_value=250000.0,
        status="CANCELLED"
    )
    active = Tender(
        title=f"Live Tender {uid}",
        tender_id=f"T-LIVE-{uid}",
        department="Test Dept",
        category="Supplies",
        bid_deadline="2026-12-31",
        estimated_value=250000.0,
        status="ACTIVE"
    )
    db.add_all([cancelled, active])
    db.commit()

    user = User(email=f"user_cancel_{uid}@test.com", hashed_password="pwd", full_name="User", role="BIDDER")
    db.add(user)
    db.commit()

    token = create_access_token(subject=user.id)
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/tenders", headers=headers)
    assert res.status_code == 200
    listed_ids = [t["tender_id"] for t in res.json()]

    assert cancelled.tender_id not in listed_ids
    assert active.tender_id in listed_ids


# ===================================================================== #
# 3. BIDDER REGISTRATION REGRESSION TESTS                               #
# ===================================================================== #

def test_bidder_registration_success(db: Session):
    uid = str(uuid.uuid4())[:8]
    payload = {
        "email": f"new_bidder_{uid}@company.com",
        "password": "StrongPassword123",
        "full_name": "Ramesh Gupta",
        "company_name": f"Gupta Infra {uid} Ltd",
        "pan": f"ZZZZZ{int(uid, 16) % 10000:04d}Z"
    }

    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json()

    assert "access_token" in data
    assert data["user"]["role"] == "BIDDER"
    assert data["user"]["email"] == payload["email"].lower()

    # Verify DB state
    created_user = db.query(User).filter(User.email == payload["email"].lower()).first()
    assert created_user is not None
    assert created_user.role == "BIDDER"
    assert created_user.vendor_id is not None

    created_vendor = db.query(Vendor).filter(Vendor.id == created_user.vendor_id).first()
    assert created_vendor is not None
    assert created_vendor.name == payload["company_name"]


def test_bidder_registration_role_escalation_blocked(db: Session):
    uid = str(uuid.uuid4())[:8]
    # Attempt to pass role=ADMIN or vendor_id in body
    payload = {
        "email": f"hacker_{uid}@test.com",
        "password": "StrongPassword123",
        "full_name": "Malicious User",
        "company_name": "Fake Corp",
        "role": "ADMIN",
        "vendor_id": "malicious-vendor-id"
    }

    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json()

    # Role must strictly be BIDDER, never ADMIN
    assert data["user"]["role"] == "BIDDER"
    created_user = db.query(User).filter(User.email == payload["email"]).first()
    assert created_user.role == "BIDDER"
    assert created_user.vendor_id != "malicious-vendor-id"


def test_bidder_registration_duplicate_prevention(db: Session):
    uid = str(uuid.uuid4())[:8]
    pan = f"YYYYY{int(uid, 16) % 10000:04d}Y"
    payload = {
        "email": f"orig_{uid}@test.com",
        "password": "StrongPassword123",
        "full_name": "Original User",
        "company_name": "Original Corp",
        "pan": pan
    }
    r1 = client.post("/api/auth/register", json=payload)
    assert r1.status_code == 201

    # Duplicate email -> 400
    dup_email_payload = {**payload, "company_name": "Another Corp", "pan": "AAAPA1234A"}
    r2 = client.post("/api/auth/register", json=dup_email_payload)
    assert r2.status_code == 400
    assert "Email already registered" in r2.json()["detail"]

    # Duplicate PAN -> 400
    dup_pan_payload = {**payload, "email": f"different_{uid}@test.com"}
    r3 = client.post("/api/auth/register", json=dup_pan_payload)
    assert r3.status_code == 400
    assert "PAN already registered" in r3.json()["detail"]


# ===================================================================== #
# 4. DOCUMENT VIEWER & PDF SECURITY REGRESSION TESTS                    #
# ===================================================================== #

def test_document_viewer_pdf_security_and_magic_bytes(db: Session, tmp_path, monkeypatch):
    uid = str(uuid.uuid4())[:8]
    vendor_a = Vendor(name=f"Vendor A {uid}")
    vendor_b = Vendor(name=f"Vendor B {uid}")
    db.add_all([vendor_a, vendor_b])
    db.commit()

    bidder_a = User(email=f"bidder_a_{uid}@test.com", hashed_password="pwd", full_name="Bidder A", role="BIDDER", vendor_id=vendor_a.id)
    bidder_b = User(email=f"bidder_b_{uid}@test.com", hashed_password="pwd", full_name="Bidder B", role="BIDDER", vendor_id=vendor_b.id)
    officer = User(email=f"officer_{uid}@test.com", hashed_password="pwd", full_name="Officer", role="PROCUREMENT_OFFICER")
    db.add_all([bidder_a, bidder_b, officer])
    db.commit()

    tender = Tender(title=f"Tender {uid}", tender_id=f"T-{uid}", department="CPCL", category="Machinery", bid_deadline="2026-12-31", estimated_value=200000.0)
    db.add(tender)
    db.commit()

    bid_a = Bid(bid_id=f"BIDA-{uid}", tender_id=tender.id, vendor_id=vendor_a.id, category="Machinery", bid_amount="₹1,20,000")
    db.add(bid_a)
    db.commit()

    # 1. Create a genuine PDF file
    genuine_pdf_path = str(tmp_path / f"genuine_{uid}.pdf")
    with open(genuine_pdf_path, "wb") as f:
        f.write(b"%PDF-1.4 genuine content for testing")

    doc_genuine = Document(
        bid_id=bid_a.id,
        document_type="PAN",
        filename="PAN_Certificate.pdf",
        file_path=genuine_pdf_path,
        file_hash="hash_genuine",
        document_status="VERIFIED"
    )
    db.add(doc_genuine)

    # 2. Create a fake file claiming to be PDF (missing %PDF-)
    fake_pdf_path = str(tmp_path / f"fake_{uid}.pdf")
    with open(fake_pdf_path, "wb") as f:
        f.write(b"NOT_A_PDF_CONTENT_MALICIOUS_EXE")

    doc_fake = Document(
        bid_id=bid_a.id,
        document_type="GST",
        filename="Fake_GST.pdf",
        file_path=fake_pdf_path,
        file_hash="hash_fake",
        document_status="VERIFIED"
    )
    db.add(doc_fake)
    db.commit()
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))

    token_a = create_access_token(subject=bidder_a.id)
    token_b = create_access_token(subject=bidder_b.id)
    token_off = create_access_token(subject=officer.id)

    # A) Unauthenticated -> 401
    res_unauth = client.get(f"/api/bids/documents/{doc_genuine.id}/view")
    assert res_unauth.status_code == 401

    # B) Valid PDF must be tested separately and must return HTTP 200.
    # A 400 response is not a successful viewer test; malformed/fake PDFs are a separate security check.
    res_own = client.get(f"/api/bids/documents/{doc_genuine.id}/view", headers={"Authorization": f"Bearer {token_a}"})
    assert res_own.status_code == 200
    assert "application/pdf" in res_own.headers["content-type"]
    assert "inline" in res_own.headers["content-disposition"]
    assert res_own.content.startswith(b"%PDF-")

    # C) Bidder B accesses Bidder A's document -> 403 Forbidden (RBAC / IDOR protection)
    res_cross = client.get(f"/api/bids/documents/{doc_genuine.id}/view", headers={"Authorization": f"Bearer {token_b}"})
    assert res_cross.status_code == 403

    # D) Officer accesses Bidder A's genuine PDF -> 200 (Officer authorized)
    res_off = client.get(f"/api/bids/documents/{doc_genuine.id}/view", headers={"Authorization": f"Bearer {token_off}"})
    assert res_off.status_code == 200

    # E) Accessing fake PDF (without %PDF- magic bytes) -> 400 Bad Request
    res_fake = client.get(f"/api/bids/documents/{doc_fake.id}/view", headers={"Authorization": f"Bearer {token_a}"})
    assert res_fake.status_code == 400
    assert "Missing %PDF- signature" in res_fake.json()["detail"]


def test_document_missing_file_and_traversal_are_handled_gracefully(db: Session, tmp_path, monkeypatch):
    uid = str(uuid.uuid4())[:8]
    vendor = Vendor(name=f"Vendor {uid}")
    bidder = User(email=f"bidder_{uid}@test.com", hashed_password="pwd", full_name="Bidder", role="BIDDER", vendor_id=vendor.id)
    db.add_all([vendor, bidder])
    db.commit()

    tender = Tender(title=f"Tender {uid}", tender_id=f"T-{uid}", department="CPCL", category="Machinery", bid_deadline="2026-12-31", estimated_value=200000.0)
    db.add(tender)
    db.commit()

    bid = Bid(bid_id=f"BID-{uid}", tender_id=tender.id, vendor_id=vendor.id, category="Machinery", bid_amount="₹1,20,000")
    db.add(bid)
    db.commit()

    valid_pdf = tmp_path / "valid.pdf"
    valid_pdf.write_bytes(b"%PDF-1.4\nvalid content")
    doc = Document(
        bid_id=bid.id,
        document_type="PAN",
        filename="valid.pdf",
        file_path=str(valid_pdf),
        file_hash="hash_valid",
        document_status="VERIFIED"
    )
    db.add(doc)
    db.commit()

    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    token = create_access_token(subject=bidder.id)
    headers = {"Authorization": f"Bearer {token}"}

    missing_doc = Document(
        bid_id=bid.id,
        document_type="GST",
        filename="missing.pdf",
        file_path=str(tmp_path / "nope.pdf"),
        file_hash="hash_missing",
        document_status="MISSING"
    )
    db.add(missing_doc)
    db.commit()

    missing_res = client.get(f"/api/bids/documents/{missing_doc.id}/view", headers=headers)
    assert missing_res.status_code == 404
    assert "Document unavailable" in missing_res.json()["detail"]

    traversal_doc = Document(
        bid_id=bid.id,
        document_type="GST",
        filename="traversal.pdf",
        file_path="../../outside/evil.pdf",
        file_hash="hash_traversal",
        document_status="VERIFIED"
    )
    db.add(traversal_doc)
    db.commit()

    traversal_res = client.get(f"/api/bids/documents/{traversal_doc.id}/view", headers=headers)
    assert traversal_res.status_code in {403, 404}
    assert "Document unavailable" in traversal_res.json()["detail"] or "not allowed" in traversal_res.json()["detail"].lower()
