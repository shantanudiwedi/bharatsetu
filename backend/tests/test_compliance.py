import pytest
from app.services.cross_check.cross_check_engine import CrossCheckEngine
from app.services.compliance.rule_engine import ComplianceRuleEngine
from app.services.risk.risk_engine import RiskEngine
from app.services.classification.classifier import DocumentClassifier

def test_fuzzy_name_matching():
    score, status = CrossCheckEngine.compare_names("Shree Lakshmi Industries Pvt Ltd", "Shree Lakshmi Industries Private Limited")
    assert score >= 90.0
    assert status == "MATCH"

def test_fuzzy_name_mismatch():
    score, status = CrossCheckEngine.compare_names("National Steel Fabricators", "National Steel Fabricators Unit")
    assert status in ["POTENTIAL_MISMATCH", "MISMATCH"]

def test_document_classification():
    doc_type, conf = DocumentClassifier.classify("GST_Certificate_2026.pdf", "Goods and Services Tax GSTIN 27AABCDE1234F1Z5")
    assert doc_type == "GST"
    assert conf > 80.0

def test_risk_scoring():
    doc_checks = [
        {"name": "GST", "status": "failed", "detail": "Address mismatch"},
        {"name": "PAN", "status": "verified", "detail": "Valid"},
        {"name": "EPFO", "status": "failed", "detail": "Establishment not found"}
    ]
    rule_results = [
        {"result": "FAIL", "finding": "GST address mismatch", "impact": "HIGH"}
    ]
    cross_checks = [
        {"status": "MISMATCH", "check_type": "ADDRESS", "explanation": "Pune vs Nagpur"}
    ]

    risk_score, risk_level, comp_score, factors = RiskEngine.calculate_scores(rule_results, doc_checks, cross_checks)
    assert risk_score >= 61
    assert risk_level == "HIGH"
    assert len(factors) >= 2
