from __future__ import annotations

import os
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv


def resolve_env_path() -> str:
    """Return the per-user .env path for the application.

    Windows: %LOCALAPPDATA%/UpdatedIOCChecker/.env
    macOS:   $HOME/Library/Application Support/UpdatedIOCChecker/.env
    Linux:   $HOME/.config/UpdatedIOCChecker/.env
    """
    import platform as _platform

    system = _platform.system().lower()
    if system.startswith("win"):
        base = os.getenv("LOCALAPPDATA", os.path.expanduser("~"))
        return str(Path(base) / "UpdatedIOCChecker" / ".env")
    if system == "darwin":
        return str(Path.home() / "Library" / "Application Support" / "UpdatedIOCChecker" / ".env")
    return str(Path.home() / ".config" / "UpdatedIOCChecker" / ".env")


def load_env_file(path: str) -> bool:
    """Load environment variables from the given .env path.

    Returns True if the file exists and loading did not raise; False otherwise.
    Does not log or expose secret values.
    """
    try:
        if not path:
            return False
        if not os.path.exists(path):
            return False
        load_dotenv(path, override=True)
        return True
    except Exception:
        return False


def save_env_kv(path: str, mapping: Dict[str, str]) -> None:
    """Persist key/value pairs to the .env file at path.

    Ensures the parent directory exists. Keys are written one per line as
    KEY=VALUE with no quoting, matching prior behavior. Secrets are not logged.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for k, v in mapping.items():
        k_s = str(k).strip()
        v_s = str(v or "").strip()
        lines.append(f"{k_s}={v_s}\n")
    p.write_text("".join(lines), encoding="utf-8")


