"""OpenAI ChatGPT AI provider.

Uses the ``openai`` SDK to call the Chat Completions API.
"""

from __future__ import annotations

import logging
import os

from openai import OpenAI

from src.ai_formatter import register_provider

logger = logging.getLogger(__name__)


class ChatGPTProvider:
    """AI formatter backed by OpenAI ChatGPT."""

    name: str = "chatgpt"

    def format(self, extracted_text: str, prompt: str) -> str:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY environment variable is not set.")

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that formats text as Markdown."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content or ""


# Auto-register when the module is imported.
register_provider("chatgpt", ChatGPTProvider)
