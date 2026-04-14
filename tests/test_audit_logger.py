"""Tests for src.audit_logger."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from src.audit_logger import (
    LOG_FILE,
    copy_to_audit,
    generate_audit_filename,
    log_entry,
)


@pytest.fixture(autouse=True)
def _use_tmp_audit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Redirect AUDIT_DIR and LOG_FILE to a temp directory for every test."""
    audit_dir = tmp_path / "audit"
    audit_dir.mkdir()
    monkeypatch.setattr("src.audit_logger.AUDIT_DIR", audit_dir)
    monkeypatch.setattr("src.audit_logger.LOG_FILE", audit_dir / "log.json")


class TestGenerateAuditFilename:
    def test_basic(self):
        now = datetime(2026, 4, 14, 11, 57, 0, tzinfo=timezone.utc)
        result = generate_audit_filename("my_document.pdf", now=now)
        assert result == "20260414_115700_my_document.pdf"

    def test_uses_current_time_when_none(self):
        result = generate_audit_filename("file.pdf")
        # Just verify format: YYYYMMDD_HHmmss_file.pdf
        assert result.endswith("_file.pdf")
        assert len(result) > len("_file.pdf")


class TestCopyToAudit:
    def test_copies_file(self, tmp_path: Path):
        # Create a source PDF file.
        source = tmp_path / "source.pdf"
        source.write_text("fake pdf content")

        now = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        audit_name = copy_to_audit(source, now=now)

        assert audit_name == "20260101_000000_source.pdf"
        # The file should exist in the (monkeypatched) audit dir.
        from src.audit_logger import AUDIT_DIR
        assert (AUDIT_DIR / audit_name).exists()


class TestLogEntry:
    def test_creates_log_file_and_appends(self):
        now = datetime(2026, 4, 14, 12, 0, 0, tzinfo=timezone.utc)
        entry = log_entry(
            original_filename="doc.pdf",
            audit_filename="20260414_120000_doc.pdf",
            status="started",
            now=now,
        )
        assert entry["status"] == "started"
        assert entry["original_filename"] == "doc.pdf"

        # Read back from file.
        from src.audit_logger import LOG_FILE
        entries = json.loads(LOG_FILE.read_text())
        assert len(entries) == 1
        assert entries[0]["status"] == "started"

    def test_appends_multiple_entries(self):
        now1 = datetime(2026, 4, 14, 12, 0, 0, tzinfo=timezone.utc)
        now2 = datetime(2026, 4, 14, 12, 1, 0, tzinfo=timezone.utc)
        log_entry("a.pdf", "ts_a.pdf", "started", now=now1)
        log_entry("a.pdf", "ts_a.pdf", "completed", output_file="output/a_notes.md", now=now2)

        from src.audit_logger import LOG_FILE
        entries = json.loads(LOG_FILE.read_text())
        assert len(entries) == 2
        assert entries[1]["status"] == "completed"
        assert entries[1]["output_file"] == "output/a_notes.md"

    def test_log_entry_with_error(self):
        entry = log_entry("b.pdf", "ts_b.pdf", "failed", error="something broke")
        assert entry["error"] == "something broke"
