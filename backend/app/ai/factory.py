from app.ai.base import AIProvider
from app.ai.providers.groq_provider import GroqProvider
from app.config import settings


def get_ai_provider() -> AIProvider:
    provider = settings.AI_PROVIDER.strip().lower()
    if provider == "groq":
        return GroqProvider(api_key=settings.GROQ_API_KEY, model=settings.AI_MODEL)
    raise ValueError(f"Provedor de IA não suportado: {provider}")
