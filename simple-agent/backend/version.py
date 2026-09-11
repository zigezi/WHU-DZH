import os
import subprocess


def get_code_version() -> str:
    """Return short git HEAD for the current code, or 'unknown' on failure."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            if version:
                return version
    except Exception:
        pass
    return "unknown"
