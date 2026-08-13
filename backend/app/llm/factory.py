from app.llm.base import BaseLLMProvider


class LLMFactory:
    """Factory stub for LLM providers (OpenAI, Gemini, Ollama, etc.). Fully implemented in Part 3."""

    @staticmethod
    def get_llm_provider(provider_type: str = "openai") -> BaseLLMProvider:
        raise NotImplementedError("LLM providers will be implemented in subsequent parts.")
