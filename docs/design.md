# PDF to Markdown Copilot Converter — Initial Design

## 1. Overview

A tool that converts highlighted text from PDF files into well-structured Markdown notes. The tool leverages AI (GitHub Copilot) to validate extracted content for coherence and to format the output as clean Markdown.

## 2. Goals

- Allow users to provide a PDF file as input.
- Scan the PDF page by page, preserving titles, headers, and highlighted text.
- Convert the extracted data into a Markdown (`.md`) file.
- Use AI (Copilot) to verify that extracted text is coherent and properly formatted.
- Persist every user-provided input in an `audit/` folder for tracking purposes.

## 3. High-Level Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌──────────────┐
│  User Input  │────▶│  PDF Processor   │────▶│  AI Formatter   │────▶│  MD Output   │
│  (PDF file)  │     │  (extract text)  │     │  (Copilot)      │     │  (.md file)  │
└──────────────┘     └──────────────────┘     └─────────────────┘     └──────────────┘
       │                                                                      │
       ▼                                                                      ▼
┌──────────────┐                                                     ┌──────────────┐
│  Audit Log   │                                                     │  Output Dir  │
│  (audit/)    │                                                     │              │
└──────────────┘                                                     └──────────────┘
```

## 4. Component Details

### 4.1 User Input Handler

- **Responsibility:** Accept a PDF file from the user (via CLI argument, file picker, or drag-and-drop).
- **Validation:** Verify the file exists and is a valid PDF.
- **Audit:** Copy the original PDF into `audit/` with a timestamped filename for traceability.

### 4.2 PDF Processor

- **Responsibility:** Parse the PDF page by page and extract:
  - **Titles / Headers** — detected by font size, weight, or style metadata.
  - **Highlighted Text** — identified by text annotations (highlight annotations) or background-color markup in the PDF.
  - **Page Numbers** — retained as metadata for reference.
- **Technology Candidates:**
  - Python: `PyMuPDF` (fitz) — excellent support for annotations and text extraction.
  - Python: `pdfplumber` — good for layout-aware text extraction.
  - Node.js: `pdf-parse`, `pdf.js` — if a JavaScript-based stack is preferred.
- **Output:** A structured intermediate representation (e.g., JSON or in-memory object) containing the extracted data per page.

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

### 4.3 AI Formatter (Copilot Integration)

- **Responsibility:**
  1. **Coherence Check** — Send the extracted text to Copilot to verify it reads correctly (e.g., incomplete sentences, OCR artefacts).
  2. **Markdown Formatting** — Ask Copilot to organise the extracted data into well-structured Markdown with proper heading levels, bullet points, and emphasis.
- **Integration Approach:**
  - Use the Copilot Chat API or a GitHub Models endpoint to submit prompts.
  - Prompt template example:
    ```
    The following text was extracted from a PDF. Please verify it makes sense,
    fix any obvious errors, and format it as clean Markdown with proper headings
    and bullet points.

    ---
    <extracted text>
    ---
    ```
- **Fallback:** If AI is unavailable, produce a basic Markdown file using simple formatting rules (headings from titles, blockquotes for highlights).

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
├── docs/
│   └── design.md              # This document
├── audit/                     # Tracked user inputs and run logs
│   └── .gitkeep
├── output/                    # Generated markdown files (gitignored)
├── src/
│   ├── main.py                # Entry point / CLI
│   ├── pdf_processor.py       # PDF parsing and extraction logic
│   ├── ai_formatter.py        # Copilot / AI integration
│   ├── markdown_writer.py     # Markdown output generation
│   └── audit_logger.py        # Audit logging utilities
├── tests/
│   ├── test_pdf_processor.py
│   ├── test_ai_formatter.py
│   └── test_markdown_writer.py
├── requirements.txt
└── .gitignore
```

## 6. Technology Stack

| Component        | Technology                  | Reason                                      |
|------------------|-----------------------------|---------------------------------------------|
| Language         | Python 3.10+                | Rich PDF libraries, Copilot SDK support     |
| PDF Parsing      | PyMuPDF (fitz)              | Best annotation + highlight extraction      |
| AI Integration   | GitHub Copilot / Models API | Coherence checking and Markdown formatting  |
| CLI Framework    | `argparse` or `click`       | Simple command-line interface                |
| Testing          | `pytest`                    | Standard Python test framework              |

## 7. User Workflow

1. **Run the tool:** `python src/main.py --input my_document.pdf`
2. The tool copies `my_document.pdf` to `audit/` with a timestamp.
3. The PDF Processor extracts titles, headers, and highlights page by page.
4. The AI Formatter sends the extracted data to Copilot for coherence and formatting.
5. The Markdown Writer produces `output/my_document_notes.md`.
6. The audit log is updated with the run details.

## 8. Future Enhancements

- **Web UI / Desktop App:** Add a graphical interface for non-technical users.
- **Batch Processing:** Support converting multiple PDFs in one run.
- **Custom Highlight Colours:** Allow users to map highlight colours to different Markdown styles (e.g., yellow = note, red = important).
- **OCR Support:** Integrate Tesseract for scanned PDFs without selectable text.
- **Export Formats:** Support additional output formats (HTML, DOCX) alongside Markdown.

## 9. Open Questions

- Should the tool support PDFs with no annotations (plain text extraction only)?
- What is the preferred AI model / endpoint for Copilot integration?
- Should the audit folder be committed to version control or gitignored?
