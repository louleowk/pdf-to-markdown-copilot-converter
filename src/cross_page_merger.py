"""Cross-page highlight merger.

Detects highlight annotations that span a page boundary and merges them into
a single logical block so the downstream formatter does not produce duplicates.
"""

from __future__ import annotations

import dataclasses
import re
from typing import Optional

from src.pdf_processor import HighlightAnnotation, PageData

# Default margin threshold (in points) for detecting annotations near edges.
DEFAULT_MARGIN_THRESHOLD = 72.0  # 1 inch

# Sentence-ending punctuation pattern.
_SENTENCE_END_RE = re.compile(r"[.!?…][\"'""']?\s*$")


@dataclasses.dataclass
class MergedHighlight:
    """A highlight that was produced by merging two cross-page annotations."""

    text: str
    pages: list[int]
    coordinates_start: dict
    coordinates_end: dict


def _is_near_bottom(annot: HighlightAnnotation, page_height: float, threshold: float) -> bool:
    """Return True if the annotation is within *threshold* of the page bottom."""
    return (page_height - annot.coordinates["y1"]) <= threshold


def _is_near_top(annot: HighlightAnnotation, threshold: float) -> bool:
    """Return True if the annotation is within *threshold* of the page top."""
    return annot.coordinates["y0"] <= threshold


def _looks_like_continuation(text_a: str, text_b: str) -> bool:
    """Heuristic: *text_a* does not end a sentence and *text_b* starts lowercase."""
    if not text_a or not text_b:
        return False
    # text_a should NOT end with sentence-ending punctuation
    if _SENTENCE_END_RE.search(text_a):
        return False
    # text_b should start with a lowercase letter
    first_alpha = next((c for c in text_b if c.isalpha()), None)
    if first_alpha is None:
        return False
    return first_alpha.islower()


def merge_cross_page_highlights(
    pages: list[PageData],
    page_heights: Optional[list[float]] = None,
    threshold: float = DEFAULT_MARGIN_THRESHOLD,
) -> tuple[list[PageData], list[MergedHighlight]]:
    """Detect and merge highlights that span page boundaries.

    Parameters
    ----------
    pages:
        List of :class:`PageData` as returned by :func:`process_pdf`.
    page_heights:
        Optional list of page heights (in points), one per page.  When *None*,
        a default height of 842 pt (A4) is assumed.
    threshold:
        Distance (in points) from page edges within which annotations are
        considered candidates for merging.

    Returns
    -------
    (updated_pages, merged_highlights):
        A copy of *pages* with cross-page duplicates removed, and the list of
        newly created :class:`MergedHighlight` instances.
    """
    default_height = 842.0  # A4 page height in points
    heights = page_heights or [default_height] * len(pages)

    merged_highlights: list[MergedHighlight] = []
    consumed_indices: set[tuple[int, int]] = set()  # (page_idx, highlight_idx)

    for i in range(len(pages) - 1):
        page_a = pages[i]
        page_b = pages[i + 1]
        h = heights[i]

        if not page_a.highlights or not page_b.highlights:
            continue

        # Check the *last* highlight on page A and the *first* on page B.
        last_idx = len(page_a.highlights) - 1
        last_h = page_a.highlights[last_idx]
        first_h = page_b.highlights[0]

        if (
            _is_near_bottom(last_h, h, threshold)
            and _is_near_top(first_h, threshold)
            and _looks_like_continuation(last_h.text, first_h.text)
        ):
            merged = MergedHighlight(
                text=last_h.text + " " + first_h.text,
                pages=[page_a.page, page_b.page],
                coordinates_start=last_h.coordinates,
                coordinates_end=first_h.coordinates,
            )
            merged_highlights.append(merged)
            consumed_indices.add((i, last_idx))
            consumed_indices.add((i + 1, 0))

    # Build updated pages with consumed highlights removed.
    updated_pages: list[PageData] = []
    for page_idx, page in enumerate(pages):
        new_highlights = [
            h
            for h_idx, h in enumerate(page.highlights)
            if (page_idx, h_idx) not in consumed_indices
        ]
        updated_pages.append(
            PageData(
                page=page.page,
                titles=page.titles,
                headers=page.headers,
                highlights=new_highlights,
            )
        )

    return updated_pages, merged_highlights
