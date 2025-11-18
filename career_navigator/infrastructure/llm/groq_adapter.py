from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from career_navigator.config import settings
from career_navigator.domain.llm import LanguageModel


class GroqAdapter(LanguageModel):
    def __init__(self):
        # Initialize Langfuse client (singleton pattern)
        Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST,
        )
        # Create callback handler (uses the singleton client)
        self.langfuse_callback_handler = CallbackHandler()
        
        self.chat = ChatGroq(
            temperature=0,
            groq_api_key=settings.GROQ_API_KEY,
            model_name="llama-3.1-8b-instant",
            callbacks=[self.langfuse_callback_handler],
        )

    def generate(self, prompt: str, max_retries: int = 3) -> str:
        """
        Generate text from prompt with retry logic.
        
        Args:
            prompt: The prompt to send to the LLM
            max_retries: Maximum number of retry attempts
            
        Returns:
            Generated text content
            
        Raises:
            Exception: If all retries fail
        """
        import time
        from groq import GroqError
        
        last_error = None
        for attempt in range(max_retries):
            try:
                messages = [HumanMessage(content=prompt)]
                ai_message = self.chat.invoke(messages)
                return ai_message.content
            except GroqError as e:
                last_error = e
                error_code = getattr(e, 'status_code', None) or getattr(e, 'code', None)
                error_str = str(e).lower()
                
                # Check if it's a retryable error (500, 503, rate limit, etc.)
                is_retryable = (
                    error_code in [500, 503, 429] or
                    "500" in error_str or
                    "503" in error_str or
                    "429" in error_str or
                    "internal server error" in error_str or
                    "rate limit" in error_str or
                    "service unavailable" in error_str
                )
                
                if is_retryable and attempt < max_retries - 1:
                    # Wait before retrying (exponential backoff)
                    wait_time = (attempt + 1) * 2
                    time.sleep(wait_time)
                    continue
                
                # For non-retryable errors or if retries exhausted, raise
                raise Exception(f"Groq API error: {str(e)}")
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                # Check if it's a retryable error
                if ("500" in error_str or "503" in error_str or "internal server error" in error_str) and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    time.sleep(wait_time)
                    continue
                raise
        
        # If we get here, all retries failed
        raise Exception(f"Failed to generate after {max_retries} attempts: {last_error}")
