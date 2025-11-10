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
            model_name="llama3-8b-8192",
            callbacks=[self.langfuse_callback_handler],
        )

    def generate(self, prompt: str) -> str:
        messages = [HumanMessage(content=prompt)]
        ai_message = self.chat.invoke(messages)
        return ai_message.content
