from fastapi.testclient import TestClient
from app.main import app
from app.db.seed_data import seed_db
from app.db.database import Base, engine, SessionLocal
from app.models.models import Document, Verification, RuleResult
import os

Base.metadata.create_all(bind=engine)
seed_db()
client = TestClient(app)
login = client.post('/api/auth/login', json={'email': 'bidder@bharatsetu.gov.in', 'password': 'bidder123'})
print('LOGIN_STATUS', login.status_code)
print('LOGIN_BODY', login.json())
if login.status_code != 200:
    raise SystemExit('login failed')
headers = {'Authorization': 'Bearer ' + login.json()['access_token']}

tenders = client.get('/api/tenders', headers=headers)
print('TENDERS_STATUS', tenders.status_code)
selected_tender = next((b for b in tenders.json() if b.get('status') == 'ACTIVE'), None)
print('SELECTED_TENDER', selected_tender['id'] if selected_tender else None)
create_resp = client.post('/api/bids', json={
    'tender_id': selected_tender['id'],
    'vendor_name': 'TechCorp India Pvt Ltd',
    'category': selected_tender['category'],
    'bid_amount': '1000000',
    'gstin': '27ABCDE1234F1Z5',
    'pan': 'ABCDE1234F',
    'udyam': 'UDYAM-MH-00-1234567',
}, headers=headers)
print('CREATE_BID_STATUS', create_resp.status_code)
print('CREATE_BID_BODY', create_resp.json())
if create_resp.status_code != 200:
    raise SystemExit('bid creation failed')
bid_id = create_resp.json()['id']

pdf = (
    b'%PDF-1.4\n'
    b'1 0 obj\n'
    b'<< /Type /Catalog /Pages 2 0 R >>\n'
    b'endobj\n'
    b'2 0 obj\n'
    b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>\n'
    b'endobj\n'
    b'3 0 obj\n'
    b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\n'
    b'endobj\n'
    b'4 0 obj\n'
    b'<< /Length 49 >>\nstream\n'
    b'BT /F1 18 Tf 50 70 Td (VALID TEST PDF) Tj ET\n'
    b'endstream\n'
    b'endobj\n'
    b'5 0 obj\n'
    b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\n'
    b'endobj\n'
    b'xref\n'
    b'0 6\n'
    b'0000000000 65535 f \n'
    b'0000000010 00000 n \n'
    b'0000000063 00000 n \n'
    b'0000000120 00000 n \n'
    b'0000000245 00000 n \n'
    b'0000000468 00000 n \n'
    b'trailer\n'
    b'<< /Size 6 /Root 1 0 R >>\n'
    b'startxref\n'
    b'492\n'
    b'%%EOF\n'
)

upl = client.post(
    f'/api/bids/{bid_id}/documents',
    headers=headers,
    files={'file': ('NEW_PAN_TEST_0242.pdf', pdf, 'application/pdf')},
)
print('UPLOAD_STATUS', upl.status_code)
print('UPLOAD_BODY', upl.json())
if upl.status_code != 200:
    raise SystemExit(f'upload failed: {upl.status_code} {upl.text}')

doc_id = upl.json().get('id')
print('DOC_ID', doc_id)
db = SessionLocal()
doc = db.query(Document).filter(Document.id == doc_id).first()
print('DB_DOC_EXISTS', bool(doc))
if doc:
    print('FILE_PATH', doc.file_path)
    print('FILE_EXISTS', os.path.exists(doc.file_path))
    print('DOC_TYPE', doc.document_type)
    print('DOCUMENT_STATUS', doc.document_status)
    v = db.query(Verification).filter(Verification.document_id == doc_id).first()
    print('VERIFICATION', v.id if v else None, v.status if v else None, v.verified if v else None)
    rr = db.query(RuleResult).filter(RuleResult.bid_id == doc.bid_id).all()
    print('RULE_RESULTS', [(r.rule_id, r.result, r.finding) for r in rr])
db.close()
