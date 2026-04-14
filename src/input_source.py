"""Input source abstraction.

Provides a protocol for fetching PDFs from various sources and a concrete
implementation for local files.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class InputSource(Protocol):
    """Protocol for input sources that resolve a reference to a local PDF path."""

    def fetch(self, reference: str) -> Path:
        """Download / locate the PDF and return a local :class:`Path`."""
        ...


class LocalFileSource:
    """Fetch a PDF from the local filesystem."""

    def fetch(self, reference: str) -> Path:
        """Return *reference* as a validated local path.

        Raises
        ------
        FileNotFoundError
            If the path does not exist.
        ValueError
            If the file does not appear to be a PDF.
        """
        path = Path(reference).resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if path.suffix.lower() != ".pdf":
            raise ValueError(f"Expected a .pdf file, got: {path.suffix}")
        return path


class GoogleDriveSource:
    """Placeholder for Google Drive input source.

    A full implementation would use ``google-api-python-client`` with OAuth 2.0
    to download a file by its Google Drive file ID or URL.
    """

    def fetch(self, reference: str) -> Path:
        """Download a PDF from Google Drive (not yet implemented)."""
        raise NotImplementedError(
            "Google Drive source is not yet implemented. "
            "Please provide a local file path instead."
        )


def get_source(reference: str) -> InputSource:
    """Return the appropriate :class:`InputSource` for *reference*.

    Currently supports:
    - ``gdrive://...`` → :class:`GoogleDriveSource`
    - Anything else    → :class:`LocalFileSource`
    """
    if reference.startswith("gdrive://"):
        return GoogleDriveSource()
    return LocalFileSource()
