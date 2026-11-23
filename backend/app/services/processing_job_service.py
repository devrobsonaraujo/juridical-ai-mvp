
import uuid
from typing import Any

import psycopg
from psycopg.rows import dict_row

from app.config import settings


ALLOWED_STATUSES = {
    "queued",
    "processing",
    "completed",
    "failed",
}

ALLOWED_SOURCE_TYPES = {"simulation", "media"}


def _validate_uuid(value: str, field: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError(
            f"{field} deve ser um UUID válido."
        ) from exc


def _validate_worker_id(worker_id: str) -> str:
    if not isinstance(worker_id, str) or not worker_id.strip():
        raise ValueError("worker_id é obrigatório.")

    return worker_id.strip()


def _validate_lease_seconds(lease_seconds: int) -> int:
    if (
        not isinstance(lease_seconds, int)
        or isinstance(lease_seconds, bool)
        or not 30 <= lease_seconds <= 3600
    ):
        raise ValueError(
            "lease_seconds deve estar entre 30 e 3600."
        )

    return lease_seconds


def _validate_attempt_token(attempt_token: str | None) -> str:
    return _validate_uuid(attempt_token, "attempt_token")


def _connect():
    if not settings.DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL não está configurada."
        )

    return psycopg.connect(
        settings.DATABASE_URL,
        connect_timeout=10,
        row_factory=dict_row,
        options="-c statement_timeout=30000",
    )


def create_processing_job(
    owner_user_id: str,
    source_type: str = "simulation",
    original_filename: str | None = None,
    storage_path: str | None = None,
) -> dict[str, Any]:
    owner_id = _validate_uuid(
        owner_user_id,
        "owner_user_id",
    )

    if source_type not in ALLOWED_SOURCE_TYPES:
        raise ValueError("source_type inválido.")

    if source_type == "media":
        if not storage_path or not storage_path.strip():
            raise ValueError(
                "Tarefas de mídia precisam de storage_path."
            )

    with _connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO public.processing_jobs (
                    owner_user_id,
                    source_type,
                    original_filename,
                    storage_path
                )
                VALUES (%s, %s, %s, %s)
                RETURNING *
                """,
                (
                    owner_id,
                    source_type,
                    original_filename,
                    storage_path,
                ),
            )
            return cursor.fetchone()


def get_processing_job(
    job_id: str,
    owner_user_id: str,
) -> dict[str, Any] | None:
    validated_job_id = _validate_uuid(
        job_id,
        "job_id",
    )
    owner_id = _validate_uuid(
        owner_user_id,
        "owner_user_id",
    )

    with _connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM public.processing_jobs
                WHERE id = %s
                  AND owner_user_id = %s
                """,
                (validated_job_id, owner_id),
            )
            return cursor.fetchone()


def list_processing_jobs(
    owner_user_id: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    owner_id = _validate_uuid(
        owner_user_id,
        "owner_user_id",
    )

    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or not 1 <= limit <= 100
    ):
        raise ValueError(
            "limit deve estar entre 1 e 100."
        )

    with _connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM public.processing_jobs
                WHERE owner_user_id = %s
                ORDER BY created_at DESC, id DESC
                LIMIT %s
                """,
                (owner_id, limit),
            )
            return cursor.fetchall()


def claim_next_processing_job(
    worker_id: str,
    lease_seconds: int = 300,
    source_type: str = "simulation",
) -> dict[str, Any] | None:
    """
    Reserva atomicamente uma tarefa.

    Por segurança, o padrão é 'simulation'.
    Tarefas de mídia ainda não serão processadas.
    """
    validated_worker_id = _validate_worker_id(worker_id)
    _validate_lease_seconds(lease_seconds)

    if source_type not in ALLOWED_SOURCE_TYPES:
        raise ValueError("source_type inválido.")

    token = str(uuid.uuid4())

    with _connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                WITH next_job AS (
                    SELECT id
                    FROM public.processing_jobs
                    WHERE status = 'queued'
                      AND source_type = %s
                      AND attempts < max_attempts
                    ORDER BY created_at ASC, id ASC
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                UPDATE public.processing_jobs AS job
                SET
                    status = 'processing',
                    progress = 0,
                    attempts = job.attempts + 1,
                    worker_id = %s,
                    attempt_token = %s,
                    lease_expires_at =
                        now() + (%s * interval '1 second'),
                    started_at = now(),
                    finished_at = NULL,
                    error_message = NULL,
                    updated_at = now()
                FROM next_job
                WHERE job.id = next_job.id
                RETURNING job.*
                """,
                (
                    source_type,
                    validated_worker_id,
                    token,
                    lease_seconds,
                ),
            )
            return cursor.fetchone()


def renew_processing_job_lease(
    job_id: str,
    worker_id: str,
    attempt_token: str,
    lease_seconds: int = 300,
) -> dict[str, Any]:
    validated_job_id = _validate_uuid(job_id, "job_id")
    validated_worker_id = _validate_worker_id(worker_id)
    validated_token = _validate_attempt_token(attempt_token)
    _validate_lease_seconds(lease_seconds)

    with _connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE public.processing_jobs
                SET
                    lease_expires_at =
                        now() + (%s * interval '1 second'),
                    updated_at = now()
                WHERE id = %s
                  AND status = 'processing'
                  AND worker_id = %s
                  AND attempt_token = %s
                  AND lease_expires_at > now()
                RETURNING *
                """,
                (
                    lease_seconds,
                    validated_job_id,
                    validated_worker_id,
                    validated_token,
                ),
            )
            result = cursor.fetchone()

    if result is None:
        raise ValueError(
            "Lease inválido, expirado ou pertencente "
            "a outra tentativa."
        )

    return result


def update_processing_job_progress(
    job_id: str,
    worker_id: str,
    attempt_token: str,
    progress: int,
) -> dict[str, Any]:
    validated_job_id = _validate_uuid(job_id, "job_id")
    validated_worker_id = _validate_worker_id(worker_id)
    validated_token = _validate_attempt_token(attempt_token)

    if (
        not isinstance(progress, int)
        or isinstance(progress, bool)
        or not 0 <= progress <= 99
    ):
        raise ValueError(
            "progress deve estar entre 0 e 99."
        )

    with _connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE public.processing_jobs
                SET
                    progress = %s,
                    updated_at = now()
                WHERE id = %s
                  AND status = 'processing'
                  AND worker_id = %s
                  AND attempt_token = %s
                  AND lease_expires_at > now()
                  AND progress <= %s
                RETURNING *
                """,
                (
                    progress,
                    validated_job_id,
                    validated_worker_id,
                    validated_token,
                    progress,
                ),
            )
            result = cursor.fetchone()

    if result is None:
        raise ValueError(
            "Não foi possível atualizar o progresso."
        )

    return result


def complete_processing_job(
    job_id: str,
    worker_id: str,
    media_id: str | None = None,
    attempt_token: str | None = None,
) -> dict[str, Any]:
    validated_job_id = _validate_uuid(job_id, "job_id")
    validated_worker_id = _validate_worker_id(worker_id)

    validated_media_id = (
        _validate_uuid(media_id, "media_id")
        if media_id is not None
        else None
    )

    validated_token = _validate_attempt_token(attempt_token)

    with _connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE public.processing_jobs
                SET
                    status = 'completed',
                    progress = 100,
                    media_id = %s,
                    worker_id = NULL,
                    attempt_token = NULL,
                    lease_expires_at = NULL,
                    error_message = NULL,
                    finished_at = now(),
                    updated_at = now()
                WHERE id = %s
                  AND status = 'processing'
                  AND worker_id = %s
                  AND attempt_token = %s
                  AND lease_expires_at > now()
                RETURNING *
                """,
                (
                    validated_media_id,
                    validated_job_id,
                    validated_worker_id,
                    validated_token,
                ),
            )
            result = cursor.fetchone()

    if result is None:
        raise ValueError(
            "Tarefa não encontrada, lease expirado "
            "ou tentativa não autorizada."
        )

    return result


def fail_processing_job(
    job_id: str,
    worker_id: str,
    error_message: str,
    attempt_token: str | None = None,
) -> dict[str, Any]:
    validated_job_id = _validate_uuid(job_id, "job_id")
    validated_worker_id = _validate_worker_id(worker_id)
    validated_token = _validate_attempt_token(attempt_token)

    # Não armazenar exceções brutas, tokens ou dados jurídicos.
    safe_error = str(error_message).strip()[:500]

    if not safe_error:
        safe_error = "Falha no processamento."

    with _connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE public.processing_jobs
                SET
                    status = 'failed',
                    worker_id = NULL,
                    attempt_token = NULL,
                    lease_expires_at = NULL,
                    error_message = %s,
                    finished_at = now(),
                    updated_at = now()
                WHERE id = %s
                  AND status = 'processing'
                  AND worker_id = %s
                  AND attempt_token = %s
                  AND lease_expires_at > now()
                RETURNING *
                """,
                (
                    safe_error,
                    validated_job_id,
                    validated_worker_id,
                    validated_token,
                ),
            )
            result = cursor.fetchone()

    if result is None:
        raise ValueError(
            "Tarefa não encontrada, lease expirado "
            "ou tentativa não autorizada."
        )

    return result


def recover_expired_processing_jobs(
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    Recupera leases expirados.

    - Se ainda há tentativas: volta para queued.
    - Se esgotou tentativas: passa para failed.

    Não modifica tarefas com lease válido.
    """
    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or not 1 <= limit <= 500
    ):
        raise ValueError("limit deve estar entre 1 e 500.")

    with _connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                WITH expired AS (
                    SELECT id
                    FROM public.processing_jobs
                    WHERE status = 'processing'
                      AND lease_expires_at <= now()
                    ORDER BY lease_expires_at ASC, id ASC
                    FOR UPDATE SKIP LOCKED
                    LIMIT %s
                )
                UPDATE public.processing_jobs AS job
                SET
                    status = CASE
                        WHEN job.attempts < job.max_attempts
                            THEN 'queued'
                        ELSE 'failed'
                    END,
                    progress = CASE
                        WHEN job.attempts < job.max_attempts
                            THEN 0
                        ELSE job.progress
                    END,
                    worker_id = NULL,
                    attempt_token = NULL,
                    lease_expires_at = NULL,
                    error_message = CASE
                        WHEN job.attempts < job.max_attempts
                            THEN NULL
                        ELSE 'Limite de tentativas atingido.'
                    END,
                    started_at = CASE
                        WHEN job.attempts < job.max_attempts
                            THEN NULL
                        ELSE job.started_at
                    END,
                    finished_at = CASE
                        WHEN job.attempts < job.max_attempts
                            THEN NULL
                        ELSE now()
                    END,
                    updated_at = now()
                FROM expired
                WHERE job.id = expired.id
                RETURNING job.*
                """,
                (limit,),
            )
            return cursor.fetchall()


def delete_processing_job(
    job_id: str,
    owner_user_id: str,
) -> bool:
    """
    Remove jobs não ativos do proprietário.

    Não remove arquivos do Storage nem mídias
    indexadas.
    """
    validated_job_id = _validate_uuid(job_id, "job_id")
    owner_id = _validate_uuid(
        owner_user_id,
        "owner_user_id",
    )

    with _connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM public.processing_jobs
                WHERE id = %s
                  AND owner_user_id = %s
                  AND status IN (
                      'queued',
                      'completed',
                      'failed'
                  )
                RETURNING id
                """,
                (validated_job_id, owner_id),
            )
            return cursor.fetchone() is not None
