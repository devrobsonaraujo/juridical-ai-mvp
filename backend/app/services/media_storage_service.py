
import os
import re
import tempfile
import uuid
from pathlib import Path
from urllib.parse import quote

import httpx

from app.config import settings


MAX_MEDIA_BYTES = 50 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".mkv",
    ".avi",
    ".mp3",
    ".wav",
    ".m4a",
    ".ogg",
    ".webm",
}

BUCKET_NAME_PATTERN = re.compile(
    r"^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$"
)


def _validate_uuid(value: str, field: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError(
            f"{field} deve ser um UUID válido."
        ) from exc


def _validate_retention_policy() -> None:
    if (
        settings.MEDIA_RETENTION_POLICY
        != "delete_after_processing"
    ):
        raise RuntimeError(
            "Política de retenção não suportada neste MVP."
        )


def _validate_storage_config() -> tuple[str, str, str]:
    _validate_retention_policy()

    base_url = settings.SUPABASE_URL.rstrip("/")
    secret = settings.SUPABASE_SERVICE_ROLE_KEY.strip()
    bucket = settings.MEDIA_STORAGE_BUCKET.strip()

    if not base_url.startswith("https://"):
        raise RuntimeError(
            "SUPABASE_URL deve utilizar HTTPS."
        )

    if not secret:
        raise RuntimeError(
            "SUPABASE_SERVICE_ROLE_KEY não configurada."
        )

    if not BUCKET_NAME_PATTERN.fullmatch(bucket):
        raise RuntimeError(
            "MEDIA_STORAGE_BUCKET inválido."
        )

    return base_url, secret, bucket


def _safe_extension(filename: str) -> str:
    if not isinstance(filename, str):
        raise ValueError("Nome de arquivo inválido.")

    normalized = filename.replace("\\", "/")
    name = normalized.rsplit("/", 1)[-1]

    extension = Path(name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            "Extensão de mídia não permitida."
        )

    return extension


def build_media_storage_path(
    owner_user_id: str,
    job_id: str,
    filename: str,
) -> str:
    owner = _validate_uuid(
        owner_user_id,
        "owner_user_id",
    )
    job = _validate_uuid(job_id, "job_id")
    extension = _safe_extension(filename)

    return f"{owner}/{job}/original{extension}"


def _validate_storage_path(
    storage_path: str,
    owner_user_id: str,
    job_id: str,
) -> str:
    if not isinstance(storage_path, str):
        raise ValueError("storage_path inválido.")

    owner = _validate_uuid(
        owner_user_id,
        "owner_user_id",
    )
    job = _validate_uuid(job_id, "job_id")

    prefix = f"{owner}/{job}/"

    if not storage_path.startswith(prefix):
        raise ValueError(
            "A mídia não pertence ao usuário e à tarefa."
        )

    filename = storage_path[len(prefix):]

    if (
        "/" in filename
        or "\\" in filename
        or filename.startswith(".")
    ):
        raise ValueError("storage_path inválido.")

    extension = _safe_extension(filename)

    if filename != f"original{extension}":
        raise ValueError(
            "Nome de objeto não permitido."
        )

    return storage_path



def _object_url(
    storage_path: str,
    authenticated_download: bool = False,
) -> tuple[str, dict[str, str]]:
    base_url, secret, bucket = (
        _validate_storage_config()
    )

    encoded_bucket = quote(bucket, safe="")
    encoded_path = quote(storage_path, safe="/")

    route = (
        "object/authenticated"
        if authenticated_download
        else "object"
    )

    url = (
        f"{base_url}/storage/v1/"
        f"{route}/{encoded_bucket}/{encoded_path}"
    )

    headers = {
        "apikey": secret,
        "Authorization": f"Bearer {secret}",
    }

    return url, headers



def upload_media_file(
    local_file_path: str,
    owner_user_id: str,
    job_id: str,
    original_filename: str,
) -> str:
    """
    Envia um arquivo local para o bucket privado.

    Retorna somente o caminho interno do objeto.
    Não retorna uma URL pública.
    """
    local_path = Path(local_file_path)

    if not local_path.is_file():
        raise FileNotFoundError(
            "Arquivo local não encontrado."
        )

    size = local_path.stat().st_size

    if size <= 0:
        raise ValueError("Arquivo de mídia vazio.")

    if size > MAX_MEDIA_BYTES:
        raise ValueError(
            "Arquivo excede o limite de 50 MiB do MVP."
        )

    storage_path = build_media_storage_path(
        owner_user_id=owner_user_id,
        job_id=job_id,
        filename=original_filename,
    )

    url, headers = _object_url(storage_path)

    headers["Content-Type"] = "application/octet-stream"
    headers["Content-Length"] = str(size)
    headers["x-upsert"] = "false"

    with open(local_path, "rb") as file:
        with httpx.Client(timeout=180.0) as client:
            response = client.post(
                url,
                headers=headers,
                content=file,
            )

    if response.status_code not in (200, 201):
        raise RuntimeError(
            "Não foi possível armazenar a mídia."
        )

    return storage_path


def download_media_file(
    storage_path: str,
    owner_user_id: str,
    job_id: str,
) -> str:
    """
    Baixa a mídia para um arquivo temporário.

    O chamador deve remover o arquivo retornado.
    """
    validated_path = _validate_storage_path(
        storage_path,
        owner_user_id,
        job_id,
    )

    url, headers = _object_url(
    validated_path,
    authenticated_download=True,
)

    extension = Path(validated_path).suffix

    fd, temporary_path = tempfile.mkstemp(
        suffix=extension
    )
    os.close(fd)

    try:
        total_bytes = 0

        with httpx.Client(timeout=180.0) as client:
            with client.stream(
                "GET",
                url,
                headers=headers,
            ) as response:
                if response.status_code != 200:
                    raise RuntimeError(
                        "Não foi possível recuperar a mídia."
                    )

                with open(
                    temporary_path,
                    "wb",
                ) as output:
                    for chunk in response.iter_bytes(
                        chunk_size=1024 * 1024
                    ):
                        total_bytes += len(chunk)

                        if total_bytes > MAX_MEDIA_BYTES:
                            raise ValueError(
                                "Download excedeu o limite permitido."
                            )

                        output.write(chunk)

        if total_bytes == 0:
            raise RuntimeError(
                "O arquivo recuperado está vazio."
            )

        return temporary_path

    except Exception:
        if os.path.isfile(temporary_path):
            os.remove(temporary_path)

        raise


def delete_media_file(
    storage_path: str,
    owner_user_id: str,
    job_id: str,
) -> bool:
    """
    Remove um objeto do bucket privado.

    Retorna True se foi removido ou se já não existe.
    """
    validated_path = _validate_storage_path(
        storage_path,
        owner_user_id,
        job_id,
    )

    url, headers = _object_url(validated_path)

    with httpx.Client(timeout=30.0) as client:
        response = client.delete(
            url,
            headers=headers,
        )

    if response.status_code in (200, 204, 404):
        return True

    raise RuntimeError(
        "Não foi possível excluir a mídia temporária."
    )
