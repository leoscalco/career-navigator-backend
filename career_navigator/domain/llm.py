from abc import ABC, abstractmethod


class LanguageModel(ABC):
    @abstractmethod
    def generate(self, prompt: str, trace_id: str | None = None, span_id: str | None = None) -> str:
        """Generates text from a prompt.
        
        Args:
            prompt: The prompt to send to the LLM
            trace_id: Optional Langfuse trace ID for unified tracing
            span_id: Optional Langfuse span ID to link this generation to a span
        """
        pass
