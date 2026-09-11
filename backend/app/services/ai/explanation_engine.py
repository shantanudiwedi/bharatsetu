from typing import List, Dict, Any, Tuple

class AIExplanationEngine:
    @staticmethod
    def generate_explanation(
        vendor_name: str,
        risk_level: str,
        risk_score: int,
        compliance_score: float,
        risk_factors: List[str],
        doc_checks: List[Dict[str, Any]]
    ) -> Tuple[str, str, int]:
        """
        Generates grounded AI recommendations summarizing verified system findings.
        CRITICAL GOV RULE: AI NEVER makes final Approve/Reject decisions. It provides objective advice to the human officer.
        """
        failed_docs = [d for d in doc_checks if d.get("status") == "failed"]
        verified_docs = [d for d in doc_checks if d.get("status") == "verified"]

        if risk_level == "HIGH":
            recommendation = (
                f"Escalation & Manual Review Recommended. The bidder {vendor_name} exhibited a High Risk profile "
                f"(Risk Score: {risk_score}/100). Primary issues identified: {', '.join(risk_factors[:2])}."
            )
            summary = (
                f"{len(failed_docs)} of {len(doc_checks)} verified documents failed automated compliance checks. "
                f"{' '.join(risk_factors)}. Detailed procurement officer review required."
            )
            confidence = 87
        elif risk_level == "MEDIUM":
            recommendation = (
                f"Further Officer Verification Recommended. {vendor_name} has a Medium Risk profile ({risk_score}/100). "
                f"Compliance signals flagged: {', '.join(risk_factors[:2])}."
            )
            summary = (
                f"{len(verified_docs)} of {len(doc_checks)} documents verified successfully. "
                f"Pending/incomplete checks: {', '.join(risk_factors)}. Recommend officer confirm operational credentials."
            )
            confidence = 82
        else:
            verified_names = [d["name"] for d in verified_docs]
            verified_list = ", ".join(verified_names) if verified_names else "None"
            recommendation = (
                "No automated compliance blockers detected. Final authorization decision "
                "remains strictly with the authorized procurement officer."
            )
            summary = (
                f"Clean profile across {len(verified_docs)} verified document(s): {verified_list}. "
                f"No risk factors identified. Note: All verifications performed via MOCK providers — "
                f"not live government API confirmation."
            )
            confidence = 96

        return recommendation, summary, confidence
