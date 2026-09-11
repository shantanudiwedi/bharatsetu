import requests
import os
from time import sleep

BASE_URL = "http://localhost:8000/api"

def print_step(name):
    print(f"\n[{name}]")

# 1. Login
print_step("AUTH TEST")
res = requests.post(f"{BASE_URL}/auth/login", json={"email": "officer@bharatsetu.gov.in", "password": "officer123"})
if res.status_code != 200:
    print("Login failed:", res.text)
assert res.status_code == 200, "Login failed"
token = res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("Login successful. Token acquired.")

# Test without token
res_no_auth = requests.get(f"{BASE_URL}/dashboard/metrics")
if res_no_auth.status_code != 401:
    print("Unauthenticated request did not return 401! Status:", res_no_auth.status_code, res_no_auth.text)
assert res_no_auth.status_code == 401, "Unauthenticated request should return 401"
print("401 Unauthorized check passed.")

# 2. Dashboard
print_step("DASHBOARD")
res = requests.get(f"{BASE_URL}/dashboard/metrics", headers=headers)
assert res.status_code == 200
print("Dashboard metrics:", res.json())

# 3. Tenders
print_step("TENDERS")
res = requests.get(f"{BASE_URL}/tenders", headers=headers)
assert res.status_code == 200
tenders = res.json()
print("Found tenders:", len(tenders))
tender_id = tenders[0]["id"]

# 4. Bids
print_step("BIDS")
res = requests.get(f"{BASE_URL}/bids", headers=headers)
assert res.status_code == 200
bids = res.json()
print("Found bids:", len(bids))

# Find the demo bids
shree_bid = next((b for b in bids if b["vendorName"] == "Shree Lakshmi Industries Pvt Ltd"), None)
bharat_bid = next((b for b in bids if b["vendorName"] == "Bharat Tech Solutions LLP"), None)

assert shree_bid, "Shree Lakshmi demo bid not found"
assert bharat_bid, "Bharat Tech demo bid not found"
print("Demo bids found.")

# 5. Upload & Verify (Shree Lakshmi)
print_step("SHREE LAKSHMI UPLOAD & VERIFY")
# Create a dummy PDF file
with open("dummy.pdf", "wb") as f:
    f.write(b"%PDF-1.4\n%Dummy PDF content\n")

# Upload
with open("dummy.pdf", "rb") as f:
    files = {"file": ("dummy.pdf", f, "application/pdf")}
    res = requests.post(f"{BASE_URL}/bids/{shree_bid['id']}/documents", headers=headers, files=files)
    if res.status_code == 400 and "Duplicate" in res.text:
        print("Document already uploaded.")
    else:
        assert res.status_code == 200, f"Upload failed: {res.text}"
        print("Upload successful.")

# Verify
res = requests.post(f"{BASE_URL}/bids/{shree_bid['id']}/verify", headers=headers)
assert res.status_code == 200, f"Verification failed: {res.text}"
print("Verification pipeline triggered.")

# Wait for background pipeline to complete if it were async, but we made it sync so it's done.

# Get Bid again to check scores
res = requests.get(f"{BASE_URL}/bids", headers=headers)
shree_bid_updated = next(b for b in res.json() if b["id"] == shree_bid["id"])
print("Shree Lakshmi Updated Risk Level:", shree_bid_updated["riskLevel"])
print("Shree Lakshmi Updated Risk Score:", shree_bid_updated.get("risk_score"))
print("AI Explanation:", shree_bid_updated["aiRecommendation"])

# Escalate
print_step("OFFICER ESCALATION")
res = requests.post(f"{BASE_URL}/bids/{shree_bid['id']}/escalate", headers=headers, json={"action": "ESCALATE", "reason": "Address mismatch requires field verification."})
assert res.status_code == 200, f"Escalation failed: {res.text}"
print("Escalation successful.")

# 6. Audit Trail
print_step("AUDIT TRAIL")
res = requests.get(f"{BASE_URL}/audit", headers=headers)
assert res.status_code == 200
print("Audit events found:", len(res.json()))

# 7. PDF Report
print_step("PDF REPORT")
res = requests.get(f"{BASE_URL}/reports/bids/{shree_bid['id']}", headers=headers)
assert res.status_code == 200
assert res.headers["content-type"] == "application/pdf"
print("PDF generation successful. Content size:", len(res.content))

print("\nALL RUNTIME TESTS PASSED")
