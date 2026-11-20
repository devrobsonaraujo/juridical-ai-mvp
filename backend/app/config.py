
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Diretório raiz do projeto juridical-ai-mvp
BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # Informações do projeto
    PROJECT_NAME: str = "Juridical AI MVP"
    VERSION: str = "1.0.0"

    # Credenciais
    GROQ_API_KEY: str

    # Configurações de IA - Etapa 4.1
    AI_PROVIDER: str = "groq"
    AI_MODEL: str = "openai/gpt-oss-120b"

    # Diretório temporário
    TEMP_DIR: str = "temp_audio"

    # Carrega o .env na raiz do projeto
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

# Garante que a pasta temporária exista
Path(settings.TEMP_DIR).mkdir(
    parents=True,
    exist_ok=True,
)
