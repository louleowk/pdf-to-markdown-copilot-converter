"""PDF Processor — extract titles, headers, and highlight annotations.

Uses PyMuPDF (``fitz``) to parse each page of a PDF and return a structured
intermediate representation suitable for downstream formatting.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF


@dataclasses.dataclass
class HighlightAnnotation:
    """A single highlight annotation extracted from a PDF."""

    text: str
    page: int
    coordinates: dict  # {"x0": float, "y0": float, "x1": float, "y1": float}


@dataclasses.dataclass
class PageData:
    """Extracted data for a single PDF page."""

    page: int
    titles: list[str] = dataclasses.field(default_factory=list)
    headers: list[str] = dataclasses.field(default_factory=list)
    highlights: list[HighlightAnnotation] = dataclasses.field(default_factory=list)


def _classify_text_blocks(page: fitz.Page) -> tuple[list[str], list[str]]:
    """Classify text blocks on a page into titles and headers by font size.

    Returns ``(titles, headers)`` where *titles* are blocks with the largest
    font size and *headers* are blocks with the second-largest font size.
    """
    blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]

    # Collect (text, max_font_size) for each block that contains text lines.
    sized_texts: list[tuple[str, float]] = []
    for block in blocks:
        if block.get("type") != 0:  # skip image blocks
            continue
        max_size = 0.0
        full_text_parts: list[str] = []
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                span_text = span.get("text", "").strip()
                if span_text:
                    full_text_parts.append(span_text)
                    if span["size"] > max_size:
                        max_size = span["size"]
        full_text = " ".join(full_text_parts).strip()
        if full_text and max_size > 0:
            sized_texts.append((full_text, max_size))

    if not sized_texts:
        return [], []

    # Determine unique font sizes (sorted descending).
    unique_sizes = sorted({s for _, s in sized_texts}, reverse=True)

    # Body text is the most common (smallest used) size; anything bigger is a
    # heading.  We treat the largest size as "title" and the next-largest as
    # "header".
    if len(unique_sizes) < 2:
        return [], []  # Only one font size → all body text

    title_size = unique_sizes[0]
    header_size = unique_sizes[1]

    titles = [t for t, s in sized_texts if s == title_size]
    headers = [t for t, s in sized_texts if s == header_size]

    return titles, headers


def _extract_highlights(page: fitz.Page, page_number: int) -> list[HighlightAnnotation]:
    """Extract highlight annotations from *page*."""
    highlights: list[HighlightAnnotation] = []
    for annot in page.annots() or []:
        if annot.type[0] != fitz.PDF_ANNOT_HIGHLIGHT:
            continue

        # Get the rectangle of the annotation and extract text within it.
        rect = annot.rect
        text = page.get_textbox(rect).strip()
        if not text:
            # Fallback: use the annotation's info content if textbox is empty.
            text = (annot.info.get("content") or "").strip()
        if text:
            highlights.append(
                HighlightAnnotation(
                    text=text,
                    page=page_number,
                    coordinates={
                        "x0": round(rect.x0, 2),
                        "y0": round(rect.y0, 2),
                        "x1": round(rect.x1, 2),
                        "y1": round(rect.y1, 2),
                    },
                )
            )
    return highlights


def process_pdf(pdf_path: Path) -> list[PageData]:
    """Parse *pdf_path* and return a list of :class:`PageData` objects.

    Each entry contains titles, headers, and highlight annotations for one page.
    """
    doc = fitz.open(str(pdf_path))
    pages: list[PageData] = []

    try:
        for page_number in range(len(doc)):
            page = doc[page_number]
            titles, headers = _classify_text_blocks(page)
            highlights = _extract_highlights(page, page_number + 1)  # 1-indexed

            pages.append(
                PageData(
                    page=page_number + 1,
                    titles=titles,
                    headers=headers,
                    highlights=highlights,
                )
            )
    finally:
        doc.close()

    return pages
