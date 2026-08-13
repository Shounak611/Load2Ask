from app.llm.base import BaseLLMProvider
from app.llm.default_llm import DefaultLLMProvider
from app.core.config import settings


class LLMFactory:
    """Factory for instantiating LLM Provider instances."""

    @staticmethod
    def get_llm(provider_name: str = "default") -> BaseLLMProvider:
        return DefaultLLMProvider()
