import os
import subprocess
import sys
from pathlib import Path
from tempfile import gettempdir


def test_vercel_upload_directory_uses_writable_temp_storage():
    backend_dir = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["VERCEL"] = "1"
    env.pop("UPLOAD_DIR", None)

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from app.core.config import settings; "
                "from pathlib import Path; "
                "path = Path(settings.UPLOAD_DIR); "
                "assert path.exists(); "
                "print(path)"
            ),
        ],
        cwd=backend_dir,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    upload_dir = Path(result.stdout.strip())
    assert upload_dir == Path(gettempdir()) / "bharatsetu_uploads"
    assert upload_dir != backend_dir.parent / "uploads"
