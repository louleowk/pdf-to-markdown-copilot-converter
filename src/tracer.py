"""Tracing utilities for debugging and verification.

When tracing is enabled via the ``--trace`` CLI flag, a unique trace ID is
generated for the run and all intermediate data is persisted under
``trace/<trace_id>/`` so that humans or other agents can verify whether the
produced Markdown file uses the correct extracted information.

Persisted artefacts (per page):
- ``page_<N>_raw.json``       — raw :class:`PageData` as returned by the PDF processor
- ``page_<N>_extracted.json`` — page data after cross-page merging

Global artefacts:
- ``merged_highlights.json``  — cross-page merged highlights
- ``raw_markdown.txt``        — Markdown before AI formatting
- ``formatted_markdown.txt``  — final Markdown after AI formatting (or fallback)
- ``trace_meta.json``         — metadata about the trace run
"""

from __future__ import annotations

import dataclasses
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.cross_page_merger import MergedHighlight
from src.pdf_processor import PageData

TRACE_DIR = Path("trace")


def generate_trace_id() -> str:
    """Return a new unique trace identifier (UUID4 hex string)."""
    return uuid.uuid4().hex


def _trace_root(trace_id: str) -> Path:
    """Return the root directory for a given *trace_id*."""
    return TRACE_DIR / trace_id


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _serialise_page_data(page: PageData) -> dict:
    """Convert a :class:`PageData` instance to a JSON-serialisable dict."""
    return dataclasses.asdict(page)


def _serialise_merged(merged: list[MergedHighlight]) -> list[dict]:
    """Convert a list of :class:`MergedHighlight` to JSON-serialisable dicts."""
    return [dataclasses.asdict(m) for m in merged]


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------


class Tracer:
    """Collects and persists trace artefacts for a single CLI run.

    Usage::

        tracer = Tracer.create()       # or Tracer.noop() when disabled
        tracer.save_page_data(pages)
        tracer.save_extracted_data(pages, merged)
        tracer.save_raw_markdown(raw_md)
        tracer.save_formatted_markdown(formatted_md)
    """

    def __init__(self, trace_id: str, root: Path) -> None:
        self.trace_id = trace_id
        self.root = root

    # -- Factory helpers ---------------------------------------------------

    @classmethod
    def create(cls, trace_id: Optional[str] = None) -> Tracer:
        """Create a new active tracer, ensuring its directory exists."""
        if trace_id is None:
            trace_id = generate_trace_id()
        root = _trace_root(trace_id)
        _ensure_dir(root)
        return cls(trace_id=trace_id, root=root)

    @classmethod
    def noop(cls) -> _NoopTracer:
        """Return a tracer that silently discards all data."""
        return _NoopTracer()

    # -- Persistence helpers -----------------------------------------------

    def _write_json(self, filename: str, data: object) -> Path:
        path = self.root / filename
        path.write_text(
            json.dumps(data, indent=2, default=str, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return path

    def _write_text(self, filename: str, text: str) -> Path:
        path = self.root / filename
        path.write_text(text, encoding="utf-8")
        return path

    # -- Public save methods ------------------------------------------------

    def save_page_data(self, pages: list[PageData]) -> None:
        """Persist the raw per-page data from the PDF processor."""
        for page in pages:
            self._write_json(
                f"page_{page.page}_raw.json",
                _serialise_page_data(page),
            )

    def save_extracted_data(
        self,
        pages: list[PageData],
        merged: list[MergedHighlight],
    ) -> None:
        """Persist per-page data after cross-page merging and the merged list."""
        for page in pages:
            self._write_json(
                f"page_{page.page}_extracted.json",
                _serialise_page_data(page),
            )
        self._write_json("merged_highlights.json", _serialise_merged(merged))

    def save_raw_markdown(self, markdown: str) -> None:
        """Persist the raw Markdown (before AI formatting)."""
        self._write_text("raw_markdown.txt", markdown)

    def save_formatted_markdown(self, markdown: str) -> None:
        """Persist the final formatted Markdown."""
        self._write_text("formatted_markdown.txt", markdown)

    def save_metadata(
        self,
        input_file: str,
        ai_provider: Optional[str] = None,
        output_file: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> None:
        """Persist a small metadata JSON summarising the trace run."""
        if now is None:
            now = datetime.now(timezone.utc)
        self._write_json(
            "trace_meta.json",
            {
                "trace_id": self.trace_id,
                "timestamp": now.isoformat(),
                "input_file": input_file,
                "ai_provider": ai_provider,
                "output_file": output_file,
            },
        )


class _NoopTracer(Tracer):
    """A tracer that does nothing — used when tracing is disabled."""

    def __init__(self) -> None:  # noqa: D107
        # Intentionally skip super().__init__ — no directory needed.
        self.trace_id = ""
        self.root = Path()

    def save_page_data(self, pages: list[PageData]) -> None:  # noqa: D102
        pass

    def save_extracted_data(  # noqa: D102
        self,
        pages: list[PageData],
        merged: list[MergedHighlight],
    ) -> None:
        pass

    def save_raw_markdown(self, markdown: str) -> None:  # noqa: D102
        pass

    def save_formatted_markdown(self, markdown: str) -> None:  # noqa: D102
        pass

    def save_metadata(  # noqa: D102
        self,
        input_file: str,
        ai_provider: Optional[str] = None,
        output_file: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> None:
        pass
