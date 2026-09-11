import sys
import os

content = open('tests/test_api_routes.py').read()
start_idx = content.find('def test_rbac_authorization(db: Session):')
end_idx = content.find('def test_tenders_and_vendors_api(db: Session):')

if start_idx != -1 and end_idx != -1:
    new_test_content = """def test_rbac_authorization(db: Session):
    import uuid
    uid = str(uuid.uuid4())[:8]
    from app.models.models import User
    from app.core.security import get_password_hash
    # Create auditor user with unique email
    auditor = User(
        email=f"auditor_{uid}@bharatsetu.gov.in",
        hashed_password=get_password_hash("auditor123"),
        full_name="Audit Specialist",
        role="AUDITOR"
    )
    db.add(auditor)
    db.commit()

    from app.core.security import create_access_token
    token = create_access_token(subject=auditor.id)
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to approve a bid with AUDITOR role (should be forbidden 403)
    res = client.post("/api/bids/GEM-2026-04827/approve", json={"action": "APPROVE"}, headers=headers)
    assert res.status_code == 403

    # Bidder specific RBAC checks
    res_login = client.post("/api/auth/login", json={"email": "bidder@bharatsetu.gov.in", "password": "bidder123"})
    bidder_token = res_login.json().get("access_token")
    if bidder_token:
        bidder_headers = {"Authorization": f"Bearer {bidder_token}"}
        
        res_approve = client.post("/api/bids/GEM-2026-04827/approve", json={"action": "APPROVE"}, headers=bidder_headers)
        assert res_approve.status_code == 403

        res_reject = client.post("/api/bids/GEM-2026-04827/reject", json={"action": "REJECT", "reason": "Testing"}, headers=bidder_headers)
        assert res_reject.status_code == 403

        res_escalate = client.post("/api/bids/GEM-2026-04827/escalate", json={"action": "ESCALATE", "reason": "Testing"}, headers=bidder_headers)
        assert res_escalate.status_code == 403

def test_sensitive_endpoints_require_auth(db: Session):
    unauth_tenders = client.get("/api/tenders")
    assert unauth_tenders.status_code == 401

    unauth_report = client.get("/api/reports/bids/GEM-2026-04827")
    assert unauth_report.status_code == 401

def test_dashboard_metrics_api(db: Session):
    res_login = client.post("/api/auth/login", json={"email": "officer@bharatsetu.gov.in", "password": "officer123"})
    token = res_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get("/api/dashboard/metrics", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "pending_review_count" in data
    assert "approved_today_count" in data
    assert "compliance_rate_percent" in data

"""
    with open('tests/test_api_routes.py', 'w') as f:
        f.write(content[:start_idx] + new_test_content + content[end_idx:])
    print('Successfully updated test_api_routes.py')
else:
    print('Could not find start or end index')
