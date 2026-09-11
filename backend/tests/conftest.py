import sys
import os
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings


@pytest.fixture(autouse=True)
def isolate_upload_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    tmp_path.mkdir(parents=True, exist_ok=True)
