from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Juridical AI MVP"
    VERSION: str = "1.0.0"
    GROQ_API_KEY: str  # Chave centralizada da Groq

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()