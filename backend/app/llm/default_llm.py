import os
from typing import Generator, Optional
from app.llm.base import BaseLLMProvider
from app.core.config import settings
from app.core.logging import logger

try:
    import google.generativeai as genai
except ImportError:
    genai = None


class DefaultLLMProvider(BaseLLMProvider):
    """Default LLM provider integrating Google Gemini API with grounded fallback support."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key or settings.GEMINI_API_KEY or settings.LLM_API_KEY
        self.model_name = model_name
        self.client = None

        if self.api_key and genai is not None:
            try:
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(self.model_name)
                logger.info(f"Initialized Google Gemini LLM provider with model '{self.model_name}'")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client: {e}")

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> str:
        if self.client:
            try:
                full_prompt = f"{system_instruction}\n\n{prompt}" if system_instruction else prompt
                response = self.client.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                    )
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                logger.error(f"Gemini LLM generation failed: {e}")

        # Grounded Fallback Generator when API key is unconfigured or offline
        return self._grounded_fallback_generate(prompt)

    def stream(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> Generator[str, None, None]:
        response_text = self.generate(prompt, system_instruction, temperature, max_tokens)
        words = response_text.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")

    def _grounded_fallback_generate(self, prompt: str) -> str:
        """Grounded fallback engine for offline testing or missing LLM API keys."""
        if "Retrieved Context:" not in prompt and "Context:" not in prompt:
            return "I could not find sufficient information in the provided sources to answer this reliably."

        # Extract content lines from prompt context
        lines = prompt.splitlines()
        extracted_facts = []
        current_source = "Source 1"

        for line in lines:
            if line.startswith("[SOURCE") or line.startswith("[Source"):
                current_source = line.strip("[]")
            elif line.startswith("Content:"):
                content_text = line.replace("Content:", "").strip()
                if content_text:
                    extracted_facts.append((current_source, content_text))
            elif line.strip() and not line.startswith("User Query:") and not line.startswith("Retrieved Context:"):
                if len(line.strip()) > 10 and "I could not find" not in line:
                    extracted_facts.append((current_source, line.strip()))

        if not extracted_facts:
            return "I could not find sufficient information in the provided sources to answer this reliably."

        facts_text = " ".join([fact for _, fact in extracted_facts[:3]])
        return f"Based on the provided context: {facts_text}"

