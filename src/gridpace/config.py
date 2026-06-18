"""
Central configuration for GridPace.
Secrets loaded from .env via pydantic-settings.
Static config loaded from config/ YAML files.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root
ROOT = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # GridStatus
    gridstatus_api_key: str = ""

    # EIA
    eia_api_key: str = ""

    # WattTime
    watttime_user: str = ""
    watttime_password: str = ""

    # Ember
    ember_api_key: str = ""

    # HuggingFace
    hf_token: str = ""
    hf_inference_model: str = "mistralai/Mistral-7B-Instruct-v0.3"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # Anthropic
    anthropic_api_key: str = ""

    # Active LLM provider
    llm_provider: str = "ollama"


# Single shared instance imported everywhere
settings = Settings()
