
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # Projeto
    PROJECT_NAME: str = "Juridical AI MVP"
    VERSION: str = "1.0.0"

    # Groq
    GROQ_API_KEY: str

    # Provedor de IA
    AI_PROVIDER: str = "groq"
    AI_MODEL: str = "openai/gpt-oss-120b"

    # Supabase Auth
    SUPABASE_URL: str
    SUPABASE_PUBLISHABLE_KEY: str

    # PostgreSQL
    DATABASE_URL: str = ""

    # Seleção de armazenamento
    STORAGE_BACKEND: str = "chroma"

    # Embeddings
    EMBEDDING_PROVIDER: str = "local"
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-small"
    EMBEDDING_DIMENSIONS: int = Field(default=384, ge=1)
    EMBEDDING_BATCH_SIZE: int = Field(default=8, ge=1, le=128)

    # Arquivos temporários
    TEMP_DIR: str = "temp_audio"

    # CORS
    CORS_ORIGINS: str = (
        "http://localhost:5173,"
        "http://127.0.0.1:5173"
    )

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    SUPABASE_SERVICE_ROLE_KEY: str = ""
    MEDIA_STORAGE_BUCKET: str = "juridical-media-temp"
    MEDIA_RETENTION_POLICY: str = "delete_after_processing"


settings = Settings()

Path(settings.TEMP_DIR).mkdir(
    parents=True,
    exist_ok=True,
)

