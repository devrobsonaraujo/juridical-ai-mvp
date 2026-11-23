
import uuid

import pytest

from app.services.media_storage_service import (
    _safe_extension,
    _validate_storage_path,
    build_media_storage_path,
    upload_media_file,
)


def new_uuid():
    return str(uuid.uuid4())


def test_build_path_isolated_by_owner_and_job():
    owner = new_uuid()
    job = new_uuid()

    path = build_media_storage_path(
        owner,
        job,
        "audiencia.mp4",
    )

    assert path == f"{owner}/{job}/original.mp4"


def test_windows_filename_is_sanitized():
    owner = new_uuid()
    job = new_uuid()

    path = build_media_storage_path(
        owner,
        job,
        r"C:\temp\audiencia.MP4",
    )

    assert path == f"{owner}/{job}/original.mp4"


def test_rejects_unsupported_extension():
    with pytest.raises(ValueError, match="Extensão"):
        _safe_extension("documento.exe")


def test_rejects_invalid_owner():
    with pytest.raises(ValueError, match="UUID"):
        build_media_storage_path(
            "invalid",
            new_uuid(),
            "audiencia.mp4",
        )


def test_rejects_cross_user_path():
    owner_a = new_uuid()
    owner_b = new_uuid()
    job = new_uuid()

    path = build_media_storage_path(
        owner_a,
        job,
        "audiencia.mp4",
    )

    with pytest.raises(ValueError, match="não pertence"):
        _validate_storage_path(
            path,
            owner_b,
            job,
        )


def test_rejects_cross_job_path():
    owner = new_uuid()
    job_a = new_uuid()
    job_b = new_uuid()

    path = build_media_storage_path(
        owner,
        job_a,
        "audiencia.mp4",
    )

    with pytest.raises(ValueError, match="não pertence"):
        _validate_storage_path(
            path,
            owner,
            job_b,
        )


def test_rejects_arbitrary_object_name():
    owner = new_uuid()
    job = new_uuid()

    with pytest.raises(ValueError, match="não permitido"):
        _validate_storage_path(
            f"{owner}/{job}/outro.mp4",
            owner,
            job,
        )


def test_upload_rejects_missing_file():
    with pytest.raises(FileNotFoundError):
        upload_media_file(
            local_file_path="arquivo_inexistente.mp4",
            owner_user_id=new_uuid(),
            job_id=new_uuid(),
            original_filename="audiencia.mp4",
        )


def test_upload_rejects_empty_file(tmp_path):
    empty_file = tmp_path / "empty.mp4"
    empty_file.write_bytes(b"")

    with pytest.raises(ValueError, match="vazio"):
        upload_media_file(
            local_file_path=str(empty_file),
            owner_user_id=new_uuid(),
            job_id=new_uuid(),
            original_filename="empty.mp4",
        )
