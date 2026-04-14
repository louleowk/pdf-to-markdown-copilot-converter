# pdf-to-markdown-copilot-converter

Convert highlighted PDF text into well-structured Markdown notes, powered by AI.

## Overview

This tool:

1. Accepts a PDF file from the user (local file or Google Drive — future).
2. Scans the PDF page by page, extracting titles, headers, and highlighted text.
3. Merges highlight annotations that span page boundaries.
4. Optionally uses a pluggable AI provider (GitHub Copilot, Google Gemini, or OpenAI ChatGPT) to verify coherence and format the extracted data.
5. Outputs a clean Markdown (`.md`) file in the `output/` directory.

All user inputs are automatically saved to the `audit/` folder for tracking purposes.

## Prerequisites

- **Python 3.10+**
- **[uv](https://docs.astral.sh/uv/)** — fast Python package manager

## Setup

```bash
# Clone the repository
git clone https://github.com/louleowk/pdf-to-markdown-copilot-converter.git
cd pdf-to-markdown-copilot-converter

# Install dependencies (creates a virtual environment automatically)
uv sync
```

## Usage

```bash
# Basic usage — extracts highlights and produces Markdown (no AI)
uv run python src/main.py --input path/to/document.pdf

# With an AI provider for coherence-checking and formatting
uv run python src/main.py --input document.pdf --ai-provider copilot
uv run python src/main.py --input document.pdf --ai-provider gemini
uv run python src/main.py --input document.pdf --ai-provider chatgpt

# Custom output directory
uv run python src/main.py --input document.pdf --output-dir my_notes/

# Verbose logging
uv run python src/main.py --input document.pdf -v
```

### AI Provider Configuration

Each AI provider requires an environment variable for authentication:

| Provider   | Environment Variable | Description              |
| ---------- | -------------------- | ------------------------ |
| `copilot`  | `GITHUB_TOKEN`       | GitHub personal token    |
| `gemini`   | `GEMINI_API_KEY`     | Google Gemini API key    |
| `chatgpt`  | `OPENAI_API_KEY`     | OpenAI API key           |

If no `--ai-provider` is specified, or if the provider is unavailable, the tool falls back to a basic rule-based formatter.

## Running Tests

```bash
uv run python -m pytest tests/ -v
```

## Project Structure

```
├── src/
│   ├── main.py                # CLI entry point
│   ├── input_source.py        # Input source abstraction (local, Google Drive)
│   ├── pdf_processor.py       # PDF parsing and annotation extraction
│   ├── cross_page_merger.py   # Merge highlights spanning page boundaries
│   ├── ai_formatter.py        # AI provider interface and registry
│   ├── providers/
│   │   ├── copilot.py         # GitHub Copilot provider
│   │   ├── gemini.py          # Google Gemini provider
│   │   └── chatgpt.py         # OpenAI ChatGPT provider
│   ├── markdown_writer.py     # Markdown output generation
│   └── audit_logger.py        # Audit logging utilities
├── tests/                     # pytest test suite
├── docs/
│   └── design.md              # Architecture and design document
├── audit/                     # Tracked user inputs and run logs
└── output/                    # Generated Markdown files (gitignored)
```

## Documentation

- **[Design Document](docs/design.md)** — Architecture, components, and technology choices.
- **[Agents.md](Agents.md)** — Shared requirements and conventions for all contributors (human and AI).
