
import math
import uuid
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from app.config import settings
from app.services.embedding_service import (
    get_embedding_service,
)
from app.services.chunking_service import chunk_segments


def _validate_owner(owner_user_id: str) -> str:
    if not isinstance(owner_user_id, str):
        raise ValueError(
            "O identificador do advogado é obrigatório."
        )

    try:
        return str(uuid.UUID(owner_user_id))
    except (ValueError, AttributeError) as exc:
        raise ValueError(
            "Identificador do advogado inválido."
        ) from exc


def _validate_database_config() -> None:
    if not settings.DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL não configurada."
        )


def _vector_literal(vector: list[float]) -> str:
    """
    Converte o embedding para representação pgvector.

    Os valores são validados antes de entrar na consulta.
    """
    if len(vector) != settings.EMBEDDING_DIMENSIONS:
        raise ValueError(
            "Dimensão inválida do vetor."
        )

    values = []

    for value in vector:
        number = float(value)

        if not math.isfinite(number):
            raise ValueError(
                "Embedding contém valor inválido."
            )

        values.append(format(number, ".9g"))

    return "[" + ",".join(values) + "]"


@contextmanager
def _connection():
    """
    Abre uma transação PostgreSQL.

    A transação é confirmada no sucesso
    e revertida automaticamente em caso de erro.
    """
    _validate_database_config()

    with psycopg.connect(
        settings.DATABASE_URL,
        connect_timeout=10,
        row_factory=dict_row,
        options="-c statement_timeout=30000",
    ) as conn:
        # Permite resolver operadores da extensão pgvector.
        with conn.cursor() as cursor:
            cursor.execute(
                "SET LOCAL search_path TO public, extensions"
            )

        yield conn


def index_transcript_segments(
    audio_filename: str,
    segments: list,
    owner_user_id: str,
) -> dict:
    """
    Persiste a mídia, transcrição e embeddings
    com proprietário obrigatório.
    """
    owner_id = _validate_owner(owner_user_id)

    if not isinstance(audio_filename, str):
        raise ValueError("Nome de arquivo inválido.")

    filename = audio_filename.strip()

    if not filename:
        raise ValueError("Nome de arquivo obrigatório.")

    if not isinstance(segments, list):
        raise ValueError("Os segmentos devem ser uma lista.")

    chunks = chunk_segments(
        segments,
        max_words=120,
        overlap_words=25,
    )

    full_text = " ".join(
        str(segment.get("text", "")).strip()
        for segment in segments
        if str(segment.get("text", "")).strip()
    )

    # Geramos embeddings antes de abrir a transação.
    # Isso evita manter uma conexão PostgreSQL aberta
    # durante a execução do modelo.
    embeddings = []

    if chunks:
        embeddings = (
            get_embedding_service().embed_documents(
                [chunk["text"] for chunk in chunks]
            )
        )

    if len(embeddings) != len(chunks):
        raise RuntimeError(
            "Quantidade de embeddings inconsistente."
        )

    media_id = str(uuid.uuid4())

    with _connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO public.media_files (
                    id,
                    owner_user_id,
                    filename,
                    status,
                    full_text,
                    segments_count
                )
                VALUES (
                    %s::uuid,
                    %s::uuid,
                    %s,
                    'processing',
                    %s,
                    %s
                )
                """,
                (
                    media_id,
                    owner_id,
                    filename,
                    full_text,
                    len(segments),
                ),
            )

            for index, (chunk, embedding) in enumerate(
                zip(chunks, embeddings)
            ):
                cursor.execute(
                    """
                    INSERT INTO public.transcript_chunks (
                        media_id,
                        owner_user_id,
                        chunk_index,
                        content,
                        start_seconds,
                        end_seconds,
                        embedding
                    )
                    VALUES (
                        %s::uuid,
                        %s::uuid,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s::extensions.vector
                    )
                    """,
                    (
                        media_id,
                        owner_id,
                        index,
                        chunk["text"],
                        float(chunk["start"]),
                        float(chunk["end"]),
                        _vector_literal(embedding),
                    ),
                )

            cursor.execute(
                """
                UPDATE public.media_files
                SET
                    status = 'completed',
                    updated_at = now()
                WHERE
                    id = %s::uuid
                    AND owner_user_id = %s::uuid
                """,
                (media_id, owner_id),
            )

    return {
        "status": "indexado",
        "chunks_count": len(chunks),
        "media_id": media_id,
    }


def get_indexed_audio_history(
    owner_user_id: str,
) -> list:
    """
    Lista somente as mídias do advogado autenticado.
    """
    owner_id = _validate_owner(owner_user_id)

    with _connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    m.id::text AS media_id,
                    m.filename,
                    COUNT(c.id)::integer AS chunks_count,
                    COALESCE(
                        LEFT(
                            (ARRAY_AGG(c.content ORDER BY c.chunk_index)
                             FILTER (WHERE c.id IS NOT NULL))[1],
                            100
                        ),
                        ''
                    ) AS preview
                FROM public.media_files AS m
                LEFT JOIN public.transcript_chunks AS c
                    ON c.media_id = m.id
                    AND c.owner_user_id = m.owner_user_id
                WHERE
                    m.owner_user_id = %s::uuid
                    AND m.status = 'completed'
                GROUP BY m.id, m.filename, m.created_at
                ORDER BY m.created_at DESC
                """,
                (owner_id,),
            )

            return list(cursor.fetchall())


def search_audio_context(
    query: str,
    n_results: int = 6,
    audio_filter: str | None = None,
    owner_user_id: str | None = None,
) -> list:
    """
    Busca vetorial com filtro obrigatório por advogado.

    O PostgreSQL calcula a distância cosseno entre
    o embedding da pergunta e os trechos armazenados.
    """
    owner_id = _validate_owner(owner_user_id)

    if not isinstance(query, str) or not query.strip():
        raise ValueError(
            "A pergunta não pode estar vazia."
        )

    if not 1 <= n_results <= 20:
        raise ValueError(
            "n_results deve estar entre 1 e 20."
        )

    filename_filter = None

    if (
        audio_filter
        and audio_filter not in (
            "Todos os Áudios",
            "Todas as Mídias",
        )
    ):
        filename_filter = audio_filter

    # Verifica primeiro se o usuário possui trechos.
    # Evita carregar o modelo de embeddings quando
    # não existem dados a pesquisar.
    with _connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM public.transcript_chunks AS c
                    JOIN public.media_files AS m
                        ON m.id = c.media_id
                        AND m.owner_user_id = c.owner_user_id
                    WHERE
                        c.owner_user_id = %s::uuid
                        AND m.status = 'completed'
                        AND (
                            %s::text IS NULL
                            OR m.filename = %s::text
                        )
                ) AS has_chunks
                """,
                (
                    owner_id,
                    filename_filter,
                    filename_filter,
                ),
            )

            row = cursor.fetchone()

            if not row or not row["has_chunks"]:
                return []

    embedding = (
        get_embedding_service().embed_query(query)
    )

    vector_value = _vector_literal(embedding)

    with _connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    c.content AS text,
                    c.start_seconds AS start,
                    c.end_seconds AS "end",
                    m.filename AS audio_filename,
                    m.id::text AS media_id
                FROM public.transcript_chunks AS c
                JOIN public.media_files AS m
                    ON m.id = c.media_id
                    AND m.owner_user_id = c.owner_user_id
                WHERE
                    c.owner_user_id = %s::uuid
                    AND m.status = 'completed'
                    AND (
                        %s::text IS NULL
                        OR m.filename = %s::text
                    )
                ORDER BY
                    c.embedding
                    OPERATOR(extensions.<=>)
                    %s::extensions.vector
                LIMIT %s
                """,
                (
                    owner_id,
                    filename_filter,
                    filename_filter,
                    vector_value,
                    n_results,
                ),
            )

            rows = cursor.fetchall()

    return [
        {
            "text": row["text"],
            "start": float(row["start"]),
            "end": float(row["end"]),
            "audio_filename": row["audio_filename"],
            "media_id": row["media_id"],
        }
        for row in rows
    ]
