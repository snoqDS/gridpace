"""
Smoke tests for config module.
These run in CI on every push.
"""

from gridpace.config import settings


def test_settings_loads():
    """Settings object initializes without errors."""
    assert settings is not None


def test_llm_provider_valid():
    """LLM provider must be one of the supported options."""
    assert settings.llm_provider in ("ollama", "huggingface", "anthropic")


def test_project_root_exists():
    """Project root path resolves to a real directory."""
    from gridpace.config import ROOT
    assert ROOT.exists()
    assert ROOT.is_dir()
