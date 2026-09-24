from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

# Auth
class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company_name: str
    gstin: Optional[str] = None
    pan: Optional[str] = None
    cin: Optional[str] = None
    udyam: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    department: str

# Tender
class TenderRequirementBase(BaseModel):
    document_type: str
    is_mandatory: bool = True
    description: Optional[str] = None

class TenderCreate(BaseModel):
    tender_id: str
    title: str
    department: str
    category: str
    bid_deadline: str
    minimum_turnover_inr: float = 0.0
    minimum_experience_years: int = 0
    msme_exemption_allowed: bool = True
    startup_exemption_allowed: bool = True
    local_content_percentage: float = 50.0
    estimated_value: float = 0.0
    requirements: List[TenderRequirementBase] = []

class TenderDeadlineUpdate(BaseModel):
    bid_deadline: str

class TenderResponse(TenderCreate):
    id: str
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

# Vendor
class VendorCreate(BaseModel):
    name: str
    gstin: Optional[str] = None
    pan: Optional[str] = None
    cin: Optional[str] = None
    udyam: Optional[str] = None
    epfo_code: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None

class VendorResponse(VendorCreate):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True

# Documents
class DocCheckSchema(BaseModel):
    id: str
    name: str
    document_type: Optional[str] = None
    status: str # verified, failed, pending
    source: str
    detail: str

class ExtractedFieldSchema(BaseModel):
    field_name: str
    field_value: Optional[str]
    confidence: float
    validation_status: str

class DocumentResponse(BaseModel):
    id: str
    bid_id: str
    document_type: str
    filename: str
    file_hash: str
    upload_timestamp: datetime
    ocr_confidence: float
    document_status: str
    verification_status: str
    detail: Optional[str]
    source: Optional[str]
    extracted_text: Optional[str] = None
    extracted_fields: List[ExtractedFieldSchema] = []
    class Config:
        from_attributes = True

class DocumentListResponse(BaseModel):
    id: str
    bid_id: str
    bid_reference: str
    tender_id: str
    tender_title: str
    filename: str
    document_type: str
    upload_timestamp: datetime
    document_status: str
    verification_status: str
    verification_result: str
    extracted_fields_status: str
    detail: Optional[str] = None
    source: Optional[str] = None
    file_available: bool = False

# Verification & Compliance
class RuleResultSchema(BaseModel):
    rule_id: str
    document_type: str
    result: str
    finding: Optional[str]
    impact: str
    recommended_action: Optional[str]

class CrossCheckSchema(BaseModel):
    check_type: str
    field_a: str
    value_a: Optional[str]
    field_b: str
    value_b: Optional[str]
    match_score: float
    status: str
    explanation: Optional[str]

# Bid Response schema matching camelCase dictionary keys
class BidCreate(BaseModel):
    tender_id: str
    vendor_name: str
    vendor_id_code: Optional[str] = None
    category: str
    bid_amount: str
    gstin: Optional[str] = None
    pan: Optional[str] = None
    cin: Optional[str] = None
    udyam: Optional[str] = None

class AuditEntrySchema(BaseModel):
    id: Optional[str] = None
    source: str
    label: str
    vendor: Optional[str] = None
    status: str # pass, fail, checking
    timestamp: str
    action: Optional[str] = None

class BidResponse(BaseModel):
    id: str
    vendorName: str
    vendor_id_code: str
    category: str
    bidAmount: str
    submittedAt: str
    riskLevel: str
    risk_score: int
    compliance_score: float
    status: str
    aiConfidence: int
    aiRecommendation: Optional[str] = None
    aiSummary: Optional[str] = None
    documents: List[DocCheckSchema] = []
    audit_trail: List[AuditEntrySchema] = []
    officer: Optional[str] = None
    tender_title: Optional[str] = None
    requirements: List[TenderRequirementBase] = []

    class Config:
        from_attributes = True

# Review Decision
class ReviewDecisionCreate(BaseModel):
    action: str # APPROVE, REJECT, ESCALATE
    reason: Optional[str] = None

# Metrics & Dashboard
class DashboardMetricsResponse(BaseModel):
    pending_review_count: int
    approved_today_count: int
    avg_verification_time: str
    flagged_cases_count: int
    total_bids_count: int
    high_risk_count: int
    compliance_rate_percent: float
    risk_distribution: Dict[str, int]
    verification_status_distribution: Dict[str, int]

# Notifications
class NotificationSchema(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime
    related_entity_id: Optional[str] = None

    class Config:
        from_attributes = True

# Support
class SupportTicketCreate(BaseModel):
    subject: str
    description: str

class SupportTicketSchema(SupportTicketCreate):
    id: str
    user_id: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    reply: str
