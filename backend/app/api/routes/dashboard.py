from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import Bid
from app.schemas.schemas import DashboardMetricsResponse
from app.core.security import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard Metrics"])

@router.get("/metrics", response_model=DashboardMetricsResponse)
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(Bid)
    if current_user.role == "BIDDER":
        if not current_user.vendor_id:
            return {
                "pending_review_count": 0, "approved_today_count": 0,
                "avg_verification_time": "0 sec", "flagged_cases_count": 0,
                "total_bids_count": 0, "high_risk_count": 0,
                "compliance_rate_percent": 0.0, "risk_distribution": {"LOW": 0, "MEDIUM": 0, "HIGH": 0},
                "verification_status_distribution": {"APPROVED": 0, "PENDING_REVIEW": 0, "FLAGGED": 0, "REJECTED": 0}
            }
        query = query.filter(Bid.vendor_id == current_user.vendor_id)
        
    bids = query.all()

    pending_review = sum(1 for b in bids if b.status.upper() == "PENDING_REVIEW")
    approved_today = sum(1 for b in bids if b.status.upper() == "APPROVED")
    flagged_cases = sum(1 for b in bids if b.status.upper() == "FLAGGED")
    total_bids = len(bids)
    high_risk = sum(1 for b in bids if b.risk_level.upper() == "HIGH")

    compliance_rates = [b.compliance_score for b in bids if b.compliance_score > 0]
    avg_compliance = round(sum(compliance_rates) / len(compliance_rates), 1) if compliance_rates else 0.0

    risk_dist = {
        "LOW": sum(1 for b in bids if b.risk_level.upper() == "LOW"),
        "MEDIUM": sum(1 for b in bids if b.risk_level.upper() == "MEDIUM"),
        "HIGH": sum(1 for b in bids if b.risk_level.upper() == "HIGH")
    }

    status_dist = {
        "APPROVED": approved_today,
        "PENDING_REVIEW": pending_review,
        "FLAGGED": flagged_cases,
        "REJECTED": sum(1 for b in bids if b.status.upper() == "REJECTED")
    }

    return {
        "pending_review_count": pending_review,
        "approved_today_count": approved_today,
        "avg_verification_time": "42 sec",
        "flagged_cases_count": flagged_cases,
        "total_bids_count": total_bids,
        "high_risk_count": high_risk,
        "compliance_rate_percent": avg_compliance,
        "risk_distribution": risk_dist,
        "verification_status_distribution": status_dist
    }
