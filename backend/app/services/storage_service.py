
from typing import Any

from app.config import settings


SUPPORTED_BACKENDS = {"chroma", "postgres"}


def get_storage_backend() -> str:
    """
    Retorna o backend de persistência configurado.

    Falha explicitamente para valores desconhecidos,
    evitando selecionar um armazenamento por engano.
    """
    backend = settings.STORAGE_BACKEND.strip().lower()

    if backend not in SUPPORTED_BACKENDS:
        raise ValueError(
            f"STORAGE_BACKEND inválido: {backend!r}. "
            "Use 'chroma' ou 'postgres'."
        )

    return backend


def get_storage_module() -> Any:
    """
    Importa apenas o serviço de armazenamento selecionado.

    Isso evita carregar o ChromaDB quando a aplicação
    estiver configurada para PostgreSQL.
    """
    backend = get_storage_backend()

    if backend == "postgres":
        from app.services import postgres_vector_service

        return postgres_vector_service

    from app.services import vector_service

    return vector_service


def index_transcript_segments(
    audio_filename: str,
    segments: list,
    owner_user_id: str,
) -> dict:
    """
    Indexa uma gravação para o advogado autenticado.
    """
    if not owner_user_id:
        raise ValueError(
            "O proprietário é obrigatório para indexação."
        )

    storage = get_storage_module()

    return storage.index_transcript_segments(
        audio_filename=audio_filename,
        segments=segments,
        owner_user_id=owner_user_id,
    )


def get_indexed_audio_history(
    owner_user_id: str,
) -> list:
    """
    Recupera somente as gravações do proprietário.
    """
    if not owner_user_id:
        raise ValueError(
            "O proprietário é obrigatório para o histórico."
        )

    storage = get_storage_module()

    return storage.get_indexed_audio_history(
        owner_user_id=owner_user_id,
    )


def search_audio_context(
    query: str,
    n_results: int = 6,
    audio_filter: str | None = None,
    owner_user_id: str | None = None,
) -> list:
    """
    Executa a busca semântica com proprietário obrigatório.
    """
    if not owner_user_id:
        raise ValueError(
            "O proprietário é obrigatório para consultas."
        )

    storage = get_storage_module()

    return storage.search_audio_context(
        query=query,
        n_results=n_results,
        audio_filter=audio_filter,
        owner_user_id=owner_user_id,
    )
