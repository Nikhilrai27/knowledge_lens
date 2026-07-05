from google import genai
from openai import OpenAI

from ..config import GEMINI_API_KEY, GROQ_API_KEY


class LLMClient:
    def __init__(self, provider: str = "groq", model: str | None = None):
        self.provider = provider
        if provider == "gemini":
            self.client = genai.Client(api_key=GEMINI_API_KEY)
            self.model = model or "gemini-2.5-flash"
        elif provider == "groq":
            self.client = OpenAI(
                api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1"
            )
            self.model = model or "llama-3.3-70b-versatile"
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def generate(self, prompt: str) -> str:
        if self.provider == "gemini":
            response = self.client.models.generate_content(
                model=self.model, contents=prompt
            )
            return response.text
        response = self.client.chat.completions.create(
            model=self.model, messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
