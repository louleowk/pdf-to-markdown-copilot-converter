"""Tests for src.tracer."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.cross_page_merger import MergedHighlight
from src.pdf_processor import HighlightAnnotation, PageData
from src.tracer import Tracer, generate_trace_id


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def trace_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect TRACE_DIR to a temp directory for every test."""
    td = tmp_path / "trace"
    monkeypatch.setattr("src.tracer.TRACE_DIR", td)
    return td


def _make_pages() -> list[PageData]:
    return [
        PageData(
            page=1,
            titles=["Title A"],
            headers=["Header A"],
            highlights=[
                HighlightAnnotation(
                    text="highlight one",
                    page=1,
                    coordinates={"x0": 0.0, "y0": 0.0, "x1": 100.0, "y1": 20.0},
                )
            ],
        ),
        PageData(
            page=2,
            titles=[],
            headers=["Header B"],
            highlights=[],
        ),
    ]


def _make_merged() -> list[MergedHighlight]:
    return [
        MergedHighlight(
            text="merged text",
            pages=[1, 2],
            coordinates_start={"x0": 0.0, "y0": 700.0, "x1": 100.0, "y1": 720.0},
            coordinates_end={"x0": 0.0, "y0": 0.0, "x1": 100.0, "y1": 20.0},
        )
    ]


# ---------------------------------------------------------------------------
# generate_trace_id
# ---------------------------------------------------------------------------


class TestGenerateTraceId:
    def test_returns_hex_string(self):
        tid = generate_trace_id()
        assert isinstance(tid, str)
        assert len(tid) == 32
        int(tid, 16)  # should not raise

    def test_unique(self):
        ids = {generate_trace_id() for _ in range(100)}
        assert len(ids) == 100


# ---------------------------------------------------------------------------
# Tracer.create
# ---------------------------------------------------------------------------


class TestTracerCreate:
    def test_creates_directory(self, trace_dir: Path):
        tracer = Tracer.create()
        assert tracer.root.exists()
        assert tracer.root.parent == trace_dir

    def test_custom_trace_id(self, trace_dir: Path):
        tracer = Tracer.create(trace_id="abc123")
        assert tracer.trace_id == "abc123"
        assert tracer.root == trace_dir / "abc123"
        assert tracer.root.is_dir()


# ---------------------------------------------------------------------------
# save_page_data
# ---------------------------------------------------------------------------


class TestSavePageData:
    def test_writes_per_page_json(self, trace_dir: Path):
        tracer = Tracer.create(trace_id="test-pages")
        pages = _make_pages()
        tracer.save_page_data(pages)

        for page in pages:
            path = tracer.root / f"page_{page.page}_raw.json"
            assert path.exists(), f"Missing {path}"
            data = json.loads(path.read_text())
            assert data["page"] == page.page
            assert data["titles"] == page.titles
            assert data["headers"] == page.headers

    def test_highlight_coordinates_serialised(self, trace_dir: Path):
        tracer = Tracer.create(trace_id="test-coords")
        pages = _make_pages()
        tracer.save_page_data(pages)

        data = json.loads((tracer.root / "page_1_raw.json").read_text())
        h = data["highlights"][0]
        assert h["text"] == "highlight one"
        assert h["coordinates"]["x0"] == 0.0


# ---------------------------------------------------------------------------
# save_extracted_data
# ---------------------------------------------------------------------------


class TestSaveExtractedData:
    def test_writes_extracted_and_merged(self, trace_dir: Path):
        tracer = Tracer.create(trace_id="test-extracted")
        pages = _make_pages()
        merged = _make_merged()
        tracer.save_extracted_data(pages, merged)

        for page in pages:
            path = tracer.root / f"page_{page.page}_extracted.json"
            assert path.exists()

        merged_path = tracer.root / "merged_highlights.json"
        assert merged_path.exists()
        merged_data = json.loads(merged_path.read_text())
        assert len(merged_data) == 1
        assert merged_data[0]["text"] == "merged text"
        assert merged_data[0]["pages"] == [1, 2]

    def test_empty_merged(self, trace_dir: Path):
        tracer = Tracer.create(trace_id="test-empty-merge")
        tracer.save_extracted_data(_make_pages(), [])
        data = json.loads((tracer.root / "merged_highlights.json").read_text())
        assert data == []


# ---------------------------------------------------------------------------
# save_raw_markdown / save_formatted_markdown
# ---------------------------------------------------------------------------


class TestSaveMarkdown:
    def test_raw_markdown(self, trace_dir: Path):
        tracer = Tracer.create(trace_id="test-raw-md")
        tracer.save_raw_markdown("# Hello\n")
        assert (tracer.root / "raw_markdown.txt").read_text() == "# Hello\n"

    def test_formatted_markdown(self, trace_dir: Path):
        tracer = Tracer.create(trace_id="test-fmt-md")
        tracer.save_formatted_markdown("# Formatted\n")
        assert (tracer.root / "formatted_markdown.txt").read_text() == "# Formatted\n"


# ---------------------------------------------------------------------------
# save_metadata
# ---------------------------------------------------------------------------


class TestSaveMetadata:
    def test_writes_metadata_json(self, trace_dir: Path):
        tracer = Tracer.create(trace_id="test-meta")
        now = datetime(2026, 4, 14, 12, 0, 0, tzinfo=timezone.utc)
        tracer.save_metadata(
            input_file="doc.pdf",
            ai_provider="copilot",
            output_file="output/doc_notes.md",
            now=now,
        )
        data = json.loads((tracer.root / "trace_meta.json").read_text())
        assert data["trace_id"] == "test-meta"
        assert data["input_file"] == "doc.pdf"
        assert data["ai_provider"] == "copilot"
        assert data["output_file"] == "output/doc_notes.md"
        assert data["timestamp"] == "2026-04-14T12:00:00+00:00"

    def test_metadata_defaults(self, trace_dir: Path):
        tracer = Tracer.create(trace_id="test-meta-defaults")
        tracer.save_metadata(input_file="x.pdf")
        data = json.loads((tracer.root / "trace_meta.json").read_text())
        assert data["ai_provider"] is None
        assert data["output_file"] is None


# ---------------------------------------------------------------------------
# _NoopTracer
# ---------------------------------------------------------------------------


class TestNoopTracer:
    def test_noop_does_not_write(self, trace_dir: Path):
        tracer = Tracer.noop()
        pages = _make_pages()
        merged = _make_merged()

        tracer.save_page_data(pages)
        tracer.save_extracted_data(pages, merged)
        tracer.save_raw_markdown("text")
        tracer.save_formatted_markdown("text")
        tracer.save_metadata(input_file="x.pdf")

        # trace_dir should still be empty.
        assert not any(trace_dir.iterdir()) if trace_dir.exists() else True
