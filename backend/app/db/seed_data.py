import os
import hashlib
from pathlib import Path
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine, Base
from app.models.models import (
    User, Tender, TenderRequirement, Vendor, Bid, Document, ExtractedField,
    Verification, RuleResult, CrossCheck, RiskAssessment, AuditEvent, DebarmentRecord
)
from app.core.security import get_password_hash
from app.core.tender_rules import MIN_TENDER_VALUE_INR
from app.services.audit.audit_logger import AuditLogger

# Determine the project root (2 levels up from this file: app/db -> app -> backend)
# UPLOAD_DIR matches config.py: ../../../uploads relative to app/core/config.py
# = project root / uploads (one level above backend)
_BACKEND_DIR = Path(__file__).resolve().parents[2]
_PROJECT_ROOT = _BACKEND_DIR.parent
_UPLOAD_DIR = _PROJECT_ROOT / "uploads"


def _make_valid_pdf(doc_type: str, vendor_name: str, gstin: str = "", pan: str = "", udyam: str = "") -> bytes:
    """Generate a minimal but genuinely valid PDF-1.4 that Chrome/Edge can render."""
    title = f"{doc_type} Certificate - {vendor_name}"
    body_lines = [
        f"Document Type: {doc_type}",
        f"Vendor / Enterprise Name: {vendor_name}",
    ]
    if gstin:
        body_lines.append(f"GSTIN: {gstin}")
    if pan:
        body_lines.append(f"PAN: {pan}")
    if udyam:
        body_lines.append(f"Udyam Registration No.: {udyam}")
    body_lines += [
        "Status: ACTIVE",
        "Issued by: Government of India (Simulated - SIH 2026 Prototype)",
        "This document is a synthetic demo asset for the BharatSetu platform.",
    ]

    # Build PDF stream content (plain text page)
    stream_lines = ["BT", "/F1 12 Tf", "50 780 Td", f"({title}) Tj"]
    y = 755
    for line in body_lines:
        y_offset = 760 - y
        stream_lines.append(f"0 -{y_offset} Td")
        safe_line = line.replace("(", "\\(").replace(")", "\\)")
        stream_lines.append(f"({safe_line}) Tj")
        y -= 20
    stream_lines.append("ET")
    stream_content = "\n".join(stream_lines)
    stream_bytes = stream_content.encode("latin-1")
    stream_len = len(stream_bytes)

    pdf = b""
    pdf += b"%PDF-1.4\n"
    offsets = []

    # Object 1: Catalog
    offsets.append(len(pdf))
    pdf += b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"

    # Object 2: Pages
    offsets.append(len(pdf))
    pdf += b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"

    # Object 3: Page
    offsets.append(len(pdf))
    pdf += b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]\n   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"

    # Object 4: Content stream
    offsets.append(len(pdf))
    pdf += (
        b"4 0 obj\n<< /Length " + str(stream_len).encode() + b" >>\nstream\n"
        + stream_bytes
        + b"\nendstream\nendobj\n"
    )

    # Object 5: Font
    offsets.append(len(pdf))
    pdf += b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"

    # Cross-reference table
    xref_offset = len(pdf)
    pdf += b"xref\n0 6\n"
    pdf += b"0000000000 65535 f \n"
    for off in offsets:
        pdf += f"{off:010d} 00000 n \n".encode()
    pdf += b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n"
    pdf += str(xref_offset).encode() + b"\n%%EOF\n"
    return pdf


def seed_db():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    # ------------------------------------------------------------------ #
    # USERS                                                                #
    # ------------------------------------------------------------------ #
    officer_user = db.query(User).filter(User.email == "officer@bharatsetu.gov.in").first()
    if not officer_user:
        officer_user = User(
            email="officer@bharatsetu.gov.in",
            hashed_password=get_password_hash("officer123"),
            full_name="Anil Kumar",
            role="PROCUREMENT_OFFICER",
            department="CPCL Industrial Procurement Wing"
        )
        db.add(officer_user)
    else:
        officer_user.hashed_password = get_password_hash("officer123")

    admin_user = db.query(User).filter(User.email == "admin@bharatsetu.gov.in").first()
    if not admin_user:
        admin_user = User(
            email="admin@bharatsetu.gov.in",
            hashed_password=get_password_hash("admin123"),
            full_name="S. Meena",
            role="ADMIN",
            department="CPCL IT Operations"
        )
        db.add(admin_user)
    else:
        admin_user.hashed_password = get_password_hash("admin123")

    db.commit()

    # ------------------------------------------------------------------ #
    # VENDORS                                                              #
    # ------------------------------------------------------------------ #
    vendor_a = db.query(Vendor).filter(Vendor.name == "TechCorp India Pvt Ltd").first()
    if not vendor_a:
        vendor_a = Vendor(
            name="TechCorp India Pvt Ltd",
            gstin="27ABCDE1234F1Z5",
            pan="ABCDE1234F",
            udyam="UDYAM-MH-00-1234567",
            epfo_code="MH/MUM/0012345",
            address="Plot 14, MIDC Industrial Area, Andheri East, Mumbai, Maharashtra"
        )
        db.add(vendor_a)
        db.commit()
        db.refresh(vendor_a)

    vendor_b = db.query(Vendor).filter(Vendor.name == "Global Heavy Industries").first()
    if not vendor_b:
        vendor_b = Vendor(
            name="Global Heavy Industries",
            gstin="33VWXYZ5678G2ZP",
            pan="VWXYZ5678G",
            udyam="UDYAM-DL-11-7654321",
            epfo_code="DL/DEL/0076543",
            address="B-42, Okhla Industrial Estate, New Delhi"
        )
        db.add(vendor_b)
        db.commit()
        db.refresh(vendor_b)

    # ------------------------------------------------------------------ #
    # BIDDERS                                                              #
    # ------------------------------------------------------------------ #
    bidder_a = db.query(User).filter(User.email == "biddera@bharatsetu.gov.in").first()
    if not bidder_a:
        bidder_a = User(
            email="biddera@bharatsetu.gov.in",
            hashed_password=get_password_hash("bidder123"),
            full_name="TechCorp India Pvt Ltd",
            role="BIDDER",
            department="Vendor",
            vendor_id=vendor_a.id
        )
        db.add(bidder_a)
    else:
        bidder_a.hashed_password = get_password_hash("bidder123")
        bidder_a.vendor_id = vendor_a.id

    bidder_b = db.query(User).filter(User.email == "bidderb@bharatsetu.gov.in").first()
    if not bidder_b:
        bidder_b = User(
            email="bidderb@bharatsetu.gov.in",
            hashed_password=get_password_hash("bidder123"),
            full_name="Global Heavy Industries",
            role="BIDDER",
            department="Vendor",
            vendor_id=vendor_b.id
        )
        db.add(bidder_b)
    else:
        bidder_b.hashed_password = get_password_hash("bidder123")
        bidder_b.vendor_id = vendor_b.id
    db.commit()

    # Default demo Bidder - Rajesh Verma (maps to TechCorp India Pvt Ltd)
    bidder_default = db.query(User).filter(User.email == "bidder@bharatsetu.gov.in").first()
    if not bidder_default:
        bidder_default = User(
            email="bidder@bharatsetu.gov.in",
            hashed_password=get_password_hash("bidder123"),
            full_name="Rajesh Verma",
            role="BIDDER",
            department="Verma Industries",
            vendor_id=vendor_a.id
        )
        db.add(bidder_default)
    else:
        bidder_default.hashed_password = get_password_hash("bidder123")
        bidder_default.vendor_id = vendor_a.id
        bidder_default.full_name = "Rajesh Verma"
        bidder_default.department = "Verma Industries"

    db.commit()

    # ------------------------------------------------------------------ #
    # TENDERS                                                              #
    # ------------------------------------------------------------------ #
    tender1 = db.query(Tender).filter(Tender.tender_id == "CPCL-2026-IND-09").first()
    if not tender1:
        tender1 = Tender(
            tender_id="CPCL-2026-IND-09",
            title="Procurement of Industrial Machinery & Heavy Pressure Valves",
            department="Chennai Petroleum Corporation Limited (CPCL)",
            category="Industrial Machinery",
            bid_deadline="2026-09-30",
            minimum_turnover_inr=50000000.0,
            minimum_experience_years=3,
            msme_exemption_allowed=True,
            startup_exemption_allowed=True,
            local_content_percentage=50.0,
            estimated_value=48275000.0
        )
        db.add(tender1)
        db.commit()

        reqs = [
            TenderRequirement(tender_id=tender1.id, document_type="GST", is_mandatory=True, description="Active GSTIN Registration Certificate"),
            TenderRequirement(tender_id=tender1.id, document_type="PAN", is_mandatory=True, description="PAN Card matching Entity Name"),
            TenderRequirement(tender_id=tender1.id, document_type="UDYAM", is_mandatory=True, description="Udyam MSME Registration Certificate"),
            TenderRequirement(tender_id=tender1.id, document_type="EPFO", is_mandatory=True, description="EPFO Establishment Registration"),
            TenderRequirement(tender_id=tender1.id, document_type="FINANCIAL", is_mandatory=True, description="Audited Financial Statements (Min Turnover Rs.5 Cr)"),
            TenderRequirement(tender_id=tender1.id, document_type="EXPERIENCE", is_mandatory=True, description="Past Performance Certificate (3 Similar Works)"),
        ]
        db.add_all(reqs)
        db.commit()
    else:
        if tender1.estimated_value < MIN_TENDER_VALUE_INR:
            tender1.estimated_value = 48275000.0
            db.commit()
        db.refresh(tender1)

    tender2 = db.query(Tender).filter(Tender.tender_id == "CPCL-2026-IT-14").first()
    if not tender2:
        tender2 = Tender(
            tender_id="CPCL-2026-IT-14",
            title="Enterprise Cyber Security & Cloud Infrastructure Services",
            department="Chennai Petroleum Corporation Limited (CPCL)",
            category="Information Technology",
            bid_deadline="2026-10-15",
            minimum_turnover_inr=15000000.0,
            minimum_experience_years=2,
            msme_exemption_allowed=True,
            startup_exemption_allowed=True,
            local_content_percentage=60.0,
            estimated_value=12500000.0
        )
        db.add(tender2)
        db.commit()

        reqs2 = [
            TenderRequirement(tender_id=tender2.id, document_type="GST", is_mandatory=True, description="Active GSTIN Registration Certificate"),
            TenderRequirement(tender_id=tender2.id, document_type="PAN", is_mandatory=True, description="PAN Card matching Entity Name"),
            TenderRequirement(tender_id=tender2.id, document_type="UDYAM", is_mandatory=False, description="Udyam MSME Certificate (Optional for Startup)"),
            TenderRequirement(tender_id=tender2.id, document_type="ISO_27001", is_mandatory=True, description="ISO 27001 Information Security Certificate"),
        ]
        db.add_all(reqs2)
        db.commit()
    else:
        if tender2.estimated_value < MIN_TENDER_VALUE_INR:
            tender2.estimated_value = 12500000.0
            db.commit()
        db.refresh(tender2)

    if tender1 and tender1.status != "ACTIVE":
        tender1.status = "ACTIVE"
        db.commit()

    tender3 = db.query(Tender).filter(Tender.tender_id == "CPCL-2026-ENG-18").first()
    if not tender3:
        tender3 = Tender(
            tender_id="CPCL-2026-ENG-18",
            title="Refinery Mechanical Maintenance & Inspection Services",
            department="Chennai Petroleum Corporation Limited (CPCL)",
            category="Industrial Maintenance",
            bid_deadline="2026-11-05",
            minimum_turnover_inr=7500000.0,
            minimum_experience_years=5,
            msme_exemption_allowed=False,
            startup_exemption_allowed=True,
            local_content_percentage=55.0,
            estimated_value=1850000.0,
            status="ACTIVE"
        )
        db.add(tender3)
        db.commit()
        db.add_all([
            TenderRequirement(tender_id=tender3.id, document_type="GST", is_mandatory=True, description="Active GSTIN certificate"),
            TenderRequirement(tender_id=tender3.id, document_type="PAN", is_mandatory=True, description="PAN verification"),
            TenderRequirement(tender_id=tender3.id, document_type="FINANCIAL", is_mandatory=True, description="Audited financials"),
            TenderRequirement(tender_id=tender3.id, document_type="EXPERIENCE", is_mandatory=True, description="Maintenance experience proof"),
        ])
        db.commit()

    tender4 = db.query(Tender).filter(Tender.tender_id == "CPCL-2026-IT-27").first()
    if not tender4:
        tender4 = Tender(
            tender_id="CPCL-2026-IT-27",
            title="Data Centre Networking and Endpoint Security Support",
            department="Chennai Petroleum Corporation Limited (CPCL)",
            category="Information Technology",
            bid_deadline="2026-11-20",
            minimum_turnover_inr=5000000.0,
            minimum_experience_years=3,
            msme_exemption_allowed=True,
            startup_exemption_allowed=True,
            local_content_percentage=60.0,
            estimated_value=2400000.0,
            status="ACTIVE"
        )
        db.add(tender4)
        db.commit()
        db.add_all([
            TenderRequirement(tender_id=tender4.id, document_type="GST", is_mandatory=True, description="Active GSTIN certificate"),
            TenderRequirement(tender_id=tender4.id, document_type="PAN", is_mandatory=True, description="PAN verification"),
            TenderRequirement(tender_id=tender4.id, document_type="ISO_27001", is_mandatory=True, description="ISO 27001 certificate"),
            TenderRequirement(tender_id=tender4.id, document_type="UDYAM", is_mandatory=False, description="Optional MSME certificate"),
        ])
        db.commit()

    # ------------------------------------------------------------------ #
    # DEMO BID - TechCorp India Pvt Ltd (vendor_a / bidder_default)       #
    # Created on normal startup so Officer dashboard is never empty.       #
    # ------------------------------------------------------------------ #
    demo_bid_code = "GEM-2026-DEMO-01"
    demo_bid = db.query(Bid).filter(Bid.bid_id == demo_bid_code).first()
    if not demo_bid:
        demo_bid = Bid(
            bid_id=demo_bid_code,
            tender_id=tender1.id,
            vendor_id=vendor_a.id,
            category="Industrial Machinery",
            bid_amount="48275000",
            status="PENDING_REVIEW",
            risk_level="LOW",
            risk_score=18,
            compliance_score=92.0,
            ai_confidence=94,
            ai_recommendation="APPROVE",
            ai_summary=(
                "TechCorp India Pvt Ltd demonstrates strong compliance across all four "
                "mandatory document categories. GST, PAN, UDYAM and EPFO records are "
                "verified against government sources. No debarment record found. "
                "Address and name cross-checks passed. Recommended for approval."
            )
        )
        db.add(demo_bid)
        db.commit()
        db.refresh(demo_bid)

        # Generate valid synthetic PDF files for all 4 doc types
        _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        doc_specs = [
            ("GST",   f"{demo_bid_code}_GST_Certificate.pdf",   vendor_a.gstin, "", ""),
            ("PAN",   f"{demo_bid_code}_PAN_Card.pdf",           "", vendor_a.pan, ""),
            ("UDYAM", f"{demo_bid_code}_UDYAM_Certificate.pdf",  "", "", vendor_a.udyam),
            ("EPFO",  f"{demo_bid_code}_EPFO_Registration.pdf",  vendor_a.epfo_code or "", "", ""),
        ]
        doc_ids = {}
        for doc_type, filename, gstin_v, pan_v, udyam_v in doc_specs:
            pdf_path = _UPLOAD_DIR / filename
            pdf_bytes = _make_valid_pdf(doc_type, vendor_a.name, gstin_v, pan_v, udyam_v)
            pdf_path.write_bytes(pdf_bytes)
            sha = hashlib.sha256(pdf_bytes).hexdigest()

            doc = Document(
                bid_id=demo_bid.id,
                document_type=doc_type,
                filename=filename,
                file_path=str(pdf_path),
                file_hash=sha,
                extracted_text=f"{doc_type} Certificate for {vendor_a.name}",
                ocr_confidence=95.0,
                document_status="VERIFIED",
                verification_status="COMPLETED",
                source="Mock Government API",
                detail=f"Verified via simulated government {doc_type} verification provider."
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            doc_ids[doc_type] = doc.id

        # Create Verification records linked to those Documents
        ver_specs = [
            ("GST",   True, "GSTIN_VERIFIED",  "Mock GST Portal",   "GSTIN 22AAAAA0000A1Z5 active; legal name matches."),
            ("PAN",   True, "PAN_VERIFIED",    "Mock NSDL PAN",     "PAN ABCDE1234F valid; entity name matches."),
            ("UDYAM", True, "UDYAM_VERIFIED",  "Mock Udyam Portal", "UDYAM-MH-00-1234567 registration active."),
            ("EPFO",  True, "EPFO_VERIFIED",   "Mock EPFO Portal",  "EPFO establishment code MH/MUM/0012345 found."),
        ]
        for doc_type, verified, status, source, detail in ver_specs:
            v = Verification(
                bid_id=demo_bid.id,
                document_id=doc_ids[doc_type],
                document_type=doc_type,
                source=source,
                is_simulated=True,
                verified=verified,
                status=status,
                reference_id=f"SIM-{doc_type}-001",
                raw_response={"verified": verified, "status": status, "detail": detail, "source": source}
            )
            db.add(v)

        # Debarment check (no document)
        v_debar = Verification(
            bid_id=demo_bid.id,
            document_id=None,
            document_type="DEBARMENT",
            source="Mock CVC Debarment List",
            is_simulated=True,
            verified=True,
            status="CLEAR",
            reference_id="SIM-DEBAR-001",
            raw_response={"verified": True, "status": "CLEAR", "detail": "No debarment record found.", "source": "Mock CVC"}
        )
        db.add(v_debar)
        db.commit()

        AuditLogger.log_event(
            db, "BID_SEEDED", "Seed Engine",
            f"Demo bid {demo_bid_code} created with 4 verified documents for SIH demo.",
            bid_id=demo_bid.id, vendor_name=vendor_a.name, status="pass"
        )

    # ------------------------------------------------------------------ #
    # AUTO-HEAL: regenerate any referenced PDF that is missing on disk    #
    # ------------------------------------------------------------------ #
    for doc in db.query(Document).all():
        if not doc.file_path or doc.file_path == "dummy":
            continue

        original_path = Path(doc.file_path)
        # Keep seeded files inside the project upload directory. This also
        # repairs absolute paths persisted by an earlier machine or checkout.
        if original_path.is_absolute() and _UPLOAD_DIR not in original_path.parents:
            p = _UPLOAD_DIR / Path(doc.filename).name
            doc.file_path = str(p)
        elif original_path.is_absolute():
            p = original_path
        else:
            p = _BACKEND_DIR / original_path

        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            vendor_name_for_pdf = "Unknown Vendor"
            if doc.bid and doc.bid.vendor:
                vendor_name_for_pdf = doc.bid.vendor.name
            p.write_bytes(_make_valid_pdf(doc.document_type, vendor_name_for_pdf))

    db.commit()

    db.close()


if __name__ == "__main__":
    seed_db()
