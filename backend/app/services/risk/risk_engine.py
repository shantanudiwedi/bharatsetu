from typing import List, Dict, Any, Tuple

class RiskEngine:
    @staticmethod
    def calculate_scores(
        rule_results: List[Dict[str, Any]],
        doc_checks: List[Dict[str, Any]],
        cross_checks: List[Dict[str, Any]]
    ) -> Tuple[int, str, float, List[str]]:
        """
        Calculates deterministic Risk Score (0-100), Risk Level (LOW, MEDIUM, HIGH),
        Compliance Score %, and Risk Factors list.
        """
        risk_score = 0
        risk_factors = []
        total_rules = max(1, len(rule_results) + len(doc_checks))
        passed_rules = 0

        # Process document checks
        for doc in doc_checks:
            status = doc.get("status", "").lower()
            name = doc.get("name", "")
            detail = doc.get("detail", "")
            
            if status == "verified":
                passed_rules += 1
            elif status == "failed":
                risk_score += 30
                risk_factors.append(f"{name} verification failed: {detail}")
            elif status == "pending":
                risk_score += 15
                risk_factors.append(f"{name} verification pending or incomplete")

        # Process rule results
        for rule in rule_results:
            result = rule.get("result")
            finding = rule.get("finding", "")
            impact = rule.get("impact", "HIGH")
            
            if result == "FAIL":
                if impact == "CRITICAL":
                    risk_score += 40
                elif impact == "HIGH":
                    risk_score += 25
                else:
                    risk_score += 15
                if finding not in risk_factors:
                    risk_factors.append(finding)
            elif result == "PASS":
                passed_rules += 1

        # Process cross checks
        for cc in cross_checks:
            if cc.get("status") == "MISMATCH":
                risk_score += 20
                risk_factors.append(f"Cross-document mismatch ({cc.get('check_type')}): {cc.get('explanation')}")
            elif cc.get("status") == "POTENTIAL_MISMATCH":
                risk_score += 10
                risk_factors.append(f"Potential cross-document inconsistency: {cc.get('explanation')}")

        # Normalize risk score to 0 - 100
        risk_score = min(100, max(0, risk_score))

        # Risk Level category
        if risk_score <= 25:
            risk_level = "LOW"
        elif risk_score <= 60:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        # Compliance score %
        compliance_score = round((passed_rules / float(total_rules)) * 100.0, 1)

        return risk_score, risk_level, compliance_score, risk_factors
