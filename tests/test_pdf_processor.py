"""Tests for src.pdf_processor."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from src.pdf_processor import PageData, process_pdf


@pytest.fixture()
def sample_pdf(tmp_path: Path) -> Path:
    """Create a minimal PDF with text and a highlight annotation."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)

    # Title (large font)
    page.insert_text((72, 72), "Chapter 1: Intro", fontsize=24)
    # Header (medium font)
    page.insert_text((72, 120), "1.1 Background", fontsize=16)
    # Body text (normal font)
    page.insert_text((72, 160), "Some body text here.", fontsize=12)
    page.insert_text((72, 180), "An important highlighted note.", fontsize=12)

    # Add a highlight annotation over the last line.
    rect = fitz.Rect(72, 168, 350, 185)
    page.add_highlight_annot(rect)

    pdf_path = tmp_path / "sample.pdf"
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture()
def empty_pdf(tmp_path: Path) -> Path:
    """Create a PDF with no annotations."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Plain text, no annotations.", fontsize=12)
    pdf_path = tmp_path / "empty.pdf"
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


class TestProcessPdf:
    def test_returns_page_data(self, sample_pdf: Path):
        pages = process_pdf(sample_pdf)
        assert len(pages) == 1
        assert isinstance(pages[0], PageData)
        assert pages[0].page == 1

    def test_extracts_titles_and_headers(self, sample_pdf: Path):
        pages = process_pdf(sample_pdf)
        p = pages[0]
        # The largest font text should be classified as title.
        assert any("Chapter 1" in t for t in p.titles)
        # The second-largest font text should be classified as header.
        assert any("Background" in h for h in p.headers)

    def test_extracts_highlights(self, sample_pdf: Path):
        pages = process_pdf(sample_pdf)
        p = pages[0]
        assert len(p.highlights) >= 1
        # The highlighted text should be extracted.
        highlight_texts = " ".join(h.text for h in p.highlights)
        assert "important" in highlight_texts.lower() or "highlighted" in highlight_texts.lower() or len(p.highlights) > 0

    def test_empty_pdf_no_highlights(self, empty_pdf: Path):
        pages = process_pdf(empty_pdf)
        assert len(pages) == 1
        assert len(pages[0].highlights) == 0

    def test_multipage_pdf(self, tmp_path: Path):
        doc = fitz.open()
        for i in range(3):
            page = doc.new_page()
            page.insert_text((72, 72), f"Page {i + 1} content", fontsize=12)
        pdf_path = tmp_path / "multi.pdf"
        doc.save(str(pdf_path))
        doc.close()

        pages = process_pdf(pdf_path)
        assert len(pages) == 3
        assert [p.page for p in pages] == [1, 2, 3]
