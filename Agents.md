# Agents.md — Shared Requirements for All Agents

This document defines requirements and conventions that **all agents** (human or AI) must follow when contributing to this repository.

---

## 1. Audit Trail Requirement

Every user-provided input **must** be persisted in the `audit/` folder for tracking purposes.

### Rules

- When a user provides a PDF file (or any input file), a copy of that file **must** be saved to the `audit/` directory before any processing begins.
- Files in `audit/` must be named with a timestamp prefix to avoid collisions:
  - Format: `YYYYMMDD_HHmmss_<original_filename>`
  - Example: `20260414_115700_my_document.pdf`
- A run log entry **must** be appended to `audit/log.json` (or created if it does not exist) with the following fields:
  - `timestamp` — ISO 8601 datetime of the run.
  - `original_filename` — The name of the input file as provided by the user.
  - `audit_filename` — The timestamped name stored in `audit/`.
  - `status` — One of `started`, `completed`, `failed`.
  - `output_file` — Path to the generated output (if applicable).
  - `error` — Error message (if status is `failed`).

### Example Log Entry

```json
{
  "timestamp": "2026-04-14T11:57:00Z",
  "original_filename": "my_document.pdf",
  "audit_filename": "20260414_115700_my_document.pdf",
  "status": "completed",
  "output_file": "output/my_document_notes.md",
  "error": null
}
```

## 2. Code Conventions

- **Language:** Python 3.10+ is the primary language for this project.
- **Style:** Follow PEP 8. Use type hints where practical.
- **Testing:** All new functionality must include corresponding tests in the `tests/` directory using `pytest`.
- **Dependencies:** Pin versions in `requirements.txt`. Do not add unnecessary dependencies.

## 3. Documentation

- Design documents go in `docs/`.
- Keep `README.md` up to date with setup and usage instructions.
- Update this file (`Agents.md`) when shared requirements change.

## 4. Output

- Generated Markdown files should be placed in the `output/` directory.
- The `output/` directory should be listed in `.gitignore` to avoid committing generated content.

## 5. Security & Privacy

- Do not commit sensitive user data to the repository.
- The `audit/` folder may contain user-provided files; ensure it is handled appropriately (e.g., gitignored in public repositories, or access-controlled in private ones).
- Never log or store API keys, tokens, or credentials.

## 6. AI Integration

- When using Copilot or any AI service, always provide a fallback path for when the AI is unavailable.
- Prompts sent to AI should be logged (without sensitive content) for debugging purposes.
- AI-generated output must be clearly marked or distinguishable from raw extracted text.
