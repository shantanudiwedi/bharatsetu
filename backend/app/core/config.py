import os
import tempfile
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = BASE_DIR / "bharatsetu.db"
VERCEL_DB_PATH = Path(tempfile.gettempdir()) / "bharatsetu.db"
DEFAULT_UPLOAD_DIR = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../uploads")))
VERCEL_UPLOAD_DIR = Path(tempfile.gettempdir()) / "bharatsetu_uploads"


def _default_database_url() -> str:
    """Use writable ephemeral storage for the Vercel demo when unset."""
    if os.getenv("VERCEL"):
        return f"sqlite:///{VERCEL_DB_PATH}"
    return f"sqlite:///{DEFAULT_DB_PATH}"


def _default_upload_dir() -> str:
    if os.getenv("VERCEL"):
        return str(VERCEL_UPLOAD_DIR)
    return os.getenv("UPLOAD_DIR") or str(DEFAULT_UPLOAD_DIR)

class Settings(BaseSettings):
    PROJECT_NAME: str = "BharatSetu Bid Compliance Verification Platform"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("JWT_SECRET", "development-only-change-this-secret")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL") or _default_database_url()
    
    # Storage & Uploads
    UPLOAD_DIR: str = _default_upload_dir()
    MAX_FILE_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB max
    ALLOWED_EXTENSIONS: set = {".pdf", ".png", ".jpg", ".jpeg"}

    # CORS
    ALLOWED_ORIGINS: list = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://0.0.0.0:4173"
    ]
    
    # Modes
    VERIFICATION_MODE: str = os.getenv("VERIFICATION_MODE", "mock")  # mock | production
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock")  # mock | openai | gemini
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    OCR_ENABLED: bool = os.getenv("OCR_ENABLED", "true").lower() == "true"

    class Config:
        case_sensitive = True

settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
