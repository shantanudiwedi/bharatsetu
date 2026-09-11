# BHARATSETU — DEMO FREEZE
**Frozen At:** 2026-09-11 00:17 IST  
**Frozen By:** Independent Verification Agent  
**Purpose:** SIH 2026 — Problem Statement 26100 — Demo on 2026-09-11

---

## ⚠️ FREEZE PROTOCOL

This codebase is FROZEN for the SIH 2026 demo.

**DO NOT:**
- Merge any new branches
- Run any database migrations
- Apply any schema changes
- Delete or rename any files
- Change any seeded test accounts
- Modify authentication or RBAC logic

---

## Verified State

| Component | Status |
|-----------|--------|
| Backend (FastAPI) | ✅ RUNNING — `127.0.0.1:8000` |
| Frontend (Vite/React) | ✅ RUNNING — `localhost:5173` |
| Pytest (38/38) | ✅ PASS |
| TypeScript typecheck | ✅ PASS |
| Production build | ✅ PASS |

---

## Implemented & Verified Features

- ✅ **Chatbot** — Secure markdown rendering, HTTP 400 on empty/whitespace query, dynamic DB compliance score, bidder isolation, officer RBAC
- ✅ **Tenders** — Hard filter: `estimated_value >= ₹1,00,000` on listings, search, and suggested tenders
- ✅ **Bidder Registration** — `/api/auth/register` with role enforcement (BIDDER only), duplicate email/PAN prevention, vendor record creation
- ✅ **PDF Security** — Magic-byte validation (`%PDF-`), IDOR protection (403 cross-bidder), inline Content-Disposition
- ✅ **Bidder Dashboard** — Dynamic metrics, compliance percentage, action items, vendor name
- ✅ **Officer Dashboard** — Flagged bids, verification queue, audit trail
- ✅ **Audit Trail** — Immutable event log, 17 seeded events
- ✅ **Suggested Tenders** — Server-side filtered, match scoring, readiness rating
- ✅ **Notifications** — Unread count, per-user scoping
- ✅ **AI Advisory Mode** — Officer Decides. AI Verifies. No auto-approval.

---

## Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Officer | `officer@bharatsetu.gov.in` | `officer123` |
| Admin | `admin@bharatsetu.gov.in` | `officer123` |
| Bidder A (active bids, 92% compliance) | `biddera@bharatsetu.gov.in` | `bidder123` |
| Bidder B | `bidderb@bharatsetu.gov.in` | `bidder123` |

---

## Demo Flow (Recommended)

1. **Login as Bidder A** → Show Dashboard (92% compliance, action items)
2. **View Suggested Tenders** → Show match scoring and ₹1L filter in effect
3. **Open Support/Chatbot** → Ask "What is my compliance status?" → Show clean formatted response with dynamic score
4. **Logout → Login as Officer** → Show flagged bids queue
5. **Open a bid** → Show document verification table, risk score, explainability
6. **Show Audit Trail** → Immutable event log
7. **Register new bidder** → Show `/register` flow with role enforcement

---

## Architecture Principles (Do Not Violate)

- **Officer Decides. AI Verifies.** — No route auto-approves bids
- **Bidder Isolation** — Bidders can only see their own vendor's data
- **No Live Government APIs** — All external integrations are MOCK/simulated
- **Stability > Security > Correctness > PPT Alignment > Polish**
