from typing import List, Dict, Any
from fastapi import APIRouter

router = APIRouter(prefix="/verification", tags=["Government Providers"])

@router.get("/providers")
def list_verification_providers() -> List[Dict[str, Any]]:
    """
    Returns architecture specification of available government verification providers.
    Displays explicitly whether providers are running in SIMULATED or PRODUCTION mode.
    """
    return [
        {"name": "GSTN Provider", "source_api": "GST Portal / GSTN", "mode": "SIMULATED", "status": "ACTIVE"},
        {"name": "Udyam Provider", "source_api": "udyamregistration.gov.in", "mode": "SIMULATED", "status": "ACTIVE"},
        {"name": "NSDL PAN Provider", "source_api": "Income Tax e-Filing / NSDL", "mode": "SIMULATED", "status": "ACTIVE"},
        {"name": "EPFO Provider", "source_api": "EPFO Unified Portal", "mode": "SIMULATED", "status": "ACTIVE"},
        {"name": "ESIC Provider", "source_api": "ESIC Portal", "mode": "SIMULATED", "status": "ACTIVE"},
        {"name": "MCA21 Provider", "source_api": "Ministry of Corporate Affairs MCA21", "mode": "SIMULATED", "status": "ACTIVE"},
        {"name": "DPIIT Startup Provider", "source_api": "Startup India Portal", "mode": "SIMULATED", "status": "ACTIVE"},
        {"name": "DigiLocker Provider", "source_api": "DigiLocker API", "mode": "SIMULATED", "status": "ACTIVE"},
        {"name": "Debarment Registry Provider", "source_api": "CVC / GeM Debarred Vendor Registry", "mode": "SIMULATED", "status": "ACTIVE"}
    ]
