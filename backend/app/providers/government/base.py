from abc import ABC, abstractmethod
from typing import Dict, Any

# Provider mode constants — kept separate from verification_status.
# verification_status=VERIFIED + provider_mode=MOCK is a valid combination and must
# never be represented as live/authoritative government verification.
PROVIDER_MODE_REAL = "REAL"          # Live government API — not yet connected
PROVIDER_MODE_DEMO = "DEMO"          # Curated demo dataset with scripted known outcomes
PROVIDER_MODE_MOCK = "MOCK"          # Simulated response for any arbitrary input
PROVIDER_MODE_UNAVAILABLE = "UNAVAILABLE"  # Provider not reachable

class VerificationProvider(ABC):
    @abstractmethod
    def verify(self, identifier: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Executes verification against official government API portal or mock simulation.
        Returns structured verification dictionary with:
          - source: human-readable source name
          - is_simulated: bool (True for all mock providers)
          - provider_mode: REAL | DEMO | MOCK | UNAVAILABLE
          - verified: bool (True if verification passed)
          - status: categorical result string
          - detail: human-readable explanation
          - reference_id: simulated reference number
        """
        pass


class MockGSTProvider(VerificationProvider):
    def verify(self, gstin: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        metadata = metadata or {}
        gstin_clean = (gstin or "").upper().strip()
        vendor_name = (metadata.get("vendor_name") or "").upper()

        if "27AABCDE1234F1Z5" in gstin_clean or "SHREE LAKSHMI" in vendor_name:
            return {
                "source": "GST Network (GSTN Mock API)",
                "is_simulated": True,
                "provider_mode": PROVIDER_MODE_MOCK,
                "verified": False,
                "status": "ACTIVE_ADDRESS_MISMATCH",
                "legal_name": "Shree Lakshmi Industries Pvt Ltd",
                "registered_address": "Flat 402, Shivajinagar, Pune, Maharashtra - 411005",
                "detail": "Address mismatch: GST lists Pune, Udyam certificate lists Nagpur.",
                "reference_id": "GST-MOCK-2026-9941"
            }
        elif "08AABCV1234K1Z1" in gstin_clean or "VIDYA" in vendor_name:
            return {
                "source": "GST Network (GSTN Mock API)",
                "is_simulated": True,
                "provider_mode": PROVIDER_MODE_MOCK,
                "verified": False,
                "status": "CANCELLED",
                "legal_name": "Vidya Educational Supplies Co.",
                "registered_address": "MI Road, Jaipur, Rajasthan - 302001",
                "detail": "GSTIN cancelled effective July 2026 for non-filing of returns.",
                "reference_id": "GST-MOCK-2026-8812"
            }
        return {
            "source": "GST Network (GSTN Mock API)",
            "is_simulated": True,
            "provider_mode": PROVIDER_MODE_MOCK,
            "verified": True,
            "status": "ACTIVE",
            "legal_name": metadata.get("vendor_name", "Registered Entity"),
            "registered_address": metadata.get("address", "Registered Address"),
            "detail": "GSTIN active and verified in mock GSTN registry.",
            "reference_id": f"GST-MOCK-2026-{abs(hash(gstin_clean or 'gst')) % 10000}"
        }

class MockUdyamProvider(VerificationProvider):
    def verify(self, udyam_no: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        metadata = metadata or {}
        return {
            "source": "Udyam Registration Portal (MSME)",
            "is_simulated": True,
            "provider_mode": PROVIDER_MODE_MOCK,
            "verified": True,
            "status": "VALID",
            "enterprise_name": metadata.get("vendor_name", "Registered MSME"),
            "classification": "Micro / Small Enterprise",
            "detail": "Udyam registration active and valid. Category: Manufacturing.",
            "reference_id": f"UDYAM-MOCK-{abs(hash(udyam_no or 'udyam')) % 100000}"
        }

class MockPANProvider(VerificationProvider):
    def verify(self, pan: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        metadata = metadata or {}
        vendor_name = (metadata.get("vendor_name") or "").upper()
        if "NATIONAL STEEL" in vendor_name and "UNIT" in vendor_name:
            return {
                "source": "NSDL PAN Database (Mock API)",
                "is_simulated": True,
                "provider_mode": PROVIDER_MODE_MOCK,
                "verified": False,
                "status": "NAME_MISMATCH",
                "pan_holder_name": "NATIONAL STEEL FABRICATORS",
                "detail": "Name mismatch: PAN registered under 'National Steel Fabricators' but bid submitted as 'National Steel Fabricators Unit'.",
                "reference_id": "PAN-MOCK-2026-7721"
            }
        return {
            "source": "NSDL PAN Database (Mock API)",
            "is_simulated": True,
            "provider_mode": PROVIDER_MODE_MOCK,
            "verified": True,
            "status": "VERIFIED",
            "pan_holder_name": metadata.get("vendor_name", "Verified Entity"),
            "detail": "PAN matches entity legal registration records.",
            "reference_id": f"PAN-MOCK-2026-{abs(hash(pan or 'pan')) % 10000}"
        }

class MockEPFOProvider(VerificationProvider):
    def verify(self, code: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        metadata = metadata or {}
        vendor_name = (metadata.get("vendor_name") or "").upper()
        if "SHREE LAKSHMI" in vendor_name:
            return {
                "source": "EPFO Portal (Mock API)",
                "is_simulated": True,
                "provider_mode": PROVIDER_MODE_MOCK,
                "verified": False,
                "status": "NOT_FOUND",
                "detail": "Establishment code not found in EPFO database for this vendor.",
                "reference_id": "EPFO-MOCK-2026-9921"
            }
        elif "GREEN EARTH" in vendor_name:
            return {
                "source": "EPFO Portal (Mock API)",
                "is_simulated": True,
                "provider_mode": PROVIDER_MODE_MOCK,
                "verified": False,
                "status": "INACTIVE",
                "detail": "Establishment code marked inactive since June 2026.",
                "reference_id": "EPFO-MOCK-2026-4412"
            }
        return {
            "source": "EPFO Portal (Mock API)",
            "is_simulated": True,
            "provider_mode": PROVIDER_MODE_MOCK,
            "verified": True,
            "status": "ACTIVE",
            "detail": "Establishment code active. 38 active employees enrolled.",
            "reference_id": f"EPFO-MOCK-2026-{abs(hash(code or 'epf')) % 10000}"
        }

class MockESICProvider(VerificationProvider):
    def verify(self, code: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        return {
            "source": "ESIC Portal (Mock API)",
            "is_simulated": True,
            "provider_mode": PROVIDER_MODE_MOCK,
            "verified": True,
            "status": "ACTIVE",
            "detail": "ESI registration active and compliant.",
            "reference_id": f"ESIC-MOCK-2026-{abs(hash(code or 'esic')) % 10000}"
        }

class MockMCAProvider(VerificationProvider):
    def verify(self, cin: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        metadata = metadata or {}
        return {
            "source": "MCA21 Corporate Registry (Mock API)",
            "is_simulated": True,
            "provider_mode": PROVIDER_MODE_MOCK,
            "verified": True,
            "status": "ACTIVE",
            "company_name": metadata.get("vendor_name", "Incorporated Company"),
            "detail": "Certificate of Incorporation active in MCA database.",
            "reference_id": f"MCA-MOCK-2026-{abs(hash(cin or 'cin')) % 10000}"
        }

class MockStartupProvider(VerificationProvider):
    def verify(self, dipp_no: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        return {
            "source": "DPIIT Startup India Portal (Mock API)",
            "is_simulated": True,
            "provider_mode": PROVIDER_MODE_MOCK,
            "verified": True,
            "status": "RECOGNIZED",
            "detail": "DPIIT Startup recognition valid. Eligible for MSME/Startup exemptions.",
            "reference_id": f"DPIIT-MOCK-{abs(hash(dipp_no or 'dpiit')) % 10000}"
        }

class MockNSICProvider(VerificationProvider):
    def verify(self, cert_no: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        return {
            "source": "NSIC Portal (Mock API)",
            "is_simulated": True,
            "provider_mode": PROVIDER_MODE_MOCK,
            "verified": True,
            "status": "ACTIVE",
            "detail": "Single Point Registration Scheme (SPRS) active.",
            "reference_id": f"NSIC-MOCK-{abs(hash(cert_no or 'nsic')) % 10000}"
        }

class MockDigiLockerProvider(VerificationProvider):
    def verify(self, doc_uri: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        return {
            "source": "DigiLocker API (Mock)",
            "is_simulated": True,
            "provider_mode": PROVIDER_MODE_MOCK,
            "verified": True,
            "status": "VERIFIED_ISSUER",
            "detail": "Digital Signature Certificate (DSC) and issuer authority verified.",
            "reference_id": f"DIGI-MOCK-{abs(hash(doc_uri or 'digi')) % 10000}"
        }

class MockDebarmentProvider(VerificationProvider):
    def verify(self, vendor_name: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        name_clean = (vendor_name or "").upper()
        if "DEBARRED" in name_clean or "BLACKLIST" in name_clean:
            return {
                "source": "CVC / GeM Debarred Vendor Registry (Mock)",
                "is_simulated": True,
                "provider_mode": PROVIDER_MODE_MOCK,
                "verified": False,
                "status": "ACTIVE_DEBARMENT",
                "authority": "CPCL Vigilance Division",
                "reason": "Prior contract default & submission of fabricated tax clearance documents.",
                "reference_id": "DEBAR-2025-0019"
            }
        return {
            "source": "CVC / GeM Debarred Vendor Registry (Mock)",
            "is_simulated": True,
            "provider_mode": PROVIDER_MODE_MOCK,
            "verified": True,
            "status": "CLEAR",
            "authority": "GeM National Registry",
            "reason": "No active debarment or blacklisting records found.",
            "reference_id": f"DEBAR-MOCK-CLEAR-{abs(hash(vendor_name)) % 10000}"
        }
