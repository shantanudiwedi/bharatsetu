import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.db.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="PROCUREMENT_OFFICER") # ADMIN, PROCUREMENT_OFFICER, REVIEWER, AUDITOR, BIDDER
    department = Column(String, default="CPCL Procurement Division")
    is_active = Column(Boolean, default=True)
    vendor_id = Column(String, ForeignKey("vendors.id"), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    
    vendor = relationship("Vendor")

class Tender(Base):
    __tablename__ = "tenders"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    tender_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    department = Column(String, nullable=False)
    category = Column(String, nullable=False)
    bid_deadline = Column(String, nullable=False)
    minimum_turnover_inr = Column(Float, default=0.0)
    minimum_experience_years = Column(Integer, default=0)
    msme_exemption_allowed = Column(Boolean, default=True)
    startup_exemption_allowed = Column(Boolean, default=True)
    local_content_percentage = Column(Float, default=50.0)
    estimated_value = Column(Float, default=0.0, nullable=False)
    status = Column(String, default="ACTIVE") # ACTIVE, CLOSED, CANCELLED
    created_at = Column(DateTime, default=utc_now)

    def __init__(self, **kwargs):
        if "estimated_value" not in kwargs:
            kwargs["estimated_value"] = 250000.0
        super().__init__(**kwargs)

    requirements = relationship("TenderRequirement", back_populates="tender", cascade="all, delete-orphan")
    bids = relationship("Bid", back_populates="tender")

class TenderRequirement(Base):
    __tablename__ = "tender_requirements"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    tender_id = Column(String, ForeignKey("tenders.id"), nullable=False)
    document_type = Column(String, nullable=False)
    is_mandatory = Column(Boolean, default=True)
    description = Column(String, nullable=True)
    validation_rule_json = Column(JSON, nullable=True)
    
    tender = relationship("Tender", back_populates="requirements")

class Vendor(Base):
    __tablename__ = "vendors"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, index=True, nullable=False)
    gstin = Column(String, index=True, nullable=True)
    pan = Column(String, index=True, nullable=True)
    cin = Column(String, index=True, nullable=True)
    udyam = Column(String, index=True, nullable=True)
    epfo_code = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    bids = relationship("Bid", back_populates="vendor")

class Bid(Base):
    __tablename__ = "bids"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    bid_id = Column(String, unique=True, index=True, nullable=False) # GEM-2026-xxxxx
    tender_id = Column(String, ForeignKey("tenders.id"), nullable=False)
    vendor_id = Column(String, ForeignKey("vendors.id"), nullable=False)
    category = Column(String, nullable=False)
    bid_amount = Column(String, nullable=False)
    submitted_at = Column(DateTime, default=utc_now)
    
    status = Column(String, default="PENDING_REVIEW") # DRAFT, PROCESSING, PENDING_REVIEW, APPROVED, REJECTED, ESCALATED
    risk_level = Column(String, default="MEDIUM") # LOW, MEDIUM, HIGH
    risk_score = Column(Integer, default=50) # 0-100
    compliance_score = Column(Float, default=0.0) # 0-100 %
    ai_confidence = Column(Integer, default=85)
    ai_recommendation = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    tender = relationship("Tender", back_populates="bids")
    vendor = relationship("Vendor", back_populates="bids")
    documents = relationship("Document", back_populates="bid", cascade="all, delete-orphan")
    verifications = relationship("Verification", back_populates="bid", cascade="all, delete-orphan")
    rule_results = relationship("RuleResult", back_populates="bid", cascade="all, delete-orphan")
    cross_checks = relationship("CrossCheck", back_populates="bid", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="bid", cascade="all, delete-orphan")
    review_decisions = relationship("ReviewDecision", back_populates="bid", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    bid_id = Column(String, ForeignKey("bids.id"), nullable=False)
    document_type = Column(String, nullable=False) # GST, PAN, UDYAM, EPFO, ESIC, MCA, FINANCIAL, WORK_EXPERIENCE, DEBARMENT, etc.
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_hash = Column(String, index=True, nullable=False) # SHA-256
    upload_timestamp = Column(DateTime, default=utc_now)
    
    extracted_text = Column(Text, nullable=True)
    ocr_confidence = Column(Float, default=95.0)
    document_status = Column(String, default="UPLOADED") # UPLOADED, PROCESSING, VERIFIED, FAILED, EXPIRED, MISSING, WARNING
    verification_status = Column(String, default="PENDING")
    detail = Column(Text, nullable=True)
    source = Column(String, nullable=True)

    bid = relationship("Bid", back_populates="documents")
    extracted_fields = relationship("ExtractedField", back_populates="document", cascade="all, delete-orphan")
    verifications = relationship("Verification", back_populates="document", cascade="all, delete-orphan")

class ExtractedField(Base):
    __tablename__ = "extracted_fields"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    field_name = Column(String, nullable=False)
    field_value = Column(String, nullable=True)
    confidence = Column(Float, default=90.0)
    validation_status = Column(String, default="VALID") # VALID, INVALID, UNCERTAIN

    document = relationship("Document", back_populates="extracted_fields")

class Verification(Base):
    __tablename__ = "verifications"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    bid_id = Column(String, ForeignKey("bids.id"), nullable=False)
    document_id = Column(String, ForeignKey("documents.id"), nullable=True)
    document_type = Column(String, nullable=False)
    source = Column(String, nullable=False) # GSTN_MOCK, UDYAM_MOCK, NSDL_MOCK, EPFO_MOCK, etc.
    is_simulated = Column(Boolean, default=True)
    # provider_mode: REAL | DEMO | MOCK | UNAVAILABLE
    # REAL = live government API (not yet connected)
    # DEMO = curated demo dataset (scripted known outcomes)
    # MOCK = simulated response for any input
    # UNAVAILABLE = provider temporarily not reachable
    provider_mode = Column(String, default="MOCK", nullable=False)
    verified = Column(Boolean, default=False)
    status = Column(String, nullable=False) # ACTIVE, CANCELLED, MATCH, MISMATCH, NOT_FOUND
    reference_id = Column(String, nullable=True)
    raw_response = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=utc_now)

    bid = relationship("Bid", back_populates="verifications")
    document = relationship("Document", back_populates="verifications")


class ComplianceRule(Base):
    __tablename__ = "compliance_rules"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    rule_id = Column(String, unique=True, nullable=False) # GST_ACTIVE, PAN_VALID, etc.
    document_type = Column(String, nullable=False)
    description = Column(String, nullable=False)
    condition = Column(String, nullable=False)
    severity = Column(String, default="HIGH") # LOW, MEDIUM, HIGH, CRITICAL

class RuleResult(Base):
    __tablename__ = "rule_results"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    bid_id = Column(String, ForeignKey("bids.id"), nullable=False)
    verification_id = Column(String, ForeignKey("verifications.id"), nullable=True)
    rule_id = Column(String, nullable=False)
    document_type = Column(String, nullable=False)
    result = Column(String, nullable=False) # PASS, FAIL, WARNING, NOT_APPLICABLE, PENDING
    finding = Column(Text, nullable=True)
    impact = Column(String, default="HIGH")
    recommended_action = Column(Text, nullable=True)

    bid = relationship("Bid", back_populates="rule_results")

class CrossCheck(Base):
    __tablename__ = "cross_checks"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    bid_id = Column(String, ForeignKey("bids.id"), nullable=False)
    check_type = Column(String, nullable=False) # NAME_MATCH, ADDRESS_MATCH, GSTIN_MATCH, PAN_MATCH
    field_a = Column(String, nullable=False)
    value_a = Column(String, nullable=True)
    field_b = Column(String, nullable=False)
    value_b = Column(String, nullable=True)
    match_score = Column(Float, default=100.0) # 0-100%
    status = Column(String, default="MATCH") # MATCH, POTENTIAL_MISMATCH, MISMATCH
    explanation = Column(Text, nullable=True)

    bid = relationship("Bid", back_populates="cross_checks")

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    bid_id = Column(String, nullable=False)
    risk_score = Column(Integer, nullable=False) # 0-100
    risk_level = Column(String, nullable=False) # LOW, MEDIUM, HIGH
    compliance_score = Column(Float, nullable=False)
    risk_factors = Column(JSON, nullable=False) # List of strings
    calculated_at = Column(DateTime, default=utc_now)

class AuditEvent(Base):
    __tablename__ = "audit_events"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    bid_id = Column(String, ForeignKey("bids.id"), nullable=True)
    user_id = Column(String, nullable=True)
    event_type = Column(String, nullable=False) # BID_CREATED, DOCUMENT_UPLOADED, OCR_COMPLETED, etc.
    source = Column(String, nullable=False)
    action_label = Column(String, nullable=False)
    vendor_name = Column(String, nullable=True)
    status = Column(String, default="pass") # pass, fail, checking
    timestamp = Column(DateTime, default=utc_now)
    details_json = Column(JSON, nullable=True)

    bid = relationship("Bid", back_populates="audit_events")

class ReviewDecision(Base):
    __tablename__ = "review_decisions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    bid_id = Column(String, ForeignKey("bids.id"), nullable=False)
    officer_id = Column(String, nullable=False)
    officer_name = Column(String, nullable=False)
    action = Column(String, nullable=False) # APPROVED, REJECTED, ESCALATED
    reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utc_now)

    bid = relationship("Bid", back_populates="review_decisions")

class DebarmentRecord(Base):
    __tablename__ = "debarment_records"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    vendor_name = Column(String, index=True, nullable=False)
    pan = Column(String, index=True, nullable=True)
    authority = Column(String, nullable=False) # CVC, GeM, CPCL, MoPNG
    status = Column(String, default="ACTIVE_DEBARMENT")
    start_date = Column(String, nullable=False)
    end_date = Column(String, nullable=False)
    reference_no = Column(String, nullable=False)
    reason = Column(Text, nullable=False)

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    notification_type = Column(String, default="INFO") # INFO, SUCCESS, WARNING, ERROR
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)
    related_entity_id = Column(String, nullable=True)

class SupportTicket(Base):
    __tablename__ = "support_tickets"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, default="OPEN") # OPEN, IN_PROGRESS, RESOLVED
    created_at = Column(DateTime, default=utc_now)
