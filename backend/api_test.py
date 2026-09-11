import requests

BASE = 'http://127.0.0.1:8000/api'

# Unauthenticated = 401
r = requests.get(f'{BASE}/bids')
print(f'Unauthenticated /bids: {r.status_code} (expect 401)')

# Admin login
r = requests.post(f'{BASE}/auth/login', json={'email': 'admin@bharatsetu.gov.in', 'password': 'admin123'})
admin_token = r.json()['access_token']
admin_user = r.json()['user']
print(f'Admin login: {admin_user["full_name"]} / {admin_user["role"]}')

# Officer login
r = requests.post(f'{BASE}/auth/login', json={'email': 'officer@bharatsetu.gov.in', 'password': 'officer123'})
officer_token = r.json()['access_token']
officer_user = r.json()['user']
print(f'Officer login: {officer_user["full_name"]} / {officer_user["role"]}')

# Bidder login
r = requests.post(f'{BASE}/auth/login', json={'email': 'bidder@bharatsetu.gov.in', 'password': 'bidder123'})
bidder_token = r.json()['access_token']
bidder_user = r.json()['user']
print(f'Bidder login: {bidder_user["full_name"]} / {bidder_user["role"]}')

# Admin list bids
r = requests.get(f'{BASE}/bids', headers={'Authorization': f'Bearer {admin_token}'})
print(f'Admin list bids: {r.status_code}, count={len(r.json())}')

# Officer list bids
r = requests.get(f'{BASE}/bids', headers={'Authorization': f'Bearer {officer_token}'})
bids = r.json()
print(f'Officer list bids: {r.status_code}, count={len(bids)}')

demo_bids = [b for b in bids if b.get('id') == 'GEM-2026-DEMO-01']
print(f'Demo bid GEM-2026-DEMO-01: {"FOUND" if demo_bids else "NOT FOUND"}')
if demo_bids:
    db = demo_bids[0]
    print(f'  Vendor: {db["vendorName"]}, Status: {db["status"]}, Risk: {db["riskLevel"]}')
    print(f'  Documents: {[(d["name"], d["status"]) for d in db["documents"]]}')

# Bidder own bids
r = requests.get(f'{BASE}/bids', headers={'Authorization': f'Bearer {bidder_token}'})
bidder_bids = r.json()
print(f'Bidder list bids: {r.status_code}, count={len(bidder_bids)} (own vendor only)')

# Bidder dashboard
r = requests.get(f'{BASE}/bidder/dashboard', headers={'Authorization': f'Bearer {bidder_token}'})
print(f'Bidder dashboard: {r.status_code}, data={r.json()}')

# Officer upload attempt = 403
r = requests.post(f'{BASE}/bids/GEM-2026-DEMO-01/documents',
    headers={'Authorization': f'Bearer {officer_token}'},
    files={'file': ('test.pdf', b'%PDF-1.4', 'application/pdf')})
print(f'Officer upload attempt: {r.status_code} (expect 403)')

# Admin upload attempt = 403
r = requests.post(f'{BASE}/bids/GEM-2026-DEMO-01/documents',
    headers={'Authorization': f'Bearer {admin_token}'},
    files={'file': ('test.pdf', b'%PDF-1.4', 'application/pdf')})
print(f'Admin upload attempt: {r.status_code} (expect 403)')

# Officer view demo bid doc
if demo_bids and demo_bids[0]['documents']:
    doc_id = demo_bids[0]['documents'][0]['id']
    r = requests.get(f'{BASE}/bids/documents/{doc_id}/view',
        headers={'Authorization': f'Bearer {officer_token}'})
    print(f'Officer view doc: {r.status_code}, content-type={r.headers.get("content-type")}, size={len(r.content)} bytes')
    print(f'  PDF header: {r.content[:8]}')

    # BidderB cross-vendor view = 403
    r2 = requests.post(f'{BASE}/auth/login', json={'email': 'bidderb@bharatsetu.gov.in', 'password': 'bidder123'})
    bidderb_token = r2.json()['access_token']
    r = requests.get(f'{BASE}/bids/documents/{doc_id}/view',
        headers={'Authorization': f'Bearer {bidderb_token}'})
    print(f'BidderB cross-vendor doc: {r.status_code} (expect 403)')

    # Bidder own doc view
    r = requests.get(f'{BASE}/bids/documents/{doc_id}/view',
        headers={'Authorization': f'Bearer {bidder_token}'})
    print(f'Bidder own doc view: {r.status_code} (expect 200)')

# Tenders
r = requests.get(f'{BASE}/tenders', headers={'Authorization': f'Bearer {bidder_token}'})
tenders = r.json()
print(f'Tenders: count={len(tenders)}')
for t in tenders[:3]:
    reqs = t.get('requirements', [])
    print(f'  {t["tender_id"]} requirements={len(reqs)}: {[rr["document_type"] for rr in reqs[:6]]}')

print('DONE')
