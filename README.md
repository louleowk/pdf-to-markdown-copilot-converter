# pdf-to-markdown-copilot-converter

Convert highlighted PDF text into well-structured Markdown notes, powered by GitHub Copilot.

## Overview

This tool:

1. Accepts a PDF file from the user.
2. Scans the PDF page by page, extracting titles, headers, and highlighted text.
3. Uses AI (GitHub Copilot) to verify coherence and format the extracted data.
4. Outputs a clean Markdown (`.md`) file.

All user inputs are automatically saved to the `audit/` folder for tracking purposes.

## Documentation

- **[Design Document](docs/design.md)** — Architecture, components, and technology choices.
- **[Agents.md](Agents.md)** — Shared requirements and conventions for all contributors (human and AI).

## Project Status

🚧 **In Design Phase** — See the [design document](docs/design.md) for the current plan.
