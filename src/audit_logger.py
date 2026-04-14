"""Audit logging utilities.

Persists user-provided inputs and records run metadata in audit/log.json.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

AUDIT_DIR = Path("audit")
LOG_FILE = AUDIT_DIR / "log.json"


def _ensure_audit_dir() -> None:
    """Create the audit directory if it does not exist."""
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def generate_audit_filename(original_filename: str, now: Optional[datetime] = None) -> str:
    """Return a timestamped audit filename.

    Format: ``YYYYMMDD_HHmmss_<original_filename>``
    """
    if now is None:
        now = datetime.now(timezone.utc)
    prefix = now.strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{original_filename}"


def copy_to_audit(source_path: Path, now: Optional[datetime] = None) -> str:
    """Copy *source_path* into the audit directory with a timestamped name.

    Returns the audit filename (not the full path).
    """
    _ensure_audit_dir()
    audit_name = generate_audit_filename(source_path.name, now=now)
    destination = AUDIT_DIR / audit_name
    shutil.copy2(source_path, destination)
    return audit_name


def _read_log() -> list[dict]:
    """Read existing log entries from *LOG_FILE*."""
    if LOG_FILE.exists():
        text = LOG_FILE.read_text(encoding="utf-8").strip()
        if text:
            return json.loads(text)  # type: ignore[no-any-return]
    return []


def _write_log(entries: list[dict]) -> None:
    """Persist *entries* to *LOG_FILE*."""
    _ensure_audit_dir()
    LOG_FILE.write_text(json.dumps(entries, indent=2, default=str) + "\n", encoding="utf-8")


def log_entry(
    original_filename: str,
    audit_filename: str,
    status: str,
    output_file: Optional[str] = None,
    error: Optional[str] = None,
    now: Optional[datetime] = None,
) -> dict:
    """Append a run-log entry to ``audit/log.json`` and return it."""
    if now is None:
        now = datetime.now(timezone.utc)

    entry: dict = {
        "timestamp": now.isoformat(),
        "original_filename": original_filename,
        "audit_filename": audit_filename,
        "status": status,
        "output_file": output_file,
        "error": error,
    }

    entries = _read_log()
    entries.append(entry)
    _write_log(entries)
    return entry
