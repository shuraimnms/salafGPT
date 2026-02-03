from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

from backend.config import settings


@dataclass
class LLMResponse:
    content: Optional[str]
    error: Optional[str] = None


class OpenRouterClient:
    def __init__(self) -> None:
        self.base_url = settings.openrouter_base_url.rstrip("/")
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model
        self.temperature = min(settings.temperature, 0.2)
        self.timeout = settings.request_timeout_s

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def chat(self, messages: list[Dict[str, str]]) -> LLMResponse:
        if not self.api_key:
            return LLMResponse(content=None, error="Missing OpenRouter API key")

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                )
        except httpx.RequestError as exc:
            return LLMResponse(content=None, error=f"Network error: {exc}")

        if response.status_code in {401, 429, 500}:
            return LLMResponse(content=None, error=f"Upstream error {response.status_code}")

        if response.status_code >= 400:
            return LLMResponse(content=None, error=f"Unexpected error {response.status_code}")

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return LLMResponse(content=None, error="Malformed response from model")

        return LLMResponse(content=content)
