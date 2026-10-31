from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Juridical AI MVP"
    VERSION: str = "1.0.0"
    GROQ_API_KEY: str
    TEMP_DIR: str = "temp_audio"

    # Configuração para carregar o .env independentemente de onde o uvicorn for chamado
    model_config = SettingsConfigDict(
        env_file=os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env")),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Garante que a pasta temporária de áudio exista
os.makedirs(settings.TEMP_DIR, exist_ok=True)