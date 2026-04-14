"""Markdown output generator.

Converts the structured intermediate representation produced by the PDF
processor (and cross-page merger) into a well-formatted Markdown file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.cross_page_merger import MergedHighlight
from src.pdf_processor import PageData


def _build_page_section(page: PageData) -> str:
    """Render a single page's data as Markdown."""
    lines: list[str] = []
    lines.append(f"## Page {page.page}")
    lines.append("")

    for title in page.titles:
        lines.append(f"### {title}")
        lines.append("")

    for header in page.headers:
        lines.append(f"#### {header}")
        lines.append("")

    for highlight in page.highlights:
        lines.append(f"> {highlight.text}")
        lines.append("")

    return "\n".join(lines)


def _build_merged_section(merged: list[MergedHighlight]) -> str:
    """Render merged (cross-page) highlights as a Markdown section."""
    if not merged:
        return ""

    lines: list[str] = []
    lines.append("## Cross-Page Highlights")
    lines.append("")
    for m in merged:
        page_range = "–".join(str(p) for p in m.pages)
        lines.append(f"> *(Pages {page_range})* {m.text}")
        lines.append("")

    return "\n".join(lines)


def build_markdown(
    pages: list[PageData],
    merged_highlights: Optional[list[MergedHighlight]] = None,
    document_title: Optional[str] = None,
) -> str:
    """Build a complete Markdown document from extracted page data.

    Parameters
    ----------
    pages:
        Per-page data as returned by :func:`process_pdf`.
    merged_highlights:
        Optional list of cross-page merged highlights.
    document_title:
        Optional overall document title.  If *None*, the first title found in
        the pages is used, or a generic fallback.
    """
    # Determine document title.
    if document_title is None:
        for p in pages:
            if p.titles:
                document_title = p.titles[0]
                break
    if document_title is None:
        document_title = "Extracted Notes"

    sections: list[str] = []
    sections.append(f"# {document_title}")
    sections.append("")

    for page in pages:
        sections.append(_build_page_section(page))

    if merged_highlights:
        sections.append(_build_merged_section(merged_highlights))

    return "\n".join(sections).rstrip() + "\n"


def write_markdown(
    content: str,
    original_filename: str,
    output_dir: Path = Path("output"),
) -> Path:
    """Write *content* to a Markdown file in *output_dir*.

    The file is named ``<original_stem>_notes.md``.

    Returns the path to the written file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(original_filename).stem
    output_path = output_dir / f"{stem}_notes.md"
    output_path.write_text(content, encoding="utf-8")
    return output_path
