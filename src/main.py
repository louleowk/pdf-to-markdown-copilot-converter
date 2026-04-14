"""CLI entry point for the PDF-to-Markdown converter."""

from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path

import click

from src.ai_formatter import format_with_ai, list_providers
from src.audit_logger import copy_to_audit, log_entry
from src.cross_page_merger import merge_cross_page_highlights
from src.input_source import get_source
from src.markdown_writer import build_markdown, write_markdown
from src.pdf_processor import process_pdf

# ---------------------------------------------------------------------------
# Eagerly import all built-in providers so they auto-register.
# ---------------------------------------------------------------------------
_PROVIDER_MODULES = [
    "src.providers.copilot",
    "src.providers.gemini",
    "src.providers.chatgpt",
]

for _mod in _PROVIDER_MODULES:
    try:
        importlib.import_module(_mod)
    except Exception:  # noqa: BLE001
        pass  # Provider may not be usable (missing deps / keys), that's fine.

# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--input", "input_ref",
    required=True,
    help="Path to a local PDF file or a gdrive:// reference.",
)
@click.option(
    "--ai-provider",
    default=None,
    type=click.Choice(list_providers() or ["copilot", "gemini", "chatgpt"], case_sensitive=False),
    help="AI provider for formatting (default: fallback / no AI).",
)
@click.option(
    "--output-dir",
    default="output",
    type=click.Path(),
    help="Directory for the generated Markdown file.",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose / debug logging.",
)
def cli(input_ref: str, ai_provider: str | None, output_dir: str, verbose: bool) -> None:
    """Convert highlighted PDF text into well-structured Markdown notes."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    # 1. Resolve input source.
    source = get_source(input_ref)
    try:
        pdf_path = source.fetch(input_ref)
    except (FileNotFoundError, ValueError, NotImplementedError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    # 2. Audit: copy original file and log start.
    audit_name = copy_to_audit(pdf_path)
    log_entry(
        original_filename=pdf_path.name,
        audit_filename=audit_name,
        status="started",
    )

    try:
        # 3. Extract data from PDF.
        click.echo(f"Processing: {pdf_path.name}")
        pages = process_pdf(pdf_path)

        # 4. Merge cross-page highlights.
        pages, merged = merge_cross_page_highlights(pages)

        # 5. Build raw Markdown from extracted data.
        raw_md = build_markdown(pages, merged)

        # 6. Optionally run through AI formatter.
        formatted_md = format_with_ai(raw_md, provider_name=ai_provider)

        # 7. Write output.
        out_path = write_markdown(formatted_md, pdf_path.name, Path(output_dir))
        click.echo(f"Output written to: {out_path}")

        # 8. Update audit log.
        log_entry(
            original_filename=pdf_path.name,
            audit_filename=audit_name,
            status="completed",
            output_file=str(out_path),
        )

    except Exception as exc:
        log_entry(
            original_filename=pdf_path.name,
            audit_filename=audit_name,
            status="failed",
            error=str(exc),
        )
        click.echo(f"Error during processing: {exc}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
