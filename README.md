# BharatSetu — AI-Powered Integrated Bid Compliance Verification Platform

**Smart India Hackathon 2026 (SIH 2026)**  
**Problem Statement ID:** 26100  
**Organization:** Ministry of Petroleum & Natural Gas (MoPNG)  
**Department:** Chennai Petroleum Corporation Limited (CPCL)  
**Category:** Software  
**Theme:** Smart Automation  

---

## Executive Overview

**BharatSetu** is an AI-assisted bid compliance verification platform for GeM procurement. It processes bidder documents, extracts relevant information, evaluates tender-specific requirements, performs simulated external verification and cross-document checks, calculates compliance and risk scores, generates an explainable summary, and keeps the final procurement decision with an authorized officer.

> [!IMPORTANT]
> **Simulated APIs**: Government verification services are simulated for the SIH prototype and would require authorized G2G/API access for production deployment.

## Demo and business-rule boundaries

- Live tender discovery uses the centralized minimum estimated tender value of **₹1,00,000 and above**.
- Tender and bid amounts remain numeric in the API/database; the frontend formats them using Indian Rupee notation.
- Seeded records and uploaded certificates are synthetic demo data and are not real government records.
- Government integrations run in explicit MOCK/DEMO mode.
- AI assists document verification and explanation; an authorized procurement officer makes the final decision.
- Document integrity is preserved with SHA-256 hashing and the audit trail; no blockchain service is required by the current demo.

---

## Key Features

1. **Integrated Multi-Document Processing Pipeline**:
   - SHA-256 file hashing for instant duplicate document detection.
   - PyMuPDF / pypdf text extraction with Tesseract OCR fallback for scanned certificates.
   - Automated document classification across 30+ compliance categories (GST, PAN, Udyam, EPFO, ESIC, MCA21, Financial Statements, Work Experience, Debarment Declarations, EMD, Local Content, etc.) with confidence scoring and manual officer overrides.

2. **Tender Engine & Requirements Parser**:
   - Allows procurement officers to define tender-specific eligibility rules (Minimum Annual Turnover, Minimum Years Experience, MSME/Startup Exemptions, Local Content % Undertakings, Mandatory vs Optional certificates).

3. **Fuzzy Cross-Document Intelligence**:
   - Cross-checks entity legal names, registered addresses, GSTIN, PAN, CIN, and financial figures across uploaded certificates using token distance fuzzy matching (`RapidFuzz`).
   - Flagging address discrepancies (e.g. Pune GST address vs Nagpur Udyam address) and name variations.

4. **Pluggable Government Verification Architecture**:
   - Pluggable `VerificationProvider` interface supporting `MockGSTProvider`, `MockUdyamProvider`, `MockPANProvider`, `MockEPFOProvider`, `MockESICProvider`, `MockMCAProvider`, `MockStartupProvider`, `MockNSICProvider`, `MockDigiLockerProvider`, and `MockDebarmentProvider`.
   - Explicitly displays `"SIMULATED GOVERNMENT VERIFICATION"` in local demo mode.

5. **Deterministic Risk & Compliance Engine**:
   - Risk Score (0–100: LOW, MEDIUM, HIGH) calculated deterministically from weighted failure signals (missing mandatory docs, address mismatch, debarment matches, expired certificates).
   - Independent Compliance Score % calculation.

6. **Explainable AI & MOCK AI Chatbot**:
   - Grounded summary engine synthesizing verified backend facts without hallucinating document details.
   - Dedicated Bidder-facing `[MOCK AI]` Support Chatbot restricted by strict vendor isolation and Role-Based Access Control (RBAC).

7. **Exact-Match Suggested Tenders Engine**:
   - Analyzes fully verified compliance evidence (`verified=True` and `document_id IS NOT NULL`) to recommend new procurement opportunities to bidders, filtering out processing/failed documents.

8. **Human-in-the-Loop & Immutable Audit Ledger**:
   - Officers retain full authority to Approve, Reject (with mandatory reason), or Flag for Escalation.
   - Every system event is recorded in an immutable audit ledger (`AuditEvent`).
   - Bidder roles are explicitly isolated from accessing administrative UI controls and backend review endpoints.

9. **PDF Compliance Verification Reports**:
   - Automated ReportLab PDF generator exporting official bid compliance verification reports.
   - Explicitly watermarked with a MOCK/DEMO disclaimer to ensure transparency.

---

## Tech Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, Axios, React Router
- **Backend**: Python 3.11 / 3.14, FastAPI, SQLAlchemy 2 ORM, Pydantic V2
- **OCR & ML**: PyMuPDF, pypdf, Tesseract OCR, RapidFuzz
- **Database**: SQLite (local development) / PostgreSQL (production architecture)
- **Deployment**: Docker, Docker Compose, Nginx

---

## Quick Start & Running Locally

### 1. Backend Setup

```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The FastAPI backend will automatically create SQLite database tables and seed representative/demo tender and bidder datasets.

- **Swagger API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 2. Frontend Setup

In a separate terminal window:

```bash
cd Frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Running Unit & End-to-End Tests

```bash
python -m pytest backend/tests
```

All 5 backend test suites cover:
- Fuzzy entity name & address matching
- Document classification confidence
- Deterministic risk scoring
- End-to-end user story compliance acceptance flow

---

## Docker Deployment

To build and run the entire full-stack application with Docker Compose:

```bash
docker-compose up --build
```

- **Frontend Application**: [http://localhost:5173](http://localhost:5173)
- **Backend API**: [http://localhost:8000](http://localhost:8000)

## Vercel Deployment

The repository includes a minimal Vercel adapter at `api/index.py`. It imports the
existing `backend/app/main.py` FastAPI object; the backend application and its
verification/compliance services are not duplicated or rewritten. `vercel.json`
builds `Frontend/`, serves its SPA routes, and routes `/api/*` requests to FastAPI.

Configure these Vercel environment variables:

- `JWT_SECRET`: required; set a long random production secret.
- `DATABASE_URL`: required for durable deployment; use an externally hosted
  PostgreSQL-compatible database rather than the local SQLite default.
- `VERIFICATION_MODE=mock` and `LLM_PROVIDER=mock` for the current prototype.
- `LLM_API_KEY`: only when selecting a non-mock LLM provider.
- `OCR_ENABLED`: optional; use `true` only if the Vercel runtime has the required
  OCR support available.

Vercel serverless storage is ephemeral. Uploaded documents, generated PDFs, and
SQLite data written by this application are not persistent across deployments or
function instances. Production deployment therefore requires external durable
object storage and an external database; the existing local SQLite/upload behavior
and Docker deployment remain unchanged. Government providers remain simulated and
the boundary remains **Officer Decides. AI Verifies.**

---

## Demo Credentials & Pre-Seeded Bidders

- **Procurement Officer**: `officer@bharatsetu.gov.in` / `officer123`
- **Admin**: `admin@bharatsetu.gov.in` / `admin123`

### Pre-Seeded Demonstration Cases:
1. **Shree Lakshmi Industries Pvt Ltd** (HIGH RISK, Score 87): GST address mismatch (Pune vs Nagpur) & EPFO establishment issue.
2. **Bharat Tech Solutions LLP** (LOW RISK, Score 12): 100% verified documents, clean history.
3. **Green Earth Agro Supplies Co.** (MEDIUM RISK): EPFO inactive since June 2026.
4. **National Steel Fabricators Unit** (HIGH RISK): PAN name mismatch.
5. **MediCare Instruments Ltd** (LOW RISK, APPROVED): CDSCO verified.
6. **Vidya Educational Supplies Co.** (HIGH/MEDIUM RISK): GST cancellation flag.
