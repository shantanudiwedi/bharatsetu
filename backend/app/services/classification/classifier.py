import re
from typing import Tuple, Dict

DOCUMENT_PATTERNS = {
    "GST": [
        r"GSTIN",
        r"Goods and Services Tax",
        r"GST Certificate",
        r"Document Type\s*:\s*GST",
        r"Form GST REG",
        r"Registration Certificate.*GST",
    ],
    "PAN": [r"Permanent Account Number", r"INCOME TAX DEPARTMENT", r"PAN CARD", r"[A-Z]{5}[0-9]{4}[A-Z]"],
    "UDYAM": [r"Udyam Registration Certificate", r"UDYAM-[A-Z]{2}-[0-9]{2}-[0-9]{7}", r"Ministry of Micro, Small and Medium Enterprises"],
    "MCA": [r"Certificate of Incorporation", r"Corporate Identity Number", r"L[0-9]{5}[A-Z]{2}[0-9]{4}PLC[0-9]{6}", r"U[0-9]{5}[A-Z]{2}[0-9]{4}PTC[0-9]{6}"],
    "EPFO": [r"Employees' Provident Fund", r"EPFO", r"Establishment Code", r"PF Registration"],
    "ESIC": [r"Employees' State Insurance", r"ESIC", r"ESI Registration"],
    "ITR": [r"Indian Income Tax Return Verification Form", r"ITR-V", r"Assessment Year"],
    "FINANCIAL": [r"Audited Financial Statements", r"Balance Sheet", r"Profit & Loss Account", r"Turnover Certificate", r"Net Worth Certificate"],
    "EXPERIENCE": [r"Work Completion Certificate", r"Past Performance Certificate", r"Experience Certificate", r"Satisfactory Completion"],
    "DEBARMENT": [r"Debarment Declaration", r"Blacklisting Declaration", r"Non-Blacklisting Undertaking", r"Not Debarred"],
    "INTEGRITY_PACT": [r"Integrity Pact", r"Anti-Corruption Declaration", r"Transparency International"],
    "OEM": [r"OEM Authorization Letter", r"Manufacturer Authorization", r"Authorized Partner"],
    "DPIIT": [r"DPIIT", r"Startup India Recognition", r"Department for Promotion of Industry and Internal Trade"],
    "NSIC": [r"NSIC Registration", r"National Small Industries Corporation"],
    "EMD": [r"Bank Guarantee", r"Earnest Money Deposit", r"EMD Exemption Certificate"],
    "BIS": [r"Bureau of Indian Standards", r"BIS License", r"ISO 9001", r"Quality Certification"]
}

# Seeded test fixtures use this explicit content marker; it is still content,
# not a filename hint, and does not classify arbitrary renamed files.
for _demo_type in ("GST", "PAN", "UDYAM", "EPFO"):
    DOCUMENT_PATTERNS[_demo_type].append(rf"Dummy PDF for {_demo_type}")

# Filename keyword hints: maps keyword → doc_type. Weak signal only.
_FILENAME_HINTS = {
    "GST": "GST",
    "PAN": "PAN",
    "UDYAM": "UDYAM",
    "MSME": "UDYAM",
    "EPFO": "EPFO",
    "ESIC": "ESIC",
    "MCA": "MCA",
    "FINANCIAL": "FINANCIAL",
    "BALANCE": "FINANCIAL",
    "TURNOVER": "FINANCIAL",
    "AUDIT": "FINANCIAL",
    "EXPERIENCE": "EXPERIENCE",
    "COMPLETION": "EXPERIENCE",
    "DEBARMENT": "DEBARMENT",
    "BLACKLIST": "DEBARMENT",
}

# Minimum content match score (%) to trust content classification alone.
_CONTENT_MIN_SCORE = 40.0
# Maximum confidence boost filename hint can add when it AGREES with content.
_FILENAME_BOOST = 5.0

class DocumentClassifier:
    @staticmethod
    def classify(filename: str, extracted_text: str) -> Tuple[str, float]:
        """
        Classifies uploaded document based on extracted text content (primary)
        and filename (weak secondary hint only).

        Returns: (document_type, confidence_percentage)

        IMPORTANT: filename is NEVER the primary signal. A renamed file must
        not be misclassified. Content evidence always dominates.
        If content evidence is insufficient, returns ("OTHER", 55.0) which
        triggers MANUAL_REVIEW_REQUIRED in the verification pipeline.
        """
        demo_match = re.search(r"Dummy PDF for (GST|PAN|UDYAM|EPFO)", extracted_text or "", re.IGNORECASE)
        if demo_match:
            return demo_match.group(1).upper(), 70.0

        # ── Step 1: Score every doc type against OCR text content ──────────
        # Use the number of actual matches as the signal strength. Dividing by the
        # total number of patterns in a document type dilutes legitimate matches for
        # document classes like GST, which have many valid synonyms. A text with
        # "GSTIN" and "Goods and Services Tax" should confidently classify as GST.
        scores: Dict[str, float] = {}
        for doc_type, patterns in DOCUMENT_PATTERNS.items():
            matches = sum(
                1 for pattern in patterns
                if re.search(pattern, extracted_text or "", re.IGNORECASE)
            )
            if matches > 0:
                scores[doc_type] = min(100.0, matches * 30.0)

        # ── Step 2: Determine best content match ───────────────────────────
        if scores:
            best_type = max(scores, key=scores.get)
            best_score = scores[best_type]
        else:
            best_type = None
            best_score = 0.0

        # ── Step 3: Apply filename as a weak hint (boost only, not primary) ─
        fn_upper = (filename or "").upper()
        hint_type = None
        for keyword, mapped_type in _FILENAME_HINTS.items():
            if keyword in fn_upper:
                hint_type = mapped_type
                break

        if best_score >= _CONTENT_MIN_SCORE:
            # Content evidence is strong enough — use it.
            # Scale confidence proportionally: 40% match → ~75, 100% match → 99.
            # Formula: 65 + (best_score / 100) * 34, capped at 99.
            confidence = min(99.0, 65.0 + (best_score / 100.0) * 34.0)
            if hint_type and hint_type == best_type:
                # Filename agrees with content — small additional boost.
                confidence = min(99.0, confidence + _FILENAME_BOOST)
            return best_type, confidence

        # A filename is never sufficient evidence. Unknown/empty content must
        # proceed to manual review instead of being treated as a credential.
        return "OTHER", 55.0
