"""GitHub Copilot AI provider.

Uses the GitHub Models / Copilot Chat Completions API.
"""

from __future__ import annotations

import logging
import os

import requests

from src.ai_formatter import register_provider

logger = logging.getLogger(__name__)

_API_URL = "https://api.githubcopilot.com/chat/completions"


class CopilotProvider:
    """AI formatter backed by GitHub Copilot."""

    name: str = "copilot"

    def format(self, extracted_text: str, prompt: str) -> str:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise EnvironmentError("GITHUB_TOKEN environment variable is not set.")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Copilot-Integration-Id": "pdf-to-markdown-converter",
        }
        payload = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that formats text as Markdown."},
                {"role": "user", "content": prompt},
            ],
            "model": "gpt-4o",
        }

        response = requests.post(_API_URL, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


# Auto-register when the module is imported.
register_provider("copilot", CopilotProvider)
