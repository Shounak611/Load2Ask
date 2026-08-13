from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator, Optional


class BaseLLMProvider(ABC):
    """Abstract base interface for LLM Providers."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> str:
        """Synchronously generate response from LLM."""
        pass

    @abstractmethod
    def stream(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> Generator[str, None, None]:
        """Stream response tokens from LLM."""
        pass
