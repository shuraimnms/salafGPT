import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "").strip()
    openrouter_base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    temperature: float = float(os.getenv("OPENROUTER_TEMPERATURE", "0.2"))
    request_timeout_s: float = float(os.getenv("OPENROUTER_TIMEOUT_S", "30"))


settings = Settings()
