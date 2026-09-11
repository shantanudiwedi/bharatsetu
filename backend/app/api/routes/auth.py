from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import User, Vendor
from app.schemas.schemas import LoginRequest, RegisterRequest, Token, UserResponse
from app.core.security import verify_password, get_password_hash, create_access_token, decode_token, oauth2_scheme, get_current_user
from app.services.validation.validators import validate_entity_name, validate_gstin, validate_pan, validate_udyam, validate_phone

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(subject=user.id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "department": user.department
        }
    }

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    # 1. Validate email
    normalized_email = payload.email.lower().strip()
    if not normalized_email:
        raise HTTPException(status_code=400, detail="Email is required")
        
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    try:
        company_name = validate_entity_name(payload.company_name)
        norm_pan = validate_pan(payload.pan) if payload.pan else None
        norm_gstin = validate_gstin(payload.gstin, norm_pan) if payload.gstin else None
        norm_udyam = validate_udyam(payload.udyam) if payload.udyam else None
        norm_phone = validate_phone(payload.contact_phone) if payload.contact_phone else None
    except ValueError as exc:
        message = str(exc)
        field = "company_name"
        if "PAN" in message:
            field = "pan"
        elif "GSTIN" in message:
            field = "gstin"
        elif "Udyam" in message:
            field = "udyam"
        elif "mobile" in message:
            field = "contact_phone"
        raise HTTPException(
            status_code=422,
            detail={"field": field, "code": "INVALID_INPUT", "message": message},
        )

    # 2. Validate password
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")

    # 3. Check duplicate PAN/GSTIN if supplied
    if norm_pan:
        existing_pan = db.query(Vendor).filter(Vendor.pan == norm_pan).first()
        if existing_pan:
            raise HTTPException(status_code=400, detail="Vendor with this PAN already registered")

    if norm_gstin:
        existing_gstin = db.query(Vendor).filter(Vendor.gstin == norm_gstin).first()
        if existing_gstin:
            raise HTTPException(status_code=400, detail="Vendor with this GSTIN already registered")

    # 4. Atomic transaction: create Vendor, then User with role='BIDDER'
    try:
        vendor = Vendor(
            name=company_name,
            gstin=norm_gstin,
            pan=norm_pan,
            cin=payload.cin.strip().upper() if payload.cin and payload.cin.strip() else None,
            udyam=norm_udyam,
            contact_email=normalized_email,
            contact_phone=norm_phone,
            address=payload.address.strip() if payload.address else None,
        )
        db.add(vendor)
        db.flush()  # obtain vendor.id

        # Server-enforced role=BIDDER. Client input cannot escalate role or assign vendor_id.
        user = User(
            email=normalized_email,
            hashed_password=get_password_hash(payload.password),
            full_name=payload.full_name.strip(),
            role="BIDDER",
            department="Vendor / Bidder Portal",
            vendor_id=vendor.id,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

    token = create_access_token(subject=user.id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "department": user.department
        }
    }

@router.get("/me", response_model=UserResponse)
def get_current_user_details(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
