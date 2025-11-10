from career_navigator.domain.llm import LanguageModel


class CareerService:
    def __init__(self, llm: LanguageModel):
        self.llm = llm

    def get_career_advice(self, topic: str) -> str:
        prompt = f"""
        Provide career advice on the following topic: {topic}.
        Keep the advice concise and actionable.
        """
        return self.llm.generate(prompt)
