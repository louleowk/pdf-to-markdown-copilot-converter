"""Tests for src.markdown_writer."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.cross_page_merger import MergedHighlight
from src.markdown_writer import build_markdown, write_markdown
from src.pdf_processor import HighlightAnnotation, PageData


def _page(
    page_num: int,
    titles: list[str] | None = None,
    headers: list[str] | None = None,
    highlights: list[str] | None = None,
) -> PageData:
    return PageData(
        page=page_num,
        titles=titles or [],
        headers=headers or [],
        highlights=[
            HighlightAnnotation(text=t, page=page_num, coordinates={"x0": 0, "y0": 0, "x1": 0, "y1": 0})
            for t in (highlights or [])
        ],
    )


class TestBuildMarkdown:
    def test_basic_structure(self):
        pages = [_page(1, titles=["My Title"], headers=["Section A"], highlights=["Note 1"])]
        md = build_markdown(pages)
        assert md.startswith("# My Title\n")
        assert "## Page 1" in md
        assert "### My Title" in md
        assert "#### Section A" in md
        assert "> Note 1" in md

    def test_custom_document_title(self):
        pages = [_page(1)]
        md = build_markdown(pages, document_title="Custom Title")
        assert md.startswith("# Custom Title\n")

    def test_fallback_title(self):
        pages = [_page(1)]
        md = build_markdown(pages)
        assert md.startswith("# Extracted Notes\n")

    def test_multiple_pages(self):
        pages = [
            _page(1, titles=["Title 1"]),
            _page(2, titles=["Title 2"]),
        ]
        md = build_markdown(pages)
        assert "## Page 1" in md
        assert "## Page 2" in md

    def test_merged_highlights_section(self):
        pages = [_page(1), _page(2)]
        merged = [
            MergedHighlight(
                text="Merged text across pages.",
                pages=[1, 2],
                coordinates_start={"x0": 0, "y0": 0, "x1": 0, "y1": 0},
                coordinates_end={"x0": 0, "y0": 0, "x1": 0, "y1": 0},
            )
        ]
        md = build_markdown(pages, merged_highlights=merged)
        assert "## Cross-Page Highlights" in md
        assert "Merged text across pages." in md
        assert "Pages 1–2" in md


class TestWriteMarkdown:
    def test_writes_file(self, tmp_path: Path):
        content = "# Hello\n\nWorld\n"
        path = write_markdown(content, "doc.pdf", output_dir=tmp_path)
        assert path == tmp_path / "doc_notes.md"
        assert path.read_text() == content

    def test_creates_output_dir(self, tmp_path: Path):
        out_dir = tmp_path / "nested" / "output"
        path = write_markdown("# Test\n", "file.pdf", output_dir=out_dir)
        assert path.exists()
        assert path.parent == out_dir
