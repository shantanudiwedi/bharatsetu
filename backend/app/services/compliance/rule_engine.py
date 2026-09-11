from typing import List, Dict, Any

class ComplianceRuleEngine:
    @staticmethod
    def evaluate_tender_rules(
        tender_data: Dict[str, Any],
        extracted_fields_map: Dict[str, str],
        doc_verifications: List[Dict[str, Any]],
        cross_checks: List[Dict[str, Any]],
        uploaded_doc_types: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Evaluates dynamic tender rules loaded from the database against extracted document fields.

        Rules are evaluated ONLY for requirements that the tender explicitly defines.
        No global mandatory documents are assumed. If a tender defines no requirements,
        no mandatory-document failures are generated.
        """
        results = []

        # 1. Tender Mandatory Documents Evaluation
        # Default is empty list — never invent requirements the tender did not define.
        required_docs = tender_data.get("required_documents", [])
        for req_doc in required_docs:
            doc_type_clean = req_doc.get("document_type", req_doc) if isinstance(req_doc, dict) else req_doc
            is_mandatory = req_doc.get("is_mandatory", True) if isinstance(req_doc, dict) else True

            if is_mandatory and not any(doc_type_clean in u_type for u_type in uploaded_doc_types):
                results.append({
                    "rule_id": f"MANDATORY_DOC_{doc_type_clean}",
                    "document_type": doc_type_clean,
                    "result": "FAIL",
                    "finding": f"Mandatory document '{doc_type_clean}' required by tender is missing from submission.",
                    "impact": "HIGH",
                    "recommended_action": f"Request bidder to upload missing mandatory document '{doc_type_clean}'."
                })

        # 2. Minimum Turnover Rule Evaluation
        min_turnover = tender_data.get("minimum_turnover_inr", 0.0)
        extracted_turnover_str = (
            extracted_fields_map.get("annual_turnover")
            or extracted_fields_map.get("revenue")
        )
        msme_exemption_allowed = tender_data.get("msme_exemption_allowed", False)
        startup_exemption_allowed = tender_data.get("startup_exemption_allowed", False)
        # Bidder qualifies for exemption if they have an MSME/UDYAM/DPIIT document uploaded.
        bidder_has_msme = any(t in ["UDYAM", "MSME", "DPIIT"] for t in uploaded_doc_types)

        if min_turnover > 0:
            if extracted_turnover_str:
                try:
                    val = float(
                        extracted_turnover_str.replace(",", "").replace("\u20b9", "").strip()
                    )
                    if val >= min_turnover:
                        results.append({
                            "rule_id": "TURNOVER_MIN",
                            "document_type": "FINANCIAL",
                            "result": "PASS",
                            "finding": (
                                f"Extracted annual turnover (\u20b9{val:,.2f}) meets/exceeds "
                                f"minimum tender requirement (\u20b9{min_turnover:,.2f})."
                            ),
                            "impact": "HIGH",
                            "recommended_action": "None required."
                        })
                    elif (msme_exemption_allowed or startup_exemption_allowed) and bidder_has_msme:
                        # Turnover below threshold but exemption is available and applicable.
                        results.append({
                            "rule_id": "TURNOVER_MIN_MSME_EXEMPT",
                            "document_type": "FINANCIAL",
                            "result": "PASS",
                            "finding": (
                                f"Extracted turnover (\u20b9{val:,.2f}) is below minimum "
                                f"(\u20b9{min_turnover:,.2f}), but MSME/Startup exemption is applicable "
                                f"per tender rules. Bidder has submitted MSME/UDYAM registration."
                            ),
                            "impact": "MEDIUM",
                            "recommended_action": "Officer to confirm MSME eligibility before final approval."
                        })
                    else:
                        results.append({
                            "rule_id": "TURNOVER_MIN",
                            "document_type": "FINANCIAL",
                            "result": "FAIL",
                            "finding": (
                                f"Extracted turnover (\u20b9{val:,.2f}) is below minimum tender "
                                f"requirement (\u20b9{min_turnover:,.2f})."
                            ),
                            "impact": "HIGH",
                            "recommended_action": "Evaluate MSME/Startup turnover exemption eligibility."
                        })
                except ValueError:
                    results.append({
                        "rule_id": "TURNOVER_MIN",
                        "document_type": "FINANCIAL",
                        "result": "WARNING",
                        "finding": (
                            f"Annual turnover figure '{extracted_turnover_str}' could not be "
                            f"parsed numerically."
                        ),
                        "impact": "MEDIUM",
                        "recommended_action": "Manual review of financial statement required."
                    })

        # 3. Minimum Experience Rule Evaluation
        # CORRECT: numeric comparison against minimum_experience_years.
        # Any non-numeric or absent value produces WARNING or FAIL — never a blind PASS.
        min_exp = tender_data.get("minimum_experience_years", 0)
        extracted_exp_str = (
            extracted_fields_map.get("experience_years")
            or extracted_fields_map.get("project_value")
        )
        if min_exp > 0:
            if extracted_exp_str:
                try:
                    exp_val = float(extracted_exp_str.replace(",", "").strip())
                    if exp_val >= min_exp:
                        results.append({
                            "rule_id": "EXPERIENCE_MIN",
                            "document_type": "EXPERIENCE",
                            "result": "PASS",
                            "finding": (
                                f"Extracted experience ({exp_val} years) meets minimum "
                                f"requirement ({min_exp} years)."
                            ),
                            "impact": "HIGH",
                            "recommended_action": "None required."
                        })
                    else:
                        results.append({
                            "rule_id": "EXPERIENCE_MIN",
                            "document_type": "EXPERIENCE",
                            "result": "FAIL",
                            "finding": (
                                f"Extracted experience ({exp_val} years) does not meet minimum "
                                f"tender requirement of {min_exp} years."
                            ),
                            "impact": "HIGH",
                            "recommended_action": (
                                "Request additional work completion certificates covering "
                                "the full required period."
                            )
                        })
                except ValueError:
                    results.append({
                        "rule_id": "EXPERIENCE_MIN",
                        "document_type": "EXPERIENCE",
                        "result": "WARNING",
                        "finding": (
                            f"Experience figure '{extracted_exp_str}' could not be parsed "
                            f"numerically for comparison against {min_exp} years minimum."
                        ),
                        "impact": "MEDIUM",
                        "recommended_action": "Manual officer review of experience certificate required."
                    })
            else:
                results.append({
                    "rule_id": "EXPERIENCE_MIN",
                    "document_type": "EXPERIENCE",
                    "result": "FAIL",
                    "finding": (
                        f"No experience details extracted from submitted documents. "
                        f"Minimum {min_exp} years experience required."
                    ),
                    "impact": "HIGH",
                    "recommended_action": (
                        "Request work completion certificate or past performance certificate."
                    )
                })

        # 4. Local Content Compliance
        # IMPORTANT: The system cannot extract/verify local content percentages from OCR.
        # When tender requires local content, return MANUAL_REVIEW_REQUIRED — never fabricate.
        local_content_pct = tender_data.get("local_content_percentage", 0.0)
        if local_content_pct and local_content_pct > 0:
            has_local_content_doc = any(
                t in ["LOCAL_CONTENT", "UNDERTAKING", "SELF_CERTIFICATION"]
                for t in uploaded_doc_types
            )
            if has_local_content_doc:
                results.append({
                    "rule_id": "LOCAL_CONTENT",
                    "document_type": "LOCAL_CONTENT",
                    "result": "WARNING",
                    "finding": (
                        f"Tender requires {local_content_pct}% local content. "
                        f"Undertaking document submitted but percentage cannot be verified by "
                        f"automated OCR. MANUAL_REVIEW_REQUIRED."
                    ),
                    "impact": "MEDIUM",
                    "recommended_action": (
                        "Officer must manually verify local content percentage against "
                        "submitted undertaking."
                    )
                })
            else:
                results.append({
                    "rule_id": "LOCAL_CONTENT",
                    "document_type": "LOCAL_CONTENT",
                    "result": "FAIL",
                    "finding": (
                        f"Tender requires {local_content_pct}% local content but no local "
                        f"content undertaking document has been submitted."
                    ),
                    "impact": "HIGH",
                    "recommended_action": (
                        "Request bidder to submit local content undertaking certificate."
                    )
                })

        # 5. GST Active Rule
        gst_ver = next(
            (v for v in doc_verifications
             if "GST" in v.get("source", "").upper() or v.get("document_type") == "GST"),
            None
        )
        if gst_ver:
            if gst_ver.get("status") == "ACTIVE":
                results.append({
                    "rule_id": "GST_ACTIVE",
                    "document_type": "GST",
                    "result": "PASS",
                    "finding": "GSTIN registration is ACTIVE on GSTN portal.",
                    "impact": "HIGH",
                    "recommended_action": "None required."
                })
            elif gst_ver.get("status") == "ACTIVE_ADDRESS_MISMATCH":
                results.append({
                    "rule_id": "GST_ADDRESS_MATCH",
                    "document_type": "GST",
                    "result": "FAIL",
                    "finding": gst_ver.get("detail", "GST registered address mismatch detected."),
                    "impact": "HIGH",
                    "recommended_action": "Request official address clarification or revised GST proof."
                })
            elif gst_ver.get("status") == "CANCELLED":
                results.append({
                    "rule_id": "GST_ACTIVE",
                    "document_type": "GST",
                    "result": "FAIL",
                    "finding": "GSTIN registration status is CANCELLED as of July 2026.",
                    "impact": "CRITICAL",
                    "recommended_action": "Disqualify bidder due to cancelled tax registration."
                })

        # 6. PAN Match Rule
        pan_ver = next(
            (v for v in doc_verifications
             if "PAN" in v.get("source", "").upper() or v.get("document_type") == "PAN"),
            None
        )
        if pan_ver:
            if pan_ver.get("status") == "VERIFIED":
                results.append({
                    "rule_id": "PAN_MATCH",
                    "document_type": "PAN",
                    "result": "PASS",
                    "finding": "PAN card matches entity registration name.",
                    "impact": "HIGH",
                    "recommended_action": "None required."
                })
            elif pan_ver.get("status") == "NAME_MISMATCH":
                results.append({
                    "rule_id": "PAN_MATCH",
                    "document_type": "PAN",
                    "result": "FAIL",
                    "finding": pan_ver.get("detail", "PAN registered name differs from bid entity name."),
                    "impact": "HIGH",
                    "recommended_action": "Manual review required to verify legal entity ownership."
                })

        # 7. EPFO Active Rule
        epfo_ver = next(
            (v for v in doc_verifications
             if "EPFO" in v.get("source", "").upper() or v.get("document_type") == "EPFO"),
            None
        )
        if epfo_ver:
            if epfo_ver.get("status") == "ACTIVE":
                results.append({
                    "rule_id": "EPFO_ACTIVE",
                    "document_type": "EPFO",
                    "result": "PASS",
                    "finding": "EPFO establishment code active with valid employee enrollment.",
                    "impact": "MEDIUM",
                    "recommended_action": "None required."
                })
            elif epfo_ver.get("status") in ["NOT_FOUND", "INACTIVE"]:
                results.append({
                    "rule_id": "EPFO_ACTIVE",
                    "document_type": "EPFO",
                    "result": "FAIL",
                    "finding": epfo_ver.get("detail", "EPFO establishment code not active."),
                    "impact": "HIGH",
                    "recommended_action": "Request latest PF challan payment receipt."
                })

        # 8. Debarment Check Rule
        debar_ver = next(
            (v for v in doc_verifications
             if "DEBAR" in v.get("source", "").upper() or v.get("document_type") == "DEBARMENT"),
            None
        )
        if debar_ver and debar_ver.get("status") == "ACTIVE_DEBARMENT":
            results.append({
                "rule_id": "DEBARMENT_CLEAR",
                "document_type": "DEBARMENT",
                "result": "FAIL",
                "finding": f"Active debarment record found on CVC/GeM registry: {debar_ver.get('reason')}",
                "impact": "CRITICAL",
                "recommended_action": "Immediate escalation and tender disqualification."
            })

        return results
