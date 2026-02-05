"""
LLM Infrastructure Module

Provides LLM client implementations.

Available Clients:
    - MockLLMClient: For testing without API calls
    - RecordingLLMClient: Wrapper that records calls

To add a real client (e.g., for vLLM or OpenAI):
1. Create a new file (e.g., vllm_client.py)
2. Implement the LLMClient interface from core.interfaces
3. Export it from this __init__.py

Usage:
    from refactored_classifier.infrastructure.llm import MockLLMClient

    llm = MockLLMClient()
"""

from .clients import MockLLMClient, RecordingLLMClient
from .interfaces import LLMClient, LLMResponse
from .vllm_client import VLLMClient, VLLMClientFactory

__all__ = [
    "LLMClient",
    "LLMResponse",
    "MockLLMClient",
    "RecordingLLMClient",
    "VLLMClient",
    "VLLMClientFactory",
]
