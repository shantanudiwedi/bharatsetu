from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def run_migrations():
    """Apply additive schema changes to existing databases without dropping tables."""
    if not settings.DATABASE_URL.startswith("sqlite"):
        return  # PostgreSQL uses Alembic; only handle SQLite dev migrations here.
    with engine.connect() as conn:
        # Check and add provider_mode column to verifications if missing.
        cols = conn.execute(text("PRAGMA table_info(verifications)")).fetchall()
        col_names = [c[1] for c in cols]
        if cols and "provider_mode" not in col_names:
            conn.execute(text(
                "ALTER TABLE verifications ADD COLUMN provider_mode TEXT NOT NULL DEFAULT 'MOCK'"
            ))
            conn.commit()

        # Check and add estimated_value column to tenders if missing.
        t_cols = conn.execute(text("PRAGMA table_info(tenders)")).fetchall()
        t_col_names = [c[1] for c in t_cols]
        if t_cols and "estimated_value" not in t_col_names:
            conn.execute(text(
                "ALTER TABLE tenders ADD COLUMN estimated_value REAL NOT NULL DEFAULT 0.0"
            ))
            conn.commit()
        rr_cols = conn.execute(text("PRAGMA table_info(rule_results)")).fetchall()
        rr_col_names = [c[1] for c in rr_cols]
        if rr_cols and "verification_id" not in rr_col_names:
            conn.execute(text(
                "ALTER TABLE rule_results ADD COLUMN verification_id TEXT REFERENCES verifications(id)"
            ))
            conn.commit()

try:
    run_migrations()
except Exception:
    pass
