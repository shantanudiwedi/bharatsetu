# BharatSetu

AI-Powered Integrated Bid Compliance Verification Platform for GeM Procurement

**Problem Statement:** SIH26100 (Smart India Hackathon 2026)
**Ministry:** Petroleum & Natural Gas (CPCL)
**Team:** AXON

## Overview
BharatSetu automates bidder compliance verification for GeM procurement — 
checking Udyam/MSME, GST, PAN, EPFO, and blacklist status against tender 
eligibility rules, producing a Compliance Score, Risk Level, and 
AI Recommendation. The officer always makes the final decision — 
AI never auto-approves or auto-rejects.

## Core Features
- **Officer Dashboard** — bidder list, risk levels, flagged issues, sortable/filterable
- **Bidder Self-Check Portal** — upload documents, see flags before final submission
- **Full audit trail** — every check logged with source, confidence, timestamp

## Architecture
Inputs (bidder docs + eligibility rules) → Orchestrator 
(Document Extraction Agent → Cross-Check Agent → Risk Scoring Agent) 
→ Decisions (Compliance Score + Risk Level + Recommendation, officer decides)

5-layer system: Experience → Application → Intelligence → Data → Integration

## Tech Stack
- Frontend: React + Tailwind CSS
- Backend: FastAPI (Python)
- OCR: Tesseract (pytesseract)
- NLP: Regex + spaCy for entity extraction
- Rules Engine: Config-driven (JSON/YAML) Python logic
- Database: SQLite (dev) 
- Deployment: Vercel (frontend), Render (backend)

## Status
https://bharatsetu-hsgd5oehm-shantanudiwedis-projects.vercel.app/

## Team AXON
Shantanu Diwedi | Sarthak Gaikwad | Purnima Dwivedi | Mahesh Giram | Aayush Satarkar | Sumedh Jadhav 
