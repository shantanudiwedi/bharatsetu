"""Vercel entrypoint for the existing BharatSetu FastAPI application."""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app

__all__ = ["app"]
