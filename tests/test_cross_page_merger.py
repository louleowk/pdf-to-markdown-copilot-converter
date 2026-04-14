"""Tests for src.cross_page_merger."""

from __future__ import annotations

import pytest

from src.cross_page_merger import (
    MergedHighlight,
    merge_cross_page_highlights,
)
from src.pdf_processor import HighlightAnnotation, PageData


def _make_highlight(text: str, page: int, y0: float, y1: float) -> HighlightAnnotation:
    return HighlightAnnotation(
        text=text,
        page=page,
        coordinates={"x0": 72, "y0": y0, "x1": 500, "y1": y1},
    )


class TestMergeCrossPageHighlights:
    def test_no_merge_when_no_highlights(self):
        pages = [
            PageData(page=1, titles=[], headers=[], highlights=[]),
            PageData(page=2, titles=[], headers=[], highlights=[]),
        ]
        updated, merged = merge_cross_page_highlights(pages)
        assert merged == []
        assert len(updated) == 2

    def test_no_merge_when_not_near_edges(self):
        pages = [
            PageData(page=1, highlights=[_make_highlight("Middle of page.", 1, 400, 414)]),
            PageData(page=2, highlights=[_make_highlight("Also middle.", 2, 400, 414)]),
        ]
        updated, merged = merge_cross_page_highlights(pages, page_heights=[842, 842])
        assert merged == []
        # Both highlights remain.
        assert len(updated[0].highlights) == 1
        assert len(updated[1].highlights) == 1

    def test_merge_when_conditions_met(self):
        # last highlight on page 1 near bottom, first on page 2 near top,
        # and text looks like a continuation.
        pages = [
            PageData(page=1, highlights=[
                _make_highlight("This sentence continues on the next", 1, 810, 830),
            ]),
            PageData(page=2, highlights=[
                _make_highlight("page with more words.", 2, 20, 40),
            ]),
        ]
        updated, merged = merge_cross_page_highlights(pages, page_heights=[842, 842])
        assert len(merged) == 1
        assert merged[0].pages == [1, 2]
        assert "continues" in merged[0].text
        assert "more words" in merged[0].text
        # The consumed highlights should be removed from the pages.
        assert len(updated[0].highlights) == 0
        assert len(updated[1].highlights) == 0

    def test_no_merge_when_sentence_ends(self):
        # The first text ends with a period → not a continuation.
        pages = [
            PageData(page=1, highlights=[
                _make_highlight("This sentence ends here.", 1, 810, 830),
            ]),
            PageData(page=2, highlights=[
                _make_highlight("new sentence starts.", 2, 20, 40),
            ]),
        ]
        updated, merged = merge_cross_page_highlights(pages, page_heights=[842, 842])
        assert merged == []

    def test_no_merge_when_next_starts_uppercase(self):
        pages = [
            PageData(page=1, highlights=[
                _make_highlight("Some incomplete thought", 1, 810, 830),
            ]),
            PageData(page=2, highlights=[
                _make_highlight("New paragraph starts here.", 2, 20, 40),
            ]),
        ]
        updated, merged = merge_cross_page_highlights(pages, page_heights=[842, 842])
        assert merged == []

    def test_preserves_non_consumed_highlights(self):
        pages = [
            PageData(page=1, highlights=[
                _make_highlight("Keep this one.", 1, 100, 114),
                _make_highlight("This continues on the next", 1, 810, 830),
            ]),
            PageData(page=2, highlights=[
                _make_highlight("page seamlessly.", 2, 20, 40),
                _make_highlight("Keep this too.", 2, 200, 214),
            ]),
        ]
        updated, merged = merge_cross_page_highlights(pages, page_heights=[842, 842])
        assert len(merged) == 1
        assert len(updated[0].highlights) == 1
        assert updated[0].highlights[0].text == "Keep this one."
        assert len(updated[1].highlights) == 1
        assert updated[1].highlights[0].text == "Keep this too."
