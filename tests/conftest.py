"""Shared pytest fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def command_llm_parser():
    """Single ``LLMCommandParser`` using ``config/llm.yaml`` (downloads GGUF on first use)."""
    from server.orders.llm_parser import LLMCommandParser

    return LLMCommandParser()
