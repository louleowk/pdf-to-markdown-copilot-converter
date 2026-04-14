# PDF to Markdown Copilot Converter — Initial Design

## 1. Overview

A tool that converts highlighted text from PDF files into well-structured Markdown notes. The tool leverages AI (GitHub Copilot) to validate extracted content for coherence and to format the output as clean Markdown.

## 2. Goals

- Allow users to provide a PDF file as input.
- Scan the PDF page by page, preserving titles, headers, and highlighted text.
- Convert the extracted data into a Markdown (`.md`) file.
- Use a **pluggable AI provider** (GitHub Copilot CLI, Google Gemini, OpenAI ChatGPT — user's choice) to verify that extracted text is coherent and properly formatted.
- Support multiple input sources: local files and Google Drive (with authentication).
- Handle cross-page highlights gracefully so split annotations are merged into a single logical block.
- Persist every user-provided input in an `audit/` folder for tracking purposes.

## 3. High-Level Architecture

```
┌──────────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌──────────────┐
│  Input Source     │────▶│  PDF Processor   │────▶│  AI Provider    │────▶│  MD Output   │
│  (local / GDrive)│     │  (extract annot.)│     │  (pluggable)    │     │  (.md file)  │
└──────────────────┘     └──────────────────┘     └─────────────────┘     └──────────────┘
       │                        │                         ▲                       │
       ▼                        ▼                         │                       ▼
┌──────────────┐     ┌──────────────────┐     ┌─────────────────────┐   ┌──────────────┐
│  Audit Log   │     │  Cross-Page      │     │  Provider Registry  │   │  Output Dir  │
│  (audit/)    │     │  Merger          │     │  (Copilot/Gemini/   │   │              │
│              │     │                  │     │   ChatGPT)          │   │              │
└──────────────┘     └──────────────────┘     └─────────────────────┘   └──────────────┘
```

## 4. Component Details

### 4.1 Input Source Handler

- **Responsibility:** Accept a PDF file from the user via one of the supported input sources.
- **Supported Sources:**
  | Source | Description |
  |---|---|
  | **Local file** | Path on the local filesystem (CLI argument, file picker, or drag-and-drop). |
  | **Google Drive** | Google Drive file ID or URL. Requires OAuth 2.0 authentication via a service account or user consent flow. |
- **Source Abstraction:** An `InputSource` interface allows future sources (Dropbox, OneDrive, S3, etc.) to be added without changing the rest of the pipeline.
  ```python
  class InputSource(Protocol):
      def fetch(self, reference: str) -> Path:
          """Download / locate the PDF and return a local Path."""
          ...
  ```
- **Validation:** Verify the file exists and is a valid PDF.
- **Audit:** Copy the original PDF into `audit/` with a timestamped filename for traceability.

### 4.2 PDF Processor

- **Responsibility:** Parse the PDF page by page and extract:
  - **Titles / Headers** — detected by font size, weight, or style metadata.
  - **Highlight Annotations** — PDF highlight annotations (the standard annotation type `/Highlight` stored in the PDF's annotation layer). These are the coloured overlays readers add to mark important text.
  - **Page Numbers** — retained as metadata for reference.
- **Technology Candidates:**
  - Python: `PyMuPDF` (fitz) — excellent support for annotations and text extraction.
  - Python: `pdfplumber` — good for layout-aware text extraction.
- **Output:** A structured intermediate representation (e.g., JSON or in-memory object) containing the extracted data per page.

#### Cross-Page Highlight Merging

Highlight annotations sometimes span a page break (i.e., the reader highlighted a passage that continues from the bottom of one page to the top of the next). The PDF Processor addresses this with a **cross-page merger**:

1. After extracting annotations from all pages, sort highlights by `(page, y-coordinate)`.
2. For each pair of consecutive highlights on adjacent pages, check:
   - The last highlight on page *N* ends near the bottom margin **and** the first highlight on page *N+1* starts near the top margin.
   - The two text fragments form an incomplete sentence when taken individually (heuristic: the first fragment does not end with sentence-ending punctuation).
3. When both conditions are met, merge the two highlights into a single logical block and tag it with the originating page range (e.g., `pages: [3, 4]`).
4. The merged highlight is stored once and excluded from the per-page lists to avoid duplication.

#### Intermediate Data Model (per page)

```json
{
  "page": 1,
  "titles": ["Chapter 1: Introduction"],
  "headers": ["1.1 Background", "1.2 Motivation"],
  "highlights": [
    {
      "text": "This is an important highlighted sentence.",
      "page": 1,
      "coordinates": { "x0": 72, "y0": 500, "x1": 540, "y1": 514 }
    }
  ]
}
```

### 4.3 AI Formatter (Pluggable Provider)

The AI component is designed as a **replaceable provider** so users can choose the AI backend that best fits their needs. At launch the tool ships with three built-in providers; adding a new one requires only implementing the `AIProvider` interface.

#### Provider Interface

```python
class AIProvider(Protocol):
    name: str  # e.g. "copilot", "gemini", "chatgpt"

    def format(self, extracted_text: str, prompt: str) -> str:
        """Send extracted text + prompt to the AI and return formatted Markdown."""
        ...
```

#### Built-in Providers

| Provider | Backend | Authentication |
|---|---|---|
| **GitHub Copilot CLI** | Copilot Chat API / GitHub Models | GitHub token (`GITHUB_TOKEN`) |
| **Google Gemini** | Gemini API (`generativelanguage.googleapis.com`) | Google API key (`GEMINI_API_KEY`) |
| **OpenAI ChatGPT** | OpenAI Chat Completions API | OpenAI API key (`OPENAI_API_KEY`) |

The user selects a provider via a CLI flag or configuration file:

```bash
python src/main.py --input doc.pdf --ai-provider gemini
```

#### Provider Registry

A lightweight registry maps provider names to their implementations. New providers can be registered at runtime or via entry points:

```python
PROVIDERS: dict[str, type[AIProvider]] = {
    "copilot": CopilotProvider,
    "gemini":  GeminiProvider,
    "chatgpt": ChatGPTProvider,
}
```

#### Responsibility

1. **Coherence Check** — Send the extracted text to the selected AI provider to verify it reads correctly (e.g., incomplete sentences, OCR artifacts).
2. **Markdown Formatting** — Ask the provider to organise the extracted data into well-structured Markdown with proper heading levels, bullet points, and emphasis.

#### Prompt Template (shared across providers)

```
The following text was extracted from a PDF. Please verify it makes sense,
fix any obvious artifacts, and format it as clean Markdown with proper headings
and bullet points.

---
<extracted text>
---
```

- **Fallback:** If all AI providers are unavailable, produce a basic Markdown file using simple formatting rules (headings from titles, blockquotes for highlights).

### 4.4 Markdown Output Generator

- **Responsibility:** Write the final Markdown content to a `.md` file.
- **Naming Convention:** `<original-filename>_notes.md` placed in an `output/` directory (configurable).
- **Structure:**
  ```markdown
  # <Document Title>

  ## Page 1

  ### <Header>

  > Highlighted: "This is an important highlighted sentence."

  ## Page 2
  ...
  ```

### 4.5 Audit Logger

- **Responsibility:** Record every user interaction for traceability.
- **What is logged:**
  - Original PDF file (copied into `audit/`).
  - Timestamp of the conversion.
  - A manifest file (`audit/log.json` or `audit/log.csv`) recording each run with metadata (filename, timestamp, status, output path).

## 5. Project Structure (Proposed)

```
pdf-to-markdown-copilot-converter/
├── README.md
├── Agents.md                  # Shared requirements for all agents
├── pyproject.toml             # Project metadata & dependencies (Poetry)
├── poetry.lock                # Locked dependency versions
├── docs/
│   └── design.md              # This document
├── audit/                     # Tracked user inputs and run logs
│   └── .gitkeep
├── output/                    # Generated markdown files (gitignored)
├── src/
│   ├── main.py                # Entry point / CLI
│   ├── input_source.py        # Input source abstraction (local, Google Drive)
│   ├── pdf_processor.py       # PDF parsing and annotation extraction
│   ├── cross_page_merger.py   # Merge highlights that span page boundaries
│   ├── ai_formatter.py        # AI provider interface and registry
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── copilot.py         # GitHub Copilot provider
│   │   ├── gemini.py          # Google Gemini provider
│   │   └── chatgpt.py         # OpenAI ChatGPT provider
│   ├── markdown_writer.py     # Markdown output generation
│   └── audit_logger.py        # Audit logging utilities
├── tests/
│   ├── test_pdf_processor.py
│   ├── test_cross_page_merger.py
│   ├── test_ai_formatter.py
│   └── test_markdown_writer.py
└── .gitignore
```

## 6. Technology Stack

| Component              | Technology                  | Reason                                                       |
|------------------------|-----------------------------|--------------------------------------------------------------|
| Language               | Python 3.10+                | Rich PDF libraries, AI SDK support                           |
| Package Management     | **Poetry**                  | Dependency resolution, lock file, virtual env creation        |
| Virtual Environment    | Poetry-managed venv         | `poetry install` creates an isolated env automatically        |
| PDF Parsing            | PyMuPDF (fitz)              | Best annotation + highlight extraction                       |
| AI Integration         | Pluggable provider registry | Copilot CLI, Google Gemini, OpenAI ChatGPT (see §4.3)       |
| Google Drive Access    | `google-api-python-client`  | OAuth 2.0 file download for remote PDFs                      |
| CLI Framework          | `click`                     | Intuitive command-line interface with option groups           |
| Testing                | `pytest`                    | Standard Python test framework                               |

## 7. User Workflow

1. **Install dependencies:** `poetry install` (creates the virtual environment automatically).
2. **Run the tool:**
   ```bash
   # Local file with default AI provider (Copilot)
   poetry run python src/main.py --input my_document.pdf

   # Google Drive file with Gemini
   poetry run python src/main.py --input gdrive://1aBcDeFgHiJk --ai-provider gemini
   ```
3. The Input Source Handler fetches/locates the PDF and copies it to `audit/` with a timestamp.
4. The PDF Processor extracts titles, headers, and highlight annotations page by page.
5. The Cross-Page Merger detects and joins highlights that span page boundaries.
6. The AI Formatter sends the extracted data to the selected AI provider for coherence and formatting.
7. The Markdown Writer produces `output/my_document_notes.md`.
8. The audit log is updated with the run details.

## 8. Future Enhancements

- **Web UI / Desktop App:** Add a graphical interface for non-technical users.
- **Batch Processing:** Support converting multiple PDFs in one run.
- **Custom Highlight Colours:** Allow users to map highlight colours to different Markdown styles (e.g., yellow = note, red = important).
- **OCR Support:** Integrate Tesseract for scanned PDFs without selectable text.
- **Export Formats:** Support additional output formats (HTML, DOCX) alongside Markdown.

## 9. Open Questions

- Should the tool support PDFs with no highlight annotations (plain text extraction only)?
- What rate limits / token budgets should be enforced per AI provider?
- Should the audit folder be committed to version control or gitignored?
- For Google Drive input, should we support shared drives and team drives?
