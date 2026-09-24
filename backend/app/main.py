import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.database import engine, Base, run_migrations
from app.db.seed_data import seed_db, seed_demo_users

from app.api.routes.auth import router as auth_router
from app.api.routes.tenders import router as tenders_router
from app.api.routes.vendors import router as vendors_router
from app.api.routes.bids import router as bids_router
from app.api.routes.review import router as review_router
from app.api.routes.audit import router as audit_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.verification import router as verification_router
from app.api.routes.reports import router as reports_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.support import router as support_router
from app.api.routes.bidder import router as bidder_router
from app.api.routes.ai import router as ai_router
from app.services.notifications.deadline_scheduler import (
    start_deadline_scheduler,
    stop_deadline_scheduler,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="BharatSetu AI-Powered Integrated Bid Compliance Verification Platform API for SIH 2026 (CPCL / MoPNG)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# AUDIT ITEM 13: Strict CORS configuration (specific origins with allow_credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(tenders_router, prefix=settings.API_V1_STR)
app.include_router(vendors_router, prefix=settings.API_V1_STR)
app.include_router(bids_router, prefix=settings.API_V1_STR)
app.include_router(review_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)
app.include_router(verification_router, prefix=settings.API_V1_STR)
app.include_router(reports_router, prefix=settings.API_V1_STR)
app.include_router(notifications_router, prefix=settings.API_V1_STR)
app.include_router(support_router, prefix=settings.API_V1_STR)
app.include_router(bidder_router, prefix=settings.API_V1_STR)
app.include_router(ai_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    run_migrations()
    if os.getenv("VERCEL"):
        seed_demo_users()
    else:
        seed_db()
    start_deadline_scheduler()


@app.on_event("shutdown")
def on_shutdown():
    stop_deadline_scheduler()


@app.get("/")
def root():
    return {
        "title": settings.PROJECT_NAME,
        "status": "ONLINE",
        "mode": settings.VERIFICATION_MODE,
        "docs": "/docs",
        "api_v1": settings.API_V1_STR
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
