"""Google Gemini AI provider.

Uses the ``google-generativeai`` SDK to call the Gemini API.
"""

from __future__ import annotations

import logging
import os

import google.generativeai as genai

from src.ai_formatter import register_provider

logger = logging.getLogger(__name__)


class GeminiProvider:
    """AI formatter backed by Google Gemini."""

    name: str = "gemini"

    def format(self, extracted_text: str, prompt: str) -> str:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY environment variable is not set.")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text


# Auto-register when the module is imported.
register_provider("gemini", GeminiProvider)
